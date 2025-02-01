import os
from gtts import gTTS
from moviepy import AudioFileClip, TextClip, concatenate_audioclips, AudioClip, concatenate_videoclips

PHRASES_FILE = "phrases.txt"
OUTPUT_VIDEO = "result.mp4"


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


def build_video_clips(phrases, silence_duration: float = 1) -> (list, list):
    video_clips = []
    temp_files = []
    
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
        
        # Создаем текстовый видеоклип с оверлеем фразы
        text = f"EN: {eng}\nRU: {rus}"
        txt_clip = TextClip(
            "Arial",
            text,
            font_size=50,
            color='white',
            bg_color='black',
            size=(1280, 720),
            method='caption'
        ).with_duration(total_duration)
        
        # Накладываем аудио на текстовый клип
        video_clip = txt_clip.with_audio(combined_audio)
        
        video_clips.append(video_clip)
    
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
