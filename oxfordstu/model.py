from dataclasses import dataclass
from typing import List, Any, TypeVar, Callable, Type, cast


T = TypeVar("T")


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


@dataclass
class Def:
    explanation: str
    subscript: str | None
    examples: List[str]

    @staticmethod
    def from_dict(obj: Any) -> "Def":
        assert isinstance(obj, dict)
        explanation = from_str(obj.get("explanation"))
        subscript = obj.get("subscript")
        examples = from_list(from_str, obj.get("examples"))
        return Def(explanation, subscript, examples)

    def to_dict(self) -> dict:
        result: dict = {}
        result["explanation"] = from_str(self.explanation)
        result["subscript"] = self.subscript
        result["examples"] = from_list(from_str, self.examples)
        return result


@dataclass
class Audio:
    uk: str | None
    us: str | None

    @staticmethod
    def from_dict(obj: Any) -> "Audio":
        assert isinstance(obj, dict)
        uk = obj.get("uk")
        us = obj.get("us")
        return Audio(uk, us)

    def to_dict(self) -> dict:
        result: dict = {}
        result["uk"] = self.uk
        result["us"] = self.us
        return result


@dataclass
class PartWord:
    # only can use to oxfordstu_dict or cambridge
    part_word_def: List[Def]
    audio: Audio

    @staticmethod
    def from_dict(obj: Any) -> "PartWord":
        assert isinstance(obj, dict)
        part_word_def = from_list(Def.from_dict, obj.get("def", []))
        audio = Audio.from_dict(obj.get("audio", {}))
        return PartWord(part_word_def, audio)

    def to_dict(self) -> dict:
        result: dict = {}
        result["def"] = from_list(lambda x: to_class(Def, x), self.part_word_def)
        result["audio"] = self.audio.to_dict()
        return result


@dataclass
class Thesaurus:
    synonyms: str | None = None
    antonyms: str | None = None

    @staticmethod
    def from_dict(obj: Any) -> "Thesaurus":
        assert isinstance(obj, dict)
        synonyms = obj.get("Synonyms")
        antonyms = obj.get("Antonyms")
        return Thesaurus(synonyms, antonyms)

    def to_dict(self) -> dict:
        result: dict = {}
        result["Synonyms"] = self.synonyms
        result["Antonyms"] = self.antonyms
        return result
