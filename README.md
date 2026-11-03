# SSB Practice Studio

[![Live Website](https://img.shields.io/badge/Live_Site-GitHub_Pages-blue?style=for-the-badge&logo=github)](https://soldier-soft.github.io/ssb_studio/)
[![Platform](https://img.shields.io/badge/Platform-Windows_10_%2F_11-0078D6?style=for-the-badge&logo=windows)](https://soldier-soft.github.io/ssb_studio/#install)
[![Tests](https://img.shields.io/badge/Tests-38%2F38_Passing-success?style=for-the-badge)](tests/)
[![Offline](https://img.shields.io/badge/Architecture-100%25_Offline-10B981?style=for-the-badge)](https://soldier-soft.github.io/ssb_studio/)

**SSB Practice Studio** is a complete, production-quality, offline-first Windows desktop application engineered for SSB (Services Selection Board) psychological test preparation.

🌐 **Live Web Portal & Downloads**: [https://soldier-soft.github.io/ssb_studio/](https://soldier-soft.github.io/ssb_studio/)

---

## ⚡ Quick Download & 1-Click Desktop Setup

1. **Download the Windows Package**:
   Download [**`SSB_Practice_Studio_Windows.zip`**](https://github.com/soldier-soft/ssb_studio/releases/latest/download/SSB_Practice_Studio_Windows.zip).
2. **Extract to Any Folder**:
   Unzip the contents to your preferred folder (e.g. `C:\SSB_Studio` or `Documents`).
3. **Double-Click Setup**:
   Run `Setup_And_Create_Desktop_Shortcut.bat`.
   - Automatically generates a shortcut named **SSB Practice Studio** on your Windows Desktop (with the official high-res icon).
   - Automatically launches the application!

Alternatively, install via PowerShell 1-liner:
```powershell
irm https://soldier-soft.github.io/ssb_studio/install.ps1 | iex
```

---

## 🎯 Psychological Test Batteries

1. **TAT (Thematic Apperception Test)**: Image series presentation with configurable viewing (default 30s) and story writing phases (default 4m 30s / 270s).
2. **WAT (Word Association Test)**: 15-second per-word timed association slides, exact source order preservation, fast text & PDF parsing, instant response auto-saving.
3. **SRT (Situation Reaction Test)**: Situation extraction from text/scanned PDFs with preservation of original serial numbers (including numbering gaps), review/split/merge dialog, and 30-second timed reaction slides.

All test content, session history, answers, evaluator notes, and analytics remain strictly local on your machine in an offline SQLite database. No cloud account or paid API is required.

---

## 🛠️ Technology Stack

- **Language & Runtime**: Python 3.12+ (tested on Python 3.13)
- **GUI Framework**: PySide6 (Qt 6 for Python) with custom Vanilla QSS stylesheets
- **Local Database**: SQLite 3 with WAL mode, foreign keys, and versioned migrations
- **PDF Extraction**: PyMuPDF (`fitz`) for fast, structure-preserving text extraction
- **Image Processing**: Pillow (`PIL`) for image validation, deduplication, and scaling
- **Report Generation**: ReportLab for formatted multi-page candidate evaluation PDF reports
- **Spreadsheet Export**: Standard CSV with UTF-8 BOM encoding (`utf-8-sig`)
- **Optical Character Recognition**: Optional Tesseract OCR with automatic binary detection
- **Testing**: pytest with injectable clock seams for deterministic monotonic timing tests
- **Packaging**: PyInstaller for building standalone Windows executables

---

## 🚀 Key Features & Modules

### 📊 Modern Command Dashboard
- **Dark Navy / Blue Visual Theme**: Tailored modern color palette (`#0A0F1D`, `#131C31`, `#3B82F6`) with dynamic light/dark theme toggle.
- **Real SQLite KPIs**: Total completed tests, total practice duration, completion rate %, and response counts calculated directly from stored records.
- **Crash Recovery**: Interrupted tests are automatically detected on launch with all typed answers preserved.
- **Quick-Start Presets**: Instant launch for TAT 12-picture exam, WAT 60-word sprint, and SRT 60-situation drills.

### 🖼️ TAT (Thematic Apperception Test) Module
- **Flexible Image Import**: Select image folders or files (`.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`).
- **Natural Filename Sorting**: Automatically orders filenames naturally (`pic1.jpg`, `pic2.jpg`, `pic10.jpg`).
- **SHA-256 Deduplication**: Identifies and excludes duplicate images.
- **Safe Asset Management**: Copies images into user data storage so moving source files doesn't break series.
- **Dual-Phase Timing**: Automatically transitions from the 30-second viewing phase to the 270-second story writing phase, then advances to the next picture.
- **Response Auto-Saving**: Debounced keystroke autosave plus mandatory flush on phase transitions.
- **Configurable Durations**: Supports custom viewing and writing times, including zero-second viewing when explicitly configured.

### ⚡ WAT (Word Association Test) Module
- **Source-Order Extraction**: Parses `.txt` and `.pdf` files, removing numbering and punctuation while preserving word order.
- **Pre-Import Review**: In-dialog word editor to verify, clean, or add words before saving.
- **15-Second Pacing**: Displays 1 word at a time with visible countdown, item counter, and progress bar.
- **Automatic Slide Advance**: Persists responses and moves to the next word immediately upon countdown expiry.

### 🎯 SRT (Situation Reaction Test) Module
- **Original Serial Preservation**: Retains original numbering patterns (`1.`, `1)`, `(1)`, `14a`) including gaps (e.g. questions 1, 2, 5).
- **Interactive Review Dialog**: Split merged questions, merge multi-line situations, reorder, or edit before saving.
- **PyMuPDF & OCR Fallback**: Automatically checks for scanned PDF pages and utilizes Tesseract OCR if available, with clear warnings about OCR uncertainty.
- **30-Second Reactions**: Displays 1 situation per slide for 30 seconds with instant response autosave.

### ⏱️ Monotonic Examination Timer Engine
- **Drift-Free Precision**: Uses `time.monotonic()` absolute deadlines rather than counter decrements so UI delays do not cause timing drift.
- **Guaranteed Single Transition**: Guarded against double transitions, duplicate saves, or negative times.
- **Exam Mode vs Practice Mode**:
  - *Exam Mode*: Strict adherence to testing rules — no pausing, skipping, or modifying previous slides.
  - *Practice Mode*: Allows pause, resume, previous/next slide navigation.
- **Audio Alerts**: Non-blocking procedural sound cues on start countdown, phase transitions, and test completion.

### 📄 Reports & Data Management
- **PDF Evaluation Reports**: Formatted ReportLab documents including session metadata, completion rate %, item prompts, candidate answers, and evaluator notes.
- **CSV Data Export**: UTF-8-SIG formatted exports for analysis in Microsoft Excel or Google Sheets.
- **Atomic SQLite Backups**: Non-blocking database backup and restore tools.

---

## 📂 Directory Layout

```
application_ssb/
├── app/
│   ├── config.py                 # Paths (%LOCALAPPDATA%/SSBPracticeStudio), defaults
│   ├── app_context.py            # Service and database container
│   └── main.py                   # Application entry point with exception hook
├── core/
│   ├── clock.py                  # Monotonic SystemClock and injectable TestClock
│   ├── timer_engine.py           # Precision deadline timer engine
│   └── natural_sort.py           # Natural numerical sorting utility
├── database/
│   ├── connection.py             # SQLite connection manager with WAL mode
│   ├── migrations.py             # Versioned schema migrations & preset seeds
│   ├── models.py                 # Dataclasses: Session, Response, Preset, ContentSet
│   └── repositories.py           # Typed SQLite repositories
├── services/
│   ├── ocr_service.py            # Tesseract OCR detection & execution
│   ├── pdf_parser.py             # PyMuPDF text & SRT regex situation parser
│   ├── import_manager.py         # File ingestion, deduplication, asset copier
│   ├── session_service.py        # Session orchestration & debounced autosave
│   ├── report_service.py         # ReportLab PDF, CSV, and SQLite backup
│   └── sound_service.py          # Procedural non-blocking audio cues
├── ui/
│   ├── styles/
│   │   ├── dark_theme.qss        # Dark navy professional stylesheet
│   │   ├── light_theme.qss       # Clean slate light stylesheet
│   │   └── theme_manager.py      # Live stylesheet switcher
│   ├── components/
│   │   ├── navbar.py             # Sidebar navigation
│   │   ├── timer_widget.py       # High-contrast countdown & phase pill
│   │   ├── stat_card.py          # KPI metrics card
│   │   └── toast.py              # Toast notifications
│   ├── screens/
│   │   ├── dashboard_screen.py   # Main cockpit & recent sessions
│   │   ├── session_builder.py    # Preset selector & custom duration builder
│   │   ├── tat_screen.py         # TAT execution view
│   │   ├── wat_screen.py         # WAT execution view
│   │   ├── srt_screen.py         # SRT execution view
│   │   ├── library_screen.py     # Content decks & import dialogs
│   │   ├── srt_preview_dialog.py # Interactive SRT review & split/merge
│   │   ├── history_screen.py     # Past session logs & evaluator notes
│   │   ├── report_screen.py      # PDF & CSV generator, database backups
│   │   └── settings_screen.py    # Theme, font size, audio, OCR configuration
│   └── main_window.py            # QMainWindow container
├── sample_content/
│   ├── sample_wat_words.txt      # 60 official-standard WAT words
│   ├── sample_srt_situations.txt # 20 SRT situations with numbering gaps
│   ├── sample_tat_images/        # Sample practice scenes
│   └── generate_sample_images.py
├── scripts/
│   ├── build_windows.py          # Automated PyInstaller packaging script
│   ├── setup_windows.bat         # Environment & dependency setup batch
│   └── run_app.bat               # One-click desktop launcher
├── tests/
│   ├── conftest.py               # In-memory DB and test clock fixtures
│   ├── test_clock_and_timer.py   # Timing deadline & transition tests
│   ├── test_natural_sort.py      # Natural sort tests
│   ├── test_parsers.py           # PyMuPDF text & serial gap tests
│   ├── test_database_and_repo.py # SQLite CRUD & real analytics tests
│   ├── test_reports.py           # PDF, CSV, and backup/restore tests
│   ├── test_session_service.py   # Session lifecycle & estimation tests
│   └── test_import_manager.py    # Deduplication & asset copy tests
├── requirements.txt
├── ssb_studio.spec
└── README.md
```

---

## 💻 Installation & Setup (Windows)

### Prerequisites
- Windows 10 or 11 (64-bit)
- Python 3.12 or newer installed and added to your `PATH`

### Step 1: Install Dependencies
Open PowerShell or Command Prompt in the project folder and run:
```cmd
pip install -r requirements.txt
```
*(Or double-click `setup_windows.bat` to automate installation and verification).*

### Step 2: Run Automated Tests
Verify all 27 unit and integration tests:
```cmd
pytest -v
```

### Step 3: Launch the Application
Run via python:
```cmd
python -m app.main
```
*(Or double-click `run_app.bat`).*

---

## 📦 Building Standalone Windows Executable (.exe)

To produce a self-contained, distributable Windows desktop executable that does not require Python on the target machine:

Run the automated build script:
```cmd
python scripts/build_windows.py
```
*(Or run PyInstaller directly: `pyinstaller ssb_studio.spec --clean --noconfirm`).*

Upon completion, the distributable executable will be generated at:
```
dist\SSBPracticeStudio\SSBPracticeStudio.exe
```

---

## 🔍 Optional Tesseract OCR Setup

Tesseract OCR is optional and only required if you wish to extract situations from scanned, non-searchable PDF documents:

1. Download the official Windows installer from: [UB-Mannheim Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki).
2. Install to the default directory (`C:\Program Files\Tesseract-OCR\tesseract.exe`).
3. Open **SSB Practice Studio** → **Settings** → Click **Detect Again**.
4. The application will detect the OCR engine automatically.

---

## 🔒 Data Privacy & Storage Locations

- **Database**: `%LOCALAPPDATA%\SSBPracticeStudio\ssb_studio.db`
- **Library Assets**: `%LOCALAPPDATA%\SSBPracticeStudio\library_assets\`
- **Database Backups**: `%LOCALAPPDATA%\SSBPracticeStudio\backups\`
- **Exported Reports**: `%LOCALAPPDATA%\SSBPracticeStudio\reports\`

All test content, candidate answers, and evaluator assessments remain strictly local. No user data is sent across the network.
