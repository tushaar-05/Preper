from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_compress import Compress

db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
compress = Compress()
