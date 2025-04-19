import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
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
from sqlalchemy.orm import DeclarativeBase, Session
import uuid
from sqlalchemy.dialects.postgresql import UUID


class PartOfSpeech(enum.Enum):
    verb = "verb"
    noun = "noun"
    adjective = "adjective"
    adverb = "adverb"
    pronoun = "pronoun"
    preposition = "preposition"
    conjunction = "conjunction"
    interjection = "interjection"


class Base(DeclarativeBase):
    pass


class Word(Base):
    __tablename__ = "words"
    __table_args__ = (Index("UX_word", "word"),)
    id = Column(Integer, primary_key=True)
    # uuid is str type!
    # id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    word = Column(String, unique=True)
    frequency = Column(Float, default=None)


class Definition(Base):
    __tablename__ = "definitions"
    __table_args__ = (
        Index("UX_speech", "part_of_speech"),
        UniqueConstraint("word_id", "id", name="definition_unique"),
    )
    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    # part_of_speech = Column(Enum(PartOfSpeech))
    part_of_speech = Column(String)
    inflection = Column(String)
    phonetic_us = Column(String)
    phonetic_uk = Column(String)
    audio_us = Column(String)
    audio_uk = Column(String)
    synonyms = Column(String)
    antonyms = Column(String)


class Explanation(Base):
    __tablename__ = "explanations"
    __table_args__ = (
        UniqueConstraint("definition_id", "phrase_id", name="explanation_unique"),
        CheckConstraint(
            "(definition_id IS NOT NULL AND phrase_id IS NULL) OR (definition_id IS NULL AND phrase_id IS NOT NULL)",
            name="only_one_fk_not_null",
        ),
    )
    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    definition_id = Column(Integer, ForeignKey("definitions.id"), nullable=True)
    phrase_id = Column(Integer, ForeignKey("phrases.id"), nullable=True)
    explain = Column(String, nullable=False)
    subscript = Column(String, nullable=True, default=None)
    create_at = Column(Integer, default=int(datetime.now().timestamp()), nullable=False)


class Example(Base):
    __tablename__ = "examples"
    __table_args__ = (
        UniqueConstraint("explanation_id", "id", name="explanation_unique"),
    )
    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    explanation_id = Column(Integer, ForeignKey("explanations.id"), nullable=False)
    example = Column(String)


class Asset(Base):
    __tablename__ = "assets"
    __table_args__ = (
        Index("UX_asset", "word_id"),
        UniqueConstraint("word_id", "id", name="word_unique"),
    )
    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    filename = Column(String, nullable=False)


class Translation(Base):
    __tablename__ = "translations"
    __table_args__ = (
        UniqueConstraint("word_id", "definition_id", name="definition_unique"),
    )

    id = Column(Integer, primary_key=True)
    definition_id = Column(Integer, ForeignKey("definitions.id"), nullable=False)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    zh_CN = Column(String)
    zh_TW = Column(String)
    ja_JP = Column(String)
    ko_KR = Column(String)
    vi_VN = Column(String)
    th_TH = Column(String)
    ar_SA = Column(String)


class Phrase(Base):
    __tablename__ = "phrases"
    __table_args__ = (UniqueConstraint("phrase", "word_id", name="phrase_unique"),)
    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    phrase = Column(String, nullable=False, unique=True)
    part_of_speech = Column(String, nullable=False)
    frequency = Column(Float, default=None)


def test_duplicate_word(engine):
    import sqlalchemy as sql

    with engine.connect() as cursor:
        idx = 0
        for _ in range(2):
            stmt = sql.insert(Word).values(word="apple")
            try:
                cursor.execute(stmt)
                idx += 1
            except:
                print("Cannot replicate word in database")
            print("Had add word index: \x1b[31m%d\x1b[0m" % idx)
        cursor.commit()
    # with Session(engine) as session:
    #     idx = 0
    #     for word in (Word(word="apple") for _ in range(2)):
    #         session.add(word)
    #         idx += 1
    #         print("Had add word index: \x1b[31m%d\x1b[0m" % idx)
    #     try:
    #         session.commit()
    #     except:
    #         print("Cannot replicate word in database")
    # Better than Session because it can reserve data when failure


def test_inflection_search(engine):
    import sqlalchemy as sql

    definitions = [
        Definition(
            word_id=101,
            part_of_speech="verb",
            inflection="watch, watches, watching, watched, watched",
        ),
        Definition(word_id=102, part_of_speech="noun", inflection="watch, watches"),
        Definition(word_id=22, part_of_speech="noun", inflection="apple, apples"),
    ]
    with Session(engine) as session:
        try:
            session.add_all(definitions)
        except:
            raise Exception("Build table error")
        session.commit()
    stmt = sql.select(Definition.word_id).where(
        Definition.inflection.like("%watching%")
        # Definition.inflection.any_("watching") #postgresql support
    )
    with engine.connect() as cursor:
        ids = cursor.execute(stmt).fetchall()
    print(ids)


if __name__ == "__main__":
    import os
    import sqlalchemy as sql

    # os.system("rm oxfordstu.db")
    DB_URL = "sqlite:///oxfordstu.db"
    # engine = create_engine(DB_URL, echo=True)
    # Base.metadata.drop_all(engine)
    # Base.metadata.create_all(engine)
    # test_duplicate_word(engine)
    # test_inflection_search(engine)
    uid = uuid.uuid4()
    # uid = "-".join(["0" * 8, "0" * 4, "0" * 4, "0" * 4, "0" * 12])
