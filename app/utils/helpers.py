def normalize_database_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    return url


def get_or_create_platform_user(db, User):
    """Return a persistent 'platform bot' user used for system notifications."""
    platform_email = "system@room2room.local"
    user = db.session.execute(db.select(User).where(User.email == platform_email)).scalar_one_or_none()
    if user:
        return user
    user = User(username="Room2room Bot", email=platform_email, is_verified=True, is_active=True)
    # Set an unusable password
    user.set_password("!disabled-platform-bot!")
    db.session.add(user)
    db.session.commit()
    return user


