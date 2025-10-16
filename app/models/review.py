from datetime import datetime

from app import db


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewed_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    exchange_id = db.Column(db.Integer, db.ForeignKey("housing_exchange.id", ondelete="SET NULL"), nullable=True)
    tourism_id = db.Column(db.Integer, db.ForeignKey("remote_tourism.id", ondelete="SET NULL"), nullable=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


