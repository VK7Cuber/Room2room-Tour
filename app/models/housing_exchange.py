from datetime import datetime

from app import db


class HousingExchange(db.Model):
    __tablename__ = "housing_exchange"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text)

    city = db.Column(db.String(128), index=True)
    address = db.Column(db.String(255))
    housing_type = db.Column(db.String(64), index=True)  # apartment, house, room, studio
    room_count = db.Column(db.Integer)

    # store as JSON arrays of strings
    amenities = db.Column(db.JSON, default=list)
    photos = db.Column(db.JSON, default=list)

    available_from = db.Column(db.Date)
    available_to = db.Column(db.Date)

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    views_count = db.Column(db.Integer, default=0, nullable=False)

    owner = db.relationship("User", backref=db.backref("housing_listings", lazy="dynamic"))


