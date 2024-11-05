import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Index,
    Enum,
    UniqueConstraint,
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
    alphabet_us = Column(String)
    alphabet_uk = Column(String)
    audio_us = Column(String)
    audio_uk = Column(String)
    chinese = Column(String)


class Explanation(Base):
    __tablename__ = "explanations"
    __table_args__ = (
        UniqueConstraint("definition_id", "id", name="explanation_unique"),
    )
    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    definition_id = Column(Integer, ForeignKey("definitions.id"), nullable=False)
    explain = Column(String, nullable=False)
    subscript = Column(String, nullable=True, default=None)
    create_at = Column(Integer, default=int(datetime.now().timestamp()), nullable=False)


class Example(Base):
    __tablename__ = "examples"
    __table_args__ = (UniqueConstraint("explanation_id", "id", name="example_unique"),)
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
    engine = create_engine(DB_URL, echo=True)
    # Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    # test_duplicate_word(engine)
    # test_inflection_search(engine)
    """ expression inserts
    print(sql.insert(Word).values(word="", id=0))
    print("=" * 10 + "definition" + "=" * 10)
    print(
        sql.insert(Definition)
        .values(
            word_id=0,
            **{
                "part_of_speech": "",
                "inflection": "",
                "alphabet_uk": "",
                "alphabet_us": "",
                "audio_uk": "",
                "audio_us": "",
                "chinese": "",
            }
        )
        .returning(Definition.id)
    )
    print("=" * 10 + "explanation" + "=" * 10)
    print(
        sql.insert(Explanation)
        .values(word_id=0, definition_id=0, **{"explain": "", "subscript": ""})
        .returning(Explanation.id)
    )
    print("=" * 10 + "example" + "=" * 10)
    print(
        sql.insert(Example).values(word_id=0, explanation_id=0, example="")
        # .returning(Example.id)
    )
"""
""" expression fetch word_id
print(
    sql.select(
        Word.id,
        Word.word,
        Asset.filename,
        Definition.part_of_speech,
        Definition.inflection,
        Definition.alphabet_uk,
        Definition.alphabet_us,
        Definition.audio_uk,
        Definition.audio_us,
        Definition.chinese,
        Explanation.subscript,
        Explanation.explain,
        Example.example,
    )
    .outerjoin(Asset, Asset.word_id == Word.id)
    .join(Definition, Word.id == Definition.word_id)
    .join(Explanation, Explanation.definition_id == Definition.id)
    .outerjoin(Example, Example.explanation_id == Explanation.id)
    .where(Word.id.in_([]))
)
"""
