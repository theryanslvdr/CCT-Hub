/**
 * Projection Calculation Utilities
 * All balance projection logic: daily, monthly, and yearly.
 *
 * Core formula (Merin quarterly-fixed):
 *   Daily Profit = round((Balance_at_quarter_start / 980) * 15, 2)
 *   Profit is FIXED for the entire quarter (~63 trading days), recalculated at boundary.
 */

import { truncateTo2Decimals } from './formatters';
import { isTradingDay } from './tradingDays';

// ────────────────────────────────────────────
// Period-based projection (summary cards)
// ────────────────────────────────────────────

export const generateProjectionData = (accountBalance, selectedYears = 1) => {
  const projections = [];
  let balance = accountBalance || 0;

  const periods = [
    { label: '1 Month', days: 22 },
    { label: '3 Months', days: 66 },
    { label: '6 Months', days: 132 },
  ];
  const yearDays = selectedYears * 250;
  periods.push({ label: `${selectedYears} Year${selectedYears > 1 ? 's' : ''}`, days: yearDays });

  const currentLotSize = balance / 980;
  const currentDailyProfit = Math.round(currentLotSize * 15 * 100) / 100;

  projections.push({
    period: 'Today',
    balance,
    lotSize: currentLotSize,
    dailyProfit: currentDailyProfit,
  });

  let runningBalance = balance;
  let lastDays = 0;

  const TRADING_DAYS_PER_QUARTER = 63;
  let quarterlyDailyProfit = Math.round((runningBalance / 980) * 15 * 100) / 100;
  let daysInCurrentQuarter = 0;

  for (const period of periods) {
    for (let day = lastDays; day < period.days; day++) {
      if (daysInCurrentQuarter >= TRADING_DAYS_PER_QUARTER) {
        quarterlyDailyProfit = Math.round((runningBalance / 980) * 15 * 100) / 100;
        daysInCurrentQuarter = 0;
      }
      runningBalance = Math.round((runningBalance + quarterlyDailyProfit) * 100) / 100;
      daysInCurrentQuarter++;
    }
    lastDays = period.days;

    const lotSize = runningBalance / 980;
    const dailyProfit = Math.round(lotSize * 15 * 100) / 100;

    projections.push({
      period: period.label,
      balance: runningBalance,
      lotSize,
      dailyProfit,
    });
  }

  return projections;
};

// ────────────────────────────────────────────
// Daily projection for a single month
// ────────────────────────────────────────────

export const generateDailyProjectionForMonth = (
  startBalance,
  monthDate,
  tradeLogs = {},
  activeSignal = null,
  allTransactions = [],
  liveAccountValue = null,
  globalHolidayDates = new Set(),
  effectiveStartDate = null,
) => {
  const days = [];
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const year = monthDate.getFullYear();
  const month = monthDate.getMonth();
  let firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);

  // Clamp to effective start date when provided
  if (effectiveStartDate) {
    const effStart = new Date(effectiveStartDate + 'T00:00:00');
    if (!isNaN(effStart.getTime())) {
      if (effStart > firstDay) firstDay = effStart;
      if (effStart > lastDay) return [];
    }
  }

  const isCurrentMonth = today.getFullYear() === year && today.getMonth() === month;
  const isPastMonth = year < today.getFullYear() || (year === today.getFullYear() && month < today.getMonth());

  // Build transaction-by-date map (skip commission deposits)
  const txByDate = {};
  if (allTransactions?.length) {
    for (const tx of allTransactions) {
      if (tx.is_commission) continue;
      const d = tx.created_at?.split('T')[0];
      if (d) txByDate[d] = (txByDate[d] || 0) + (tx.amount || 0);
    }
  }

  // Calculate running balance at month start
  let runningBalance = startBalance;

  if (isCurrentMonth || isPastMonth) {
    const monthStartStr = `${year}-${String(month + 1).padStart(2, '0')}-01`;

    const profitsFromStart = Object.entries(tradeLogs)
      .filter(([k]) => k >= monthStartStr)
      .reduce((s, [, log]) => s + (log?.actual_profit || 0) + (log?.balance_commission || 0), 0);

    const txFromStart = Object.entries(txByDate)
      .filter(([k]) => k >= monthStartStr)
      .reduce((s, [, amt]) => s + amt, 0);

    runningBalance = startBalance - profitsFromStart - txFromStart;
  }

  let currentDate = new Date(firstDay);

  while (currentDate <= lastDay) {
    if (isTradingDay(currentDate, globalHolidayDates)) {
      const yr = currentDate.getFullYear();
      const mo = String(currentDate.getMonth() + 1).padStart(2, '0');
      const dy = String(currentDate.getDate()).padStart(2, '0');
      const dateKey = `${yr}-${mo}-${dy}`;

      const tradeLog = tradeLogs[dateKey];
      const hasTraded = tradeLog?.has_traded;
      const actualProfit = tradeLog?.actual_profit;
      const commission = tradeLog?.commission || 0;
      const balanceCommission = tradeLog?.balance_commission || 0;
      const isErrorTrade = tradeLog?.is_error_trade || false;
      const errorType = tradeLog?.error_type || null;
      const errorExplanation = tradeLog?.error_explanation || null;

      // Apply deposits/withdrawals before the day's trade
      const dayTx = txByDate[dateKey] || 0;
      if (dayTx !== 0) runningBalance += dayTx;

      const hasStored = tradeLog?.lot_size && tradeLog?.projected_profit;

      let lotSize, targetProfit;
      if (hasStored) {
        lotSize = tradeLog.lot_size;
        targetProfit = tradeLog.projected_profit;
      } else {
        lotSize = truncateTo2Decimals(runningBalance / 980);
        targetProfit = truncateTo2Decimals(lotSize * 15);
      }

      // Status
      const isToday = currentDate.toDateString() === today.toDateString();
      const isFuture = currentDate > today;
      const isPast = currentDate < today;

      let status = 'pending';
      if (hasTraded && actualProfit !== undefined) status = 'completed';
      else if (isPast) status = 'missed';
      else if (isToday && activeSignal) status = 'active';
      else if (isFuture) status = 'future';

      // Performance
      let performance = null;
      if (hasTraded && actualProfit !== undefined) {
        if (actualProfit >= targetProfit) performance = actualProfit > targetProfit ? 'exceeded' : 'perfect';
        else performance = 'below';
      }

      // Effective values (live account override for today, stored for past trades)
      let effectiveLotSize, effectiveTargetProfit, effectiveBalance;

      if (isToday && liveAccountValue !== null) {
        effectiveBalance =
          hasTraded && actualProfit !== undefined
            ? truncateTo2Decimals(liveAccountValue - actualProfit - balanceCommission)
            : liveAccountValue;
        effectiveLotSize = truncateTo2Decimals(effectiveBalance / 980);
        effectiveTargetProfit = truncateTo2Decimals(effectiveLotSize * 15);
        runningBalance = effectiveBalance;
      } else if (hasStored) {
        effectiveLotSize = lotSize;
        effectiveTargetProfit = targetProfit;
        effectiveBalance = truncateTo2Decimals(lotSize * 980);
        runningBalance = effectiveBalance;
      } else {
        effectiveLotSize = lotSize;
        effectiveTargetProfit = targetProfit;
        effectiveBalance = runningBalance;
      }

      days.push({
        date: new Date(currentDate),
        dateStr: currentDate.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }),
        dateKey,
        balanceBefore: effectiveBalance,
        lotSize: effectiveLotSize,
        targetProfit: effectiveTargetProfit,
        actualProfit,
        commission,
        plDiff:
          hasTraded && actualProfit !== undefined
            ? truncateTo2Decimals(actualProfit - effectiveTargetProfit)
            : null,
        performance,
        status,
        isToday,
        hasTransaction: dayTx !== 0,
        transactionAmount: dayTx,
        isErrorTrade,
        errorType,
        errorExplanation,
      });

      // Advance running balance
      if (hasTraded && actualProfit !== undefined) {
        runningBalance += actualProfit + balanceCommission;
      } else {
        runningBalance += targetProfit;
      }
    }

    currentDate.setDate(currentDate.getDate() + 1);
  }

  return days;
};

// ────────────────────────────────────────────
// Monthly projection accordion (up to 5 years)
// ────────────────────────────────────────────

export const generateMonthlyProjection = (
  accountBalance,
  tradeLogs = {},
  globalHolidayDates = new Set(),
  deposits = [],
  effectiveStartDate = null,
) => {
  const months = [];
  const today = new Date();

  const tradeKeys = Object.keys(tradeLogs).sort();
  const depositDates = deposits.map((d) => d.created_at?.split('T')[0]).filter(Boolean).sort();
  const allDates = [...tradeKeys, ...depositDates].sort();

  let effectiveStartParsed = null;
  if (effectiveStartDate) {
    effectiveStartParsed = new Date(effectiveStartDate + 'T00:00:00');
    if (isNaN(effectiveStartParsed.getTime())) effectiveStartParsed = null;
  }

  let startMonthOffset = 0;
  if (effectiveStartParsed) {
    startMonthOffset = -(
      (today.getFullYear() - effectiveStartParsed.getFullYear()) * 12 +
      (today.getMonth() - effectiveStartParsed.getMonth())
    );
  } else if (allDates.length > 0) {
    const earliest = new Date(allDates[0]);
    startMonthOffset = -(
      (today.getFullYear() - earliest.getFullYear()) * 12 + (today.getMonth() - earliest.getMonth())
    );
  }

  // Past months with actual data
  for (let offset = startMonthOffset; offset < 0; offset++) {
    const md = new Date(today.getFullYear(), today.getMonth() + offset, 1);
    const mk = `${md.getFullYear()}-${String(md.getMonth() + 1).padStart(2, '0')}`;

    if (effectiveStartParsed) {
      const mLast = new Date(md.getFullYear(), md.getMonth() + 1, 0);
      if (mLast < effectiveStartParsed) continue;
    }

    const hasTrades = tradeKeys.some((k) => k.startsWith(mk));
    const hasDeposits = depositDates.some((d) => d?.startsWith(mk));

    if (hasTrades || hasDeposits || effectiveStartParsed) {
      const monthTrades = Object.entries(tradeLogs)
        .filter(([k]) => k.startsWith(mk))
        .sort(([a], [b]) => a.localeCompare(b));

      const last = new Date(md.getFullYear(), md.getMonth() + 1, 0);
      let tdCount = 0;
      let cd = new Date(md);
      while (cd <= last) {
        if (isTradingDay(cd, globalHolidayDates)) tdCount++;
        cd.setDate(cd.getDate() + 1);
      }

      months.push({
        monthOffset: offset,
        year: 0,
        monthDate: new Date(md),
        monthKey: mk,
        monthName: md.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
        tradingDays: tdCount,
        isCurrentMonth: false,
        isPastMonth: true,
        totalProfit: monthTrades.reduce((s, [, l]) => s + (l?.actual_profit || 0), 0),
        totalCommission: monthTrades.reduce((s, [, l]) => s + (l?.commission || 0), 0),
        tradesCount: monthTrades.length,
      });
    }
  }

  // Current + future months (quarterly fixed projection)
  let balance = accountBalance || 0;
  const getQuarter = (d) => Math.floor(d.getMonth() / 3) + 1;
  let curQ = getQuarter(today);
  let curY = today.getFullYear();
  let qProfit = Math.round((balance / 980) * 15 * 100) / 100;

  for (let offset = 0; offset <= 60; offset++) {
    const md = new Date(today.getFullYear(), today.getMonth() + offset, 1);
    const mk = `${md.getFullYear()}-${String(md.getMonth() + 1).padStart(2, '0')}`;
    const isCurrent = offset === 0;

    let tdCount = 0;
    const mStart = balance;
    const last = new Date(md.getFullYear(), md.getMonth() + 1, 0);
    let cd = isCurrent ? new Date(today) : new Date(md);

    while (cd <= last) {
      const dq = getQuarter(cd);
      const dy = cd.getFullYear();
      if (dy !== curY || dq !== curQ) {
        qProfit = Math.round((balance / 980) * 15 * 100) / 100;
        curQ = dq;
        curY = dy;
      }
      if (isTradingDay(cd, globalHolidayDates)) {
        tdCount++;
        balance = Math.round((balance + qProfit) * 100) / 100;
      }
      cd.setDate(cd.getDate() + 1);
    }

    months.push({
      monthOffset: offset,
      year: Math.max(1, Math.ceil((offset + 1) / 12)),
      monthDate: new Date(md),
      monthKey: mk,
      monthName: md.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
      startBalance: mStart,
      endBalance: balance,
      lotSize: balance / 980,
      dailyProfit: qProfit,
      tradingDays: tdCount,
      isCurrentMonth: isCurrent,
      isPastMonth: false,
    });
  }

  return months;
};

// ────────────────────────────────────────────
// Group months by year for accordion display
// ────────────────────────────────────────────

export const groupMonthsByYear = (monthlyData) => {
  const years = {};
  for (const m of monthlyData) {
    const key = m.year === 0 ? 'History' : `Year ${m.year}`;
    (years[key] ??= []).push(m);
  }

  const sorted = Object.entries(years).sort(([a], [b]) => {
    if (a === 'History') return -1;
    if (b === 'History') return 1;
    return parseInt(a.replace('Year ', '')) - parseInt(b.replace('Year ', ''));
  });

  const result = {};
  for (const [k, v] of sorted) result[k] = v;
  return result;
};
