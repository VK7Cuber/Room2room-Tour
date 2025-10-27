import os, uuid, io
from flask import current_app
from werkzeug.utils import secure_filename
from typing import Optional

_S3_CLIENT = None

def _get_s3_client():
    """Create and cache boto3 client if S3 is configured."""
    global _S3_CLIENT
    cfg = current_app.config
    bucket = cfg.get("S3_BUCKET")
    if not bucket:
        return None
    if _S3_CLIENT is not None:
        return _S3_CLIENT
    try:
        import boto3  # type: ignore

        kwargs = {}
        if cfg.get("S3_ENDPOINT_URL"):
            kwargs["endpoint_url"] = cfg["S3_ENDPOINT_URL"]
        if cfg.get("S3_REGION"):
            kwargs["region_name"] = cfg["S3_REGION"]
        if cfg.get("S3_ACCESS_KEY_ID") and cfg.get("S3_SECRET_ACCESS_KEY"):
            kwargs["aws_access_key_id"] = cfg["S3_ACCESS_KEY_ID"]
            kwargs["aws_secret_access_key"] = cfg["S3_SECRET_ACCESS_KEY"]
        # forcing addressing style if provided (useful for Vercel + custom endpoint)
        addressing = cfg.get("S3_ADDRESSING_STYLE")
        if addressing:
            kwargs.setdefault("config", boto3.session.Config(s3={"addressing_style": addressing}))
        _S3_CLIENT = boto3.client("s3", **kwargs)
        return _S3_CLIENT
    except Exception:
        return None

def _s3_public_url(key: str) -> str:
    cfg = current_app.config
    public_base = (cfg.get("S3_PUBLIC_URL") or "").rstrip("/")
    if public_base:
        return f"{public_base}/{key}"
    # fall back to virtual-hosted–style URL if endpoint is standard
    bucket = cfg.get("S3_BUCKET")
    region = cfg.get("S3_REGION") or "us-east-1"
    endpoint = (cfg.get("S3_ENDPOINT_URL") or "").rstrip("/")
    if endpoint and "amazonaws.com" not in endpoint:
        # Prefer path-style for generic endpoints: https://endpoint/bucket/key
        return f"{endpoint}/{bucket}/{key}"
    # Fallback to virtual-hosted style for AWS
    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"

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
    """Store uploaded image in object storage if configured, otherwise on local disk.

    Returns either a public URL (when S3 is enabled) or a relative path under static/ for url_for('static').
    Uses an in-memory buffer to avoid issues with consumed/closed streams on fallback.
    """
    if not file_storage or not getattr(file_storage, 'filename', ''):
        return ""
    filename = secure_filename(file_storage.filename)
    ext = os.path.splitext(filename)[1].lower()
    new_name = f"{uuid.uuid4().hex}{ext}"
    key = f"{subdir}/{new_name}"

    # Read content once into memory to support both S3 and local paths reliably
    try:
        try:
            file_storage.stream.seek(0)
        except Exception:
            pass
        content: bytes = file_storage.read()
    finally:
        try:
            # avoid leaving stream in inconsistent state
            file_storage.close()
        except Exception:
            pass

    if not content:
        return ""

    # MIME validation + optional HEIC->JPEG conversion
    try:
        from PIL import Image
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
        except Exception:
            pass
        img = Image.open(io.BytesIO(content))
        # If HEIC/HEIF, convert to JPEG
        fmt = (img.format or "").upper()
        if fmt in {"HEIC", "HEIF"}:
            buf = io.BytesIO()
            rgb = img.convert("RGB")
            rgb.save(buf, format="JPEG", quality=90)
            content = buf.getvalue()
            ext = ".jpg"
            key = f"{subdir}/{uuid.uuid4().hex}{ext}"
        else:
            # ensure it's an image format we support
            if fmt not in {"JPEG", "JPG", "PNG", "WEBP"}:
                return ""
    except Exception:
        # Not an image or cannot be parsed
        return ""

    # Try S3-compatible storage
    s3 = _get_s3_client()
    bucket = current_app.config.get("S3_BUCKET")
    if s3 and bucket:
        try:
            # Re-detect mimetype after possible conversion
            extra_args = {"ContentType": (getattr(file_storage, 'mimetype', None) or "image/jpeg")}
            if current_app.config.get("S3_SET_PUBLIC_ACL", True):
                extra_args["ACL"] = "public-read"
            s3.upload_fileobj(io.BytesIO(content), bucket, key, ExtraArgs=extra_args)
            return _s3_public_url(key)
        except Exception:
            # Fall back to local save if S3 fails
            pass

    # Local filesystem fallback (best-effort; may be read-only in serverless)
    try:
        folder = os.path.join(current_app.static_folder, subdir)
        os.makedirs(folder, exist_ok=True)
        save_path = os.path.join(folder, new_name)
        with open(save_path, 'wb') as f:
            f.write(content)
        return f"{subdir}/{new_name}"
    except Exception as e:
        try:
            current_app.logger.error("Local media save failed: %s", e)
        except Exception:
            pass
        return ""

def delete_media_file(path_or_url: str) -> None:
    """Delete media from storage.

    If S3 is configured and the given value looks like a URL to the bucket (or a key),
    delete from S3. Otherwise attempt to delete a local static file.
    """
    if not path_or_url:
        return
    # Try S3
    s3 = _get_s3_client()
    bucket = current_app.config.get("S3_BUCKET")
    if s3 and bucket:
        try:
            key = path_or_url
            public = (current_app.config.get("S3_PUBLIC_URL") or "").rstrip("/")
            endpoint = (current_app.config.get("S3_ENDPOINT_URL") or "").rstrip("/")
            if path_or_url.startswith("http"):
                # Strip host part
                if public and path_or_url.startswith(public + "/"):
                    key = path_or_url[len(public) + 1 :]
                elif endpoint and bucket in path_or_url:
                    # endpoint/bucket/key
                    key = path_or_url.split(bucket + "/", 1)[-1]
                else:
                    # https://bucket.s3.region.amazonaws.com/key
                    marker = f"{bucket}."  # after bucket.
                    if marker in path_or_url:
                        key = path_or_url.split('.amazonaws.com/', 1)[-1]
            if key and not key.startswith("http"):
                s3.delete_object(Bucket=bucket, Key=key)
                return
        except Exception:
            pass
    # Local delete fallback
    try:
        base = current_app.static_folder
        # If we received a URL path like "/static/..." convert to relative
        rel = path_or_url
        if rel.startswith("/static/"):
            rel = rel[len("/static/") :]
        abs_path = os.path.join(base, rel)
        if os.path.isfile(abs_path):
            os.remove(abs_path)
    except Exception:
        pass


