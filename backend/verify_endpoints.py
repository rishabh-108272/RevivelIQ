import httpx
import json

BASE_URL = "http://localhost:8000"

def verify():
    print("Connecting to backend...")
    client = httpx.Client()
    
    # 1. Login
    login_payload = {
        "email": "rishabhverma3648@gmail.com",
        "password": "admin123"
    }
    
    res = client.post(f"{BASE_URL}/api/auth/login", json=login_payload)
    if res.status_code != 200:
        print(f"Login failed! Status: {res.status_code}, Body: {res.text}")
        return
        
    login_data = res.json()
    token = login_data["access_token"]
    print("Login successful! Token acquired.")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 2. Reseed Database to trigger campaign generation and crisis alerts
    print("Triggering database reseed & metrics sync (this will run the multi-agent pipeline)...")
    res = client.post(f"{BASE_URL}/api/analytics/reseed", headers=headers, timeout=60.0)
    print(f"Reseed status: {res.status_code}, Response: {res.text}")
    
    # 3. Verify campaigns list
    print("Fetching campaigns...")
    res = client.get(f"{BASE_URL}/api/campaigns", headers=headers)
    print(f"Get campaigns status: {res.status_code}")
    if res.status_code == 200:
        campaigns = res.json()
        print(f"Retrieved {len(campaigns)} campaigns.")
        if campaigns:
            print("First campaign details:")
            print(f"- Customer: {campaigns[0]['customer_name']}")
            print(f"- Net Recovery Value: ${campaigns[0]['net_recovery_value']}")
            print(f"- Timeline Steps: {len(campaigns[0]['outreach_timeline'])}")
            
    # 4. Verify crisis alerts
    print("Fetching crisis alerts...")
    res = client.get(f"{BASE_URL}/api/alerts", headers=headers)
    print(f"Get alerts status: {res.status_code}")
    if res.status_code == 200:
        alerts = res.json()
        print(f"Retrieved {len(alerts)} active alerts.")
        for a in alerts[:3]:
            print(f"- [{a['severity']}] {a['title']}: {a['root_cause']} (Confidence: {a['confidence']*100:.0f}%)")

    # 5. Verify board report
    print("Fetching Board Report (Markdown)...")
    res = client.get(f"{BASE_URL}/api/reports/board?format=markdown", headers=headers)
    print(f"Board report status: {res.status_code}")
    if res.status_code == 200:
        print("Board Report (First 300 chars):")
        print(res.text[:300] + "...")

    # 6. Verify organization simulator
    print("Testing organization simulation...")
    sim_payload = {"scenario": "resolve_high"}
    res = client.post(f"{BASE_URL}/api/simulations/organization", json=sim_payload, headers=headers)
    print(f"Org simulation status: {res.status_code}")
    if res.status_code == 200:
        sim_data = res.json()
        print("Simulation result:")
        print(f"- Scenario: {sim_data['scenario']}")
        print(f"- Projected Churn Reduction: {sim_data['projected_churn_reduction']}%")
        print(f"- Protected Revenue: ${sim_data['projected_revenue_protected']}")
        print(f"- Health Score Boost: +{sim_data['projected_health_score_improvement']} pts")
        print(f"- Explanation: {sim_data['explanation']}")

if __name__ == "__main__":
    verify()
