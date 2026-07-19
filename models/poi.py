from datetime import datetime
from extensions import db

class POI(db.Model):
    __tablename__ = 'pois'
    
    id = db.Column(db.Integer, primary_key=True)
    destination = db.Column(db.String(255), unique=True, index=True, nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    poi_data = db.Column(db.JSON, nullable=False)  # Stores categorized POI details
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        """Serialize POI details."""
        return {
            'id': self.id,
            'destination': self.destination,
            'lat': self.lat,
            'lon': self.lon,
            'poi_data': self.poi_data,
            'updated_at': self.updated_at.isoformat()
        }
