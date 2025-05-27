from datetime import datetime, timedelta, timezone
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
    Table,
    SQLColumnExpression,
    MetaData,
    UniqueConstraint,
    ForeignKeyConstraint,
    PrimaryKeyConstraint,
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
        PrimaryKeyConstraint("user_id", "word_id"),
        # UniqueConstraint("word_id", "user_id", name="acquaintance_key"),
    )
    word_id = Column(Integer)
    user_id = Column(Text)
    acquaint = Column(Integer, nullable=False, default=0)
    last_learned_time = Column(Integer)


class Collection(Base):
    __tablename__ = "collections"
    __table_args__ = (
        PrimaryKeyConstraint("user_id", "id"),
        UniqueConstraint("user_id", "name", name="collection_name"),
        UniqueConstraint("user_id", "id", name="collection_key"),
    )
    id = Column(Integer)
    user_id = Column(Text)
    name = Column(Text, nullable=False)
    index = Column(Integer, nullable=False)
    icon = Column(Integer)
    color = Column(Integer)


class CollectWord(Base):
    __tablename__ = "collect_words"
    __table_args__ = (
        Index("IX_collect_word", "user_id", "word_id"),
        Index("IX_collect_word_in_id", "user_id", "collection_id"),
        PrimaryKeyConstraint("user_id", "word_id", "collection_id"),
        ForeignKeyConstraint(
            ["collection_id", "user_id"],
            ["collections.id", "collections.user_id"],
            ondelete="CASCADE",
        ),
    )
    word_id = Column(Integer)
    collection_id = Column(Integer)
    user_id = Column(Text)


class PunchDay(Base):
    __tablename__ = "punch_days"
    __table_args__ = (PrimaryKeyConstraint("user_id", "date"),)
    date = Column(Integer)
    user_id = Column(Text)
    study_minute = Column(Integer, nullable=False, default=0)
    study_word_ids = Column(Text, nullable=False, default="")
    punch_time = Column(Integer, default=int(datetime.now().timestamp()))


class SharedApp(Base):
    __tablename__ = "shared_apps"
    __table_args__ = (
        PrimaryKeyConstraint("user_id", "date", "app_id"),
        Index("IX_shared_app", "user_id", "date"),
    )
    date = Column(Integer)
    user_id = Column(Text)
    app_id = Column(Text, nullable=False)


class ReportIssue(Base):
    __tablename__ = "report_issues"
    __table_args__ = (PrimaryKeyConstraint("word_id", "user_id"),)
    word_id = Column(Integer)
    user_id = Column(Text)
    word = Column(Text, nullable=False, index=True)
    issue = Column(Text)
    time = Column(DateTime, default=datetime.now())


def parse_condition(
    tablename: str, user_id: str, exclude_ids: list[int]
) -> SQLColumnExpression:
    match tablename:
        case Acquaintance.__tablename__:
            return (Acquaintance.user_id == user_id) & (
                Acquaintance.word_id.not_in(exclude_ids)
            )
        case Collection.__tablename__:
            return (Collection.user_id == user_id) & (Collection.id.not_in(exclude_ids))
        case CollectWord.__tablename__:
            return (CollectWord.user_id == user_id) & (
                CollectWord.word_id.not_in(exclude_ids)
            )
        case PunchDay.__tablename__:
            return (PunchDay.user_id == user_id) & (PunchDay.date.not_in(exclude_ids))
        case _:
            raise ValueError("No this table name %s" % tablename)


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
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    import os, sys, json

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
    from config import config

    DB_URL = config.REMOTE_DB
    # DB_URL = "sqlite:///test.db"
    remote_engine = sql.create_engine(DB_URL)
    # Base.metadata.drop_all(remote_engine)
    # ReportIssue.__table__.create(remote_engine)
    # Base.metadata.create_all(remote_engine)
    # Acquaintance.__table__.drop(remote_engine)
    # # Collection.__table__.drop(remote_engine)
    # CollectWord.__table__.drop(remote_engine)
    # PunchDay.__table__.drop(remote_engine)
    # SharedApp.__table__.create(remote_engine)

    # with Session(remote_engine) as session:
    #     # create_acquaint(session)
    #     create_collection(session)
    #     # create_punch(session)
    #     session.commit()
    #     # insert collect_word need after collections builded and existed
    #     create_collect_word(session)
    #     session.commit()
    now = datetime.now()
    date = datetime(year=now.year, month=now.month, day=now.day)
    data = {"user_id": "123", "date": int(date.timestamp()), "app_id": "fuck you"}
    stmt = pg_insert(SharedApp).values(data)
    ins_cte = stmt.on_conflict_do_nothing().returning(1).cte("ins")
    stmt = sql.select(
        sql.exists(sql.select("*").select_from(ins_cte)).label("inserted")
    )
    print(stmt)
    with Session(remote_engine) as session:
        has_shared = session.execute(stmt).scalar()
        print("first time shared = %r" % has_shared)
        has_shared = session.execute(stmt).scalar()
        print("second time shared = %r" % has_shared)
        # session.commit()

    # cursor.commit()

"""
INSERT INTO report_issues (word_id, user_id, word, issue, time)
VALUE (?,?,?,?,?) ON CONFLICT DO UPDATE SET issue=excluded.issue time=excluded.time
"""
