from flask_login import UserMixin
from tab_view import db


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    last_login_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    is_admin = db.Column(db.Boolean, default=False)

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
        return f'<Device {self.name}>'
    

class Media(db.Model):
    __tablename__ = 'media'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    media_type = db.Column(db.String(10))  # 'image' or 'video'
    uploaded_at = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f'<Media {self.filename}>'
    

class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=False)
    device = db.relationship('Device')
    media = db.relationship('Media')

    def __repr__(self):
        return f'<Schedule {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': self.end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'device_id': self.device_id,
            'media_id': self.media_id
        }
    