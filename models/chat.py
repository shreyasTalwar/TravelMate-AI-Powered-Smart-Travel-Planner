from datetime import datetime
from extensions import db

class TripMember(db.Model):
    __tablename__ = 'trip_members'
    
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='collaborator')  # 'owner', 'collaborator'
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    trip = db.relationship('Trip', backref=db.backref('members', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('joined_trips', lazy=True, cascade='all, delete-orphan'))

    def to_dict(self):
        """Serialize member details."""
        return {
            'id': self.id,
            'trip_id': self.trip_id,
            'user_id': self.user_id,
            'role': self.role,
            'joined_at': self.joined_at.isoformat()
        }

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    trip = db.relationship('Trip', backref=db.backref('messages', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('messages', lazy=True, cascade='all, delete-orphan'))

    def to_dict(self):
        """Serialize message details."""
        return {
            'id': self.id,
            'trip_id': self.trip_id,
            'user_id': self.user_id,
            'username': self.user.name,
            'message': self.message,
            'created_at': self.created_at.isoformat()
        }
