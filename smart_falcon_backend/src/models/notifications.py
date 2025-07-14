from src.models.user import db
from datetime import datetime
import json

class NotificationMessage(db.Model):
    __tablename__ = 'notification_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    message_text = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(50), default='signal')  # signal, notification, test
    sent_successfully = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'message_text': self.message_text,
            'message_type': self.message_type,
            'sent_successfully': self.sent_successfully,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

