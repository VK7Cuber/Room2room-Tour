from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app import db
from app.forms.account import ProfileForm
from app.models.remote_tourism import RemoteTourism
from app.models.booking import Booking
from app.models.housing_exchange import HousingExchange
from app.models.review import Review
from sqlalchemy import select, func


account_bp = Blueprint("account", __name__, url_prefix="/account")


@account_bp.get("/")
@login_required
def dashboard():
    listings_count = db.session.execute(
        select(func.count(HousingExchange.id)).where(HousingExchange.owner_id == current_user.id)
    ).scalar() or 0
    bookings_count = db.session.execute(
        select(func.count(Booking.id)).where(Booking.user_id == current_user.id)
    ).scalar() or 0
    tours_count = db.session.execute(
        select(func.count(RemoteTourism.id)).where(RemoteTourism.guide_id == current_user.id)
    ).scalar() or 0
    # средний рейтинг на основе полученных отзывов
    avg_rating = db.session.execute(
        select(func.avg(Review.rating)).where(Review.reviewed_id == current_user.id)
    ).scalar()
    avg_rating = float(avg_rating) if avg_rating is not None else 0.0

    stats = {
        "listings": listings_count,
        "bookings": bookings_count,
        "reviews": current_user.review_count or 0,
        "tours": tours_count,
        "rating": avg_rating,
    }
    return render_template("account/dashboard.html", stats=stats)


@account_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data.strip() if form.first_name.data else None
        current_user.last_name = form.last_name.data.strip() if form.last_name.data else None
        current_user.city = form.city.data.strip() if form.city.data else None
        current_user.phone = form.phone.data.strip() if form.phone.data else None
        if form.avatar.data:
            from app.utils.helpers import save_image
            rel_path = save_image(form.avatar.data, subdir="avatars")
            if rel_path:
                current_user.avatar = rel_path
            else:
                flash("Не удалось загрузить изображение. Проверьте формат или повторите позже.", "warning")
        current_user.description = form.description.data.strip() if form.description.data else None
        db.session.commit()
        flash("Профиль обновлён", "success")
        return redirect(url_for("account.profile"))
    return render_template("account/profile.html", form=form)


@account_bp.get("/tours")
@login_required
def my_tours():
    tours = (
        db.session.execute(
            db.select(RemoteTourism).where(RemoteTourism.guide_id == current_user.id).order_by(RemoteTourism.created_date.desc())
        ).scalars().all()
    )
    return render_template("account/my_tours.html", tours=tours)


@account_bp.get("/my-excursions")
@login_required
def my_excursions():
    # ближайшие брони, где текущий пользователь — гид тура
    from app.models.remote_tourism import RemoteTourism
    from app.models.booking import Booking
    from sqlalchemy import select
    q = (
        select(Booking, RemoteTourism)
        .join(RemoteTourism, Booking.tourism_id == RemoteTourism.id)
        .where(RemoteTourism.guide_id == current_user.id)
        .order_by(Booking.start_date.asc())
    )
    rows = db.session.execute(q).all()
    items = [
        {
            "booking": b,
            "tour": t,
        }
        for (b, t) in rows
    ]
    return render_template("account/my_excursions.html", items=items)


@account_bp.get("/bookings")
@login_required
def my_bookings():
    bookings = (
        db.session.execute(
            db.select(Booking).where(Booking.user_id == current_user.id).order_by(Booking.created_date.desc())
        ).scalars().all()
    )
    return render_template("account/my_bookings.html", bookings=bookings)


