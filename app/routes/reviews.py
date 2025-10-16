from flask import Blueprint, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import select

from app import db
from app.models import Review, User, HousingExchange, RemoteTourism
from app.forms.reviews import ReviewForm


reviews_bp = Blueprint("reviews", __name__, url_prefix="/reviews")


def _recalculate_user_rating(user_id: int) -> None:
    rows = db.session.execute(select(Review.rating).where(Review.reviewed_id == user_id)).all()
    if not rows:
        user = db.session.get(User, user_id)
        if user:
            user.rating = 0
            user.review_count = 0
            db.session.commit()
        return
    ratings = [r[0] for r in rows]
    avg = sum(ratings) / len(ratings)
    user = db.session.get(User, user_id)
    if user:
        user.rating = round(avg, 2)
        user.review_count = len(ratings)
    db.session.commit()


@reviews_bp.post("/user/<int:reviewed_id>")
@login_required
def create_user_review(reviewed_id: int):
    if reviewed_id == current_user.id:
        flash("Нельзя оставить отзыв самому себе", "warning")
        return redirect(request.referrer or url_for("main.index"))

    form = ReviewForm()
    if form.validate_on_submit():
        rev = Review(
            reviewer_id=current_user.id,
            reviewed_id=reviewed_id,
            rating=form.rating.data,
            comment=form.comment.data or None,
        )
        db.session.add(rev)
        db.session.commit()
        _recalculate_user_rating(reviewed_id)
        flash("Отзыв сохранён", "success")
    else:
        flash("Проверьте корректность оценки", "danger")
    return redirect(request.referrer or url_for("main.index"))


@reviews_bp.post("/exchange/<int:listing_id>")
@login_required
def create_exchange_review(listing_id: int):
    listing = db.session.get(HousingExchange, listing_id)
    if not listing:
        flash("Объявление не найдено", "warning")
        return redirect(request.referrer or url_for("exchange.listing_search"))
    if listing.owner_id == current_user.id:
        flash("Нельзя оставить отзыв на своё объявление", "warning")
        return redirect(url_for("exchange.listing_detail", listing_id=listing.id))

    form = ReviewForm()
    if form.validate_on_submit():
        rev = Review(
            reviewer_id=current_user.id,
            reviewed_id=listing.owner_id,
            exchange_id=listing.id,
            rating=form.rating.data,
            comment=form.comment.data or None,
        )
        db.session.add(rev)
        db.session.commit()
        _recalculate_user_rating(listing.owner_id)
        flash("Отзыв добавлен", "success")
    else:
        flash("Проверьте корректность оценки", "danger")
    return redirect(url_for("exchange.listing_detail", listing_id=listing.id))


@reviews_bp.post("/tour/<int:tour_id>")
@login_required
def create_tour_review(tour_id: int):
    tour = db.session.get(RemoteTourism, tour_id)
    if not tour:
        flash("Предложение не найдено", "warning")
        return redirect(request.referrer or url_for("tourism.tourism_search"))
    if tour.guide_id == current_user.id:
        flash("Нельзя оставить отзыв на самого себя", "warning")
        return redirect(url_for("tourism.tourism_detail", tour_id=tour.id))

    form = ReviewForm()
    if form.validate_on_submit():
        rev = Review(
            reviewer_id=current_user.id,
            reviewed_id=tour.guide_id,
            tourism_id=tour.id,
            rating=form.rating.data,
            comment=form.comment.data or None,
        )
        db.session.add(rev)
        db.session.commit()
        _recalculate_user_rating(tour.guide_id)
        flash("Отзыв добавлен", "success")
    else:
        flash("Проверьте корректность оценки", "danger")
    return redirect(url_for("tourism.tourism_detail", tour_id=tour.id))


