from pydub import AudioSegment
import speech_recognition as sr


def mp3_to_wav(mp3_file_path, wav_file_path):
    try:
        audio = AudioSegment.from_mp3(mp3_file_path)
        audio.export(wav_file_path, format="wav")
        print(f"Converted {mp3_file_path} to {wav_file_path}")
    except Exception as e:
        print(f"Error converting MP3 to WAV: {e}")


def transcribe_audio(wav_file_path):
    recognizer = sr.Recognizer()

    try:
        # Load the WAV audio file
        with sr.AudioFile(wav_file_path) as source:
            print("Listening...")
            audio = recognizer.record(source)
            # Recognize speech using Google Web Speech API
            text = recognizer.recognize_google(audio, language="uz-UZ")
            print("Transcription: " + text)
    except sr.UnknownValueError:
        print("Sorry, I did not understand that.")
    except sr.RequestError as e:
        print(f"Sorry, there was an error with the request: {e}")
    except Exception as e:
        print(f"Error transcribing audio: {e}")


# Paths to the input MP3 file and output WAV file
mp3_file_path = "uzbek_audio.mp3"
wav_file_path = "uzbek_audio.wav"

# Convert MP3 to WAV and transcribe it
mp3_to_wav(mp3_file_path, wav_file_path)
transcribe_audio(wav_file_path)
