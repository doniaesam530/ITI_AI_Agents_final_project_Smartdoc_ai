from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

from settings import settings

# Same direct Session(engine) pattern used since Lecture 3 — unchanged.
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})


class Base(DeclarativeBase):
    pass
