from db.database import Database
from core.config import settings
from db.base import Base


target_metadata = Base.metadata

db = Database(settings.DATABASE_URL)


def get_db():
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()


def get_db_session():
    session = db.get_session()
    try:
        return session
    finally:
        session.close()
