import os
import shutil
from tab_view import db
from tab_view.models import Media, Tag

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "static", "assets")
UPLOADS_DIR = os.path.join(BASE_DIR, "static", "uploads")

SOURCE_IMG = os.path.join(ASSETS_DIR, "default.png")
TARGET_IMG = os.path.join(UPLOADS_DIR, "default.png")


def seed_data():
    """
    Populates the database with initial data required for the application:
    1. System tags.
    2. Default Media file.

    This function must be executed within an active Application Context.
    """
    print("🌱 Seeding database...")

    # --- 1. FILE SETUP ---
    if not os.path.exists(UPLOADS_DIR):
        os.makedirs(UPLOADS_DIR)

    if not os.path.exists(TARGET_IMG):
        if os.path.exists(SOURCE_IMG):
            shutil.copy(SOURCE_IMG, TARGET_IMG)
            print("   ✅ Copied default.png to uploads.")
        else:
            print("   ⚠️ Error: Source default.png not found in assets!")

    # --- 2. TAG SETUP ---
    # Define mandatory tags that must exist
    required_tags = ["Other", "eNStudios", "System"]

    system_tag_id = None

    for tag_name in required_tags:
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name, is_system=True)
            db.session.add(tag)
            print(f"   ✅ Created tag: {tag_name}")

        # Commit immediately to generate and retrieve the ID
        db.session.commit()

        # Cache the 'System' tag ID for the default media assignment
        if tag_name == "System":
            system_tag_id = tag.id

    # --- 3. MEDIA SETUP (Default Image) ---
    media = db.session.get(Media, 1)
    if not media:
        if system_tag_id:
            default_media = Media(
                id=1, filename="default.png", media_type="image", tag_id=system_tag_id
            )
            db.session.add(default_media)
            try:
                db.session.commit()
                print("   ✅ Created Default Media (ID: 1).")
            except Exception as e:
                db.session.rollback()
                print(f"   ❌ Error creating media: {e}")
        else:
            print("   ❌ Critical: System tag missing, cannot create default media.")
    else:
        print("   ℹ️ Default Media already exists.")

    print("🌱 Seeding complete.")


if __name__ == "__main__":
    # Allows manual execution: python tab_view/seed.py
    from tab_view import create_app

    app = create_app()
    with app.app_context():
        seed_data()
