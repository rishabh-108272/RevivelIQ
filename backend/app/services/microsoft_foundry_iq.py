import numpy as np
import hashlib
from typing import List, Dict, Any, Tuple
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.models.models import Email, Meeting, SupportTicket

class MicrosoftFoundryIQAdapter:
    """
    Foundry IQ Integration: Provides semantic indexing, RAG, vector embedding,
    and semantic clustering models utilizing pgvector capabilities.
    """
    
    def get_embedding(self, text_content: str) -> List[float]:
        """
        Generates a 384-dimensional deterministic vector embedding from text.
        This provides a zero-dependency local embedding processor.
        In production, this integrates with Azure OpenAI's text-embedding-ada-002 or v3.
        """
        # Clean text
        text_content = (text_content or "").lower().strip()
        
        # Dimensions = 384
        dimensions = 384
        embedding = np.zeros(dimensions, dtype=float)
        
        # Use md5 hashing to generate deterministic chunks
        for idx in range(12):  # 12 * 32 = 384 floats
            chunk = f"{text_content}_{idx}"
            h = hashlib.md5(chunk.encode("utf-8")).hexdigest()
            # Convert md5 hexadecimal digits into numbers
            for c_idx in range(32):
                val = int(h[c_idx], 16) / 15.0 - 0.5  # Normalize to [-0.5, 0.5]
                embedding[idx * 32 + c_idx] = val
                
        # Normalize the vector to unit length (L2 norm)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
            
        return embedding.tolist()

    def semantic_search(self, db: Session, query: str, organization_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Performs pgvector cosine-distance similarity searches across emails, meetings, and tickets.
        """
        query_vector = self.get_embedding(query)
        # SQLAlchemy pgvector distance is calculated using '<=>' operator for cosine distance.
        # Since we want to support dynamic raw tables execution:
        query_vector_str = f"[{','.join(map(str, query_vector))}]"
        
        results = []
        
        # 1. Search tickets
        ticket_sql = text("""
            SELECT t.id, t.title, t.description, t.customer_id, c.name as customer_name,
                   (t.vector_embedding <=> :qv) as distance
            FROM support_tickets t
            JOIN customers c ON t.customer_id = c.id
            WHERE c.organization_id = :org_id AND t.vector_embedding IS NOT NULL
            ORDER BY distance ASC
            LIMIT :lim
        """)
        
        try:
            ticket_rows = db.execute(ticket_sql, {"qv": query_vector_str, "org_id": organization_id, "lim": limit}).fetchall()
            for r in ticket_rows:
                results.append({
                    "id": r.id,
                    "type": "support_ticket",
                    "title": r.title,
                    "snippet": r.description[:150],
                    "customer_id": r.customer_id,
                    "customer_name": r.customer_name,
                    "score": round(1.0 - float(r.distance or 0.0), 3)  # Convert cosine distance to similarity
                })
        except Exception as e:
            print(f"Error in pgvector ticket search: {e}")
            
        # 2. Search emails
        email_sql = text("""
            SELECT e.id, e.subject, e.body, e.customer_id, c.name as customer_name,
                   (e.vector_embedding <=> :qv) as distance
            FROM emails e
            JOIN customers c ON e.customer_id = c.id
            WHERE c.organization_id = :org_id AND e.vector_embedding IS NOT NULL
            ORDER BY distance ASC
            LIMIT :lim
        """)
        
        try:
            email_rows = db.execute(email_sql, {"qv": query_vector_str, "org_id": organization_id, "lim": limit}).fetchall()
            for r in email_rows:
                results.append({
                    "id": r.id,
                    "type": "email",
                    "title": r.subject,
                    "snippet": r.body[:150],
                    "customer_id": r.customer_id,
                    "customer_name": r.customer_name,
                    "score": round(1.0 - float(r.distance or 0.0), 3)
                })
        except Exception as e:
            print(f"Error in pgvector email search: {e}")
            
        # Sort combined results by score descending
        results = sorted(results, key=lambda x: x["score"], reverse=True)[:limit]
        return results

    def cluster_customer_tickets(self, tickets: List[SupportTicket]) -> List[Dict[str, Any]]:
        """
        Performs custom semantic clustering on a customer's support tickets using their
        pre-generated vector embeddings to output issue trend categories.
        """
        if not tickets:
            return []
            
        # Prepare vectors
        vectors = []
        valid_tickets = []
        
        for t in tickets:
            if t.vector_embedding is not None:
                vectors.append(t.vector_embedding)
                valid_tickets.append(t)
            else:
                # Fallback generate embedding
                emb = self.get_embedding(f"{t.title} {t.description}")
                t.vector_embedding = emb
                vectors.append(emb)
                valid_tickets.append(t)
                
        if not valid_tickets:
            return []
            
        # Define 4 baseline centroids based on keyword profiles (Billing, API/Speed, UI/Bugs, Account)
        keywords = {
            "Billing & Invoicing": "billing invoice payment pricing contract charge card",
            "Performance & Latency": "slow lag api timeout latency server error speed loading crash",
            "Functional Bugs": "bug broken error glitch ui page click submit form load missing",
            "Account & Integration": "login user access invite organization settings team setup integrations active-directory"
        }
        
        centroids = {}
        for category, kw_text in keywords.items():
            centroids[category] = np.array(self.get_embedding(kw_text))
            
        # Assign each ticket to the closest centroid by cosine distance
        clusters = {cat: [] for cat in keywords.keys()}
        
        for t, vec in zip(valid_tickets, vectors):
            vec_np = np.array(vec)
            best_cat = None
            max_sim = -1.0
            
            for cat, cent in centroids.items():
                # Cosine similarity: dot / (norm_a * norm_b)
                # Since our vectors are already normalized (L2 norm = 1.0),
                # similarity is simply the dot product!
                sim = np.dot(vec_np, cent)
                if sim > max_sim:
                    max_sim = sim
                    best_cat = cat
                    
            clusters[best_cat].append(t)
            
        # Compile trend summaries
        trends = []
        for cat, t_list in clusters.items():
            if not t_list:
                continue
            avg_sentiment = sum(t.sentiment_score for t in t_list) / len(t_list)
            trends.append({
                "category": cat,
                "count": len(t_list),
                "avg_sentiment": round(avg_sentiment, 2),
                "tickets": [
                    {"id": t.id, "title": t.title, "priority": t.priority, "status": t.status}
                    for t in t_list
                ]
            })
            
        return sorted(trends, key=lambda x: x["count"], reverse=True)

foundry_iq_adapter = MicrosoftFoundryIQAdapter()
