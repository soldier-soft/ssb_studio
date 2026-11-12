import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import DailyTaskPage from './pages/DailyTaskPage';
import FocusPage from './pages/FocusPage';
import WatPage from './pages/WatPage';
import SrtPage from './pages/SrtPage';
import TatPage from './pages/TatPage';
import DownloadPage from './pages/DownloadPage';

export default function App() {
  const [activePage, setActivePage] = useState('dashboard');
  const [theme, setTheme] = useState(localStorage.getItem('ssb_theme') || 'dark');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('ssb_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] relative">
      <div className="bg-grid" />

      {/* Navigation Header */}
      <Navbar
        activePage={activePage}
        setActivePage={setActivePage}
        theme={theme}
        toggleTheme={toggleTheme}
      />

      {/* Main Routed Page Content */}
      <main className="pb-16">
        {activePage === 'dashboard' && <Dashboard setActivePage={setActivePage} />}
        {activePage === 'dailytask' && <DailyTaskPage setActivePage={setActivePage} />}
        {activePage === 'focus' && <FocusPage />}
        {activePage === 'wat' && <WatPage />}
        {activePage === 'srt' && <SrtPage />}
        {activePage === 'tat' && <TatPage />}
        {activePage === 'download' && <DownloadPage />}
      </main>
    </div>
  );
}
