from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from sqlalchemy import select, or_, and_

from app import db
from app.models import RemoteTourism, User, Message
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
        photos = [s.strip() for s in (form.photos.data or "").split(",") if s.strip()]
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
        flash("Предложение добавлено", "success")
        return redirect(url_for("tourism.tourism_detail", tour_id=tour.id))
    return render_template("tourism/new.html", form=form)


@tourism_bp.get("/<int:tour_id>")
def tourism_detail(tour_id: int):
    tour = db.session.get(RemoteTourism, tour_id)
    if not tour:
        flash("Предложение не найдено", "warning")
        return redirect(url_for("tourism.tourism_search"))
    return render_template("tourism/detail.html", tour=tour)


@tourism_bp.post("/start/<int:tour_id>")
@login_required
def start_from_tour(tour_id: int):
    tour = db.session.get(RemoteTourism, tour_id)
    if not tour:
        flash("Предложение не найдено", "warning")
        return redirect(url_for("tourism.tourism_search"))
    if tour.guide_id == current_user.id:
        return redirect(url_for("tourism.tourism_detail", tour_id=tour.id))

    msg = Message(
        sender_id=current_user.id,
        receiver_id=tour.guide_id,
        content=f"Здравствуйте! Интересует удалённая экскурсия: {tour.title}",
    )
    db.session.add(msg)
    db.session.commit()
    return redirect(url_for("messages.chat", user_id=tour.guide_id))


