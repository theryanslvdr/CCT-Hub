/**
 * Profit Tracker Calculation Utilities
 * Pure functions extracted from ProfitTrackerPage.jsx for reusability and maintainability.
 */

// Truncate to 2 decimal places without rounding
export const truncateTo2Decimals = (num) => {
  return Math.trunc(num * 100) / 100;
};

// Format full currency amount (no abbreviation)
export const formatFullCurrency = (amount) => {
  if (amount === null || amount === undefined) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
};

// Format large numbers - Desktop: Full amount unless 100K+, Mobile: Always abbreviated
export const formatLargeNumber = (amount, forceCompact = false) => {
  if (amount === null || amount === undefined) return '$0.00';
  
  const absAmount = Math.abs(amount);
  const sign = amount < 0 ? '-' : '';
  
  const shouldAbbreviate = forceCompact || absAmount >= 1e5;
  
  if (shouldAbbreviate) {
    if (absAmount >= 1e12) return `${sign}$${(absAmount / 1e12).toFixed(2)}T`;
    if (absAmount >= 1e9) return `${sign}$${(absAmount / 1e9).toFixed(2)}B`;
    if (absAmount >= 1e6) return `${sign}$${(absAmount / 1e6).toFixed(2)}M`;
    if (absAmount >= 1e5) return `${sign}$${(absAmount / 1e3).toFixed(1)}K`;
  }
  
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
};

// Compact number format for mobile (always uses abbreviations)
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

// Mask financial amounts when hidden
export const MASKED_VALUE = '••••••';
export const maskAmount = (formattedValue, hide) => hide ? MASKED_VALUE : formattedValue;

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
  
  const holidays = [
    { year: 2025, month: 11, day: 25 },
    { year: 2025, month: 11, day: 26 },
    { year: 2025, month: 11, day: 31 },
    { year: 2026, month: 0, day: 1 },
    { year: 2026, month: 0, day: 2 },
  ];
  
  const isYearSpecificHoliday = holidays.some(h => 
    h.year === year && h.month === month && h.day === day
  );
  
  if (isYearSpecificHoliday) return true;
  
  const genericHolidays = [
    { month: 0, day: 1 },
    { month: 11, day: 25 },
    { month: 11, day: 26 },
  ];
  
  return genericHolidays.some(h => h.month === month && h.day === day);
};

// Check if date is a trading day (weekday and not holiday)
export const isTradingDay = (date, globalHolidayDates = new Set()) => {
  const dayOfWeek = date.getDay();
  if (dayOfWeek === 0 || dayOfWeek === 6) return false;
  
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const dateKey = `${year}-${month}-${day}`;
  if (globalHolidayDates.has(dateKey)) return false;
  
  return true;
};

// Generate projection for specific periods using QUARTERLY FIXED daily profit
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
  const currentDailyProfit = Math.round((currentLotSize * 15) * 100) / 100;
  
  projections.push({
    period: 'Today',
    balance: balance,
    lotSize: currentLotSize,
    dailyProfit: currentDailyProfit,
  });
  
  let runningBalance = balance;
  let lastDays = 0;
  
  const TRADING_DAYS_PER_QUARTER = 63;
  let quarterlyDailyProfit = Math.round(((runningBalance / 980) * 15) * 100) / 100;
  let daysInCurrentQuarter = 0;
  
  for (const period of periods) {
    for (let day = lastDays; day < period.days; day++) {
      if (daysInCurrentQuarter >= TRADING_DAYS_PER_QUARTER) {
        quarterlyDailyProfit = Math.round(((runningBalance / 980) * 15) * 100) / 100;
        daysInCurrentQuarter = 0;
      }
      runningBalance = Math.round((runningBalance + quarterlyDailyProfit) * 100) / 100;
      daysInCurrentQuarter++;
    }
    lastDays = period.days;
    
    const lotSize = runningBalance / 980;
    const dailyProfit = Math.round((lotSize * 15) * 100) / 100;
    
    projections.push({
      period: period.label,
      balance: runningBalance,
      lotSize: lotSize,
      dailyProfit: dailyProfit,
    });
  }
  
  return projections;
};
export const generateDailyProjectionForMonth = (startBalance, monthDate, tradeLogs = {}, activeSignal = null, allTransactions = [], liveAccountValue = null, globalHolidayDates = new Set(), effectiveStartDate = null) => {
  const days = [];
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const year = monthDate.getFullYear();
  const month = monthDate.getMonth();
  let firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  
  // If effectiveStartDate is set and falls within or after this month, adjust firstDay
  if (effectiveStartDate) {
    const effStartParsed = new Date(effectiveStartDate + 'T00:00:00');
    if (!isNaN(effStartParsed.getTime())) {
      // Only show days on or after the effective start date
      if (effStartParsed > firstDay) {
        firstDay = effStartParsed;
      }
      // If effective start is after this month entirely, return empty
      if (effStartParsed > lastDay) {
        return [];
      }
    }
  }
  
  const isCurrentMonth = today.getFullYear() === year && today.getMonth() === month;
  const isPastMonth = (year < today.getFullYear()) || (year === today.getFullYear() && month < today.getMonth());
  
  // Create a map of deposits/withdrawals by date for quick lookup
  // Note: Withdrawals already have NEGATIVE amounts in the database
  const transactionsByDate = {};
  if (allTransactions && allTransactions.length > 0) {
    allTransactions.forEach(tx => {
      const txDate = tx.created_at ? tx.created_at.split('T')[0] : null;
      if (txDate) {
        if (!transactionsByDate[txDate]) {
          transactionsByDate[txDate] = 0;
        }
        // The amount is already negative for withdrawals, so just add it
        transactionsByDate[txDate] += (tx.amount || 0);
      }
    });
  }
  
  // Calculate the starting balance for this month by working backwards from current balance
  let runningBalance = startBalance;
  
  // For past or current months, we need to subtract ALL profits and transactions 
  // that happened FROM THE START OF THIS MONTH until today to find the starting balance
  if (isCurrentMonth || isPastMonth) {
    const monthStartDate = new Date(year, month, 1);
    const monthStartStr = `${year}-${String(month + 1).padStart(2, '0')}-01`;
    
    // Get all trades and transactions from the start of THIS month until today
    // (for current month) or until end of month (for past months)
    const endOfPeriodStr = isCurrentMonth 
      ? today.toISOString().split('T')[0] 
      : `${year}-${String(month + 1).padStart(2, '0')}-${String(lastDay.getDate()).padStart(2, '0')}`;
    
    // But we also need to subtract profits from FUTURE months (months after the one we're viewing)
    // to get the correct starting balance for this month
    
    // Sum up ALL profits + commissions from the start of this month onwards
    const profitsFromThisMonthOnwards = Object.entries(tradeLogs)
      .filter(([key, _]) => key >= monthStartStr)
      .reduce((sum, [_, log]) => {
        return sum + (log?.actual_profit || 0) + (log?.commission || 0);
      }, 0);
    
    // Sum up ALL deposits/withdrawals from the start of this month onwards
    const transactionsFromThisMonthOnwards = Object.entries(transactionsByDate)
      .filter(([dateKey, _]) => dateKey >= monthStartStr)
      .reduce((sum, [_, amount]) => sum + amount, 0);
    
    // Starting balance for the month = current balance - all profits since month start - all transactions since month start
    runningBalance = startBalance - profitsFromThisMonthOnwards - transactionsFromThisMonthOnwards;
  }
  
  let currentDate = new Date(firstDay);
  
  while (currentDate <= lastDay) {
    if (isTradingDay(currentDate, globalHolidayDates)) {
      // Use LOCAL date format to avoid timezone issues
      const year = currentDate.getFullYear();
      const month = String(currentDate.getMonth() + 1).padStart(2, '0');
      const day = String(currentDate.getDate()).padStart(2, '0');
      const dateKey = `${year}-${month}-${day}`;
      
      const tradeLog = tradeLogs[dateKey];
      const hasTraded = tradeLog?.has_traded;
      const actualProfit = tradeLog?.actual_profit;
      const commission = tradeLog?.commission || 0;  // Daily commission from referrals
      const isErrorTrade = tradeLog?.is_error_trade || false;
      const errorType = tradeLog?.error_type || null;
      const errorExplanation = tradeLog?.error_explanation || null;
      
      // Apply any deposits/withdrawals for this date BEFORE calculating lot size
      // (deposits should affect the balance BEFORE the day's trade)
      const dayTransaction = transactionsByDate[dateKey] || 0;
      if (dayTransaction !== 0) {
        runningBalance += dayTransaction;
      }
      
      // For completed trades, use the STORED lot_size and projected_profit from trade logs
      // This ensures Trade History and Daily Projection show consistent values
      const hasStoredTradeData = tradeLog && tradeLog.lot_size && tradeLog.projected_profit;
      
      // Calculate lot size and target profit based on current running balance
      // But use stored values for completed trades to maintain consistency
      let lotSize, targetProfit;
      if (hasStoredTradeData) {
        // Use stored values from when the trade was logged
        lotSize = tradeLog.lot_size;
        targetProfit = tradeLog.projected_profit;
      } else {
        // Recalculate for days without trades
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
        status = 'missed'; // Past day without trade
      } else if (isToday && activeSignal) {
        status = 'active';
      } else if (isFuture) {
        status = 'future';
      }
      
      // Calculate P/L difference based on projected profit (stored or calculated)
      const plDiff = hasTraded && actualProfit !== undefined 
        ? truncateTo2Decimals(actualProfit - targetProfit)
        : null;
      
      // Determine performance based on values
      let performance = null;
      if (hasTraded && actualProfit !== undefined) {
        if (actualProfit >= targetProfit) {
          performance = actualProfit > targetProfit ? 'exceeded' : 'perfect';
        } else if (actualProfit > 0) {
          performance = 'below';
        } else {
          performance = 'below';
        }
      }
      
      // For today, recalculate lot size and target profit based on live account value
      // For past days with trades, use stored values; for future days, use calculated values
      let effectiveLotSize, effectiveTargetProfit, effectiveBalance;
      
      if (isToday && liveAccountValue !== null) {
        // CRITICAL FIX: "Balance Before" should show the balance BEFORE today's trade
        // If we traded today, the live account value already INCLUDES today's profit + commission
        // So we need to subtract them to get the true "Balance Before"
        if (hasTraded && actualProfit !== undefined) {
          // Calculate what the balance was BEFORE we traded
          effectiveBalance = truncateTo2Decimals(liveAccountValue - actualProfit - commission);
        } else {
          // No trade yet today, live value IS the balance before
          effectiveBalance = liveAccountValue;
        }
        effectiveLotSize = truncateTo2Decimals(effectiveBalance / 980);
        effectiveTargetProfit = truncateTo2Decimals(effectiveLotSize * 15);
        // CRITICAL FIX: Sync runningBalance with effectiveBalance for today
        runningBalance = effectiveBalance;
      } else if (hasStoredTradeData) {
        // CRITICAL: For days with stored trade data, derive balance FROM the stored lot_size
        // This ensures Balance Before matches the LOT Size (Balance = LOT × 980)
        effectiveLotSize = lotSize;
        effectiveTargetProfit = targetProfit;
        effectiveBalance = truncateTo2Decimals(lotSize * 980);
        // CRITICAL FIX: Sync runningBalance with effectiveBalance to prevent divergence
        // This ensures the next day's calculation starts from the correct base
        runningBalance = effectiveBalance;
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
        commission: commission,  // Daily commission from referrals
        plDiff: hasTraded && actualProfit !== undefined 
          ? truncateTo2Decimals(actualProfit - effectiveTargetProfit)
          : null,
        performance: performance,
        status: status,
        isToday: isToday,
        hasTransaction: dayTransaction !== 0,
        transactionAmount: dayTransaction,
        // Error trade properties
        isErrorTrade: isErrorTrade,
        errorType: errorType,
        errorExplanation: errorExplanation,
      });
      
      // Add profit AND commission to running balance for next day's calculation
      // Balance formula: Next Day Balance = Today's Balance + Today's Profit + Today's Commission
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

// Generate monthly projection data for accordion (up to 5 years = 60 months)
// Now includes past months if user has trade data in those months
// effectiveStartDate filters out months before the user's start date (for "new trader" resets)
export const generateMonthlyProjection = (accountBalance, tradeLogs = {}, globalHolidayDates = new Set(), deposits = [], effectiveStartDate = null) => {
  const months = [];
  const today = new Date();
  
  // Find the earliest trade or deposit date to determine if we need to show past months
  const tradeKeys = Object.keys(tradeLogs).sort();
  const depositDates = deposits.map(d => d.created_at?.split('T')[0]).filter(Boolean).sort();
  const allDates = [...tradeKeys, ...depositDates].sort();
  
  // Parse effective start date for filtering (for "new trader" users who reset)
  let effectiveStartParsed = null;
  if (effectiveStartDate) {
    effectiveStartParsed = new Date(effectiveStartDate + 'T00:00:00');
    if (isNaN(effectiveStartParsed.getTime())) {
      effectiveStartParsed = null;
    }
  }
  
  let startMonthOffset = 0;
  
  // For licensees with an effectiveStartDate, use that to determine history months
  // even if they have no personal trade logs or deposits
  if (effectiveStartParsed) {
    const monthsDiff = (today.getFullYear() - effectiveStartParsed.getFullYear()) * 12 +
                       (today.getMonth() - effectiveStartParsed.getMonth());
    startMonthOffset = -monthsDiff;
  } else if (allDates.length > 0) {
    const earliestDate = new Date(allDates[0]);
    const monthsDiff = (today.getFullYear() - earliestDate.getFullYear()) * 12 + 
                       (today.getMonth() - earliestDate.getMonth());
    startMonthOffset = -monthsDiff; // Negative to go back in time
  }
  
  // For past months, we need to calculate forward from the earliest data point
  // For future months, we project forward from current balance
  
  // First, gather all past months with data
  const pastMonths = [];
  for (let monthOffset = startMonthOffset; monthOffset < 0; monthOffset++) {
    const monthDate = new Date(today.getFullYear(), today.getMonth() + monthOffset, 1);
    const monthKey = `${monthDate.getFullYear()}-${String(monthDate.getMonth() + 1).padStart(2, '0')}`;
    
    // Skip months that are entirely before the effective start date
    // For "new trader" users, don't show months before their reset date
    if (effectiveStartParsed) {
      const monthLastDay = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0);
      if (monthLastDay < effectiveStartParsed) {
        continue; // Skip this month entirely
      }
    }
    
    const hasTradesInMonth = tradeKeys.some(key => key.startsWith(monthKey));
    const hasDepositsInMonth = depositDates.some(d => d?.startsWith(monthKey));
    
    if (hasTradesInMonth || hasDepositsInMonth || effectiveStartParsed) {
      // Get trades for this month
      const monthTrades = Object.entries(tradeLogs)
        .filter(([key]) => key.startsWith(monthKey))
        .sort(([a], [b]) => a.localeCompare(b));
      
      // Count trading days and sum profits
      const lastDay = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0);
      let tradingDays = 0;
      let currentDate = new Date(monthDate);
      
      while (currentDate <= lastDay) {
        if (isTradingDay(currentDate, globalHolidayDates)) {
          tradingDays++;
        }
        currentDate.setDate(currentDate.getDate() + 1);
      }
      
      // For past months, we show actual data from trade logs
      const totalProfit = monthTrades.reduce((sum, [_, log]) => sum + (log?.actual_profit || 0), 0);
      
      pastMonths.push({
        monthOffset: monthOffset,
        year: 0, // Will be labeled as "History"
        monthDate: new Date(monthDate),
        monthKey: monthKey,
        monthName: monthDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
        tradingDays: tradingDays,
        isCurrentMonth: false,
        isPastMonth: true,
        totalProfit: totalProfit,
        tradesCount: monthTrades.length,
      });
    }
  }
  
  // Add past months to the result (they'll appear first due to negative monthOffset)
  months.push(...pastMonths);
  
  // Now add current and future months with projections
  // IMPORTANT: Use QUARTERLY FIXED daily profit formula
  // Daily Profit = round((Balance at Quarter Start / 980) * 15, 2)
  // Daily profit is FIXED for entire quarter, only recalculated at new quarter boundaries
  
  let balance = accountBalance || 0;
  
  // Helper to get quarter number (1-4) from a date
  const getQuarter = (date) => Math.floor(date.getMonth() / 3) + 1;
  
  // Track current quarter for quarterly recalculation
  let currentQuarter = getQuarter(today);
  let currentYear = today.getFullYear();
  // Calculate quarterly fixed daily profit at the START of this quarter
  let quarterlyDailyProfit = Math.round(((balance / 980) * 15) * 100) / 100;
  
  for (let monthOffset = 0; monthOffset <= 60; monthOffset++) {
    const monthDate = new Date(today.getFullYear(), today.getMonth() + monthOffset, 1);
    const monthKey = `${monthDate.getFullYear()}-${String(monthDate.getMonth() + 1).padStart(2, '0')}`;
    
    const isCurrentMonth = monthOffset === 0;
    
    // Calculate trading days in this month
    let tradingDays = 0;
    let monthStartBalance = balance;
    const lastDay = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0);
    
    // For current month, start from today
    let currentDate = isCurrentMonth ? new Date(today) : new Date(monthDate);
    
    while (currentDate <= lastDay) {
      // Check if we've entered a new quarter - recalculate daily profit
      const dateQuarter = getQuarter(currentDate);
      const dateYear = currentDate.getFullYear();
      if (dateYear !== currentYear || dateQuarter !== currentQuarter) {
        // New quarter started - recalculate daily profit based on current balance
        quarterlyDailyProfit = Math.round(((balance / 980) * 15) * 100) / 100;
        currentQuarter = dateQuarter;
        currentYear = dateYear;
      }
      
      if (isTradingDay(currentDate, globalHolidayDates)) {
        tradingDays++;
        // Use the FIXED quarterly daily profit, not a recalculated one
        balance = Math.round((balance + quarterlyDailyProfit) * 100) / 100;
      }
      currentDate.setDate(currentDate.getDate() + 1);
    }
    
    // Include current month (offset 0) in Year 1
    const yearNumber = Math.max(1, Math.ceil((monthOffset + 1) / 12));
    
    months.push({
      monthOffset: monthOffset,
      year: yearNumber,
      monthDate: new Date(monthDate),
      monthKey: monthKey,
      monthName: monthDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
      startBalance: monthStartBalance,
      endBalance: balance,
      lotSize: balance / 980,
      dailyProfit: quarterlyDailyProfit, // Show the fixed quarterly daily profit
      tradingDays: tradingDays,
      isCurrentMonth: isCurrentMonth,
      isPastMonth: false,
    });
  }
  
  return months;
};

// Group months by year for accordion
// Year 0 = "History" (past months with trade data) - should appear FIRST
export const groupMonthsByYear = (monthlyData) => {
  const years = {};
  monthlyData.forEach(m => {
    const yearKey = m.year === 0 ? 'History' : `Year ${m.year}`;
    if (!years[yearKey]) {
      years[yearKey] = [];
    }
    years[yearKey].push(m);
  });
  
  // Return as array of [yearKey, months] sorted so History comes first
  const sortedYears = Object.entries(years).sort(([a], [b]) => {
    if (a === 'History') return -1;
    if (b === 'History') return 1;
    return parseInt(a.replace('Year ', '')) - parseInt(b.replace('Year ', ''));
  });
  
  // Convert back to object but maintain order
  const orderedYears = {};
  sortedYears.forEach(([key, value]) => {
    orderedYears[key] = value;
  });
  
  return orderedYears;
};

// Generate projection for specific periods using QUARTERLY FIXED daily profit
// Formula: Daily Profit = round((Balance at Quarter Start / 980) * 15, 2)
// Daily profit is FIXED for entire quarter (~63 trading days), recalculated at new quarter
