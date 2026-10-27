# import os
# import tempfile
# from pathlib import Path
# import json
# import urllib.parse
# import io
# import asyncio

# import streamlit as st
# from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

# from modules.transcribe import transcribe_media
# from modules.summarize import lexrank_summarize, generate_abstract
# from modules.quiz import generate_quiz
# from modules.downloader import download_youtube_media

# # 🧠 Copilot-inspired theme
# st.set_page_config(page_title="AI AV Summarizer & Quiz", layout="wide")
# st.markdown("""
# <style>
# :root {
#     --accent: #1E3A8A;
#     --accent-2: #3B82F6;
#     --silver: #F1F5F9;
#     --ink: #0F172A;
#     --card: #E2E8F0;
# }
# body {
#     background-color: var(--silver);
#     color: var(--ink);
# }
# h1, h2, h3 {
#     color: var(--ink);
# }
# .stButton>button {
#     background: var(--accent);
#     color: white;
#     border-radius: 8px;
#     padding: 0.5rem 1rem;
#     border: 1px solid var(--accent);
# }
# .stButton>button:hover {
#     background: var(--accent-2);
#     border-color: var(--accent-2);
# }
# .pill {
#     background: var(--card);
#     border-radius: 999px;
#     padding: 4px 10px;
#     display: inline-block;
#     font-size: 12px;
#     color: var(--ink);
#     margin-bottom: 8px;
# }
# .card {
#     background: var(--card);
#     border: 1px solid #CBD5E1;
#     padding: 16px;
#     border-radius: 10px;
#     box-shadow: 0 1px 2px rgba(0,0,0,0.03);
# }
# </style>
# """, unsafe_allow_html=True)

# # 🔊 TTS helper
# def _tts_generate_bytes(text: str) -> bytes:
#     try:
#         import edge_tts
#         async def _synth() -> bytes:
#             communicate = edge_tts.Communicate(text, voice="en-US-AriaNeural")
#             buf = io.BytesIO()
#             async for chunk in communicate.stream():
#                 if chunk["type"] == "audio":
#                     buf.write(chunk["data"])
#             return buf.getvalue()
#         try:
#             return asyncio.run(_synth())
#         except RuntimeError:
#             loop = asyncio.new_event_loop()
#             asyncio.set_event_loop(loop)
#             return loop.run_until_complete(_synth())
#     except Exception:
#         return b""

# # 📥 Save uploaded file
# def _save_uploaded_file(uploaded_file) -> str:
#     suffix = Path(uploaded_file.name).suffix
#     with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
#         tmp.write(uploaded_file.read())
#         return tmp.name

# # 🔁 Abstract rephraser
# tokenizer = AutoTokenizer.from_pretrained("Vamsi/T5_Paraphrase_Paws", use_fast=False)
# model = AutoModelForSeq2SeqLM.from_pretrained("Vamsi/T5_Paraphrase_Paws")
# paraphraser = pipeline("text2text-generation", model=model, tokenizer=tokenizer)

# def main():
#     st.title("Audio/Video Summarization and Quiz Generation")
#     st.caption("Transcribe with faster-whisper, summarize via LexRank, generate quizzes with RAKE.")

#     # Initialize session state
#     if "pipeline_ran" not in st.session_state:
#         st.session_state["pipeline_ran"] = False
#         st.session_state["transcript"] = ""
#         st.session_state["summary"] = ""
#         st.session_state["abstract"] = ""
#         st.session_state["quiz"] = {}

#     # Sidebar settings
#     with st.sidebar:
#         st.header("Settings")
#         model_size = st.selectbox("Whisper model", ["tiny", "base", "small", "medium", "large-v3"], index=2)
#         compute_type = st.selectbox("Compute type", ["int8", "int8_float16", "float16", "float32"], index=0)
#         language = st.text_input("Language hint (e.g., en)", value="")
#         summary_sentences = st.slider("Summary sentences", min_value=3, max_value=12, value=6)
#         num_mcq = st.slider("Number of MCQs", 1, 15, 5)
#         num_cloze = st.slider("Number of Cloze Qs", 1, 15, 5)

#     # Input source
#     mode = st.radio("Input source", ["YouTube URL", "Upload file"], index=0, horizontal=True)
#     tmp_path = None
#     if mode == "YouTube URL":
#         url = st.text_input("Paste YouTube link")
#         if url:
#             with st.spinner("Downloading from YouTube..."):
#                 try:
#                     tmp_path = download_youtube_media(url, prefer_audio=True)
#                     st.success(f"Downloaded to {tmp_path}")
#                 except Exception as e:
#                     st.error(f"Download failed: {e}")
#                     return
#         else:
#             st.info("Paste a YouTube URL to continue.")
#             return
#     else:
#         uploaded = st.file_uploader("Upload audio/video", type=["mp3", "wav", "m4a", "mp4", "mkv", "mov", "avi"])
#         if uploaded is None:
#             st.info("Upload a file to begin.")
#             return
#         tmp_path = _save_uploaded_file(uploaded)
#         st.success(f"Saved upload to {tmp_path}")

#     # Run pipeline
#     if st.button("Run Pipeline", type="primary"):
#         with st.spinner("Transcribing..."):
#             transcript, segments = transcribe_media(tmp_path, model_size=model_size, compute_type=compute_type, language=language or None)
#         with st.spinner("Summarizing..."):
#             summary = lexrank_summarize(transcript, num_sentences=summary_sentences)
#         with st.spinner("Generating abstract..."):
#             abstract_text = generate_abstract(summary)
#         with st.spinner("Generating quiz..."):
#             quiz = generate_quiz(transcript, num_mcq=num_mcq, num_cloze=num_cloze)

#         # Store results
#         st.session_state["transcript"] = transcript
#         st.session_state["summary"] = summary
#         st.session_state["abstract"] = abstract_text
#         st.session_state["quiz"] = quiz
#         st.session_state["pipeline_ran"] = True

#         st.rerun()

#     # Render results if pipeline has run
#     if st.session_state["pipeline_ran"]:
#         st.subheader("Transcript")
#         col1, col2 = st.columns([0.9, 0.1])
#         with col2:
#             if st.button("🔊", key="tts_transcript"):
#                 audio = _tts_generate_bytes(st.session_state["transcript"])
#                 st.audio(audio, format="audio/mp3")
#         st.text_area("Full transcript", st.session_state["transcript"], height=200)

#         st.subheader("Summary")
#         col3, col4 = st.columns([0.9, 0.1])
#         with col4:
#             if st.button("🔊", key="tts_summary"):
#                 audio = _tts_generate_bytes(st.session_state["summary"])
#                 st.audio(audio, format="audio/mp3")
#         st.write(st.session_state["summary"])

#         st.subheader("Abstract")
#         col5, col6 = st.columns([0.9, 0.1])
#         with col6:
#             if st.button("🔊", key="tts_abstract"):
#                 audio = _tts_generate_bytes(st.session_state["abstract"])
#                 st.audio(audio, format="audio/mp3")
#         st.write(st.session_state["abstract"])

#         if st.button("🔁 Rephrase Abstract"):
#             rephrased = paraphraser("paraphrase: " + st.session_state["summary"], max_length=200, do_sample=True)[0]['generated_text']
#             st.session_state["abstract"] = rephrased
#             st.rerun()

#         st.subheader("Quiz")
#         quiz = st.session_state["quiz"]

#         st.markdown("<div class='pill'>MCQ</div>", unsafe_allow_html=True)
#         for i, q in enumerate(quiz["mcq"], 1):
#             with st.container(border=True):
#                 st.markdown(f"**Q{i}.** {q['question']}")
#                 selected = st.radio("Choose an option:", q["options"], key=f"mcq_radio_{i}")
#                 if st.button("Submit", key=f"mcq_submit_{i}"):
#                     if selected == q["answer"]:
#                         st.success("✅ Correct")
#                     else:
#                         st.error("❌ Incorrect")
#                         st.info(f"Correct answer: {q['answer']}")

#         if quiz["cloze"]:
#             st.markdown("<div class='pill'>Cloze</div>", unsafe_allow_html=True)
#             for i, q in enumerate(quiz["cloze"], 1):
#                 with st.container(border=True):
#                     st.markdown(f"**Q{i}.** {q['question']}")
#                     with st.expander("Show answer"):
#                         st.info(q["answer"])

#         st.download_button("Download Transcript", st.session_state["transcript"], file_name="transcript.txt", mime="text/plain")
#         st.download_button("Download Summary", st.session_state["summary"], file_name="summary.txt", mime="text/plain")

# if __name__ == "__main__":
#     os.makedirs("modules", exist_ok=True)
#     main()
import asyncio
import hashlib
import io
import json
import os
import re
import tempfile
import urllib.parse
import uuid
from pathlib import Path

import streamlit as st

from modules.transcribe import transcribe_media
from modules.summarize import generate_abstract, lexrank_summarize, quick_abstract
from modules.quiz import generate_quiz
from modules.downloader import download_youtube_media


st.set_page_config(page_title="AI AV Summarizer & Quiz", layout="wide")
st.markdown("""
<style>
.main .block-container {
    max-width: 1180px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}
[data-testid="stMetric"] {
    background: #141B2D;
    border: 1px solid #28334B;
    padding: 1rem;
    border-radius: 14px;
}
[data-testid="stTabs"] button {
    font-weight: 600;
}
[data-testid="stFileUploader"] section {
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)

# 🔊 TTS helper
def _tts_generate_bytes(text: str) -> bytes:
    import edge_tts

    async def _synth() -> bytes:
        communicate = edge_tts.Communicate(text, voice="en-US-AriaNeural")
        buf = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buf.write(chunk["data"])
        return buf.getvalue()

    audio_bytes = asyncio.run(_synth())
    if not audio_bytes:
        raise RuntimeError("The speech service returned no audio.")
    return audio_bytes


def _show_tts_audio(text: str) -> None:
    try:
        audio = _tts_generate_bytes(text)
    except Exception as error:
        st.warning(f"Speech generation failed: {error}")
        return
    st.audio(audio, format="audio/mp3")

# 📥 Save uploaded file
def _save_uploaded_file(uploaded_file) -> str:
    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        return tmp.name


def _is_supported_youtube_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url.strip())
    hostname = (parsed.hostname or "").lower()
    return (
        parsed.scheme in {"http", "https"}
        and (hostname == "youtu.be" or hostname == "youtube.com" or hostname.endswith(".youtube.com"))
    )


def _normalize_answer(answer: str) -> str:
    return re.sub(r"\W+", " ", answer.casefold()).strip()


def _initialize_session_state() -> None:
    defaults = {
        "pipeline_ran": False,
        "transcript": "",
        "summary": "",
        "abstract": "",
        "quiz": {},
        "quiz_id": str(uuid.uuid4()),
        "media_cache_key": None,
        "media_path": None,
        "summary_style_result": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _reset_quiz_answers() -> None:
    answer_keys = [
        key for key in st.session_state
        if key.startswith(("mcq_answer_", "cloze_answer_", "cloze_checked_"))
    ]
    for key in answer_keys:
        del st.session_state[key]


def _render_quiz(quiz: dict, quiz_id: str) -> None:
    mcq_questions = quiz.get("mcq", [])
    cloze_questions = quiz.get("cloze", [])
    total_questions = len(mcq_questions) + len(cloze_questions)

    if not total_questions:
        st.info("No quiz questions were generated. Try a longer recording with clear speech.")
        return

    reset_column, score_column = st.columns([1, 3])
    with reset_column:
        if st.button("Reset quiz", key="reset_quiz", use_container_width=True):
            _reset_quiz_answers()
            st.rerun()

    correct_count = 0
    answered_count = 0

    if mcq_questions:
        st.subheader("Multiple choice")
        for index, question in enumerate(mcq_questions, start=1):
            answer_key = f"mcq_answer_{quiz_id}_{index}"
            options = question.get("options", [])
            with st.container(border=True):
                st.markdown(f"**Q{index}.** {question.get('question', '')}")
                selected = st.radio(
                    "Choose an answer",
                    options,
                    index=None,
                    key=answer_key,
                    label_visibility="collapsed",
                )
                if selected is not None:
                    answered_count += 1
                    if selected == question.get("answer"):
                        correct_count += 1
                        st.success("Correct")
                    else:
                        st.error("Not quite. Try another option.")

    if cloze_questions:
        st.subheader("Fill in the blank")
        for index, question in enumerate(cloze_questions, start=1):
            answer_key = f"cloze_answer_{quiz_id}_{index}"
            checked_key = f"cloze_checked_{quiz_id}_{index}"
            with st.container(border=True):
                st.markdown(f"**Q{index}.** {question.get('question', '')}")
                typed_answer = st.text_input(
                    "Your answer",
                    key=answer_key,
                    placeholder="Type the missing word or phrase",
                )
                if st.button("Check answer", key=f"cloze_check_{quiz_id}_{index}"):
                    st.session_state[checked_key] = True
                if st.session_state.get(checked_key) and typed_answer.strip():
                    answered_count += 1
                    if _normalize_answer(typed_answer) == _normalize_answer(question.get("answer", "")):
                        correct_count += 1
                        st.success("Correct")
                    else:
                        st.error("Not quite. Check the spelling and try again.")

    with score_column:
        st.metric("Score", f"{correct_count} / {total_questions}")
        st.caption(f"{answered_count} of {total_questions} answered")


def main():
    _initialize_session_state()
    st.title("Audio/Video Summarization and Quiz Generation")
    st.caption("Turn a video or audio recording into a transcript, concise summary, and interactive quiz.")

    with st.sidebar:
        st.header("Settings")
        with st.expander("Transcription", expanded=True):
            model_size = st.selectbox(
                "Whisper model",
                ["tiny", "base", "small", "medium", "large-v3"],
                index=0,
                help="Tiny is fastest on CPU. Larger models may improve accuracy but take longer.",
            )
            compute_type = st.selectbox(
                "Compute type",
                ["int8", "int8_float16", "float16", "float32"],
                index=0,
                help="int8 is recommended for CPU-only systems.",
            )
            language = st.text_input(
                "Language hint",
                value="",
                placeholder="e.g. en",
                help="Optional two-letter language code. Leave blank for automatic detection.",
            )
        with st.expander("Summary"):
            summary_sentences = st.slider(
                "Summary sentences",
                min_value=3,
                max_value=12,
                value=6,
                help="Maximum number of key sentences to include.",
            )
            summary_style = st.radio(
                "Summary style",
                ["Concise paragraph", "Key sentences"],
                index=0,
                help="Choose the style used for the generated summary.",
            )
        with st.expander("Quiz"):
            num_mcq = st.slider("Multiple-choice questions", 1, 15, 5, help="Number of quiz questions with choices.")
            num_cloze = st.slider("Fill-in-the-blank questions", 1, 15, 5, help="Number of questions answered by typing.")

    st.subheader("Choose your media")
    mode = st.radio(
        "Input source",
        ["YouTube URL", "Upload file"],
        index=0,
        horizontal=True,
        help="Paste a YouTube link or upload an audio/video file.",
    )
    tmp_path = None
    input_valid = True
    if mode == "YouTube URL":
        url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Use a youtube.com or youtu.be video URL.",
        )
        if url:
            if not _is_supported_youtube_url(url):
                st.error("Enter a valid YouTube URL starting with https://www.youtube.com/ or https://youtu.be/.")
                input_valid = False
            else:
                media_key = ("youtube", url.strip())
                cached_path = st.session_state["media_path"]
                if st.session_state["media_cache_key"] == media_key and cached_path and Path(cached_path).is_file():
                    tmp_path = cached_path
                else:
                    with st.spinner("Downloading audio from YouTube..."):
                        try:
                            tmp_path = download_youtube_media(url.strip(), prefer_audio=True)
                        except Exception as error:
                            st.error(f"Could not download this video: {error}")
                            input_valid = False
                    if tmp_path:
                        st.session_state["media_cache_key"] = media_key
                        st.session_state["media_path"] = tmp_path
                        st.success("Audio is ready to process.")
                    elif input_valid:
                        st.error("The video downloader did not return a media file.")
                        input_valid = False
        else:
            st.info("Paste a YouTube URL to continue.")
            input_valid = False
    else:
        uploaded = st.file_uploader(
            "Upload audio or video",
            type=["mp3", "wav", "m4a", "mp4", "mkv", "mov", "avi"],
            help="Supported formats: MP3, WAV, M4A, MP4, MKV, MOV, AVI.",
        )
        if uploaded is None:
            st.info("Upload a media file to continue.")
            input_valid = False
        elif uploaded.size == 0:
            st.error("The selected file is empty. Choose another media file.")
            input_valid = False
        else:
            file_digest = hashlib.sha256(uploaded.getbuffer()).hexdigest()
            media_key = ("upload", uploaded.name, file_digest)
            cached_path = st.session_state["media_path"]
            if st.session_state["media_cache_key"] == media_key and cached_path and Path(cached_path).is_file():
                tmp_path = cached_path
            else:
                try:
                    tmp_path = _save_uploaded_file(uploaded)
                except OSError as error:
                    st.error(f"Could not save the uploaded file: {error}")
                    input_valid = False
                if tmp_path:
                    st.session_state["media_cache_key"] = media_key
                    st.session_state["media_path"] = tmp_path
                    st.success(f"{uploaded.name} is ready to process.")

    if input_valid and tmp_path:
        run_pipeline = st.button("Generate results", type="primary", use_container_width=True)
        if run_pipeline:
            stage = "transcription"
            progress = None
            try:
                with st.status("Preparing your results...", expanded=True) as progress:
                    progress.write("1/4 Loading the speech model and transcribing media")
                    transcript, _ = transcribe_media(
                        tmp_path,
                        model_size=model_size,
                        compute_type=compute_type,
                        language=language.strip() or None,
                    )
                    if not transcript.strip():
                        raise ValueError("No speech was detected. Try a clearer recording or choose another file.")

                    stage = "summary"
                    progress.write("2/4 Creating summary and abstract")
                    summary = lexrank_summarize(transcript, num_sentences=summary_sentences)
                    abstract_text = quick_abstract(summary)

                    stage = "quiz"
                    progress.write("3/4 Building your quiz")
                    quiz = generate_quiz(transcript, num_mcq=num_mcq, num_cloze=num_cloze)

                    stage = "saving"
                    progress.write("4/4 Saving results")
                    st.session_state["transcript"] = transcript
                    st.session_state["summary"] = summary
                    st.session_state["abstract"] = abstract_text
                    st.session_state["quiz"] = quiz
                    st.session_state["summary_style_result"] = summary_style
                    _reset_quiz_answers()
                    st.session_state["quiz_id"] = str(uuid.uuid4())
                    st.session_state["pipeline_ran"] = True
                    progress.update(label="Your results are ready", state="complete", expanded=False)
            except Exception as error:
                if progress is not None:
                    progress.update(label=f"Could not complete {stage}", state="error", expanded=True)
                st.error(f"Failed during {stage}: {error}")

    if st.session_state["pipeline_ran"]:
        transcript_tab, summary_tab, quiz_tab, downloads_tab = st.tabs(
            ["Transcript", "Summary", "Quiz", "Downloads"]
        )
        with transcript_tab:
            st.subheader("Transcript")
            if st.button("🔊 Play transcript", key="tts_transcript"):
                _show_tts_audio(st.session_state["transcript"])
            st.text_area(
                "Transcribed text",
                st.session_state["transcript"],
                height=360,
                label_visibility="collapsed",
            )

        with summary_tab:
            st.subheader("Summary")
            st.caption(f"Style: {st.session_state['summary_style_result']}")
            with st.container(border=True):
                st.markdown(st.session_state["summary"] or "_No summary was generated._")
                if st.button("🔊 Play summary", key="tts_summary"):
                    _show_tts_audio(st.session_state["summary"])

            st.subheader("Abstract")
            with st.container(border=True):
                st.markdown(st.session_state["abstract"] or "_No abstract was generated._")
                if st.button("🔊 Play abstract", key="tts_abstract"):
                    _show_tts_audio(st.session_state["abstract"])
            if st.button("Rewrite abstract with synonyms (slower)", key="rewrite_abstract"):
                try:
                    with st.spinner("Loading paraphrase resources..."):
                        abstract_text = generate_abstract(st.session_state["summary"])
                    st.session_state["abstract"] = abstract_text
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not rewrite the abstract: {error}")

        with quiz_tab:
            st.subheader("Knowledge check")
            _render_quiz(st.session_state["quiz"], st.session_state["quiz_id"])

        with downloads_tab:
            st.subheader("Download your results")
            download_columns = st.columns(4)
            with download_columns[0]:
                st.download_button(
                    "Transcript",
                    st.session_state["transcript"],
                    file_name="transcript.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            with download_columns[1]:
                st.download_button(
                    "Summary",
                    st.session_state["summary"],
                    file_name="summary.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            with download_columns[2]:
                st.download_button(
                    "Abstract",
                    st.session_state["abstract"],
                    file_name="abstract.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            with download_columns[3]:
                st.download_button(
                    "Quiz",
                    json.dumps(st.session_state["quiz"], indent=2),
                    file_name="quiz.json",
                    mime="application/json",
                    use_container_width=True,
                )
    else:
        st.info("Your transcript, summary, and quiz will appear here after processing.")

if __name__ == "__main__":
    os.makedirs("modules", exist_ok=True)
    main()