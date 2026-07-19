from datetime import datetime
from extensions import db

class Trip(db.Model):
    __tablename__ = 'trips'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    destination = db.Column(db.String(255), nullable=False)
    budget = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    travellers = db.Column(db.Integer, nullable=False, default=1)
    interests = db.Column(db.JSON, nullable=True)  # List of interests, e.g., ["adventure", "food"]
    status = db.Column(db.String(50), nullable=False, default='planned')  # 'planned', 'completed', 'cancelled'
    invite_code = db.Column(db.String(6), unique=True, index=True, nullable=True)  # Invite code for group sharing
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to user
    user = db.relationship('User', backref=db.backref('trips', lazy=True, cascade='all, delete-orphan'))

    def to_dict(self):
        """Serialize trip details."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'destination': self.destination,
            'budget': float(self.budget),
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'travellers': self.travellers,
            'interests': self.interests,
            'status': self.status,
            'invite_code': self.invite_code,
            'created_at': self.created_at.isoformat()
        }
