# SSB Practice Studio — Officer Assessment Psychological Tests

[![Live Website](https://img.shields.io/badge/Live_Site-GitHub_Pages-blue?style=for-the-badge&logo=github)](https://soldier-soft.github.io/ssb_studio/)
[![React](https://img.shields.io/badge/Front_End-React_19_%2B_Vite-61DAFB?style=for-the-badge&logo=react)](https://soldier-soft.github.io/ssb_studio/)
[![Platform](https://img.shields.io/badge/Platform-Windows_10_%2F_11-0078D6?style=for-the-badge&logo=windows)](https://soldier-soft.github.io/ssb_studio/#download)
[![Tests](https://img.shields.io/badge/Tests-38%2F38_Passing-success?style=for-the-badge)](tests/)
[![Offline](https://img.shields.io/badge/Architecture-100%25_Offline-10B981?style=for-the-badge)](https://soldier-soft.github.io/ssb_studio/)
[![Developer](https://img.shields.io/badge/Developer-Lt._V._Elangovan-gold?style=for-the-badge)](https://github.com/soldier-soft)

> ### 🎖️ Developed by **Lt. V. Elangovan**
> Dedicated to mentoring and empowering defense aspirants preparing for Services Selection Board (SSB) Interviews across the **Indian Army, Navy, Air Force, and Coast Guard** (NDA, CDS, AFCAT, TGC, NCC Special Entry, and direct entries).

🌐 **Official Live Web Portal**: [https://soldier-soft.github.io/ssb_studio/](https://soldier-soft.github.io/ssb_studio/)

---

## 🚀 What's New in v2.0 (React & Enhanced Audio Experience)

1. **Modern React & Animated Interface**:
   - Rebuilt front-end with React 19, Tailwind CSS, Lucide icons, and responsive animated page transitions.
   - Dynamic Dark Tactical Navy Theme & Clean Slate Light Theme.
2. **Dedicated Focus Page**:
   - Immersive full-screen countdown timer for deep study and practice drills.
   - **5-Minute Audio Warning**: Plays a distinct 4-tone reminder chime when 5:00 minutes remain.
   - Completion fanfare with celebratory confetti and session hour logging.
3. **Smart Non-Repeating ID Engine**:
   - Every word, situation, and picture carries a unique stable ID (`wat-01..60`, `srt-01..60`, `tat-01..12`).
   - Items are tracked persistently across practice sessions without repeats.
   - **2-Day Difference Filter**: Ensures your current practice set excludes items completed during the last 2 calendar days!
   - **Auto-Shuffle**: Once all items in a pool are exhausted, it automatically shuffles the entire collection once and restarts fresh from the first.
4. **Curated Daily Task Routine**:
   - Daily recommended workout: **2 TAT Pictures**, **15 WAT Words**, and **15 SRT Situations**.
   - Built-in streak counter, phase transitions, and daily performance debrief.
5. **Procedural Web Audio Synthesizer**:
   - 100% offline procedural audio cues (start beeps, 5s hurry-up ticks, slide advance chimes, and completion bugle) with in-navbar volume and mute controls.

---

## ⚡ Quick Download & 1-Click Desktop Setup (Windows 10/11)

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
- **Sub-Second Response Auto-Save**: Candidate's spontaneous response is instantly persisted upon typing or timer expiry.
- **Format Flexibility**: 15-word sprints or full 60-word battery with unique non-repeating IDs.

### 2. 🎯 Situation Reaction Test (SRT)
- **Rule 1 (1 to 60 Sequential Ordering)**: Adheres strictly to natural question sequence (1 to 60) without sorting distortions.
- **Rule 2 (Strict Reaction Stems `(...)`)**: Multi-line situations are merged and standardized with `( ... )` reaction endings.
- **Timed Cadence**: Practice with 30-second per-situation pacing or full 30-minute exam conditions.

### 3. 🖼️ Thematic Apperception Test (TAT)
- **12 Successive Picture Slides**:
  - **30-second Viewing Phase**: High-resolution image displayed for initial character and backdrop observation.
  - **4-minute (240s) Writing Phase**: Candidate writes story outlining what led to the scene, current action, thoughts & feelings, and positive resolution.
  - **Slide #12 Blank Slide**: Official blank slide prompting spontaneous imagination.

---

## 🔒 100% Offline-First Architecture

- **Zero Cloud Dependence**: Never sends your responses, scores, or personal records over the internet.
- **Local Storage**: All practice history, cycles, and streak data are stored locally on your device.
- **Performance Reports**: Export multi-page candidate evaluation PDF reports formatted via ReportLab or spreadsheets in UTF-8 CSV in the desktop app.
- **Theme Support**: Seamlessly switch between **Dark Navy Theme** and **Clean Slate Light Theme**.

---

## 👨‍✈️ Developer & Credits

Designed, engineered, and maintained by **Lt. V. Elangovan**.

- **GitHub Repository**: [https://github.com/soldier-soft/ssb_studio](https://github.com/soldier-soft/ssb_studio)
- **Live Portal**: [https://soldier-soft.github.io/ssb_studio/](https://soldier-soft.github.io/ssb_studio/)
- **License**: Open Source for Indian Armed Forces Aspirants & Mentors.
