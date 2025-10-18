from datetime import datetime, date

from app import db


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    exchange_id = db.Column(db.Integer, db.ForeignKey("housing_exchange.id", ondelete="SET NULL"), nullable=True, index=True)
    tourism_id = db.Column(db.Integer, db.ForeignKey("remote_tourism.id", ondelete="SET NULL"), nullable=True, index=True)

    start_date = db.Column(db.Date, nullable=False, default=date.today)
    end_date = db.Column(db.Date, nullable=False, default=date.today)
    hours = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(32), nullable=False, default="pending", index=True)
    total_price = db.Column(db.Integer, nullable=False, default=0)

    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


