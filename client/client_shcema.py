from datetime import datetime, timedelta
from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    Boolean,
    Text,
    Float,
    ForeignKey,
    Index,
    Enum,
    UniqueConstraint,
    ForeignKeyConstraint,
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
    user_id = Column(Text, primary_key=True)
    acquaint = Column(Integer, nullable=False, default=0)
    last_learned_time = Column(Integer)


class Collection(Base):
    __tablename__ = "collections"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="collection_name"),
        UniqueConstraint("user_id", "id", name="collection_key"),
    )
    id = Column(Integer, primary_key=True)
    user_id = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    index = Column(Integer, nullable=False)
    icon = Column(Integer)
    color = Column(Integer)


class CollectWord(Base):
    __tablename__ = "collect_words"
    __table_args__ = (
        Index("Pop_collect_word", "word_id"),
        UniqueConstraint(
            "word_id", "collection_id", "user_id", name="collect_word_unique"
        ),
        ForeignKeyConstraint(
            ["collection_id", "user_id"], ["collections.id", "collections.user_id"]
        ),
    )
    word_id = Column(Integer, primary_key=True)
    collection_id = Column(Integer, primary_key=True)
    user_id = Column(Text, primary_key=True)


"""
CREATE TABLE collect_words (
        word_id INTEGER NOT NULL, 
        collection_id INTEGER NOT NULL, 
        user_id TEXT NOT NULL, 
        PRIMARY KEY (word_id, collection_id, user_id), 
        CONSTRAINT collect_word_unique UNIQUE (word_id, collection_id, user_id), 
        FOREIGN KEY(collection_id, user_id) REFERENCES collections (id, user_id)
);
"""


class PunchDay(Base):
    __tablename__ = "punch_days"
    date = Column(Integer, primary_key=True)
    user_id = Column(Text, primary_key=True)
    study_minute = Column(Integer, nullable=False, default=0)
    study_word_ids = Column(Text, nullable=False, default="")
    punch_time = Column(Integer, default=int(datetime.now().timestamp()))


def create_acquaint(session: Session):
    a1 = Acquaintance(word_id=810, user_id="123")
    a2 = Acquaintance(word_id=810, user_id="321")
    a3 = Acquaintance(word_id=811, user_id="123")
    session.add_all([a1, a2, a3])


def create_collection(session: Session):
    c1 = Collection(user_id="123", index=0, name="test", id=1)
    c2 = Collection(user_id="123", index=1, name="test1", id=2)
    c3 = Collection(user_id="321", index=0, name="test", id=1)
    session.add_all([c1, c2, c3])


def create_collect_word(session: Session):
    c1 = CollectWord(user_id="123", word_id=810, collection_id=1)
    c2 = CollectWord(user_id="123", word_id=810, collection_id=2)
    c3 = CollectWord(user_id="321", word_id=810, collection_id=1)
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

    DB_URL = config.REMOTE_DB
    # DB_URL = "sqlite:///test.db"
    remote_engine = sql.create_engine(DB_URL)
    # Base.metadata.drop_all(remote_engine)
    # Base.metadata.create_all(remote_engine)
    # Acquaintance.__table__.drop(remote_engine)
    # # Collection.__table__.drop(remote_engine)
    # CollectWord.__table__.drop(remote_engine)
    # PunchDay.__table__.drop(remote_engine)

    # with Session(remote_engine) as session:
    #     create_acquaint(session)
    #     create_collection(session)
    #     create_punch(session)
    #     session.commit()
    #     # insert collect_word need after collections builded and existed
    #     create_collect_word(session)
    #     session.commit()
    with remote_engine.connect() as cursor:
        query = sql.text(
            "INSERT INTO collect_words (word_id, collection_id, user_id) VALUES (34, 1, '123')"
        )
        cursor.execute(query)
        # cursor.commit()
