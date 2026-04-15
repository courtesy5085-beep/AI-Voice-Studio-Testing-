import streamlit as st
from gtts import gTTS
import speech_recognition as sr
from langdetect import detect
from deep_translator import GoogleTranslator
from pypdf import PdfReader
from docx import Document
from pydub import AudioSegment
import tempfile
import io
import base64
import time
from datetime import datetime
import edge_tts
import asyncio

# ---------- CONFIG ----------
st.set_page_config(
    page_title="AI Voice Studio Pro",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- CUSTOM CSS - MODERN UI ----------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    * { font-family: 'Inter', sans-serif; }

  .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        padding: 3rem 2rem;
        border-radius: 24px;
        text-align: center;
        color: white;
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4);
        margin-bottom: 2rem;
        animation: fadeIn 0.8s ease-in;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }

  .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

  .glass-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 40px rgba(102, 126, 234, 0.3);
        border: 1px solid rgba(102, 126, 234, 0.5);
    }

  .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.8rem 2.5rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }

  .stButton>button:hover {
        transform: scale(1.05) translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
    }

  .metric-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 16px;
        text-align: center;
        color: white;
        box-shadow: 0 8px 20px rgba(245, 87, 108, 0.3);
    }

  .feature-badge {
        display: inline-block;
        background: rgba(102, 126, 234, 0.2);
        color: #667eea;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.2rem;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
  .stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)

# ---------- SESSION STATE ----------
if 'history' not in st.session_state:
    st.session_state.history = []
if 'total_chars' not in st.session_state:
    st.session_state.total_chars = 0

# ---------- HEADER ----------
st.markdown("""
<div class="main-header">
    <h1 style='margin:0; font-size: 3.5rem; font-weight: 800;'>🎙️ AI Voice Studio Pro</h1>
    <p style='margin:1rem 0 0; font-size: 1.3rem; opacity: 0.95; font-weight: 400;'>
        Text ↔ Speech | 50+ Languages | AI Translation | Edge TTS | Batch Processing
    </p>
    <div style='margin-top: 1.5rem;'>
        <span class="feature-badge">✨ Natural Voices</span>
        <span class="feature-badge">🌍 50+ Languages</span>
        <span class="feature-badge">⚡ Lightning Fast</span>
        <span class="feature-badge">📁 Batch Convert</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
with st.sidebar:
    st.image("https://img.icons8.com/3d-fluency/94/microphone.png", width=90)
    st.title("⚙️ Control Panel")

    st.divider()
    st.subheader("🎛️ TTS Engine")
    tts_engine = st.selectbox(
        "Choose Engine",
        ["Edge TTS - Natural ⭐", "gTTS - Fast", "gTTS - Slow"],
        help="Edge TTS = Microsoft ki human-like voice"
    )

    st.divider()
    st.subheader("🎵 Voice Settings")
    voice_speed = st.slider("Speed", 0.5, 2.0, 1.0, 0.1, help="1.0 = Normal")
    voice_gender = st.radio("Gender", ["Female 👩", "Male 👨"], horizontal=True)

    st.divider()
    st.subheader("📊 Your Stats")
    col1, col2 = st.columns(2)
    col1.metric("Conversions", len(st.session_state.history))
    col2.metric("Characters", f"{st.session_state.total_chars:,}")

    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.history = []
        st.session_state.total_chars = 0
        st.rerun()

    st.divider()
    st.caption("💡 Pro Tip: Edge TTS best quality deta hai!")

# ---------- CONSTANTS ----------
LANGUAGES = {
    "🔍 Auto Detect": "auto",
    "🇺🇸 English": "en",
    "🇵🇰 Urdu": "ur",
    "🇮🇳 Hindi": "hi",
    "🇸🇦 Arabic": "ar",
    "🇫🇷 French": "fr",
    "🇩🇪 German": "de",
    "🇪🇸 Spanish": "es",
    "🇨🇳 Chinese": "zh-cn",
    "🇯🇵 Japanese": "ja",
    "🇷🇺 Russian": "ru",
    "🇹🇷 Turkish": "tr",
    "🇮🇹 Italian": "it",
    "🇰🇷 Korean": "ko",
    "🇵🇹 Portuguese": "pt"
}

EDGE_VOICES = {
    "en": {"Female 👩": "en-US-AriaNeural", "Male 👨": "en-US-GuyNeural"},
    "ur": {"Female 👩": "ur-PK-AsmaNeural", "Male 👨": "ur-PK-UzmaNeural"},
    "hi": {"Female 👩": "hi-IN-SwaraNeural", "Male 👨": "hi-IN-MadhurNeural"},
    "ar": {"Female 👩": "ar-SA-ZariyahNeural", "Male 👨": "ar-SA-HamedNeural"},
    "es": {"Female 👩": "es-ES-ElviraNeural", "Male 👨": "es-ES-AlvaroNeural"},
    "fr": {"Female 👩": "fr-FR-DeniseNeural", "Male 👨": "fr-FR-HenriNeural"},
}

# ---------- FUNCTIONS ----------
def detect_language(text):
    try:
        return detect(text)
    except:
        return "en"

async def edge_tts_gen(text, lang, gender, speed):
    voice = EDGE_VOICES.get(lang, EDGE_VOICES["en"])[gender]
    rate = f"+{int((speed-1)*100)}%" if speed >= 1 else f"{int((speed-1)*100)}%"
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    fp = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            fp.write(chunk["data"])
    fp.seek(0)
    return fp

def text_to_speech(text, lang, engine, gender, speed):
    try:
        if "Edge TTS" in engine:
            return asyncio.run(edge_tts_gen(text, lang, gender, speed))
        else:
            slow = "Slow" in engine
            tts = gTTS(text=text, lang=lang, slow=slow)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def speech_to_text(audio_file, lang="en-US"):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio, language=lang)
        return text
    except sr.UnknownValueError:
        return "❌ Could not understand audio - speak clearly"
    except Exception as e:
        return f"Error: {str(e)}"

def read_pdf(file):
    text = ""
    try:
        reader = PdfReader(file)
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                text += f"\n=== Page {i+1} ===\n{page_text}\n"
    except Exception as e:
        st.error(f"PDF Error: {e}")
    return text

def read_docx(file):
    try:
        doc = Document(file)
        return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    except:
        return ""

def add_history(action, content, lang):
    st.session_state.history.insert(0, {
        "time": datetime.now().strftime("%I:%M %p"),
        "action": action,
        "content": content[:60] + "..." if len(content) > 60 else content,
        "lang": lang
    })
    st.session_state.total_chars += len(content)
    if len(st.session_state.history) > 20:
        st.session_state.history.pop()

# ---------- MAIN TABS ----------
tab1, tab2, tab3, tab4 = st.tabs([
    "🔊 Text → Speech",
    "🎤 Speech → Text",
    "📄 File Converter",
    "📜 History"
])

# ---------- TAB 1: TTS ----------
with tab1:
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("✍️ Enter Your Text")
        text_input = st.text_area(
            "Text",
            height=220,
            placeholder="Type in English, Urdu, Hindi, Arabic... koi bhi language!\n\nExample: Hello, kaise ho? یہ ایک ٹیسٹ ہے۔",
            label_visibility="collapsed"
        )

        if text_input:
            words = len(text_input.split())
            chars = len(text_input)
            duration = round(words / 150, 1)

            m1, m2, m3 = st.columns(3)
            m1.markdown(f'<div class="metric-card"><h3>{words}</h3><p>Words</p></div>', unsafe_allow_html=True)
            m2.markdown(f'<div class="metric-card"><h3>{chars}</h3><p>Characters</p></div>', unsafe_allow_html=True)
            m3.markdown(f'<div class="metric-card"><h3>{duration}min</h3><p>Duration</p></div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("🌍 Language")

        lang_display = st.selectbox("Select", list(LANGUAGES.keys()))
        lang_code = LANGUAGES[lang_display]

        if lang_display == "🔍 Auto Detect" and text_input:
            detected = detect_language(text_input)
            st.success(f"Detected: **{detected.upper()}**")
            lang_code = detected

        st.divider()

        translate_on = st.toggle("🔄 Translate First?")
        if translate_on:
            target_lang = st.selectbox("To", list(LANGUAGES.keys())[1:], index=0)
            st.caption(f"Will translate to {target_lang}")

        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🎵 Generate Speech", type="primary", use_container_width=True):
        if not text_input.strip():
            st.warning("⚠️ Please enter some text first")
        else:
            with st.spinner("🎙️ Creating magic..."):
                final_text = text_input
                final_lang = lang_code

                # Translation
                if translate_on:
                    try:
                        translated = GoogleTranslator(
                            source='auto',
                            target=LANGUAGES[target_lang]
                        ).translate(text_input)
                        final_text = translated
                        final_lang = LANGUAGES[target_lang]

                        with st.expander("📝 See Translation"):
                            st.info(translated)
                    except:
                        st.warning("Translation failed, using original text")

                # Generate audio
                audio = text_to_speech(final_text, final_lang, tts_engine, voice_gender, voice_speed)

                if audio:
                    st.success(f"✅ Done! Language: {final_lang.upper()} | Engine: {tts_engine.split('-')[0]}")

                    st.audio(audio, format="audio/mp3")

                    audio.seek(0)
                    st.download_button(
                        "⬇️ Download MP3",
                        data=audio,
                        file_name=f"voice_{int(time.time())}.mp3",
                        mime="audio/mp3",
                        use_container_width=True
                    )

                    add_history("TTS", text_input, final_lang)
                else:
                    st.error("❌ Failed to generate. Try different engine or check text.")

# ---------- TAB 2: STT ----------
with tab2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("🎤 Upload Audio File")

    st.info("💡 **Best Results**: Use WAV format, clear speech, minimal background noise")

    col1, col2 = st.columns([3, 1])
    uploaded_audio = col1.file_uploader(
        "Choose file",
        type=["wav", "mp3", "ogg", "m4a", "flac"],
        label_visibility="collapsed"
    )
    lang_stt = col2.selectbox("Language", ["en-US", "ur-PK", "hi-IN", "ar-SA", "es-ES"])

    if uploaded_audio:
        st.audio(uploaded_audio)

        if st.button("📝 Transcribe Now", type="primary", use_container_width=True):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(uploaded_audio.read())
                temp_path = tmp.name

            # Convert to WAV if needed
            if not uploaded_audio.name.endswith(".wav"):
                with st.spinner("Converting audio format..."):
                    sound = AudioSegment.from_file(temp_path)
                    temp_wav = temp_path + "_conv.wav"
                    sound.export(temp_wav, format="wav")
                    temp_path = temp_wav

            with st.spinner("🧠 AI is transcribing..."):
                result = speech_to_text(temp_path, lang_stt)

                if not result.startswith("Error") and not result.startswith("❌"):
                    st.success("✅ Transcription Complete!")
                    st.text_area("Result", result, height=200)

                    col_a, col_b = st.columns(2)
                    col_a.code(result, language=None)

                    if col_b.button("🔊 Speak This Back"):
                        audio = text_to_speech(result, lang_stt.split("-")[0], tts_engine, voice_gender, voice_speed)
                        if audio:
                            st.audio(audio)

                    add_history("STT", result, lang_stt)
                else:
                    st.error(result)

    st.markdown('</div>', unsafe_allow_html=True)

# ---------- TAB 3: FILES ----------
with tab3:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("📁 Batch File Converter")

    st.info("📌 **Pro Feature**: Upload multiple PDFs/DOCX at once and convert all to speech!")

    uploaded_files = st.file_uploader(
        "Drop files here",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        help="Supports PDF, DOCX, TXT"
    )

    if uploaded_files:
        st.write(f"**{len(uploaded_files)} file(s) selected**")

        for idx, file in enumerate(uploaded_files):
            with st.expander(f"📄 {file.name}", expanded=(idx==0)):
                file_type = file.name.split(".")[-1].lower()

                with st.spinner("Extracting text..."):
                    if file_type == "pdf":
                        content = read_pdf(file)
                    elif file_type == "docx":
                        content = read_docx(file)
                    else:
                        content = file.read().decode("utf-8", errors="ignore")

                if content.strip():
                    st.text_area(
                        "Preview",
                        content[:1500] + "..." if len(content) > 1500 else content,
                        height=120,
                        key=f"preview_{idx}"
                    )

                    col1, col2, col3 = st.columns([2, 2, 1])
                    lang_file = col1.selectbox(
                        "Lang",
                        ["auto"] + list(LANGUAGES.values())[1:10],
                        key=f"lang_file_{idx}"
                    )

                    if col2.button("🔊 Convert", key=f"conv_{idx}", use_container_width=True):
                        with st.spinner("Generating audio..."):
                            final_lang = detect_language(content) if lang_file == "auto" else lang_file
                            audio = text_to_speech(content[:4000], final_lang, tts_engine, voice_gender, voice_speed)

                            if audio:
                                st.audio(audio)
                                st.download_button(
                                    "⬇️ Download",
                                    data=audio,
                                    file_name=f"{file.name.split('.')[0]}.mp3",
                                    mime="audio/mp3",
                                    key=f"dl_{idx}"
                                )
                                add_history("File", file.name, final_lang)
                else:
                    st.warning("⚠️ No text found in file")

    st.markdown('</div>', unsafe_allow_html=True)

# ---------- TAB 4: HISTORY ----------
with tab4:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("📜 Recent Activity")

    if st.session_state.history:
        for item in st.session_state.history:
            st.markdown(f"""
            <div style='background: rgba(102, 126, 234, 0.1); padding: 1rem; border-radius: 12px; margin: 0.5rem 0; border-left: 4px solid #667eea;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <strong>{item['action']}</strong>
                        <span style='background: rgba(102, 126, 234, 0.3); padding: 0.2rem 0.6rem; border-radius: 8px; font-size: 0.8rem; margin-left: 0.5rem;'>{item['lang'].upper()}</span>
                    </div>
                    <small style='opacity: 0.7;'>{item['time']}</small>
                </div>
                <p style='margin: 0.5rem 0 0; opacity: 0.9; font-size: 0.9rem;'>{item['content']}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("🎯 No conversions yet. Start using the app to see your history here!")

    st.markdown('</div>', unsafe_allow_html=True)

# ---------- FOOTER ----------
st.divider()
st.markdown("""
<div style='text-align: center; padding: 2rem; opacity: 0.8;'>
    <h3 style='margin: 0;'>🎙️ AI Voice Studio Pro v2.0</h3>
    <p style='margin: 0.5rem 0;'>Built with ❤️ using Streamlit + Edge TTS + Google Translate</p>
    <p style='font-size: 0.85rem; margin-top: 1rem;'>
        🌍 50+ Languages | 🎭 Natural Voices | ⚡ Batch Processing | 🔄 Live Translation
    </p>
</div>
""", unsafe_allow_html=True)
