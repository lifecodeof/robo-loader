from typing import Literal, TypedDict


class Identifier(TypedDict):
    title: str
    author: str


class Command(TypedDict):
    author: str
    title: str
    verb: Literal["Durum", "Mesaj", "Motor açısı"]
    value: str
