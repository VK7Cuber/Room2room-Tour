import os, uuid
from flask import current_app
from werkzeug.utils import secure_filename

def normalize_database_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    return url


def get_or_create_platform_user(db, User):
    """Return a persistent 'platform bot' user used for system notifications."""
    platform_email = "system@room2room.local"
    user = db.session.execute(db.select(User).where(User.email == platform_email)).scalar_one_or_none()
    if user:
        # Update avatar if not set
        if not user.avatar:
            user.avatar = "images/Room2roomTour_logo.svg"
            db.session.commit()
        return user
    user = User(username="Room2room Bot", email=platform_email, is_verified=True, is_active=True)
    # Set an unusable password
    user.set_password("!disabled-platform-bot!")
    # Set logo as avatar
    user.avatar = "images/Room2roomTour_logo.svg"
    db.session.add(user)
    db.session.commit()
    return user

def save_image(file_storage, subdir: str = "uploads") -> str:
    """Save uploaded image to static/subdir and return relative path for url_for('static')."""
    if not file_storage or not getattr(file_storage, 'filename', ''):
        return ""
    filename = secure_filename(file_storage.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in {'.png', '.jpg', '.jpeg', '.webp'}:
        return ""
    new_name = f"{uuid.uuid4().hex}{ext}"
    folder = os.path.join(current_app.static_folder, subdir)
    os.makedirs(folder, exist_ok=True)
    save_path = os.path.join(folder, new_name)
    file_storage.save(save_path)
    return f"{subdir}/{new_name}"

def delete_media_file(rel_path: str) -> None:
    """Delete file by relative path under static folder; ignore errors."""
    if not rel_path:
        return
    try:
        base = current_app.static_folder
        abs_path = os.path.join(base, rel_path)
        if os.path.isfile(abs_path):
            os.remove(abs_path)
    except Exception:
        # silently ignore any filesystem issues
        pass


