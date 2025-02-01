import os
from gtts import gTTS
from moviepy import AudioFileClip, concatenate_audioclips, AudioClip

PHRASES_FILE = "phrases.txt"


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


def main():
    phrases = load_phrases(PHRASES_FILE)
    if not phrases:
        print("File with phrases is empty or not found.")
        return

    clips, temp_files = build_audio_clips(phrases, silence_duration=1)

    combined_audio = concatenate_audioclips(clips)
    output_filename = "result.mp3"
    combined_audio.write_audiofile(output_filename)

    for filepath in temp_files:
        if os.path.exists(filepath):
            os.remove(filepath)

    print(f"Result audio file is saved as '{output_filename}'")


if __name__ == "__main__":
    main()
