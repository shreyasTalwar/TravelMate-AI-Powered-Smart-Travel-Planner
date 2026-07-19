from datetime import datetime
from extensions import db

class SafetyAssessment(db.Model):
    __tablename__ = 'safety_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    destination = db.Column(db.String(255), unique=True, index=True, nullable=False)
    safety_score = db.Column(db.Integer, nullable=False)  # 1 to 5 scale
    safety_data = db.Column(db.JSON, nullable=False)       # JSON data: neighborhoods, tips, hotlines, etc.
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        """Serialize safety details."""
        return {
            'id': self.id,
            'destination': self.destination,
            'safety_score': self.safety_score,
            'safety_data': self.safety_data,
            'updated_at': self.updated_at.isoformat()
        }
