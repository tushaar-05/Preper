from app.extensions import db
from datetime import datetime

class SiteConfig(db.Model):
    __tablename__ = 'site_config'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_val(key, default=None):
        config = SiteConfig.query.filter_by(key=key).first()
        return config.value if config else default

    @staticmethod
    def set_val(key, value, description=None):
        config = SiteConfig.query.filter_by(key=key).first()
        if not config:
            config = SiteConfig(key=key, value=value, description=description)
            db.session.add(config)
        else:
            config.value = value
            if description:
                config.description = description
        db.session.commit()
