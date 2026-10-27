# Video Summarizer

A Streamlit app that turns a YouTube link or an uploaded media file into a transcript, summary, abstract, and quiz. It can also generate spoken audio for supported results.

## Features

- Transcribes audio and video with Faster-Whisper.
- Downloads YouTube media with yt-dlp.
- Generates summaries, abstracts, and quizzes from the transcript.
- Provides an interactive quiz with answer feedback, scoring, and reset.
- Keeps results in the app while switching between Transcript, Summary, Quiz, and Downloads.
- Offers text-to-speech where the speech service is available.

## Requirements

- Windows 10/11 (the commands below use PowerShell).
- Python 3.10–3.12; Python 3.12 is recommended.
- FFmpeg installed and available on `PATH`. It is used to extract and convert media audio.
- Node.js recommended for YouTube extraction with yt-dlp. Confirm it is available with `node --version`.
- Internet access for YouTube downloads, first-time model downloads, and online speech generation.

To check the media tools:

```powershell
ffmpeg -version
node --version
```

Install FFmpeg and Node.js separately if either command is not recognized. Restart PowerShell after updating `PATH`.

## Run locally

Open PowerShell in this folder:

```powershell
cd path\to\video-summarizer
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Streamlit prints a local URL (usually `http://localhost:8501`) when the app is ready.

If PowerShell does not recognize `py -3.12`, install Python 3.12 and enable the Python launcher, or create the environment with `python -m venv .venv` using a supported Python interpreter.

If package downloads time out or your configured package index has no matching wheels, retry using the Tsinghua PyPI mirror:

```powershell
python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

## First run and performance

The selected Whisper model is downloaded the first time it is used. This can take several minutes depending on your connection and model size; subsequent runs can reuse the local model cache. Larger models generally take longer and need more memory. CPU transcription speed also depends on the media duration and computer.

YouTube extraction may be limited if yt-dlp cannot find a JavaScript runtime. Installing Node.js and restarting the app usually resolves that warning. Some videos may still be unavailable because of YouTube restrictions or regional access.

The Hugging Face unauthenticated warning is informational. A token is optional; if you use one, set it only in your local PowerShell session and do not commit it:

```powershell
$env:HF_TOKEN = "your-token"
```

## Troubleshooting

- **`No matching distribution found` for NumPy or SciPy:** Check that the active interpreter is Python 3.10–3.12 with `python --version` and `python -m pip --version`. Recreate `.venv` with a supported interpreter rather than reusing an environment copied from another machine.
- **`ffmpeg` is not recognized:** Install FFmpeg, add its `bin` directory to `PATH`, restart PowerShell, and verify with `ffmpeg -version`.
- **YouTube JavaScript-runtime warning:** Install Node.js, restart PowerShell, and verify `node --version`.
- **Speech generation fails or returns HTTP 403:** Speech generation depends on an external online service and may fail due to connectivity or service-side restrictions. Other generated results remain available.
- **First transcription is slow:** Allow the initial model download to finish. Choose a smaller Whisper model in the app for faster CPU processing.

## Project files

```text
video-summarizer/
├── .gitignore
├── .streamlit/
│   └── config.toml
├── modules/
│   ├── __init__.py
│   ├── downloader.py
│   ├── quiz.py
│   ├── summarize.py
│   └── transcribe.py
├── app.py
├── requirements.txt
└── README.md
```

`requirements.txt` is the only dependency manifest. It lists the app's direct runtime dependencies with the versions verified in the working environment. PyTorch, Transformers, SciPy, and other packages from the old alternate requirements file are not used by the active Streamlit app.

The Git ignore rules leave the local virtual environment and unused legacy prototype folders out of the GitHub repository. Keep those local files if you need them for older experiments; they are not needed to run the Streamlit app.

## Publish only this folder to GitHub

1. On GitHub, create a **new empty repository** (for example, `video-summarizer`). Do not initialize it with a README, license, or `.gitignore`; this folder already contains those project files.
2. In PowerShell, change into this folder—not the parent project folder:

   ```powershell
   cd E:\AIAVSQ\MiniProject\AIAVSMQG\video-summarizer
   ```

3. Initialize Git and review exactly what will be published:

   ```powershell
   git init -b main
   git add .
   git status --short
   ```

   Check that the staged files include `app.py`, `modules`, `.streamlit`, `requirements.txt`, and `README.md`. `requirements_simple.txt` has been removed. The environment folders (`Lib`, `Scripts`, `Include`, and similar) should not appear.

4. Commit and push. Replace the URL with the HTTPS URL of your new GitHub repository:

   ```powershell
   git commit -m "Prepare video summarizer project"
   git remote add origin https://github.com/YOUR-USERNAME/video-summarizer.git
   git push -u origin main
   ```

Because Git is initialized inside `video-summarizer`, the parent folder and its other contents will not be added to this repository. Do not run `git init` from `AIAVSMQG`.

To download a clean copy without GitHub, use **Code → Download ZIP** on the GitHub repository page. Alternatively, after committing, create a ZIP of only the committed files from PowerShell:

```powershell
git archive --format=zip --output ..\video-summarizer.zip HEAD
```

Avoid zipping the local folder directly: `.gitignore` excludes files from Git, but does not remove them from the folder or from a File Explorer ZIP.
