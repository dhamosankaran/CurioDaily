from sqlalchemy import create_engine, text
from app.core.config import settings

def check_database():
    engine = create_engine(str(settings.DATABASE_URL))
    with engine.connect() as conn:
        # Check if we can create a table
        conn.execute(text("CREATE TABLE IF NOT EXISTS test_table (id serial PRIMARY KEY)"))
        print("Successfully created test table")

        # Check if alembic_version table exists
        result = conn.execute(text("SELECT to_regclass('public.alembic_version')"))
        if result.scalar():
            print("alembic_version table exists")
        else:
            print("alembic_version table does not exist")

        # Check permissions
        result = conn.execute(text("SELECT grantee, privilege_type FROM information_schema.role_table_grants WHERE table_name='alembic_version'"))
        print("Permissions for alembic_version table:")
        for row in result:
            print(f"Grantee: {row[0]}, Privilege: {row[1]}")

if __name__ == "__main__":
    check_database()