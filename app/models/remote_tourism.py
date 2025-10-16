from datetime import datetime

from app import db


class RemoteTourism(db.Model):
    __tablename__ = "remote_tourism"

    id = db.Column(db.Integer, primary_key=True)
    guide_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    city = db.Column(db.String(128), index=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text)
    price_per_hour = db.Column(db.Integer, nullable=False, default=0)
    duration_hours = db.Column(db.Integer, nullable=False, default=1)

    photos = db.Column(db.JSON, default=list)
    available_from = db.Column(db.Date)
    available_to = db.Column(db.Date)

    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    booking_count = db.Column(db.Integer, default=0, nullable=False)

    guide = db.relationship("User", backref=db.backref("tour_offers", lazy="dynamic"))


