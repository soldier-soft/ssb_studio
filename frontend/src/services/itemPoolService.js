/**
 * Non-repeater Item Pool & 2-Day Difference Tracking Service.
 * Implements persistent cycle tracking, automatic shuffling upon exhaustion,
 * and 2-day history exclusion for SSB candidates.
 * Developed by Lt. V. Elangovan
 */

import { INITIAL_WAT_WORDS, INITIAL_SRT_SITUATIONS, INITIAL_TAT_SCENES } from '../data/questionBank';

const STORAGE_KEYS = {
  CYCLES: 'ssb_pool_cycles_v1',
  HISTORY: 'ssb_history_log_v1',
  STREAK: 'ssb_daily_streak_v1',
};

// Standard Fisher-Yates array shuffler
function shuffleArray(arr) {
  const result = [...arr];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

// Format Date as YYYY-MM-DD
function getDateString(d = new Date()) {
  return d.toISOString().split('T')[0];
}

// Get date strings for today and yesterday (last 2 days)
function getLast2DaysDateStrings() {
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);
  return [getDateString(today), getDateString(yesterday)];
}

class ItemPoolService {
  constructor() {
    this.rawBanks = {
      wat: INITIAL_WAT_WORDS,
      srt: INITIAL_SRT_SITUATIONS,
      tat: INITIAL_TAT_SCENES,
    };
  }

  _getCycles() {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.CYCLES);
      if (data) return JSON.parse(data);
    } catch (e) {}
    return {
      wat: shuffleArray(this.rawBanks.wat.map((i) => i.id)),
      srt: shuffleArray(this.rawBanks.srt.map((i) => i.id)),
      tat: shuffleArray(this.rawBanks.tat.map((i) => i.id)),
    };
  }

  _saveCycles(cycles) {
    localStorage.setItem(STORAGE_KEYS.CYCLES, JSON.stringify(cycles));
  }

  _getHistory() {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.HISTORY);
      if (data) return JSON.parse(data);
    } catch (e) {}
    return [];
  }

  _saveHistory(history) {
    // Keep last 30 days of history
    const trimmed = history.slice(-500);
    localStorage.setItem(STORAGE_KEYS.HISTORY, JSON.stringify(trimmed));
  }

  /**
   * Get IDs practiced within the last 2 calendar days.
   */
  getLast2DaysItemIds(type) {
    const last2Days = getLast2DaysDateStrings();
    const history = this._getHistory();
    const ids = new Set();
    history.forEach((entry) => {
      if (last2Days.includes(entry.dateStr) && (!type || entry.type === type)) {
        ids.add(entry.id);
      }
    });
    return ids;
  }

  /**
   * Core non-repeater retrieval algorithm:
   * 1. Check current unpracticed cycle pool.
   * 2. Apply difference: exclude items seen in last 2 days.
   * 3. If remaining unpracticed items are exhausted, re-seed pool, shuffle once, and restart.
   */
  getItems(type, count = 15) {
    const allItems = this.rawBanks[type] || [];
    const itemMap = new Map(allItems.map((i) => [i.id, i]));
    const cycles = this._getCycles();
    let currentPool = cycles[type] || [];

    const last2DaysIds = this.getLast2DaysItemIds(type);

    // Candidates are unpracticed items not in the last 2 days
    let candidates = currentPool.filter((id) => !last2DaysIds.has(id));

    // If remaining candidate pool has less than requested, pool is exhausted
    // Re-seed all items, shuffle once, and begin fresh cycle!
    if (candidates.length < count) {
      const freshlyShuffled = shuffleArray(allItems.map((i) => i.id));
      // Re-apply 2-day exclusion
      const freshCandidates = freshlyShuffled.filter((id) => !last2DaysIds.has(id));
      
      // If total bank is smaller than 2-day set (e.g. TAT with 12 items), use freshly shuffled directly
      candidates = freshCandidates.length >= count ? freshCandidates : freshlyShuffled;
      currentPool = freshlyShuffled;
    }

    const selectedIds = candidates.slice(0, count);

    // Remove selected IDs from current cycle
    const remainingInPool = currentPool.filter((id) => !selectedIds.includes(id));
    cycles[type] = remainingInPool;
    this._saveCycles(cycles);

    // Record to history
    const todayStr = getDateString();
    const history = this._getHistory();
    selectedIds.forEach((id) => {
      history.push({
        id,
        type,
        dateStr: todayStr,
        timestamp: Date.now(),
      });
    });
    this._saveHistory(history);

    // Return the actual hydrated item objects
    return selectedIds.map((id) => itemMap.get(id)).filter(Boolean);
  }

  /**
   * Daily Task Routine:
   * 2 TAT Pictures, 15 WAT Words, 15 SRT Situations
   * Distinct from last 2 days' items.
   */
  getDailyTask() {
    const tat = this.getItems('tat', 2);
    const wat = this.getItems('wat', 15);
    const srt = this.getItems('srt', 15);

    return {
      date: getDateString(),
      tat,
      wat,
      srt,
    };
  }

  /**
   * Get metrics regarding cycle progress and 2-day difference.
   */
  getPoolMetrics() {
    const cycles = this._getCycles();
    const last2DaysWat = this.getLast2DaysItemIds('wat').size;
    const last2DaysSrt = this.getLast2DaysItemIds('srt').size;
    const last2DaysTat = this.getLast2DaysItemIds('tat').size;

    return {
      wat: {
        total: this.rawBanks.wat.length,
        remainingInCycle: cycles.wat?.length || 0,
        practicedLast2Days: last2DaysWat,
      },
      srt: {
        total: this.rawBanks.srt.length,
        remainingInCycle: cycles.srt?.length || 0,
        practicedLast2Days: last2DaysSrt,
      },
      tat: {
        total: this.rawBanks.tat.length,
        remainingInCycle: cycles.tat?.length || 0,
        practicedLast2Days: last2DaysTat,
      },
    };
  }

  /**
   * Track Daily Practice Streak
   */
  recordDailyCompletion() {
    const today = getDateString();
    let streakData = { count: 1, lastCompletedDate: today };
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.STREAK);
      if (saved) {
        const parsed = JSON.parse(saved);
        const last = new Date(parsed.lastCompletedDate);
        const now = new Date(today);
        const diffDays = Math.round((now - last) / (1000 * 60 * 60 * 24));
        if (diffDays === 1) {
          streakData.count = (parsed.count || 0) + 1;
        } else if (diffDays === 0) {
          streakData.count = parsed.count || 1;
        } else {
          streakData.count = 1;
        }
      }
    } catch (e) {}
    localStorage.setItem(STORAGE_KEYS.STREAK, JSON.stringify(streakData));
    return streakData.count;
  }

  getStreak() {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.STREAK);
      if (saved) return JSON.parse(saved).count || 0;
    } catch (e) {}
    return 0;
  }
}

export const itemPoolService = new ItemPoolService();
export default itemPoolService;

