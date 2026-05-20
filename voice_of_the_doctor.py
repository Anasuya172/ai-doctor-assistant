from dotenv import load_dotenv
load_dotenv()

import os
import platform
import subprocess
from gtts import gTTS
import elevenlabs

# API KEY
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")


# =====================================================
# 🔊 AUDIO PLAY FUNCTION (WORKS ON WINDOWS)
# =====================================================
def play_audio(file):
    import subprocess
    subprocess.run([
        'ffplay',
        '-nodisp',      # no window
        '-autoexit',    # auto close
        file
    ])


# =====================================================
# 🔊 gTTS (FREE + ALWAYS WORKS)
# =====================================================
def text_to_speech_with_gtts(text, output_file):
    tts = gTTS(text=text, lang="en")
    tts.save(output_file)

    print("✅ gTTS saved:", output_file)
    play_audio(output_file)


# =====================================================
# 🔊 ElevenLabs (PREMIUM VOICE)
# =====================================================
def text_to_speech_with_elevenlabs(input_text, output_filepath):
    try:
        audio = elevenlabs.generate(
            text=input_text,
            voice="Aria",
            model="eleven_monolingual_v1",
            api_key=ELEVENLABS_API_KEY
        )

        # Handle generator response safely
        with open(output_filepath, "wb") as f:
            if isinstance(audio, bytes):
                f.write(audio)
            else:
                for chunk in audio:
                    f.write(chunk)

        print(f"ElevenLabs audio saved: {output_filepath}")

        if platform.system() == "Windows":
            os.startfile(output_filepath)

        return output_filepath

    except Exception as e:
        print("ElevenLabs Error:", e)


# =====================================================
# 🚀 MAIN
# =====================================================
if __name__ == "__main__":

    text = "Hi this is AI with Hassan, now everything is working perfectly!"

    # 🔹 gTTS (works 100%)
    text_to_speech_with_gtts(text, "gtts_output.mp3")

    # 🔹 ElevenLabs (uncomment if API working)
    # text_to_speech_with_elevenlabs(text, "eleven_output.mp3")
















