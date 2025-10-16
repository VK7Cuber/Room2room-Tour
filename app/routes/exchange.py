from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from sqlalchemy import select, and_, or_

from app import db
from app.models.housing_exchange import HousingExchange
from app.forms.exchange import ListingForm, FilterForm


exchange_bp = Blueprint("exchange", __name__, url_prefix="/exchange")


@exchange_bp.route("/my")
@login_required
def my_listings():
    listings = (
        db.session.execute(
            select(HousingExchange).where(HousingExchange.owner_id == current_user.id).order_by(HousingExchange.created_date.desc())
        ).scalars().all()
    )
    return render_template("exchange/my_listings.html", listings=listings)


@exchange_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_listing():
    form = ListingForm()
    if form.validate_on_submit():
        amenities = [s.strip() for s in (form.amenities.data or "").split(",") if s.strip()]
        photos = [s.strip() for s in (form.photos.data or "").split(",") if s.strip()]
        listing = HousingExchange(
            owner_id=current_user.id,
            title=form.title.data.strip(),
            description=form.description.data.strip() if form.description.data else None,
            city=form.city.data.strip() if form.city.data else None,
            address=form.address.data.strip() if form.address.data else None,
            housing_type=form.housing_type.data or None,
            room_count=form.room_count.data,
            available_from=form.available_from.data,
            available_to=form.available_to.data,
            amenities=amenities,
            photos=photos,
        )
        db.session.add(listing)
        db.session.commit()
        flash("Объявление создано", "success")
        return redirect(url_for("exchange.my_listings"))
    return render_template("exchange/new.html", form=form)


@exchange_bp.route("/")
def listing_search():
    form = FilterForm(request.args)
    conditions = [HousingExchange.is_active.is_(True)]
    if form.q.data:
        q = f"%{form.q.data.strip().lower()}%"
        conditions.append(or_(HousingExchange.title.ilike(q), HousingExchange.description.ilike(q)))
    if form.city.data:
        conditions.append(HousingExchange.city.ilike(f"%{form.city.data.strip()}%"))
    if form.housing_type.data:
        conditions.append(HousingExchange.housing_type == form.housing_type.data)
    if form.rooms_min.data is not None:
        conditions.append(HousingExchange.room_count >= form.rooms_min.data)
    if form.rooms_max.data is not None:
        conditions.append(HousingExchange.room_count <= form.rooms_max.data)

    listings = db.session.execute(
        select(HousingExchange).where(and_(*conditions)).order_by(HousingExchange.created_date.desc())
    ).scalars().all()

    return render_template("exchange/search.html", listings=listings, form=form)


@exchange_bp.get("/<int:listing_id>")
def listing_detail(listing_id: int):
    listing = db.session.get(HousingExchange, listing_id)
    if not listing:
        flash("Объявление не найдено", "warning")
        return redirect(url_for("exchange.listing_search"))
    return render_template("exchange/detail.html", listing=listing)


