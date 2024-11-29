from typing import Any, Literal, TypedDict


class Identifier(TypedDict):
    title: str
    author: str
    module_name: str


CommandVerb = Literal["Durum", "Mesaj", "Motor0 açısı", "Motor1 açısı", "event"]


class Command(TypedDict):
    module_name: str
    author: str
    title: str
    verb: CommandVerb
    value: Any
