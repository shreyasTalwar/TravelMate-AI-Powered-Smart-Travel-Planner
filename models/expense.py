from datetime import datetime
from extensions import db

class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id', ondelete='CASCADE'), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 'Hotel', 'Transport', 'Food', 'Activities', 'Shopping', 'Emergency Fund'
    amount = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    description = db.Column(db.String(255), nullable=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to trip
    trip = db.relationship('Trip', backref=db.backref('expenses', lazy=True, cascade='all, delete-orphan'))

    def to_dict(self):
        """Serialize expense details."""
        return {
            'id': self.id,
            'trip_id': self.trip_id,
            'category': self.category,
            'amount': float(self.amount),
            'description': self.description,
            'date': self.date.isoformat(),
            'created_at': self.created_at.isoformat()
        }
