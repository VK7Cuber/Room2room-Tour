import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

    # Database
    DB_USER = os.getenv("POSTGRES_USER", "postgres")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "SpeedcubingVK7")
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("POSTGRES_PORT", "5434")
    DB_NAME = os.getenv("POSTGRES_DB", "Room2roomTourDatabase")

    _db_url = os.getenv(
        "DATABASE_URL",
        f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    )
    # Allow passing asyncpg URL; convert to sync driver for Flask-SQLAlchemy
    if _db_url.startswith("postgresql+asyncpg://"):
        _db_url = _db_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail (placeholder settings)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 25))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "false").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@room2room.local")

    # Media storage (S3-compatible object storage recommended for Render)
    # If S3_BUCKET is set, uploads will be stored in object storage; otherwise local filesystem is used.
    S3_BUCKET = os.getenv("S3_BUCKET", "")
    S3_REGION = os.getenv("S3_REGION", "eu-central-1")
    S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "")  # e.g. https://storage.yandexcloud.net
    S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID", "")
    S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY", "")
    # Public base URL for serving objects (CDN or bucket website). If empty, SDK URL will be used.
    S3_PUBLIC_URL = os.getenv("S3_PUBLIC_URL", "")  # e.g. https://<bucket>.storage.yandexcloud.net
    # Whether to attempt deleting objects from storage when users remove photos
    S3_DELETE_ENABLED = os.getenv("S3_DELETE_ENABLED", "true").lower() == "true"
    # Whether to set ACL=public-read on upload (disable if bucket uses policy-only public)
    S3_SET_PUBLIC_ACL = os.getenv("S3_SET_PUBLIC_ACL", "true").lower() == "true"
    # Addressing style for custom endpoints: 'path' works well with Yandex/other S3-compatible services
    S3_ADDRESSING_STYLE = os.getenv("S3_ADDRESSING_STYLE", "path")

    # App timezone for displaying naive UTC timestamps
    APP_TZ = os.getenv("APP_TZ", "Europe/Moscow")

