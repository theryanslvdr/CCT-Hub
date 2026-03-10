/**
 * Profit Tracker Calculation Utilities — Barrel Re-export
 *
 * This file re-exports everything from the three focused modules so that
 * existing imports throughout the codebase continue to work unchanged.
 *
 * Modules:
 *   formatters.js   — Currency & number display helpers
 *   tradingDays.js  — Business day, holiday, and trading-day checks
 *   projections.js  — Balance projection calculations (daily / monthly / yearly)
 */

export {
  truncateTo2Decimals,
  formatFullCurrency,
  formatLargeNumber,
  formatCompact,
  MASKED_VALUE,
  maskAmount,
  formatMoney,
} from './formatters';

export {
  addBusinessDays,
  isHoliday,
  isTradingDay,
} from './tradingDays';

export {
  generateProjectionData,
  generateDailyProjectionForMonth,
  generateMonthlyProjection,
  groupMonthsByYear,
} from './projections';
