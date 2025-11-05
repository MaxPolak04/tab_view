from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_apscheduler import APScheduler
from tab_view.utils import wait_for_db
from tab_view.config import Config


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
scheduler = APScheduler()


def create_app():
    """Create and configure the Flask application"""

    app = Flask(__name__)
    app.config.from_object(Config)

    app.config['SCHEDULER_API_ENABLED'] = False


    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    scheduler.init_app(app)


    login_manager.login_view = 'auth.signin'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    

    from .auth import auth_bp
    from .devices import devices_bp
    from .media import media_bp
    from .users import users_bp
    from .events import events_bp
    from .errors import errors_bp


    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(devices_bp, url_prefix='/devices')
    app.register_blueprint(media_bp, url_prefix='/media')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(events_bp, url_prefix='/api/v1/events')
    # app.register_blueprint(errors_bp, url_prefix='/error')


    csrf.exempt(events_bp)


    @app.route('/')
    def index():
        return redirect(url_for('devices.get_all_devices'))
    

    with app.app_context():
        wait_for_db(app)

        from datetime import datetime, timedelta
        from .models import Event
        
        def cleanup_old_events():
            """Removes events that ended more than a month ago"""
            try:
                cutoff_date = datetime.now() - timedelta(days=30)
                old_events = Event.query.filter(Event.end_time < cutoff_date).all()
                
                deleted_count = len(old_events)
                
                for event in old_events:
                    db.session.delete(event)
                
                db.session.commit()
                print(f"[CLEANUP] Usunięto {deleted_count} starych eventów - {datetime.now()}")
                
            except Exception as e:
                db.session.rollback()
                print(f"[CLEANUP ERROR] {str(e)}")
        
        # Add task - runs daily at 3:00 AM.
        if not scheduler.get_job('cleanup_old_events'):
            scheduler.add_job(
                id='cleanup_old_events',
                func=cleanup_old_events,
                trigger='cron',
                hour=3,
                minute=0
            )
        
        # Start the scheduler
        scheduler.start()
        print("[SCHEDULER] Automatyczne czyszczenie eventów uruchomione")


    return app
