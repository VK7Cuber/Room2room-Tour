from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from sqlalchemy import select, or_, and_, func
from datetime import date

from app import db
from app.models import RemoteTourism, User, Message, Booking
from app.forms.booking import TourBookingForm
from app.forms.tourism import TourismOfferForm, TourismFilterForm


tourism_bp = Blueprint("tourism", __name__, url_prefix="/tourism")


@tourism_bp.get("/")
def tourism_search():
    form = TourismFilterForm(request.args)
    conditions = [RemoteTourism.is_active.is_(True)]
    if form.q.data:
        q = f"%{form.q.data.strip().lower()}%"
        conditions.append(or_(RemoteTourism.title.ilike(q), RemoteTourism.description.ilike(q)))
    if form.city.data:
        conditions.append(RemoteTourism.city.ilike(f"%{form.city.data.strip()}%"))

    tours = db.session.execute(
        select(RemoteTourism).where(and_(*conditions)).order_by(RemoteTourism.created_date.desc())
    ).scalars().all()
    return render_template("tourism/search.html", form=form, tours=tours)


@tourism_bp.route("/new", methods=["GET", "POST"])
@login_required
def tourism_new():
    form = TourismOfferForm()
    if form.validate_on_submit():
        photos = []
        if "photos" in request.files:
            files = request.files.getlist("photos")
            from app.utils.helpers import save_image
            for f in files:
                rel = save_image(f, subdir="tour_photos")
                if rel:
                    photos.append(rel)
                else:
                    flash("Некоторые файлы отклонены: неподдерживаемый формат или повреждённое изображение (HEIC конвертируется автоматически).", "warning")
        tour = RemoteTourism(
            guide_id=current_user.id,
            city=form.city.data.strip() if form.city.data else None,
            title=form.title.data.strip(),
            description=form.description.data.strip() if form.description.data else None,
            price_per_hour=form.price_per_hour.data,
            duration_hours=form.duration_hours.data,
            photos=photos,
            available_from=form.available_from.data,
            available_to=form.available_to.data,
        )
        db.session.add(tour)
        db.session.commit()
        if not photos:
            flash("Предложение добавлено без изображений.", "info")
        else:
            flash("Предложение добавлено", "success")
        return redirect(url_for("tourism.tourism_detail", tour_id=tour.id))
    return render_template("tourism/new.html", form=form)


@tourism_bp.route("/edit/<int:tour_id>", methods=["GET", "POST"])
@login_required
def tourism_edit(tour_id: int):
    tour = db.session.get(RemoteTourism, tour_id)
    if not tour or tour.guide_id != current_user.id:
        flash("Предложение не найдено", "warning")
        return redirect(url_for("account.my_tours"))
    form = TourismOfferForm(obj=tour)
    if request.method == "GET":
        form.photos.data = None
    if form.validate_on_submit():
        tour.city = form.city.data.strip() if form.city.data else None
        tour.title = form.title.data.strip()
        tour.description = form.description.data.strip() if form.description.data else None
        tour.price_per_hour = form.price_per_hour.data
        tour.duration_hours = form.duration_hours.data
        # handle deletions
        to_delete = set(request.form.getlist("delete_photos"))
        if to_delete:
            from app.utils.helpers import delete_media_file
            tour.photos = [p for p in (tour.photos or []) if p not in to_delete]
            for p in to_delete:
                delete_media_file(p)

        new_photos = []
        if "photos" in request.files:
            files = request.files.getlist("photos")
            from app.utils.helpers import save_image
            for f in files:
                rel = save_image(f, subdir="tour_photos")
                if rel:
                    new_photos.append(rel)
        if new_photos:
            tour.photos = (tour.photos or []) + new_photos
        tour.available_from = form.available_from.data
        tour.available_to = form.available_to.data
        db.session.commit()
        flash("Предложение обновлено", "success")
        return redirect(url_for("account.my_tours"))
    return render_template("tourism/edit.html", form=form, tour=tour)


@tourism_bp.post("/delete/<int:tour_id>")
@login_required
def tourism_delete(tour_id: int):
    tour = db.session.get(RemoteTourism, tour_id)
    if not tour or tour.guide_id != current_user.id:
        flash("Предложение не найдено", "warning")
        return redirect(url_for("account.my_tours"))
    # собрать клиентов c активными бронями и уведомить их, потом удалить брони и тур
    bookings = db.session.execute(
        select(Booking).where(Booking.tourism_id == tour.id)
    ).scalars().all()
    from app.utils.helpers import get_or_create_platform_user
    platform_user = get_or_create_platform_user(db, User)
    informed_user_ids = set()
    for b in bookings:
        # уведомляем только клиентов; не уведомляем гида
        if b.user_id not in informed_user_ids:
            chat_url = url_for("messages.chat", user_id=tour.guide_id, _external=True)
            notify = Message(
                sender_id=platform_user.id,
                receiver_id=b.user_id,
                content=(
                    f"Забронированное вами объявление было удалено гидом.\n"
                    f"Экскурсия: {tour.title}. Для связи с гидом: {chat_url}"
                ),
            )
            db.session.add(notify)
            informed_user_ids.add(b.user_id)
        db.session.delete(b)
    db.session.delete(tour)
    db.session.commit()
    flash("Предложение удалено", "info")
    return redirect(url_for("account.my_tours"))


@tourism_bp.get("/<int:tour_id>")
def tourism_detail(tour_id: int):
    tour = db.session.get(RemoteTourism, tour_id)
    if not tour:
        flash("Предложение не найдено", "warning")
        return redirect(url_for("tourism.tourism_search"))
    return render_template("tourism/detail.html", tour=tour)


@tourism_bp.route("/<int:tour_id>/book", methods=["GET", "POST"])
@login_required
def tourism_book(tour_id: int):
    tour = db.session.get(RemoteTourism, tour_id)
    if not tour:
        flash("Предложение не найдено", "warning")
        return redirect(url_for("tourism.tourism_search"))
    if tour.guide_id == current_user.id:
        flash("Нельзя бронировать собственную экскурсию", "warning")
        return redirect(url_for("tourism.tourism_detail", tour_id=tour.id))

    form = TourBookingForm()
    if form.validate_on_submit():
        # запрет дат из прошлого
        today = date.today()
        if (form.start_date.data and form.start_date.data < today) or (form.end_date.data and form.end_date.data < today):
            flash("Невозможно забронировать экскурсию на выбранную дату", "danger")
            return render_template("tourism/book.html", tour=tour, form=form)
        if form.start_date.data > form.end_date.data:
            flash("Дата начала позже даты окончания", "danger")
            return render_template("tourism/book.html", tour=tour, form=form)
        if tour.available_from and form.start_date.data < tour.available_from:
            flash("Данная экскурсия не проводится в указанные даты.", "danger")
            return render_template("tourism/book.html", tour=tour, form=form)
        if tour.available_to and form.end_date.data > tour.available_to:
            flash("Данная экскурсия не проводится в указанные даты.", "danger")
            return render_template("tourism/book.html", tour=tour, form=form)

        overlap_exists = db.session.execute(
            select(func.count(Booking.id)).where(
                Booking.tourism_id == tour.id,
                Booking.status != "cancelled",
                Booking.start_date <= form.end_date.data,
                Booking.end_date >= form.start_date.data,
            )
        ).scalar()
        if overlap_exists:
            flash("Данная экскурсия в этом промежутке времени недоступна, так как забронирована другим пользователем", "danger")
            return render_template("tourism/book.html", tour=tour, form=form)

        total_price = (form.hours.data or tour.duration_hours) * (tour.price_per_hour or 0)
        booking = Booking(
            user_id=current_user.id,
            tourism_id=tour.id,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            hours=form.hours.data or tour.duration_hours or 1,
            status="pending",
            total_price=total_price,
        )
        db.session.add(booking)
        db.session.commit()

        from app.utils.helpers import get_or_create_platform_user
        from app.models import User
        platform_user = get_or_create_platform_user(db, User)
        chat_url = url_for("messages.chat", user_id=current_user.id, _external=True)
        notify = Message(
            sender_id=platform_user.id,
            receiver_id=tour.guide_id,
            content=(
                f"Новая бронь вашей экскурсии '{tour.title}'.\n"
                f"Клиент: {current_user.username} ({chat_url})\n"
                f"Даты: {booking.start_date} — {booking.end_date}. Часов: {form.hours.data}."
            ),
        )
        db.session.add(notify)
        db.session.commit()
        flash("Бронирование создано", "success")
        return redirect(url_for("account.my_bookings"))

    return render_template("tourism/book.html", tour=tour, form=form)


@tourism_bp.post("/start/<int:tour_id>")
@login_required
def start_from_tour(tour_id: int):
    tour = db.session.get(RemoteTourism, tour_id)
    if not tour:
        flash("Предложение не найдено", "warning")
        return redirect(url_for("tourism.tourism_search"))
    if tour.guide_id == current_user.id:
        return redirect(url_for("tourism.tourism_detail", tour_id=tour.id))

    # Проверяем, была ли ранее переписка между пользователем и гидом
    exists = db.session.execute(
        select(func.count(Message.id)).where(
            or_(
                and_(Message.sender_id == current_user.id, Message.receiver_id == tour.guide_id),
                and_(Message.sender_id == tour.guide_id, Message.receiver_id == current_user.id),
            )
        )
    ).scalar() or 0

    if not exists:
        msg = Message(
            sender_id=current_user.id,
            receiver_id=tour.guide_id,
            content=f"Здравствуйте! Интересует удалённая экскурсия: {tour.title}",
        )
        db.session.add(msg)
        db.session.commit()
    return redirect(url_for("messages.chat", user_id=tour.guide_id))


