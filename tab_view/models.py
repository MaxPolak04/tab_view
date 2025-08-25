from flask_login import UserMixin
from tab_view import db


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    last_login_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f'<User {self.username}>'
    

class Device(db.Model):
    __tablename__ = 'devices'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    device_url = db.Column(db.String(200), unique=True, nullable=False)
    uploaded_at = db.Column(db.DateTime, server_default=db.func.now())
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'))
    media = db.relationship('Media')

    def __repr__(self):
        return f'<Device {self.title}>'
    

class Media(db.Model):
    __tablename__ = 'media'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    media_type = db.Column(db.String(10))  # 'image' lub 'video'
    uploaded_at = db.Column(db.DateTime, server_default=db.func.now())
