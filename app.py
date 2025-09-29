import os
import time
import streamlit as st
import speech_recognition as sr
from moviepy.editor import VideoFileClip
from pydub import AudioSegment, silence
import tempfile

st.set_page_config(page_title="MindScribe - Audio/Video Transcriber")
st.title("🧠 MindScribe: AI-Powered Transcriber")

uploaded_file = st.file_uploader("Upload an Audio or Video File", type=["mp3", "wav", "ogg", "mp4", "mkv", "mov"])

recognizer = sr.Recognizer()

def extract_audio(file_path):
    if file_path.lower().endswith((".mp4", ".mkv", ".mov")):
        video = VideoFileClip(file_path)
        temp_audio_path = file_path + ".wav"
        video.audio.write_audiofile(temp_audio_path)
        return temp_audio_path
    return file_path

def clean_audio(audio_path):
    sound = AudioSegment.from_file(audio_path)
    sound = sound.set_channels(1)  # mono
    sound = sound.set_frame_rate(16000)
    sound = sound.normalize()
    return sound

def split_into_chunks(audio, min_silence_len=700, silence_thresh=-40):
    return silence.split_on_silence(audio,
                                    min_silence_len=min_silence_len,
                                    silence_thresh=silence_thresh,
                                    keep_silence=400)

def transcribe_chunks(chunks):
    recognizer = sr.Recognizer()
    full_transcript = ""

    for i, chunk in enumerate(chunks):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            chunk.export(f.name, format="wav")
            temp_path = f.name

        st.info(f"🎧 Transcribing chunk {i+1} of {len(chunks)}...")
        try:
            with sr.AudioFile(temp_path) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)
                full_transcript += text + " "
        except sr.UnknownValueError:
            full_transcript += "[Unclear audio] "
        except sr.RequestError:
            st.error("❌ API unavailable or check your internet connection")
            break
        finally:
            # Delay to ensure file is released
            time.sleep(0.1)
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except PermissionError:
                    pass  # Ignore if still locked

    return full_transcript.strip()


if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp.write(uploaded_file.read())
        temp_path = temp.name

    st.info("🎧 Extracting and preprocessing audio...")
    audio_path = extract_audio(temp_path)
    clean = clean_audio(audio_path)
    chunks = split_into_chunks(clean)

    if not chunks:
        st.warning("⚠️ Could not detect speech chunks. Try a different file or speak louder.")
    else:
        st.success(f"✅ {len(chunks)} audio chunks ready for transcription.")
        transcript = transcribe_chunks(chunks)

        if transcript:
            st.subheader("📄 Final Transcript")
            st.text_area("Transcript:", transcript, height=300)

            st.download_button("📥 Download Transcript", transcript, file_name="transcript.txt")
