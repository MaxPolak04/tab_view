import uuid

from flask_login import UserMixin

from tab_view import db


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    last_login_at = db.Column(
        db.DateTime, server_default=db.func.now(), onupdate=db.func.now()
    )
    is_admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<User {self.username}>"


class Device(db.Model):
    __tablename__ = "devices"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    device_url = db.Column(db.String(200), unique=True, nullable=False)
    uploaded_at = db.Column(db.DateTime, server_default=db.func.now())
    media_id = db.Column(db.Integer, db.ForeignKey("media.id"))
    media = db.relationship("Media")

    def __repr__(self):
        return f"<Device {self.name}>"


class Media(db.Model):
    __tablename__ = "media"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    media_type = db.Column(db.String(10))  # 'image' or 'video'
    uploaded_at = db.Column(db.DateTime, server_default=db.func.now())
    tag_id = db.Column(db.Integer, db.ForeignKey("tags.id"), nullable=False)

    def __repr__(self):
        return f"<Media {self.filename}>"


class Tag(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    is_system = db.Column(db.Boolean, default=False)  # for "Other" and "eNStudios"
    media = db.relationship("Media", backref="tag", lazy=True)

    def __repr__(self):
        return f"<Tag {self.name}>"


class EventMedia(db.Model):
    __tablename__ = "event_media"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    media_id = db.Column(db.Integer, db.ForeignKey("media.id"), nullable=False)
    order = db.Column(db.Integer, default=0)
    duration = db.Column(db.Integer, default=10)
    event = db.relationship("Event", back_populates="event_media")
    media = db.relationship("Media")

    def __repr__(self):
        return f"<EventMedia event={self.event_id} media={self.media_id} \
            order={self.order}>"


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(
        db.String(36), default=lambda: str(uuid.uuid4()), nullable=False
    )
    title = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    color = db.Column(db.String(7), default="#3788d8")
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime, server_default=db.func.now(), onupdate=db.func.now()
    )
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)
    device = db.relationship("Device")
    event_media = db.relationship(
        "EventMedia", back_populates="event", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Event {self.id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "start": self.start_time.isoformat() if self.start_time else None,
            "end": self.end_time.isoformat() if self.end_time else None,
            "color": self.color,
            "extendedProps": {
                "device_id": self.device_id,
                "media_playlist": [
                    {
                        "media_id": em.media_id,
                        "filename": em.media.filename,
                        "media_type": em.media.media_type,
                        "order": em.order,
                        "duration": em.duration,
                    }
                    for em in sorted(self.event_media, key=lambda x: x.order)
                ],
            },
        }
