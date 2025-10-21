from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import os
import re
from markupsafe import Markup
from zoneinfo import ZoneInfo


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()


def create_app() -> Flask:
    load_dotenv()

    app = Flask(__name__, template_folder="templates", static_folder="static")

    app.config.from_object("config.Config")

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.account import account_bp
    from .routes.exchange import exchange_bp
    from .routes.tourism import tourism_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(account_bp)
    from .routes.messages import messages_bp
    app.register_blueprint(exchange_bp)
    app.register_blueprint(messages_bp)
    from .routes.reviews import reviews_bp
    from .routes.bookings import bookings_bp
    app.register_blueprint(tourism_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(bookings_bp)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    # Ensure models are imported so Flask-Login user_loader is registered
    from .models import user as _user  # noqa: F401

    @app.before_request
    def _inject_unread_counter():
        # lightweight unread count for the navbar badge
        try:
            from flask import g
            from sqlalchemy import select
            from .models import Message
            if hasattr(login_manager, 'user_callback') and getattr(login_manager._load_user(), 'is_authenticated', False):
                user = login_manager._load_user()
                from . import db
                cnt = db.session.execute(
                    select(db.func.count(Message.id)).where(Message.receiver_id == user.id, Message.is_read.is_(False))
                ).scalar() or 0
                g.unread_count = cnt
        except Exception:
            # avoid breaking requests if DB is not reachable for some reason
            pass

    # Jinja filter: linkify urls (used for platform notifications)
    _url_re = re.compile(r"(https?://[\w\-./?=&%#:+]+)")

    def linkify(text: str) -> Markup:
        if not text:
            return Markup("")
        escaped = Markup.escape(text)
        return Markup(_url_re.sub(r'<a href="\1" target="_blank" rel="noopener">\1</a>', str(escaped)))

    app.jinja_env.filters["linkify"] = linkify

    # media filter: converts stored relative paths (uploads/..) to full static URL
    from flask import url_for

    def media(src: str):
        if not src:
            return ""
        if src.startswith("http") or src.startswith("data:"):
            return src
        return url_for("static", filename=src)

    app.jinja_env.filters["media"] = media

    # datetime formatting filter with timezone (default Europe/Moscow)
    def format_dt(value, fmt: str = "%d.%m.%Y %H:%M", tz_name: str | None = None) -> Markup:
        if not value:
            return Markup("")
        try:
            tz = ZoneInfo(tz_name or os.getenv("APP_TZ", "Europe/Moscow"))
        except Exception:
            tz = None
        # Assume stored timestamps are UTC naive
        dt = value
        try:
            utc = ZoneInfo("UTC")
            if getattr(dt, "tzinfo", None) is None:
                dt = dt.replace(tzinfo=utc)
            if tz:
                dt = dt.astimezone(tz)
        except Exception:
            pass
        return Markup(dt.strftime(fmt))

    app.jinja_env.filters["format_dt"] = format_dt

    return app

