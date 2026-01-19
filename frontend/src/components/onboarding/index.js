// Onboarding Wizard Step Components
// Each step is extracted into its own component for better maintainability

export { StepUserType } from './StepUserType';
export { StepNewTraderBalance } from './StepNewTraderBalance';
export { StepExperiencedStart } from './StepExperiencedStart';

// Helper functions used across steps
export const formatMoney = (amount) => {
  if (typeof amount !== 'number' || isNaN(amount)) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
};

export const calculateLotSize = (balance) => {
  const numBalance = parseFloat(balance) || 0;
  return Math.floor((numBalance / 980) * 100) / 100; // Truncate to 2 decimals
};

export const calculateProjectedProfit = (lotSize) => {
  return Math.floor((lotSize * 15) * 100) / 100; // Truncate to 2 decimals
};
