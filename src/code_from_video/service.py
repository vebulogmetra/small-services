import os
from pathlib import Path

import cv2
import inquirer
import pytesseract
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from pytube import YouTube

from src.code_from_video.settings import (
    default_code_output_dir,
    default_video_output_dir,
)

current_dir: str = Path(__file__).parent


def check_file_exists(filepath: str) -> bool:
    return os.path.isfile(path=filepath)


def download_youtube_video(url: str, output_path: str) -> str:
    yt = YouTube(url)
    stream = yt.streams.get_highest_resolution()
    video_filename: str = stream.default_filename.lower().replace(" ", "_")
    video_filepath: str = os.path.join(output_path, video_filename)
    print("[:::] Checking file video already exists...")
    video_exists: bool = check_file_exists(filepath=video_filepath)
    print(f"[:::] Video exists is {video_exists}")
    # Если видео не скачано ранее, скачиваем
    if not video_exists:
        print("[:::] Download video...")
        stream.download(output_path=output_path, filename=video_filename)

    return video_filepath


def trim_video(video_filepath: str, start_time: int, end_time: int) -> str:
    filename = video_filepath.split("/")[-1]
    trimmed_video_filepath = video_filepath.replace(filename, "_trimmed.mp4")
    # Обрезка видео
    ffmpeg_extract_subclip(
        filename=video_filepath,
        t1=start_time,
        t2=end_time,
        targetname=trimmed_video_filepath,
    )
    return trimmed_video_filepath


# Распознавание кода на видео
def recognize_code_in_video_frame(video_path: str) -> set[str]:
    print(f"[:::] Recognize code in video: {video_path} ...")
    cap = cv2.VideoCapture(video_path)
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    print("frame_rate: ", frame_rate)
    frame_no = 0
    res_code = []
    while cap.isOpened():
        frame_no += 1
        ret, frame = cap.read()
        if not ret:
            break
        # 10 сек таймаут на распознавание
        code: str = pytesseract.image_to_string(image=frame, lang="eng", timeout=10)
        # print("Код на кадре", frame_no, ":", code)
        if code:
            res_code.append(code)
    cap.release()
    return set(res_code)


# Сохранение распознанного кода в файл
def save_to_file(data: list[str], output_file: str):
    print(f"[:::] Write code to file: {output_file}")
    with open(output_file, "a") as file_:
        for line in data:
            if line:
                file_.write("\n")
                file_.write(line)
                file_.write("=" * 20)
                file_.write("\n")


def get_url_from_input() -> str:
    questions = [
        inquirer.Text(
            "video_url",
            message="Ссылка на видео",
        ),
    ]
    answers: dict = inquirer.prompt(questions)
    video_url: str = answers.get("video_url", None)
    if not video_url:
        raise ValueError("Нет входных данных")
    return video_url


def validate_url(url: str):
    is_https: bool = url.startswith("https://")
    is_youtube_domain: bool = url.__contains__("youtube")
    # :TODO Добавить ещё проверок
    if not is_https or not is_youtube_domain:
        raise ValueError("Invalid URL format")


def get_time_from_input() -> str:
    questions = [
        inquirer.Text(
            "start_time_str",
            message="С какого времени начнём? [MM:SS]",
        ),
    ]
    answers: dict = inquirer.prompt(questions)
    start_time_str: str = answers.get("start_time_str", None)

    if not start_time_str:
        raise ValueError("Нет входных данных")
    return start_time_str


def validate_fragment_time(time_str: str):
    is_correct_len: bool = len(time_str) <= 5
    mm, ss = time_str.split(":")
    is_nums: bool = mm.isalnum() and ss.isalnum()

    if not is_correct_len or not is_nums:
        raise ValueError("Invalid Time format")


def time_str_to_seconds(time_str: str) -> int:
    try:
        m, s = map(int, time_str.split(":"))
        total_seconds: int = m * 60 + s
        return total_seconds
    except ValueError:
        raise ValueError("Invalid Time format")


def main():
    # https://www.youtube.com/shorts/BhPNtdwtOmo
    youtube_url = get_url_from_input()
    print("[:::] Validate url...")
    validate_url(url=youtube_url)
    # :TODO возможность использовать видео целиком, если не вводить время
    # 00:23
    start_time = get_time_from_input()
    print("[:::] Validate start time...")
    validate_fragment_time(time_str=start_time)
    # 23
    start_time_sec: int = time_str_to_seconds(time_str=start_time)
    # 23 + 1
    end_time_sec: int = start_time_sec + 1

    video_output_path: str = os.path.join(current_dir, default_video_output_dir)
    video_filepath: str = download_youtube_video(
        url=youtube_url, output_path=video_output_path
    )
    print(f"[:::] Downloaded video path: {video_filepath}")
    trim_video_filepath: str = trim_video(
        video_filepath=video_filepath, start_time=start_time_sec, end_time=end_time_sec
    )
    print(f"[:::] Trimmed video path: {trim_video_filepath}")

    video_title = video_filepath.split("/")[-1].split(".")[0]
    code_filename = f"code_{video_title}.txt"
    code_output_filepath: str = os.path.join(
        current_dir, default_code_output_dir, code_filename
    )
    code = recognize_code_in_video_frame(video_path=trim_video_filepath)
    os.remove(path=trim_video_filepath)

    save_to_file(data=code, output_file=code_output_filepath)
