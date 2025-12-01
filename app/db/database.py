from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.base import Base


class Database:
    def __init__(
        self, 
        db_url: str,
        pool_size: int = 5,
        max_overflow: int = 0        
    ):
        self.engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=pool_size,
            max_overflow=max_overflow,
        )

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )


    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        return self.SessionLocal()

    def close(self):
        self.engine.dispose()
