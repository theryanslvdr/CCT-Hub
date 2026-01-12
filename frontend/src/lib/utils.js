import { clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

// Format currency
export function formatCurrency(amount, currency = 'USD') {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
  }).format(amount);
}

// Format number with commas
export function formatNumber(num, decimals = 2) {
  return num.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

// Calculate exit value (LOT × 15)
export function calculateExitValue(lotSize) {
  return lotSize * 15;
}

// Calculate withdrawal fees
export function calculateWithdrawalFees(amount) {
  const merinFee = amount * 0.03;
  const totalFees = merinFee;
  const netAmount = amount - totalFees;
  
  return {
    grossAmount: amount,
    merinFee: Math.round(merinFee * 100) / 100,
    totalFees: Math.round(totalFees * 100) / 100,
    netAmount: Math.round(netAmount * 100) / 100,
  };
}

// Calculate deposit fees (1% + $1 Binance fee)
export function calculateDepositFees(amount) {
  const depositFee = amount * 0.01;
  const binanceFee = 1;
  const totalFees = depositFee + binanceFee;
  const receiveAmount = amount - totalFees;
  
  return {
    binanceAmount: amount,
    depositFee: Math.round(depositFee * 100) / 100,
    binanceFee,
    totalFees: Math.round(totalFees * 100) / 100,
    receiveAmount: Math.round(receiveAmount * 100) / 100,
  };
}

// Format date
export function formatDate(date, format = 'short') {
  const d = new Date(date);
  if (format === 'short') {
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }
  if (format === 'long') {
    return d.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
  }
  if (format === 'time') {
    return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  }
  return d.toISOString();
}

// Get performance message
export function getPerformanceMessage(performance) {
  const messages = {
    exceeded: [
      "Amazing! You beat the target! 🎉",
      "Incredible trade! Well done! 🚀",
      "You crushed it! Keep it up! 💪",
    ],
    perfect: [
      "Perfect! 1:1! 🎯",
      "Nice Trade! Spot on! ✨",
      "You played safe! 👌",
    ],
    below: [
      "Keep going! You got this! 💪",
      "Every trade is a lesson! 📚",
      "Tomorrow is a new opportunity! 🌅",
    ],
  };
  
  const list = messages[performance] || messages.below;
  return list[Math.floor(Math.random() * list.length)];
}

// Get time until trade
export function getTimeUntilTrade(tradeTime) {
  if (!tradeTime) return null;
  
  const [hours, minutes] = tradeTime.split(':').map(Number);
  const now = new Date();
  const trade = new Date();
  trade.setUTCHours(hours, minutes, 0, 0);
  
  // If trade time has passed today, set for tomorrow
  if (trade < now) {
    trade.setDate(trade.getDate() + 1);
  }
  
  const diff = trade - now;
  const hoursUntil = Math.floor(diff / (1000 * 60 * 60));
  const minutesUntil = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  const secondsUntil = Math.floor((diff % (1000 * 60)) / 1000);
  
  return {
    hours: hoursUntil,
    minutes: minutesUntil,
    seconds: secondsUntil,
    total: diff,
  };
}

// Convert timezone
export function convertTimezone(date, timezone = 'UTC') {
  return new Date(date).toLocaleString('en-US', { timeZone: timezone });
}

// Local storage helpers
export const storage = {
  get: (key) => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : null;
    } catch {
      return null;
    }
  },
  set: (key, value) => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      // Handle error
    }
  },
  remove: (key) => {
    localStorage.removeItem(key);
  },
};
