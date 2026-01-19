/**
 * Profit Tracker Utility Functions
 * Shared calculations and formatters for the profit tracking system
 */

// Truncate to 2 decimal places without rounding
export const truncateTo2Decimals = (num) => {
  return Math.trunc(num * 100) / 100;
};

// Format large numbers (millions, billions, trillions)
export const formatLargeNumber = (amount) => {
  if (amount === null || amount === undefined) return '$0.00';
  
  const absAmount = Math.abs(amount);
  const sign = amount < 0 ? '-' : '';
  
  if (absAmount >= 1e12) {
    return `${sign}$${(absAmount / 1e12).toFixed(2)} Trillion`;
  } else if (absAmount >= 1e9) {
    return `${sign}$${(absAmount / 1e9).toFixed(2)} Billion`;
  } else if (absAmount >= 1e6) {
    return `${sign}$${(absAmount / 1e6).toFixed(2)} Million`;
  } else {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  }
};

// Standard money formatting
export const formatMoney = (amount) => {
  if (amount === null || amount === undefined) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
};

// Calculate business days from now
export const addBusinessDays = (date, days) => {
  const result = new Date(date);
  let added = 0;
  while (added < days) {
    result.setDate(result.getDate() + 1);
    const dayOfWeek = result.getDay();
    if (dayOfWeek !== 0 && dayOfWeek !== 6) {
      added++;
    }
  }
  return result;
};

// Common holidays (Merin non-trading days)
export const isHoliday = (date) => {
  const year = date.getFullYear();
  const month = date.getMonth();
  const day = date.getDate();
  
  // Holiday list - add more as needed
  const holidays = [
    // 2025 holidays
    { year: 2025, month: 11, day: 25 },  // Christmas
    { year: 2025, month: 11, day: 26 },  // Boxing Day
    { year: 2025, month: 11, day: 31 },  // New Year's Eve
    // 2026 holidays
    { year: 2026, month: 0, day: 1 },    // New Year's Day
    { year: 2026, month: 0, day: 2 },    // New Year Holiday
  ];
  
  // Check year-specific holidays first
  const isYearSpecificHoliday = holidays.some(h => 
    h.year === year && h.month === month && h.day === day
  );
  
  if (isYearSpecificHoliday) return true;
  
  // Generic annual holidays (applied to all years not covered above)
  const genericHolidays = [
    { month: 0, day: 1 },   // New Year's Day
    { month: 11, day: 25 }, // Christmas
    { month: 11, day: 26 }, // Boxing Day
  ];
  
  return genericHolidays.some(h => h.month === month && h.day === day);
};

// Check if date is a trading day (weekday and not holiday)
// Now accepts globalHolidays parameter to use dynamic holidays from backend
export const isTradingDay = (date, globalHolidayDates = new Set()) => {
  const dayOfWeek = date.getDay();
  if (dayOfWeek === 0 || dayOfWeek === 6) return false; // Weekend
  
  // Check global holidays from backend
  const dateKey = date.toISOString().split('T')[0];
  if (globalHolidayDates.has(dateKey)) return false;
  
  return true;
};

// Calculate lot size from balance
export const calculateLotSize = (balance) => {
  const numBalance = parseFloat(balance) || 0;
  return truncateTo2Decimals(numBalance / 980);
};

// Calculate projected profit from lot size
export const calculateProjectedProfit = (lotSize) => {
  return truncateTo2Decimals(lotSize * 15);
};

// Calculate exit value (same as projected profit for now)
export const calculateExitValue = (lotSize) => {
  return calculateProjectedProfit(lotSize);
};

/**
 * Generate daily projection for a specific month
 * Core calculation function for the Daily Projection table
 * 
 * @param {number} startBalance - Starting balance for calculations
 * @param {Date} monthDate - The month to generate projection for
 * @param {Object} tradeLogs - Trade logs keyed by date (YYYY-MM-DD)
 * @param {Object} activeSignal - Currently active trading signal
 * @param {Array} allTransactions - All deposits/withdrawals
 * @param {number} liveAccountValue - Live account value for current day
 * @param {Set} globalHolidayDates - Set of holiday dates (YYYY-MM-DD format)
 * @returns {Array} Array of daily projection objects
 */
export const generateDailyProjectionForMonth = (
  startBalance, 
  monthDate, 
  tradeLogs = {}, 
  activeSignal = null, 
  allTransactions = [], 
  liveAccountValue = null, 
  globalHolidayDates = new Set()
) => {
  const days = [];
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const year = monthDate.getFullYear();
  const month = monthDate.getMonth();
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  
  const isCurrentMonth = today.getFullYear() === year && today.getMonth() === month;
  const isPastMonth = (year < today.getFullYear()) || (year === today.getFullYear() && month < today.getMonth());
  
  // Create a map of deposits/withdrawals by date for quick lookup
  const transactionsByDate = {};
  if (allTransactions && allTransactions.length > 0) {
    allTransactions.forEach(tx => {
      const txDate = tx.created_at ? tx.created_at.split('T')[0] : null;
      if (txDate) {
        if (!transactionsByDate[txDate]) {
          transactionsByDate[txDate] = 0;
        }
        transactionsByDate[txDate] += (tx.amount || 0);
      }
    });
  }
  
  // Calculate the starting balance for this month
  let runningBalance = startBalance;
  
  if (isCurrentMonth || isPastMonth) {
    const monthPrefix = `${year}-${String(month + 1).padStart(2, '0')}`;
    
    // Sum up all profits + commissions in this month
    const monthTrades = Object.entries(tradeLogs)
      .filter(([key, _]) => key.startsWith(monthPrefix))
      .sort(([a], [b]) => a.localeCompare(b));
    
    const totalMonthProfit = monthTrades.reduce((sum, [_, log]) => {
      return sum + (log?.actual_profit || 0) + (log?.commission || 0);
    }, 0);
    
    // Sum up all deposits/withdrawals in this month
    const totalMonthTransactions = Object.entries(transactionsByDate)
      .filter(([dateKey, _]) => dateKey.startsWith(monthPrefix))
      .reduce((sum, [_, amount]) => sum + amount, 0);
    
    runningBalance = startBalance - totalMonthProfit - totalMonthTransactions;
  }
  
  let currentDate = new Date(firstDay);
  
  while (currentDate <= lastDay) {
    if (isTradingDay(currentDate, globalHolidayDates)) {
      const dateKey = currentDate.toISOString().split('T')[0];
      const tradeLog = tradeLogs[dateKey];
      const hasTraded = tradeLog?.has_traded;
      const actualProfit = tradeLog?.actual_profit;
      const commission = tradeLog?.commission || 0;
      
      // Apply any deposits/withdrawals for this date BEFORE calculating lot size
      const dayTransaction = transactionsByDate[dateKey] || 0;
      if (dayTransaction !== 0) {
        runningBalance += dayTransaction;
      }
      
      // For completed trades, use the STORED lot_size and projected_profit
      const hasStoredTradeData = tradeLog && tradeLog.lot_size && tradeLog.projected_profit;
      
      let lotSize, targetProfit;
      if (hasStoredTradeData) {
        lotSize = tradeLog.lot_size;
        targetProfit = tradeLog.projected_profit;
      } else {
        lotSize = truncateTo2Decimals(runningBalance / 980);
        targetProfit = truncateTo2Decimals(lotSize * 15);
      }
      
      // Determine status
      let status = 'pending';
      const isToday = currentDate.toDateString() === today.toDateString();
      const isFuture = currentDate > today;
      const isPast = currentDate < today;
      
      if (hasTraded && actualProfit !== undefined) {
        status = 'completed';
      } else if (isPast) {
        status = 'missed';
      } else if (isToday && activeSignal) {
        status = 'active';
      } else if (isFuture) {
        status = 'future';
      }
      
      // Determine performance
      let performance = null;
      if (hasTraded && actualProfit !== undefined) {
        if (actualProfit >= targetProfit) {
          performance = actualProfit > targetProfit ? 'exceeded' : 'perfect';
        } else {
          performance = 'below';
        }
      }
      
      // Calculate effective values for display
      let effectiveLotSize, effectiveTargetProfit, effectiveBalance;
      if (isToday && liveAccountValue !== null) {
        effectiveBalance = liveAccountValue;
        effectiveLotSize = truncateTo2Decimals(liveAccountValue / 980);
        effectiveTargetProfit = truncateTo2Decimals(effectiveLotSize * 15);
      } else if (hasStoredTradeData) {
        effectiveLotSize = lotSize;
        effectiveTargetProfit = targetProfit;
        effectiveBalance = truncateTo2Decimals(lotSize * 980);
      } else {
        effectiveLotSize = lotSize;
        effectiveTargetProfit = targetProfit;
        effectiveBalance = runningBalance;
      }
      
      days.push({
        date: new Date(currentDate),
        dateStr: currentDate.toLocaleDateString('en-US', { 
          weekday: 'short', 
          month: 'short', 
          day: 'numeric' 
        }),
        dateKey: dateKey,
        balanceBefore: effectiveBalance,
        lotSize: effectiveLotSize,
        targetProfit: effectiveTargetProfit,
        actualProfit: actualProfit,
        commission: commission,
        plDiff: hasTraded && actualProfit !== undefined 
          ? truncateTo2Decimals(actualProfit - effectiveTargetProfit)
          : null,
        performance: performance,
        status: status,
        isToday: isToday,
        hasTransaction: dayTransaction !== 0,
        transactionAmount: dayTransaction,
      });
      
      // Add profit AND commission to running balance for next day
      if (hasTraded && actualProfit !== undefined) {
        runningBalance += actualProfit + commission;
      } else {
        runningBalance += targetProfit;
      }
    }
    
    currentDate.setDate(currentDate.getDate() + 1);
  }
  
  return days;
};
