from datetime import datetime, timedelta
from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    Boolean,
    String,
    Float,
    ForeignKey,
    Index,
    Enum,
    UniqueConstraint,
    CheckConstraint,
    # ARRAY, #only support postgresql
    create_engine,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


class Acquaintance(Base):
    __tablename__ = "acquaintances"
    __table_args__ = (
        Index("UX_acquaintance", "user_id"),
        UniqueConstraint("word_id", "user_id", name="acquaintance_key"),
    )
    word_id = Column(Integer, primary_key=True)
    user_id = Column(String, primary_key=True)
    acquaint = Column(Integer, nullable=False, default=0)
    last_learned_time = Column(Integer)
    updated_at = Column(DateTime, nullable=False, default=datetime.now())
    deleted = Column(Boolean, default=False, nullable=False)


class Collection(Base):
    __tablename__ = "collections"
    __table_args__ = (
        UniqueConstraint("user_id", "index", name="collection_key"),
        UniqueConstraint("user_id", "name"),
    )
    # id = Column(Integer, primary_key=True)
    name = Column(String, primary_key=True)
    user_id = Column(String, primary_key=True)
    index = Column(Integer, nullable=False)
    icon = Column(Integer)
    color = Column(Integer)
    updated_at = Column(DateTime, nullable=False, default=datetime.now())
    deleted = Column(Boolean, default=False, nullable=False)


class CollectWord(Base):
    __tablename__ = "collect_words"
    __table_args__ = (
        UniqueConstraint("word_id", "mark", "user_id", name="collection_unique"),
    )
    mark = Column(String, primary_key=True)
    word_id = Column(Integer, primary_key=True)
    user_id = Column(String, primary_key=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.now())
    deleted = Column(Boolean, default=False, nullable=False)


class PunchDay(Base):
    __tablename__ = "punch_days"
    user_id = Column(String, primary_key=True)
    date = Column(Integer, primary_key=True)
    study_minute = Column(Integer, nullable=False, default=0)
    study_word_id = Column(String, nullable=False, default="")
    punch_time = Column(Integer, default=int(datetime.now().timestamp()))
    updated_at = Column(DateTime, nullable=False, default=datetime.now())
    deleted = Column(Boolean, default=False, nullable=False)


def create_acquaint(session: Session):
    a1 = Acquaintance(word_id=810, user_id="123")
    a2 = Acquaintance(word_id=810, user_id="321")
    a3 = Acquaintance(word_id=811, user_id="123")
    session.add_all([a1, a2, a3])


def create_collection(session: Session):
    c1 = Collection(user_id="123", index=1, name="test1")
    c2 = Collection(user_id="123", index=0, name="test")
    c3 = Collection(user_id="321", index=0, name="test")
    session.add_all([c1, c2, c3])


def create_collect_word(session: Session):
    c1 = CollectWord(user_id="123", word_id=810, mark="test1")
    c2 = CollectWord(user_id="123", word_id=810, mark="test")
    c3 = CollectWord(user_id="321", word_id=810, mark="test")
    session.add_all([c1, c2, c3])


def create_punch(session: Session):
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    t1 = PunchDay(date=int(now.timestamp()), user_id="123")
    t3 = PunchDay(date=int(tomorrow.timestamp()), user_id="123")
    t2 = PunchDay(date=int(now.timestamp()), user_id="321")
    session.add_all([t1, t2, t3])
    # session.add_all([t1])


if __name__ == "__main__":
    import sqlalchemy as sql
    import os, sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
    from __init__ import config

    DB_URL = config.DB_URL
    # DB_URL = "sqlite:///test.db"
    remote_engine = sql.create_engine(DB_URL or "")
    Base.metadata.drop_all(remote_engine)
    Base.metadata.create_all(remote_engine)
    # Acquaintance.__table__.drop(remote_engine)
    # # Collection.__table__.drop(remote_engine)
    # CollectWord.__table__.drop(remote_engine)
    # PunchDay.__table__.drop(remote_engine)

    with Session(remote_engine) as session:
        create_acquaint(session)
        create_collection(session)
        create_collect_word(session)
        create_punch(session)
        session.commit()
