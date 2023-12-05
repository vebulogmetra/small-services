""" Скачивание видео с YouTube в аудиоформате MP3 """
import os
from dataclasses import asdict
from pathlib import Path
from pprint import pprint

import inquirer
from pytube import YouTube

from src.youtube_mp3_downloader.schemas import Audio, VideoInfo
from src.youtube_mp3_downloader.settings import default_urls_filename, output_audio_dir

current_dir: str = Path(__file__).parent


def validate_urls(urls: list[str]) -> None:
    for url in urls:
        print("[:::] Validate url ", url)
        is_https: bool = url.startswith("https://")
        is_youtube_domain: bool = url.__contains__("youtube")
        if not is_https or not is_youtube_domain:
            raise ValueError(f"Invalid URL format: '{url}'")


def progress_callback(*args, **kwargs):
    print("Идёт зарузка...")


def fetch_videos_as_audio(videos: list[VideoInfo]) -> list[Audio]:
    output_audios = []
    for video in videos:
        if not video.video_local_exists:
            yt = YouTube(url=video.video_url)
            # yt.register_on_complete_callback(func=compile)
            yt.register_on_progress_callback(func=progress_callback)
            video_stream = yt.streams.filter(
                only_audio=True, file_extension="mp4"
            ).first()

            # Загрузка видео, без кадров, только звук
            downloaded_video_filename: str = (
                video_stream.default_filename.lower().replace(" ", "_")
            )

            print("[:::] Fetch audio for ", downloaded_video_filename)

            video_stream.download(
                output_path=os.path.join(current_dir, output_audio_dir),
                filename=downloaded_video_filename,
            )

            video_filepath: str = os.path.join(
                current_dir, output_audio_dir, downloaded_video_filename
            )
            audio_filepath: str = video_filepath.replace(".mp4", ".mp3")

            os.rename(video_filepath, audio_filepath)

            audio = Audio(
                title=video_stream.title,
                author=yt.author,
                length_str=f"{(yt.length // 60):02d}:{(yt.length % 60):02d}",
                size=f"{video_stream.filesize_mb} Mb",
                filepath=os.path.join(current_dir, output_audio_dir, audio_filepath),
            )
            output_audios.append(audio)
        else:
            audio = Audio(
                title=video.video_title,
                author="No info",
                length_str="No info",
                size="No info",
                filepath=os.path.join(
                    current_dir, output_audio_dir, f"{video.video_title}.mp3"
                ),
            )
            output_audios.append(audio)
    return output_audios


def get_urls_from_input() -> list[str]:
    questions = [
        inquirer.Text(
            "urls",
            message="Ссылки на видео (разделяйте ссылки пробелами) или оставьте пустым",
        ),
    ]
    answers: dict = inquirer.prompt(questions)
    urls: str = answers.get("urls", None)
    urls: list[str] = urls.split()
    return urls


def get_urls_from_file() -> list[str]:
    questions = [
        inquirer.Text(
            "urls_filepath",
            message=f"Путь к файлу со ссылками (по умолчанию '{default_urls_filename}')",
            default=default_urls_filename,
        ),
    ]
    answers: dict = inquirer.prompt(questions)
    urls_filepath: str = answers.get("urls_filepath", None)
    if urls_filepath:
        if urls_filepath == default_urls_filename:
            urls_filepath = os.path.join(current_dir, urls_filepath)
        with open(urls_filepath, "r") as file:
            video_urls = file.readlines()
            video_urls = [url_str.strip() for url_str in video_urls]
        if not video_urls:
            raise ValueError("Файл пуст")
    else:
        raise ValueError("Нет входных данных")
    return video_urls


def check_file_local_exists(filepath: str) -> bool:
    return os.path.isfile(path=filepath)


def fetch_video_info(video_urls: list[str]) -> list[VideoInfo]:
    video_titles = []
    for url in video_urls:
        print("[:::] Fetch video info from ", url)
        yt = YouTube(url=url)
        video_stream = yt.streams.filter(only_audio=True, file_extension="mp4").first()
        video_title_like_filename: str = video_stream.default_filename.lower().replace(
            " ", "_"
        )
        video_filepath: str = os.path.join(
            current_dir, output_audio_dir, video_title_like_filename
        )
        audio_filepath: str = video_filepath.replace(".mp4", ".mp3")
        video_local_exists: bool = check_file_local_exists(filepath=audio_filepath)
        video_obj = VideoInfo(
            video_url=url,
            video_title=video_title_like_filename,
            video_local_exists=video_local_exists,
        )
        video_titles.append(video_obj)
    return video_titles


def main():
    video_urls: list[str] = get_urls_from_input()
    if not video_urls:
        video_urls: list[str] = get_urls_from_file()
    print("[:::] Validate urls...")
    validate_urls(urls=video_urls)
    print("[:::] Fetch videos info...")
    videos: list[VideoInfo] = fetch_video_info(video_urls=video_urls)

    for idx, video in enumerate(iterable=videos, start=1):
        if video.video_local_exists:
            print(f"[:::] Видео {idx}: {video.video_title} | Уже загружено")
        else:
            print(f"[:::] Видео {idx}: {video.video_title} | Будет загружено")
    print("[:::] Fetch videos as audio...")
    audios: list[Audio] = fetch_videos_as_audio(videos=videos)
    for idx, audio in enumerate(iterable=audios, start=1):
        print(f"[:::] MP3 файл {idx}:")
        pprint(asdict(audio))
        print("[:::] ", "#" * 30, end="\n")
