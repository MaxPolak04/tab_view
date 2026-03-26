from flask import render_template
from flask_login import login_required

from tab_view.dashboard import dashboard_bp
from tab_view.models import Device, Media, Tag


@dashboard_bp.route("/")
@login_required
def index():
    devices = Device.query.all()
    media_list = Media.query.all()
    tags = Tag.query.all()

    return render_template(
        "dashboard/index.html",
        devices=devices,
        tags=tags,
        media_list=[
            {
                "id": m.id,
                "filename": m.filename,
                "media_type": m.media_type,
                "tag_id": m.tag_id,
            }
            for m in media_list
        ],
    )
