/**
 * Trading Day & Holiday Utilities
 * Pure functions for determining trading days, business days, and holidays.
 */

/** Add N business days to a date (skips weekends) */
export const addBusinessDays = (date, days) => {
  const result = new Date(date);
  let added = 0;
  while (added < days) {
    result.setDate(result.getDate() + 1);
    if (result.getDay() !== 0 && result.getDay() !== 6) {
      added++;
    }
  }
  return result;
};

/**
 * Check if a date is a known Merin non-trading holiday.
 * Includes both year-specific and recurring generic holidays.
 */
export const isHoliday = (date) => {
  const year = date.getFullYear();
  const month = date.getMonth();
  const day = date.getDate();

  const yearSpecific = [
    { year: 2025, month: 11, day: 25 },
    { year: 2025, month: 11, day: 26 },
    { year: 2025, month: 11, day: 31 },
    { year: 2026, month: 0, day: 1 },
    { year: 2026, month: 0, day: 2 },
  ];

  if (yearSpecific.some((h) => h.year === year && h.month === month && h.day === day)) {
    return true;
  }

  const generic = [
    { month: 0, day: 1 },
    { month: 11, day: 25 },
    { month: 11, day: 26 },
  ];

  return generic.some((h) => h.month === month && h.day === day);
};

/**
 * Check if a given date is a trading day.
 * A trading day is a weekday that is not in the globalHolidayDates set.
 */
export const isTradingDay = (date, globalHolidayDates = new Set()) => {
  const dow = date.getDay();
  if (dow === 0 || dow === 6) return false;

  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return !globalHolidayDates.has(`${y}-${m}-${d}`);
};
