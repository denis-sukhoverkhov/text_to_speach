import glob
import os
import random
from gtts import gTTS
from moviepy import AudioFileClip, ColorClip, CompositeVideoClip, ImageClip, TextClip, concatenate_audioclips, AudioClip, concatenate_videoclips
from icrawler.builtin import GoogleImageCrawler

PHRASES_FILE = "phrases.txt"
OUTPUT_VIDEO = "result.mp4"
TEMP_IMAGES_DIR = "temp_images"


def load_phrases(filepath: str):
    phrases = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Use "|||" as a separator between English and Russian phrases
            if "|||" in line:
                eng, rus = line.split("|||", 1)
                phrases.append((eng.strip(), rus.strip()))
            else:
                print(f"Invalid line: {line}")
    return phrases


def generate_audio(text: str, lang: str, filename: str) -> str:
    tts = gTTS(text=text, lang=lang)
    tts.save(filename)
    return filename


def create_silence(duration: float, fps: int = 44100) -> AudioClip:
    return AudioClip(lambda t: 0, duration=duration, fps=fps)


def build_audio_clips(phrases, silence_duration: float = 1) -> (list, list):
    """
    Form audio clips from phrases with silence between them.
    """
    clips = []
    temp_files = []

    for idx, (eng, rus) in enumerate(phrases):
        eng_file = f"temp_eng_{idx}.mp3"
        rus_file = f"temp_rus_{idx}.mp3"
        generate_audio(eng, "en", eng_file)
        generate_audio(rus, "ru", rus_file)
        temp_files.extend([eng_file, rus_file])

        eng_clip = AudioFileClip(eng_file)
        rus_clip = AudioFileClip(rus_file)
        silence_clip = create_silence(silence_duration)

        clips.extend([eng_clip, silence_clip, rus_clip, silence_clip, silence_clip])

    return clips, temp_files


def download_image(query: str, idx: int) -> str:
    # Создаем директорию, если ее нет
    os.makedirs(TEMP_IMAGES_DIR, exist_ok=True)
    
    # Очистка временной директории (удаляем все файлы в ней)
    for filename in os.listdir(TEMP_IMAGES_DIR):
        file_path = os.path.join(TEMP_IMAGES_DIR, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
    
    # Создаем экземпляр краулера с указанием директории хранения
    crawler = GoogleImageCrawler(storage={'root_dir': TEMP_IMAGES_DIR})
    
    # Скачиваем несколько изображений (например, до 3) для большего выбора
    crawler.crawl(keyword=query, max_num=3)
    
    # Получаем список скачанных файлов
    images = glob.glob(os.path.join(TEMP_IMAGES_DIR, "*"))
    if images:
        # Выбираем случайное изображение из найденных
        chosen = random.choice(images)
        new_filename = os.path.join(TEMP_IMAGES_DIR, f"image_{idx}.jpg")
        os.rename(chosen, new_filename)
        return new_filename
    else:
        return None

def build_video_clips(phrases, silence_duration: float = 1) -> (list, list):
    video_clips = []
    temp_files = []
    temp_img_files = []
    
    for idx, (eng, rus) in enumerate(phrases):
        # Генерация аудио для английской и русской версии
        eng_file = f"temp_eng_{idx}.mp3"
        rus_file = f"temp_rus_{idx}.mp3"
        generate_audio(eng, "en", eng_file)
        generate_audio(rus, "ru", rus_file)
        temp_files.extend([eng_file, rus_file])
        
        # Загружаем аудиоклипы
        eng_clip = AudioFileClip(eng_file)
        rus_clip = AudioFileClip(rus_file)
        silence_clip = create_silence(silence_duration)
        
        # Объединяем аудио:
        #   [английская озвучка, пауза, русская озвучка, 2 паузы (для дополнительной задержки)]
        combined_audio = concatenate_audioclips([
            eng_clip,
            silence_clip,
            rus_clip,
            silence_clip,
            silence_clip
        ])
        
        total_duration = combined_audio.duration

        image_file = download_image(eng, idx)
        if image_file:
            temp_img_files.append(image_file)

            img_clip = ImageClip(image_file).resized(new_size=(1280, 720)).with_duration(total_duration)
        else:
            # Если изображение не найдено, создаем черный фон
            img_clip = ImageClip("black", duration=total_duration, size=(1280, 720))
        
        # Создаем текстовый видеоклип с оверлеем фразы
        text = f"EN: {eng}\nRU: {rus}"
        txt_clip = TextClip(
            "Arial",
            text,
            font_size=50,
            color='white',
            # bg_color='black',
            # size=(1280, 720),
            method='label'
        ).with_duration(total_duration)

        padding = 20
        bg_width = txt_clip.w + 2 * padding
        bg_height = txt_clip.h + 2 * padding
        bg_clip = ColorClip(size=(bg_width, bg_height), color=(0, 0, 0)).with_duration(total_duration)

        text_with_bg = CompositeVideoClip([
            bg_clip.with_position("center"),
            txt_clip.with_position("center")
        ]).with_duration(total_duration)

        text_with_bg = text_with_bg.with_position(("center", "bottom"))
        
        # Накладываем аудио на текстовый клип
        composite_clip = CompositeVideoClip([img_clip, text_with_bg]).with_audio(combined_audio)
        
        video_clips.append(composite_clip)
    
    return video_clips, temp_files


def main():
    phrases = load_phrases(PHRASES_FILE)
    if not phrases:
        print("File with phrases is empty or not found.")
        return

    video_clips, temp_files = build_video_clips(phrases, silence_duration=1)

    final_video = concatenate_videoclips(video_clips, method="compose")
    final_video.write_videofile(OUTPUT_VIDEO, fps=24)

    for filepath in temp_files:
        if os.path.exists(filepath):
            os.remove(filepath)

    print(f"Result file is saved as '{OUTPUT_VIDEO}'")


if __name__ == "__main__":
    main()
