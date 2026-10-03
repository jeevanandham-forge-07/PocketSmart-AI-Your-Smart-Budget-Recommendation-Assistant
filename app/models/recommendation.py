import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class RecommendationRecord(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    planner_type = Column(String(50), nullable=False, index=True)  # 'home', 'party', 'jewelry'
    title = Column(String(255), nullable=False)
    user_budget = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    
    # Store raw json input parameters & full response
    input_data = Column(Text, nullable=False)  # JSON string
    result_summary = Column(Text, nullable=False)  # JSON string of items & breakdown
    
    total_estimated_cost = Column(Float, nullable=False)
    remaining_budget = Column(Float, nullable=False)
    outfit_image_path = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="recommendations")

    @property
    def parsed_input(self) -> dict:
        try:
            return json.loads(self.input_data)
        except Exception:
            return {}

    @property
    def parsed_result(self) -> dict:
        try:
            return json.loads(self.result_summary)
        except Exception:
            return {}

    def __repr__(self):
        return f"<RecommendationRecord id={self.id} planner={self.planner_type} budget={self.user_budget}>"
