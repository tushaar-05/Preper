from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_compress import Compress

from datetime import timedelta, timezone

db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
compress = Compress()

# Global IST Timezone
IST = timezone(timedelta(hours=5, minutes=30))
