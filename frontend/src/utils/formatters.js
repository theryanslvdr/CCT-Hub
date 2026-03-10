/**
 * Currency & Number Formatting Utilities
 * Pure functions for displaying monetary values across the application.
 */

/** Truncate to 2 decimal places without rounding */
export const truncateTo2Decimals = (num) => {
  return Math.trunc(num * 100) / 100;
};

/** Format full currency amount (never abbreviated) */
export const formatFullCurrency = (amount) => {
  if (amount === null || amount === undefined) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
};

/**
 * Format large numbers with smart abbreviation.
 * Desktop: full amount unless >= 100K.  Mobile (forceCompact): always abbreviated.
 */
export const formatLargeNumber = (amount, forceCompact = false) => {
  if (amount === null || amount === undefined) return '$0.00';

  const absAmount = Math.abs(amount);
  const sign = amount < 0 ? '-' : '';

  if (forceCompact || absAmount >= 1e5) {
    if (absAmount >= 1e12) return `${sign}$${(absAmount / 1e12).toFixed(2)}T`;
    if (absAmount >= 1e9) return `${sign}$${(absAmount / 1e9).toFixed(2)}B`;
    if (absAmount >= 1e6) return `${sign}$${(absAmount / 1e6).toFixed(2)}M`;
    if (absAmount >= 1e5) return `${sign}$${(absAmount / 1e3).toFixed(1)}K`;
  }

  return formatFullCurrency(amount);
};

/** Compact number format — always uses abbreviations */
export const formatCompact = (amount) => {
  if (amount === null || amount === undefined) return '$0';
  const absAmount = Math.abs(amount);
  const sign = amount < 0 ? '-' : '';

  if (absAmount >= 1e12) return `${sign}$${(absAmount / 1e12).toFixed(2)}T`;
  if (absAmount >= 1e9) return `${sign}$${(absAmount / 1e9).toFixed(2)}B`;
  if (absAmount >= 1e6) return `${sign}$${(absAmount / 1e6).toFixed(2)}M`;
  if (absAmount >= 1e3) return `${sign}$${(absAmount / 1e3).toFixed(2)}K`;
  return `${sign}$${absAmount.toFixed(2)}`;
};

/** Mask financial values when the user toggles visibility */
export const MASKED_VALUE = '••••••';
export const maskAmount = (formattedValue, hide) => (hide ? MASKED_VALUE : formattedValue);

/** Standard money formatting (alias for formatFullCurrency) */
export const formatMoney = formatFullCurrency;
