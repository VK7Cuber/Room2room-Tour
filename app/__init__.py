from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import os


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
    app.register_blueprint(tourism_bp)
    app.register_blueprint(reviews_bp)

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

    return app

