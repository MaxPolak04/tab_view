import os
import shutil
from tab_view import create_app, db
from tab_view.models import Media


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'static', 'assets')
UPLOADS_DIR = os.path.join(BASE_DIR, 'static', 'uploads')

SOURCE_IMG = os.path.join(ASSETS_DIR, 'default.png')
TARGET_IMG = os.path.join(UPLOADS_DIR, 'default.png')


def seed_media():
    app = create_app()
    with app.app_context():
        print("🌱 Seeding Media setup...")

        if not os.path.exists(UPLOADS_DIR):
            os.makedirs(UPLOADS_DIR)

        if not os.path.exists(TARGET_IMG):
            if os.path.exists(SOURCE_IMG):
                print(f"   Copying default.png from {SOURCE_IMG} to {TARGET_IMG}")
                shutil.copy(SOURCE_IMG, TARGET_IMG)
            else:
                print("   ⚠️ Error: Source default.png not found in assets!")
        else:
            print("   ℹ️ default.png already exists in volume. Skipping copy.")

        media = db.session.get(Media, 1)
        
        if not media:
            print("   Creating Media record ID=1 in database...")
            default_media = Media(
                id=1,
                filename='default.png',
                media_type='image'
            )
            db.session.add(default_media)
            try:
                db.session.commit()
                print("   ✅ Media ID=1 created.")
            except Exception as e:
                db.session.rollback()
                print(f"   ❌ Database error: {e}")
        else:
            print("   ℹ️ Media record ID=1 already exists.")

if __name__ == '__main__':
    seed_media()
