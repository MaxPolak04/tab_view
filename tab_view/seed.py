import os
import shutil

from werkzeug.security import generate_password_hash

from tab_view import db
from tab_view.models import Media, Tag, User

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "static", "assets")
UPLOADS_DIR = os.path.join(BASE_DIR, "static", "uploads")

SOURCE_IMG = os.path.join(ASSETS_DIR, "default.png")
TARGET_IMG = os.path.join(UPLOADS_DIR, "default.png")


def seed_data():
    """
    Populates the database with initial data required for the application:
    1. Default Admin User (admin / admin).
    2. System tag.
    3. Default Media file.

    This function must be executed within an active Application Context.
    """
    print("🌱 Seeding database...")

    # --- 1. ADMIN USER SETUP ---
    admin_user = User.query.filter_by(username="admin").first()
    if not admin_user:
        hashed_password = generate_password_hash("admin")
        admin_user = User(username="admin", password=hashed_password, is_admin=True)
        db.session.add(admin_user)
        db.session.commit()
        print("   ✅ Created default admin user (admin / admin).")
    else:
        print("   ℹ️ Admin user already exists.")

    # --- 2. FILE SETUP ---
    if not os.path.exists(UPLOADS_DIR):
        os.makedirs(UPLOADS_DIR)

    if not os.path.exists(TARGET_IMG):
        if os.path.exists(SOURCE_IMG):
            shutil.copy(SOURCE_IMG, TARGET_IMG)
            print("   ✅ Copied default.png to uploads.")
        else:
            print("   ⚠️ Error: Source default.png not found in assets!")

    # --- 3. TAG SETUP (Only "System") ---
    system_tag_name = "System"
    system_tag = Tag.query.filter_by(name=system_tag_name).first()

    if not system_tag:
        system_tag = Tag(name=system_tag_name, is_system=True)
        db.session.add(system_tag)
        db.session.commit()
        print(f"   ✅ Created tag: {system_tag_name}")
    else:
        if not system_tag.is_system:
            system_tag.is_system = True
            db.session.commit()

    # --- 4. MEDIA SETUP (Default Image) ---
    media = db.session.get(Media, 1)
    if not media:
        default_media = Media(
            id=1, filename="default.png", media_type="image", tag_id=system_tag.id
        )
        db.session.add(default_media)
        try:
            db.session.commit()
            print("   ✅ Created Default Media (ID: 1).")
        except Exception as e:
            db.session.rollback()
            print(f"   ❌ Error creating media: {e}")
    else:
        print("   ℹ️ Default Media already exists.")

    print("🌱 Seeding complete.")


if __name__ == "__main__":
    # Allows manual execution: python tab_view/seed.py
    from tab_view import create_app

    app = create_app()
    with app.app_context():
        seed_data()
