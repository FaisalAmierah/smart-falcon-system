from src.models.user import db
from datetime import datetime
import json

class Wallet(db.Model):
    __tablename__ = 'wallets'
    
    id = db.Column(db.Integer, primary_key=True)
    wallet_unique_id = db.Column(db.String(50), unique=True, nullable=False)
    wallet_type = db.Column(db.String(20), nullable=False)  # KOL or New Wallet
    wallet_number = db.Column(db.Integer, nullable=False)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total_calls = db.Column(db.Integer, default=0)
    successful_calls = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='ACTIVE')
    
    def __repr__(self):
        return f'<Wallet {self.wallet_unique_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'wallet_unique_id': self.wallet_unique_id,
            'wallet_type': self.wallet_type,
            'wallet_number': self.wallet_number,
            'date_added': self.date_added.isoformat() if self.date_added else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'total_calls': self.total_calls,
            'successful_calls': self.successful_calls,
            'success_rate': self.success_rate,
            'status': self.status
        }

class Signal(db.Model):
    __tablename__ = 'signals'
    
    id = db.Column(db.Integer, primary_key=True)
    signal_id = db.Column(db.String(50), unique=True, nullable=False)
    contract_address = db.Column(db.String(100), nullable=False)
    signal_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    token_name = db.Column(db.String(100))
    total_wallets_involved = db.Column(db.Integer, default=0)
    wallets_details = db.Column(db.Text)  # JSON string
    initial_ath_usd = db.Column(db.Float, default=0.0)
    final_ath_usd = db.Column(db.Float, default=0.0)
    profit_multiplier = db.Column(db.Float, default=0.0)
    performance_status = db.Column(db.String(20), default='PENDING')  # PENDING, SUCCESS, FAILURE
    evaluation_complete = db.Column(db.Boolean, default=False)
    decision = db.Column(db.String(20))  # BUY, STRONG_BUY, IGNORE
    confidence_score = db.Column(db.Float, default=0.0)
    decision_reasons = db.Column(db.Text)  # JSON string
    
    def __repr__(self):
        return f'<Signal {self.signal_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'signal_id': self.signal_id,
            'contract_address': self.contract_address,
            'signal_time': self.signal_time.isoformat() if self.signal_time else None,
            'token_name': self.token_name,
            'total_wallets_involved': self.total_wallets_involved,
            'wallets_details': json.loads(self.wallets_details) if self.wallets_details else [],
            'initial_ath_usd': self.initial_ath_usd,
            'final_ath_usd': self.final_ath_usd,
            'profit_multiplier': self.profit_multiplier,
            'performance_status': self.performance_status,
            'evaluation_complete': self.evaluation_complete,
            'decision': self.decision,
            'confidence_score': self.confidence_score,
            'decision_reasons': json.loads(self.decision_reasons) if self.decision_reasons else []
        }

class SignalWalletLink(db.Model):
    __tablename__ = 'signal_wallet_links'
    
    id = db.Column(db.Integer, primary_key=True)
    link_id = db.Column(db.String(50), unique=True, nullable=False)
    signal_id = db.Column(db.String(50), db.ForeignKey('signals.signal_id'), nullable=False)
    wallet_unique_id = db.Column(db.String(50), db.ForeignKey('wallets.wallet_unique_id'), nullable=False)
    mc_at_buy = db.Column(db.Float, default=0.0)
    
    # Relationships
    signal = db.relationship('Signal', backref=db.backref('wallet_links', lazy=True))
    wallet = db.relationship('Wallet', backref=db.backref('signal_links', lazy=True))
    
    def __repr__(self):
        return f'<SignalWalletLink {self.link_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'link_id': self.link_id,
            'signal_id': self.signal_id,
            'wallet_unique_id': self.wallet_unique_id,
            'mc_at_buy': self.mc_at_buy
        }

class TelegramMessage(db.Model):
    __tablename__ = 'telegram_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.String(50), unique=True, nullable=False)
    channel_type = db.Column(db.String(20), nullable=False)  # kol_track, phanes_nf, phanes_15m
    message_text = db.Column(db.Text, nullable=False)
    received_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    processing_result = db.Column(db.Text)  # JSON string for processing results
    
    def __repr__(self):
        return f'<TelegramMessage {self.message_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'message_id': self.message_id,
            'channel_type': self.channel_type,
            'message_text': self.message_text,
            'received_time': self.received_time.isoformat() if self.received_time else None,
            'processed': self.processed,
            'processing_result': json.loads(self.processing_result) if self.processing_result else {}
        }

class SystemConfig(db.Model):
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(50), unique=True, nullable=False)
    config_value = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemConfig {self.config_key}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'config_key': self.config_key,
            'config_value': self.config_value,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

