from dataclasses import dataclass


@dataclass
class Audio:
    title: str
    author: str
    length_str: str
    size: str
    filepath: str
