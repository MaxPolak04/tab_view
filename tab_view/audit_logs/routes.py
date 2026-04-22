import logging

from flask import render_template, request

from tab_view import db
from tab_view.models import AuditLog, User
from tab_view.utils import admin_required

from . import logs_bp

logger = logging.getLogger(__name__)


@logs_bp.route("/")
@admin_required
def view_logs():
    page = request.args.get("page", 1, type=int)
    search_query = request.args.get("q", "").strip()
    entity_filter = request.args.get("entity", "").strip()
    action_filter = request.args.get("action", "").strip()
    user_filter = request.args.get("user", type=int)

    query = AuditLog.query

    if search_query:
        query = query.filter(AuditLog.details.ilike(f"%{search_query}%"))

    if entity_filter:
        query = query.filter(AuditLog.entity_type == entity_filter)

    if action_filter:
        query = query.filter(AuditLog.action == action_filter)

    if user_filter:
        query = query.filter(AuditLog.user_id == user_filter)

    query = query.order_by(AuditLog.timestamp.desc())

    pagination = query.paginate(page=page, per_page=20)
    logs = pagination.items

    unique_actions = [
        r[0] for r in db.session.query(AuditLog.action).distinct().all() if r[0]
    ]
    unique_entities = [
        r[0] for r in db.session.query(AuditLog.entity_type).distinct().all() if r[0]
    ]
    all_users = User.query.order_by(User.username.asc()).all()

    return render_template(
        "admin/logs.html",
        logs=logs,
        pagination=pagination,
        search_query=search_query,
        current_entity=entity_filter,
        current_action=action_filter,
        current_user_filter=user_filter,
        unique_actions=unique_actions,
        unique_entities=unique_entities,
        all_users=all_users,
    )
