from dataclasses import dataclass


@dataclass
class Audio:
    title: str
    author: str
    length_str: str
    size: str
    filepath: str


@dataclass
class VideoInfo:
    video_url: str
    video_title: str
    video_local_exists: bool
