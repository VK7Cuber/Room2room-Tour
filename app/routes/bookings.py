from flask import Blueprint, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import select

from app import db
from app.models import Booking, RemoteTourism, Message, User
from app.utils.helpers import get_or_create_platform_user


bookings_bp = Blueprint("bookings", __name__, url_prefix="/bookings")


@bookings_bp.post("/<int:booking_id>/cancel")
@login_required
def cancel_booking(booking_id: int):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        flash("Бронь не найдена", "warning")
        return redirect(request.referrer or url_for("account.my_bookings"))

    # Разрешаем отмену владельцу брони или гиду предложения
    allowed = booking.user_id == current_user.id
    if not allowed and booking.tourism_id:
        tour = db.session.get(RemoteTourism, booking.tourism_id)
        if tour and tour.guide_id == current_user.id:
            allowed = True

    if not allowed:
        flash("Недостаточно прав для отмены брони", "danger")
        return redirect(request.referrer or url_for("account.my_bookings"))

    # Сформировать уведомление гиду перед удалением
    client_link = request.url_root.rstrip("/") + url_for("messages.chat", user_id=booking.user_id)
    platform_user = get_or_create_platform_user(db, User)
    guide_id = None
    if booking.tourism_id:
        tour = db.session.get(RemoteTourism, booking.tourism_id)
        guide_id = tour.guide_id if tour else None
    if guide_id:
        notify = Message(
            sender_id=platform_user.id,
            receiver_id=guide_id,
            content=(
                f"Бронь отменена. Клиент: {current_user.username} ({client_link}).\n"
                f"Бронь: {booking.start_date} — {booking.end_date}."
            ),
        )
        db.session.add(notify)

    # Полное удаление брони
    db.session.delete(booking)
    db.session.commit()
    flash("Бронь удалена", "info")
    return redirect(request.referrer or url_for("account.my_bookings"))


