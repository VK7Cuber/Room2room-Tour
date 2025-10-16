from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app import db
from app.forms.account import ProfileForm
from app.models.remote_tourism import RemoteTourism


account_bp = Blueprint("account", __name__, url_prefix="/account")


@account_bp.get("/")
@login_required
def dashboard():
    # Placeholder counters until features are implemented
    stats = {
        "listings": 0,
        "bookings": 0,
        "reviews": current_user.review_count or 0,
        "messages": 0,
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
        current_user.avatar = form.avatar.data.strip() if form.avatar.data else None
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


