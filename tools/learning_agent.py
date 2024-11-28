from dataclasses import dataclass
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

@dataclass
class Experience:
    """Stored experience for learning"""
    task_type: str
    input_state: Dict
    action_taken: Dict
    outcome: Dict
    performance_metrics: Dict
    timestamp: datetime

class LearningAgent:
    """Agent that learns from past experiences"""
    
    def __init__(self):
        self.experiences: List[Experience] = []
        self.success_patterns: Dict = {}
        self.failure_patterns: Dict = {}
        
    async def learn_from_experience(self, experience: Experience):
        """Learn from new experience"""
        try:
            # Store experience
            self.experiences.append(experience)
            
            # Analyze patterns
            if experience.outcome.get("success", False):
                await self._update_success_patterns(experience)
            else:
                await self._update_failure_patterns(experience)
                
            # Prune old experiences
            if len(self.experiences) > 1000:
                self.experiences = self.experiences[-1000:]
                
        except Exception as e:
            logger.error(f"Learning failed: {e}")
            raise
            
    async def get_recommendation(self, task_type: str, state: Dict) -> Optional[Dict]:
        """Get recommendation based on past experiences"""
        try:
            # Find similar experiences
            similar = [
                exp for exp in self.experiences
                if exp.task_type == task_type and
                self._similarity(exp.input_state, state) > 0.8
            ]
            
            if not similar:
                return None
                
            # Get best performing action
            similar.sort(key=lambda x: x.performance_metrics.get("score", 0))
            best = similar[-1]
            
            return {
                "recommended_action": best.action_taken,
                "confidence": self._calculate_confidence(best),
                "similar_experiences": len(similar)
            }
            
        except Exception as e:
            logger.error(f"Recommendation failed: {e}")
            raise 