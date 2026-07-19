from datetime import datetime
from extensions import db

class Itinerary(db.Model):
    __tablename__ = 'itineraries'
    
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id', ondelete='CASCADE'), nullable=False)
    ai_itinerary = db.Column(db.JSON, nullable=False)  # Stores structured itinerary JSON
    version = db.Column(db.Integer, nullable=False, default=1)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to trip
    trip = db.relationship('Trip', backref=db.backref('itineraries', lazy=True, cascade='all, delete-orphan'))

    def to_dict(self):
        """Serialize itinerary details."""
        return {
            'id': self.id,
            'trip_id': self.trip_id,
            'ai_itinerary': self.ai_itinerary,
            'version': self.version,
            'generated_at': self.generated_at.isoformat()
        }
