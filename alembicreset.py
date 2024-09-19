import os
import shutil
from sqlalchemy import create_engine, text
from app.core.config import settings

def reset_alembic():
    # Remove existing migration files
    migrations_dir = os.path.join('alembic', 'versions')
    if os.path.exists(migrations_dir):
        shutil.rmtree(migrations_dir)
    os.makedirs(migrations_dir)

    # Reset database
    engine = create_engine(str(settings.DATABASE_URL))
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        conn.execute(text("DROP TABLE IF EXISTS users"))
        conn.execute(text("DROP TABLE IF EXISTS items"))
        # Add more DROP TABLE statements for other tables in your schema
        conn.commit()

    print("Alembic state reset. Database tables dropped.")

if __name__ == "__main__":
    reset_alembic()