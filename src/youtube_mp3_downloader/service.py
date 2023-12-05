""" Скачивание видео с YouTube в аудиоформате MP3 """
import argparse
import os
from pathlib import Path

from pytube import YouTube

video_url_filename = "videos_to_mp3.txt"
output_audio_dir = "output_audio"
current_dir: str = Path(__file__).parent
from dataclasses import asdict

from .schemas import Audio


def get_video_urls() -> list[str]:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--urls", nargs="+", help="Список ссылок на видео (разделяйте ссылки пробелами)"
    )
    parser.add_argument(
        "--file_path",
        default=os.path.join(current_dir, video_url_filename),
        help="Путь к файлу с ссылками",
    )
    args = parser.parse_args()

    if args.urls:
        video_urls = args.urls
    else:
        with open(args.file_path, "r") as file:
            video_urls = file.readlines()
            video_urls = [url_str.strip() for url_str in video_urls]

    if not video_urls:
        raise ValueError("No video link found")

    return video_urls


def validate_urls(urls: list[str]) -> None:
    for url in urls:
        is_https: bool = url.startswith("https://")
        is_youtube_domain: bool = url.__contains__("youtube")
        if not is_https or not is_youtube_domain:
            raise ValueError(f"Invalid URL format: '{url}'")


def check_file_exists(filepath: str) -> bool:
    return os.path.isfile(path=filepath)


def progress_callback(*args, **kwargs):
    print("Идёт зарузка...")


def fetch_videos_as_audio(urls: list[str]) -> list[Audio]:
    output_audios = []
    for url in urls:
        yt = YouTube(url=url)
        # yt.register_on_complete_callback(func=compile)
        yt.register_on_progress_callback(func=progress_callback)
        video_stream = yt.streams.filter(only_audio=True, file_extension="mp4").first()

        # Загрузка видео, без кадров, только звук
        downloaded_video_filename: str = video_stream.default_filename.lower().replace(
            " ", "_"
        )
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
    return output_audios


def main():
    video_urls: list[str] = get_video_urls()
    validate_urls(urls=video_urls)
    for idx, url in enumerate(iterable=video_urls, start=1):
        # video_file_exists: bool = check_file_exists(filepath=)
        print(f"Видео {idx}: {url} | Будет загружено")
    audios: list[Audio] = fetch_videos_as_audio(urls=video_urls)
    for idx, audio in enumerate(iterable=audios, start=1):
        print(f"MP3 файл {idx}: \n {asdict(audio)}")
        print("#" * 30, end="\n")
