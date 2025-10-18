from flask import Blueprint, redirect, url_for, flash, request, render_template
from flask_login import login_required, current_user
from sqlalchemy import select

from app import db
from app.models import Booking, RemoteTourism, Message, User
from app.utils.helpers import get_or_create_platform_user
from datetime import date
from sqlalchemy import and_, func


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

    platform_user = get_or_create_platform_user(db, User)
    # Кто инициатор? Если гид — уведомляем клиента. Если клиент — уведомляем гида
    tour = db.session.get(RemoteTourism, booking.tourism_id) if booking.tourism_id else None
    if tour and current_user.id == tour.guide_id:
        # инициатор — гид
        client_link = url_for("messages.chat", user_id=tour.guide_id, _external=True)
        notify = Message(
            sender_id=platform_user.id,
            receiver_id=booking.user_id,
            content=(
                f"Гид {current_user.username} отменил вашу бронь экскурсии '{tour.title}'.\n"
                f"Период: {booking.start_date} — {booking.end_date}. Для связи: {client_link}"
            ),
        )
        db.session.add(notify)
    elif tour and current_user.id == booking.user_id:
        # инициатор — клиент
        client_link = url_for("messages.chat", user_id=booking.user_id, _external=True)
        notify = Message(
            sender_id=platform_user.id,
            receiver_id=tour.guide_id,
            content=(
                f"Бронь отменена клиентом {current_user.username}.\n"
                f"Период: {booking.start_date} — {booking.end_date}. Клиент: {client_link}"
            ),
        )
        db.session.add(notify)

    # Полное удаление брони
    db.session.delete(booking)
    db.session.commit()
    flash("Бронь удалена", "info")
    return redirect(request.referrer or url_for("account.my_bookings"))


@bookings_bp.route("/edit/<int:booking_id>", methods=["GET", "POST"])
@login_required
def edit(booking_id: int):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        flash("Бронь не найдена", "warning")
        return redirect(url_for("account.my_excursions"))
    tour = db.session.get(RemoteTourism, booking.tourism_id) if booking.tourism_id else None
    if not tour or tour.guide_id != current_user.id:
        flash("Недостаточно прав", "danger")
        return redirect(url_for("account.my_excursions"))

    from app.forms.booking import TourBookingForm
    form = TourBookingForm()
    if request.method == "GET":
        form.start_date.data = booking.start_date
        form.end_date.data = booking.end_date
        form.hours.data = booking.hours

    if form.validate_on_submit():
        today = date.today()
        if form.start_date.data < today or form.end_date.data < today:
            flash("Невозможно забронировать экскурсию на выбранную дату", "danger")
            return render_template("bookings/edit.html", form=form, tour=tour, booking=booking)
        if form.start_date.data > form.end_date.data:
            flash("Дата начала позже даты окончания", "danger")
            return render_template("bookings/edit.html", form=form, tour=tour, booking=booking)
        if tour.available_from and form.start_date.data < tour.available_from:
            flash("Данная экскурсия не проводится в указанные даты.", "danger")
            return render_template("bookings/edit.html", form=form, tour=tour, booking=booking)
        if tour.available_to and form.end_date.data > tour.available_to:
            flash("Данная экскурсия не проводится в указанные даты.", "danger")
            return render_template("bookings/edit.html", form=form, tour=tour, booking=booking)

        overlap_exists = db.session.execute(
            select(func.count(Booking.id)).where(
                Booking.tourism_id == tour.id,
                Booking.id != booking.id,
                Booking.status != "cancelled",
                Booking.start_date <= form.end_date.data,
                Booking.end_date >= form.start_date.data,
            )
        ).scalar()
        if overlap_exists:
            flash("Экскурсия в эти даты уже забронирована", "danger")
            return render_template("bookings/edit.html", form=form, tour=tour, booking=booking)

        booking.start_date = form.start_date.data
        booking.end_date = form.end_date.data
        booking.hours = form.hours.data
        booking.total_price = (form.hours.data or tour.duration_hours or 1) * (tour.price_per_hour or 0)
        db.session.commit()

        platform_user = get_or_create_platform_user(db, User)
        chat_url = url_for("messages.chat", user_id=tour.guide_id, _external=True)
        notify = Message(
            sender_id=platform_user.id,
            receiver_id=booking.user_id,
            content=(
                f"Гид внёс изменения в вашу бронь экскурсии '{tour.title}'.\n"
                f"Новые даты: {booking.start_date} — {booking.end_date}. Часов: {booking.hours}.\nДля связи: {chat_url}"
            ),
        )
        db.session.add(notify)
        db.session.commit()
        flash("Бронь обновлена", "success")
        return redirect(url_for("account.my_excursions"))

    return render_template("bookings/edit.html", form=form, tour=tour, booking=booking)


