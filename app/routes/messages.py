from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from sqlalchemy import select, or_, and_

from app import db
from app.models import Message, HousingExchange, User


messages_bp = Blueprint("messages", __name__, url_prefix="/messages")


@messages_bp.get("/")
@login_required
def inbox():
    # Показываем последние сообщения по собеседнику
    subq = (
        select(
            Message.receiver_id.label("peer"), Message.sender_id.label("me"), Message.timestamp
        ).where(Message.sender_id == current_user.id)
        .union_all(
            select(
                Message.sender_id.label("peer"), Message.receiver_id.label("me"), Message.timestamp
            ).where(Message.receiver_id == current_user.id)
        )
        .subquery()
    )
    # Просто получим всех, с кем есть диалоги
    peers = db.session.execute(
        select(User).where(User.id.in_(select(subq.c.peer)))
    ).scalars().all()

    # Счётчик непрочитанных
    unread_map = dict(
        db.session.execute(
            select(Message.sender_id, db.func.count(Message.id)).where(
                Message.receiver_id == current_user.id, Message.is_read.is_(False)
            ).group_by(Message.sender_id)
        ).all()
    )

    return render_template("messages/inbox.html", peers=peers, unread_map=unread_map)


@messages_bp.route("/chat/<int:user_id>", methods=["GET", "POST"])
@login_required
def chat(user_id: int):
    peer = db.session.get(User, user_id)
    if not peer:
        flash("Пользователь не найден", "warning")
        return redirect(url_for("messages.inbox"))

    # read-only chat if platform bot
    is_read_only = bool(getattr(peer, "email", None) == "system@room2room.local")

    if request.method == "POST" and not is_read_only:
        content = (request.form.get("content") or "").strip()
        exchange_id = request.form.get("exchange_id")
        if not content:
            flash("Введите сообщение", "warning")
            return redirect(url_for("messages.chat", user_id=user_id))
        msg = Message(
            sender_id=current_user.id,
            receiver_id=peer.id,
            exchange_id=int(exchange_id) if exchange_id else None,
            content=content,
        )
        db.session.add(msg)
        db.session.commit()
        return redirect(url_for("messages.chat", user_id=user_id))

    # Прочитать входящие
    db.session.execute(
        db.update(Message)
        .where(Message.sender_id == peer.id, Message.receiver_id == current_user.id, Message.is_read.is_(False))
        .values(is_read=True)
    )
    db.session.commit()

    msgs = db.session.execute(
        select(Message)
        .where(
            or_(
                and_(Message.sender_id == current_user.id, Message.receiver_id == peer.id),
                and_(Message.sender_id == peer.id, Message.receiver_id == current_user.id),
            )
        )
        .order_by(Message.timestamp.asc())
    ).scalars().all()

    return render_template("messages/chat.html", peer=peer, messages=msgs, is_read_only=is_read_only)


@messages_bp.post("/start/<int:listing_id>")
@login_required
def start_from_listing(listing_id: int):
    listing = db.session.get(HousingExchange, listing_id)
    if not listing:
        flash("Объявление не найдено", "warning")
        return redirect(url_for("exchange.listing_search"))
    if listing.owner_id == current_user.id:
        return redirect(url_for("exchange.listing_detail", listing_id=listing.id))

    # Если переписка уже существует между пользователями — не отправляем приветствие повторно
    exists = db.session.execute(
        select(db.func.count(Message.id)).where(
            or_(
                and_(Message.sender_id == current_user.id, Message.receiver_id == listing.owner_id),
                and_(Message.sender_id == listing.owner_id, Message.receiver_id == current_user.id),
            )
        )
    ).scalar() or 0

    if not exists:
        msg = Message(
            sender_id=current_user.id,
            receiver_id=listing.owner_id,
            exchange_id=listing.id,
            content=f"Здравствуйте! Заинтересовался вашим объявлением: {listing.title}",
        )
        db.session.add(msg)
        db.session.commit()
    return redirect(url_for("messages.chat", user_id=listing.owner_id))


