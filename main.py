import os
from pathlib import Path
import json
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
import webrtcvad
import wave
import speech_recognition as sr
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from vosk import Model, KaldiRecognizer
from pathlib import Path


# Шаг 1: Разбиение видео на части
def split_video(video_path, output_dir, chunk_duration=300):
    """
    Разделяет длинное видео на части.
    video_path: Путь к исходному видео.
    output_dir: Директория для сохранения частей.
    chunk_duration: Длительность одной части в секундах (по умолчанию 5 минут).
    """
    video = VideoFileClip(video_path)
    video_duration = int(video.duration)  # Общая длительность видео в секундах
    chunk_paths = []

    for start_time in range(0, video_duration, chunk_duration):
        end_time = min(start_time + chunk_duration, video_duration)
        chunk_path = os.path.join(output_dir, f"chunk_{start_time}-{end_time}.mp4")
        ffmpeg_extract_subclip(video_path, start_time, end_time, targetname=chunk_path)
        chunk_paths.append(chunk_path)

    print(f"Видео разбито на {len(chunk_paths)} частей.")
    return chunk_paths


# Шаг 2: Извлечение аудио из каждого видеофрагмента
def extract_audio_from_chunks(chunk_paths, output_dir):
    """
    Извлекает аудиодорожки из видеофрагментов.
    chunk_paths: Список путей к частям видео.
    output_dir: Директория для сохранения аудиофайлов.
    """
    audio_paths = []
    for chunk_path in chunk_paths:
        audio_path = os.path.join(output_dir, str(os.path.basename(chunk_path)).replace(".mp4", ".wav"))
        video = VideoFileClip(chunk_path)
        audio = video.audio
        audio.write_audiofile(audio_path, codec="pcm_s16le")  # WAV формат
        audio.close()
        video.close()
        audio_paths.append(audio_path)

    print(f"Аудио извлечено из {len(audio_paths)} частей.")
    return audio_paths


# Шаг 3: Фильтрация речи с использованием WebRTC VAD
# def detect_voice(audio_path, frame_duration_ms=30):
#     """
#     Определяет участки с речью (человеческой) с использованием WebRTC VAD.
#     audio_path: Путь к аудиофайлу.
#     frame_duration_ms: Длительность одного кадра в миллисекундах.
#     """
#     vad = webrtcvad.Vad(3)  # Уровень агрессивности (0-3), 3 — самый строгий режим
#
#     # Преобразуем в моно, если необходимо
#     audio = AudioSegment.from_wav(audio_path)
#     if audio.channels != 1:
#         audio = audio.set_channels(1)
#         audio.export(audio_path, format="wav")
#
#     if audio.frame_rate not in (8000, 16000, 32000):
#         audio = audio.set_frame_rate(16000)
#         audio.export(audio_path, format="wav")
#
#     with wave.open(audio_path, 'rb') as wf:
#         assert wf.getnchannels() == 1  # Mono
#         assert wf.getsampwidth() == 2  # 16-bit PCM
#         assert wf.getframerate() in (8000, 16000, 32000)  # Поддерживаемые частоты
#
#         frame_size = int(wf.getframerate() * frame_duration_ms / 1000)
#         intervals = []
#         start_time = 0
#
#         while True:
#             frame = wf.readframes(frame_size)
#             if len(frame) < frame_size * wf.getsampwidth():
#                 break
#             is_speech = vad.is_speech(frame, wf.getframerate())
#             if is_speech:
#                 intervals.append((start_time, start_time + frame_duration_ms))
#             start_time += frame_duration_ms
#
#     return intervals


# Шаг 4: Распознавание речи для аудиофрагментов с речью
# def recognize_speech_from_audio(audio_path, voice_segments, language="en-US"):
#     """
#     Распознаёт речь только в тех участках аудио, где есть человеческая речь.
#     :param audio_path: Путь к аудиофайлу.
#     :param voice_segments: Список интервалов с активной речью.
#     :param language: Язык распознавания.
#     :return: Объединённый текст.
#     """
#     recognizer = sr.Recognizer()
#     full_text = ""
#     audio = AudioSegment.from_file(audio_path)
#
#     for start, end in voice_segments:
#         print(f"Обработка интервала с речью: {start} - {end}")
#         segment = audio[start:end]  # Вырезаем фрагмент с речью
#         segment.export("temp.wav", format="wav")  # Экспортируем фрагмент во временный файл
#
#         with sr.AudioFile("temp.wav") as source:
#             audio_data = recognizer.record(source)
#
#         try:
#             text = recognizer.recognize_google(audio_data, language=language)
#             full_text += text + " "
#             print(f"Распознанный текст: {text}")
#         except sr.UnknownValueError:
#             print(f"Не удалось распознать речь в интервале {start} - {end}")
#         except sr.RequestError as e:
#             print(f"Ошибка сервиса: {e}")
#
#         os.remove("temp.wav")  # Удаляем временный файл
#
#     return full_text

# Шаг 5: Полный процесс с разбиением видео и извлечением текста
# def process_video_to_text(video_path, output_dir, chunk_duration=300, language="en-US"):
#     """
#     Процесс обработки видео: разбиение, извлечение аудио и распознавание текста.
#     :param video_path: Путь к видеофайлу.
#     :param output_dir: Директория для сохранения промежуточных файлов.
#     :param chunk_duration: Длительность одного фрагмента видео (в секундах).
#     :param language: Язык для распознавания.
#     :return: Распознанный текст.
#     """
#     # Разбиваем видео на части
#     chunk_paths = split_video(video_path, output_dir, chunk_duration)
#
#     # Извлекаем аудио из каждого фрагмента
#     audio_paths = extract_audio_from_chunks(chunk_paths, output_dir)
#
#     full_text = ""
#     for audio_path in audio_paths:
#         # Определяем интервалы с речью
#         voice_segments = detect_voice(audio_path)
#
#         # Распознаём текст из аудио, где есть речь
#         text = recognize_speech_from_audio(audio_path, voice_segments, language)
#         full_text += text
#
#     print("Обработка завершена.")
#     return full_text
# ---------------------------------------------------------------------------------------------------
# Шаг 5
def convert_audio_to_vosk_format(audio_path, output_path):
    """
    Конвертирует аудиофайл в формат mono WAV с частотой 16000 Гц.
    audio_path: Путь к исходному аудиофайлу.
   output_path: Путь для сохранения преобразованного файла.
    """
    # Загружаем аудиофайл
    audio = AudioSegment.from_file(audio_path)

    # Конвертируем в моно
    audio = audio.set_channels(1)

    # Конвертируем в 16-битный формат PCM и частоту 16000 Гц
    audio = audio.set_frame_rate(16000)

    output_path = Path(output_path, 'wav_files')
    os.makedirs(output_path, exist_ok=True)

    # Сохраняем в формате WAV
    converted_path = os.path.join(output_path, str(os.path.basename(audio_path)).replace(".wav", "_converted.wav"))
    audio.export(converted_path, format="wav")

    print(f"Файл {audio_path} преобразован в {converted_path}")
    return converted_path

# Шаг 6
def recognize_speech_from_audio(audio_path, model_path, output_dir, start_time=0):
    """
    Распознаёт речь из аудиофайлов с использованием Vosk и сохраняет текст.
    audio_path: Путь к аудиофайлу.
    model_path: Путь к модели Vosk.
    output_dir: Директория для сохранения результатов.
    start_time: Начальное время (в секундах) для отсчета времени в тексте.
    """
    output_dir = Path(output_dir, 'results')
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Модель Vosk не найдена по пути: {model_path}")

    try:
        with wave.open(audio_path, "rb") as wf:
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() not in (8000, 16000, 32000):
                raise ValueError
    except (wave.Error, ValueError):
        print("Преобразование аудиофайла в поддерживаемый формат...")
        audio_path = convert_audio_to_vosk_format(audio_path, output_dir)

    model = Model(model_path)

    with wave.open(audio_path, "rb") as wf:
        recognizer = KaldiRecognizer(model, wf.getframerate())
        recognizer.SetWords(True)  # Включить временные метки слов

        text_file_path = os.path.join(output_dir, os.path.splitext(os.path.basename(audio_path))[0] + ".txt")
        current_time = start_time

        with open(text_file_path, "w", encoding="utf-8") as file:
            buffer = ""
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    if "result" in result and result["result"]:
                        for word_info in result["result"]:
                            word = word_info["word"]
                            word_start = word_info["start"] + current_time
                            minutes = int(word_start // 60)
                            seconds = int(word_start % 60)
                            if len(buffer.split()) >= 10 or (word_start - current_time) >= 5:
                                file.write(f"[{minutes:02}:{seconds:02}] {buffer.strip()}\n")
                                buffer = ""
                            buffer += f" {word}"
                current_time += len(data) / wf.getframerate()

            # Запись оставшегося в буфере текста
            if buffer.strip():
                file.write(f"[{int(current_time // 60):02}:{int(current_time % 60):02}] {buffer.strip()}\n")

        print(f"Текст для {audio_path} сохранён в {text_file_path}")

# Шаг 3
def process_video_to_text(video_path, output_dir, chunk_duration=300, language="en-US"):
    chunk_paths = split_video(video_path, output_dir, chunk_duration)
    audio_paths = extract_audio_from_chunks(chunk_paths, output_dir)

    full_text = ""
    for audio_path in audio_paths:
        text = recognize_speech_from_audio(audio_path, "model/vosk-model-en-us-0.22-lgraph", output_dir)
        text = str(text) + '\n'
        full_text += text

    print("Обработка завершена.")
    return full_text


if __name__ == "__main__":
    video_path = "data/TheStoryOfMaths1.mp4"  # Путь к видеофайлу
    output_dir = "output_chunks"  # Папка для сохранения частей видео и аудио
    os.makedirs(output_dir, exist_ok=True)

    recognized_text = process_video_to_text(video_path, output_dir, language="en-US")
    print("Полный распознанный текст:")
    print(recognized_text)
