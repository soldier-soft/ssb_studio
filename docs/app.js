// ===================================================================
//  SSB Practice Studio — Interactive Portal Script
// ===================================================================

document.addEventListener("DOMContentLoaded", () => {
  // 1. Theme Toggle
  const themeBtn = document.getElementById("themeToggle");
  const currentTheme = localStorage.getItem("ssb_theme") || "dark";
  document.documentElement.setAttribute("data-theme", currentTheme);
  updateThemeButton(currentTheme);

  if (themeBtn) {
    themeBtn.addEventListener("click", () => {
      const active = document.documentElement.getAttribute("data-theme");
      const next = active === "light" ? "dark" : "light";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("ssb_theme", next);
      updateThemeButton(next);
    });
  }

  function updateThemeButton(theme) {
    if (!themeBtn) return;
    if (theme === "light") {
      themeBtn.innerHTML = "☀️ Light";
    } else {
      themeBtn.innerHTML = "🌙 Dark";
    }
  }

  // 2. Copy Quick-Install Script
  const copyBtn = document.getElementById("copyBtn");
  const copyMethodBtn = document.getElementById("copyMethodBtn");

  function attachCopy(btn) {
    if (!btn) return;
    btn.addEventListener("click", () => {
      const codeText = "irm https://soldier-soft.github.io/ssb_studio/install.ps1 | iex";
      navigator.clipboard.writeText(codeText).then(() => {
        const original = btn.innerText;
        btn.innerText = "✓ Copied!";
        btn.style.background = "#10b981";
        btn.style.color = "#ffffff";
        setTimeout(() => {
          btn.innerText = original;
          btn.style.background = "";
          btn.style.color = "";
        }, 2200);
      });
    });
  }

  attachCopy(copyBtn);
  attachCopy(copyMethodBtn);

  // 3. Interactive Web Demo Simulator
  const simWord = document.getElementById("simWord");
  const simCaption = document.getElementById("simCaption");
  const simDigits = document.getElementById("simDigits");
  const simPhase = document.getElementById("simPhase");

  const sampleWords = [
    { word: "COURAGE", sub: "WORD #1 OF 60 • ASSOCIATE SPONTANEOUSLY" },
    { word: "LEADER", sub: "WORD #2 OF 60 • ASSOCIATE SPONTANEOUSLY" },
    { word: "DUTY", sub: "WORD #3 OF 60 • ASSOCIATE SPONTANEOUSLY" },
    { word: "OBSTACLE", sub: "WORD #4 OF 60 • ASSOCIATE SPONTANEOUSLY" },
    { word: "MISSION", sub: "WORD #5 OF 60 • ASSOCIATE SPONTANEOUSLY" },
  ];

  let currentIdx = 0;
  let secondsLeft = 15;

  if (simDigits && simWord) {
    setInterval(() => {
      secondsLeft--;
      if (secondsLeft < 0) {
        currentIdx = (currentIdx + 1) % sampleWords.length;
        secondsLeft = 15;

        // Word transition animation
        simWord.style.opacity = "0.2";
        simWord.innerText = sampleWords[currentIdx].word;
        if (simCaption) simCaption.innerText = sampleWords[currentIdx].sub;

        setTimeout(() => {
          simWord.style.opacity = "1";
        }, 120);
      }

      const formatted = `00:${secondsLeft < 10 ? "0" : ""}${secondsLeft}`;
      simDigits.innerText = formatted;

      if (secondsLeft <= 5) {
        simDigits.style.color = "#ef4444";
      } else {
        simDigits.style.color = "";
      }
    }, 1000);
  }
});

