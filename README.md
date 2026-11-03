# SSB Practice Studio — Officer Assessment Psychological Tests

[![Live Website](https://img.shields.io/badge/Live_Site-GitHub_Pages-blue?style=for-the-badge&logo=github)](https://soldier-soft.github.io/ssb_studio/)
[![Platform](https://img.shields.io/badge/Platform-Windows_10_%2F_11-0078D6?style=for-the-badge&logo=windows)](https://soldier-soft.github.io/ssb_studio/#install)
[![Tests](https://img.shields.io/badge/Tests-38%2F38_Passing-success?style=for-the-badge)](tests/)
[![Offline](https://img.shields.io/badge/Architecture-100%25_Offline-10B981?style=for-the-badge)](https://soldier-soft.github.io/ssb_studio/)
[![Developer](https://img.shields.io/badge/Developer-Lt._V._Elangovan-gold?style=for-the-badge)](https://github.com/soldier-soft)

> ### 🎖️ Developed by **Lt. V. Elangovan**
> Dedicated to mentoring and empowering defense aspirants preparing for Services Selection Board (SSB) Interviews across the **Indian Army, Navy, Air Force, and Coast Guard** (NDA, CDS, AFCAT, TGC, NCC Special Entry, and direct entries).

🌐 **Official Live Web Portal**: [https://soldier-soft.github.io/ssb_studio/](https://soldier-soft.github.io/ssb_studio/)

---

## ⚡ Quick Download & 1-Click Desktop Setup

### Option 1: Direct ZIP Package (Recommended)
1. **Download the Package**:
   - [**Direct Download (ZIP, ~72 MB)**](https://raw.githubusercontent.com/soldier-soft/ssb_studio/main/docs/download/SSB_Practice_Studio_Windows.zip)
   - Or click the download button on the [Live Web Portal](https://soldier-soft.github.io/ssb_studio/).
2. **Extract the ZIP Archive**:
   - Right-click `SSB_Practice_Studio_Windows.zip` and select **Extract All...** to any folder (e.g. `C:\SSB_Studio` or `Downloads\SSB_Studio`).
3. **Run 1-Click Desktop Setup**:
   - Double-click **`Setup_And_Create_Desktop_Shortcut.bat`**.
   - It automatically generates a shortcut named **SSB Practice Studio** on your Windows Desktop (with the official high-resolution application icon) and launches the application immediately!

### Option 2: Windows PowerShell 1-Liner (Instant Install & Run)
Open Windows PowerShell and run:
```powershell
irm https://soldier-soft.github.io/ssb_studio/install.ps1 | iex
```
*(Automatically downloads the package, extracts it to `%LOCALAPPDATA%\SSBPracticeStudioApp`, creates your Desktop shortcut, and launches the app!)*

### Option 3: Run from Source
```bash
git clone https://github.com/soldier-soft/ssb_studio.git
cd ssb_studio
pip install -r requirements.txt
python app/main.py
```

> [!NOTE]
> **Windows SmartScreen Note**: When launching an open-source indie executable on Windows 10/11 for the first time, SmartScreen may show a prompt: *"Windows protected your PC"*. Simply click **More info** &rarr; **Run anyway**. The application is 100% offline, privacy-safe, and contains zero trackers.

---

## 🎯 Psychological Test Batteries Conducted

SSB Practice Studio provides authentic simulation for all three written psychological batteries conducted on Day 2 of SSB Interviews:

### 1. ⚡ Word Association Test (WAT)
- **60 Words at 15-Second Cadence**: Realistic countdown timer with automatic, monotonic slide advance.
- **Sub-Second Response Auto-Save**: Candidate's spontaneous response is instantly persisted to SQLite upon typing or timer expiry.
- **Format Flexibility**: Import words from custom `.txt` or `.pdf` coaching materials with automatic number stripping and order preservation.
- **Modes**: Strict **Exam Mode** (no pause, no skip) or **Practice Mode** (with back/next navigation).

### 2. 🎯 Situation Reaction Test (SRT)
- **Rule 1 (1 to 60 Sequential Ordering)**: Adheres strictly to natural question sequence (1 to 60) without sorting distortions.
- **Rule 2 (Strict Reaction Stems `(...)`)**: Multi-line situations are merged and standardized with `( ... )` reaction endings.
- **Timed Cadence**: Practice with 30-second per-situation pacing or full 30-minute exam conditions.
- **PDF & Multi-Column Extraction**: Intelligent block parser extracts situations cleanly from scanned or digital PDFs.

### 3. 🖼️ Thematic Apperception Test (TAT)
- **12 Successive Picture Slides**:
  - **30-second Viewing Phase**: High-resolution image displayed for initial character and backdrop observation.
  - **4-minute (270s) Writing Phase**: Candidate writes story outlining what led to the scene, current action, thoughts & feelings, and positive resolution.
  - **Slide #12 Blank Slide**: Official blank slide prompting spontaneous imagination.
- **Image Import & Deduplication**: Safe copying into local app storage with SHA-256 deduplication and natural filename sorting (`pic1.jpg`, `pic2.jpg`, `pic10.jpg`).

---

## 🔒 100% Offline-First Architecture

- **Zero Cloud Dependence**: Never sends your responses, scores, or personal records over the internet.
- **Local SQLite Storage**: Encrypted with WAL mode and atomic integrity checks.
- **Performance Reports**: Export multi-page candidate evaluation PDF reports formatted via ReportLab or spreadsheets in UTF-8 CSV.
- **Theme Support**: Seamlessly switch between **Dark Navy Theme** and **Clean Slate Light Theme**.

---

## 👨‍✈️ Developer & Credits

Designed, engineered, and maintained by **Lt. V. Elangovan**.

- **GitHub Repository**: [https://github.com/soldier-soft/ssb_studio](https://github.com/soldier-soft/ssb_studio)
- **Live Portal**: [https://soldier-soft.github.io/ssb_studio/](https://soldier-soft.github.io/ssb_studio/)
- **License**: Open Source for Indian Armed Forces Aspirants & Mentors.
