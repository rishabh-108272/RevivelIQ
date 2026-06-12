from abc import ABC, abstractmethod
from typing import Dict, Any
from sqlalchemy.orm import Session

class BaseAgent(ABC):
    """
    Abstract Base Class for all ReviveIQ decision intelligence agents.
    Defines signature patterns for model executions.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Returns agent registration name."""
        pass
        
    @abstractmethod
    def run(self, db: Session, customer_id: int, **kwargs) -> Dict[str, Any]:
        """
        Executes intelligence logic for a given customer.
        Returns dictionary containing scores, telemetry, and explanations.
        """
        pass
