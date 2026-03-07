import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { ValueTooltip } from '@/components/ui/value-tooltip';
import { Wallet, ArrowDownToLine, TrendingUp, Calculator, Eye, EyeOff } from 'lucide-react';
import { formatFullCurrency, formatLargeNumber, formatCompact, MASKED_VALUE, maskAmount } from '@/utils/profitCalculations';
import { formatNumber } from '@/lib/utils';

export function StatsCards({
  isLicensee,
  simulatedView,
  displayAccountValue,
  effectiveTotalDeposits,
  effectiveTotalProfit,
  effectiveLotSize,
  licenseeAccountGrowth,
  hiddenCards,
  toggleCardVisibility,
  selectedCurrency,
  setSelectedCurrency,
  getCurrencySymbol,
  convertAmount,
  openBalanceVerification,
}) {
  return (
    <div className={`grid gap-3 ${isLicensee ? 'grid-cols-2 sm:grid-cols-4' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4'}`}>
      {/* Account Value */}
      <Card className="glass-card" data-testid="account-value-card">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <p className="text-xs text-zinc-400">Account Value</p>
                {!isLicensee && !simulatedView && (
                  <button
                    onClick={() => openBalanceVerification(displayAccountValue)}
                    className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 transition-colors"
                    title="Sync with Merin balance"
                    data-testid="sync-balance-btn"
                  >
                    Sync
                  </button>
                )}
                <button
                  onClick={() => toggleCardVisibility('accountValue')}
                  className="text-zinc-500 hover:text-zinc-300 transition-colors"
                  title={hiddenCards.accountValue ? "Show value" : "Hide value"}
                  data-testid="toggle-account-value"
                >
                  {hiddenCards.accountValue ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                </button>
              </div>
              <ValueTooltip exactValue={hiddenCards.accountValue ? MASKED_VALUE : formatFullCurrency(displayAccountValue)}>
                <p className="text-2xl font-bold font-mono text-white mt-1">
                  <span className="hidden md:inline">{maskAmount(formatLargeNumber(displayAccountValue), hiddenCards.accountValue)}</span>
                  <span className="md:hidden">{maskAmount(formatCompact(displayAccountValue), hiddenCards.accountValue)}</span>
                </p>
              </ValueTooltip>
            </div>
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center flex-shrink-0">
              <Wallet className="w-5 h-5 text-white" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Total Deposits */}
      <Card className="glass-card" data-testid="total-deposits-card">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <p className="text-xs text-zinc-400">Deposits</p>
                <Select value={selectedCurrency} onValueChange={setSelectedCurrency}>
                  <SelectTrigger className="w-16 h-5 text-[10px] bg-zinc-900/50 border-zinc-700">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="USD">USD</SelectItem>
                    <SelectItem value="PHP">PHP</SelectItem>
                    <SelectItem value="EUR">EUR</SelectItem>
                    <SelectItem value="GBP">GBP</SelectItem>
                  </SelectContent>
                </Select>
                <button
                  onClick={() => toggleCardVisibility('deposits')}
                  className="text-zinc-500 hover:text-zinc-300 transition-colors"
                  title={hiddenCards.deposits ? "Show value" : "Hide value"}
                  data-testid="toggle-deposits"
                >
                  {hiddenCards.deposits ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                </button>
              </div>
              <ValueTooltip exactValue={hiddenCards.deposits ? MASKED_VALUE : `${getCurrencySymbol(selectedCurrency)}${formatNumber(convertAmount(effectiveTotalDeposits, selectedCurrency))} (${formatFullCurrency(effectiveTotalDeposits)} USDT)`}>
                <p className="text-2xl font-bold font-mono text-white mt-1">
                  <span className="hidden md:inline">{maskAmount(`${getCurrencySymbol(selectedCurrency)}${formatNumber(convertAmount(effectiveTotalDeposits, selectedCurrency))}`, hiddenCards.deposits)}</span>
                  <span className="md:hidden">{maskAmount(formatCompact(effectiveTotalDeposits), hiddenCards.deposits)}</span>
                </p>
              </ValueTooltip>
              <p className="text-[10px] text-zinc-500 hidden md:block">{hiddenCards.deposits ? '' : `≈ ${formatFullCurrency(effectiveTotalDeposits)} USDT`}</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500 to-cyan-600 flex items-center justify-center flex-shrink-0">
              <ArrowDownToLine className="w-5 h-5 text-white" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Total Profit */}
      <Card className="glass-card" data-testid="total-profit-card">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <p className="text-xs text-zinc-400">Total Profit</p>
                <button
                  onClick={() => toggleCardVisibility('profit')}
                  className="text-zinc-500 hover:text-zinc-300 transition-colors"
                  title={hiddenCards.profit ? "Show value" : "Hide value"}
                  data-testid="toggle-profit"
                >
                  {hiddenCards.profit ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                </button>
              </div>
              <ValueTooltip exactValue={hiddenCards.profit ? MASKED_VALUE : formatFullCurrency(effectiveTotalProfit)}>
                <p className={`text-2xl font-bold font-mono mt-1 ${effectiveTotalProfit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  <span className="hidden md:inline">{maskAmount(`${effectiveTotalProfit >= 0 ? '+' : ''}${formatLargeNumber(effectiveTotalProfit)}`, hiddenCards.profit)}</span>
                  <span className="md:hidden">{maskAmount(`${effectiveTotalProfit >= 0 ? '+' : ''}${formatCompact(effectiveTotalProfit)}`, hiddenCards.profit)}</span>
                </p>
              </ValueTooltip>
            </div>
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center flex-shrink-0">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* LOT Size - Hidden for licensees */}
      {!isLicensee && (
        <Card className="glass-card" data-testid="current-lot-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <p className="text-xs text-zinc-400">LOT Size</p>
                  <button
                    onClick={() => toggleCardVisibility('lotSize')}
                    className="text-zinc-500 hover:text-zinc-300 transition-colors"
                    title={hiddenCards.lotSize ? "Show value" : "Hide value"}
                    data-testid="toggle-lot-size"
                  >
                    {hiddenCards.lotSize ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                  </button>
                </div>
                <p className="text-2xl font-bold font-mono text-purple-400 mt-1">
                  {maskAmount(effectiveLotSize.toFixed(2), hiddenCards.lotSize)}
                </p>
                <p className="text-[10px] text-zinc-500">Balance / 980</p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                <Calculator className="w-5 h-5 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Account Growth - Only for licensees */}
      {isLicensee && (
        <Card className="glass-card" data-testid="account-growth-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <p className="text-xs text-zinc-400">Account Growth</p>
                  <button
                    onClick={() => toggleCardVisibility('growth')}
                    className="text-zinc-500 hover:text-zinc-300 transition-colors"
                    title={hiddenCards.growth ? "Show value" : "Hide value"}
                    data-testid="toggle-growth"
                  >
                    {hiddenCards.growth ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                  </button>
                </div>
                <p className={`text-2xl font-bold font-mono mt-1 ${
                  licenseeAccountGrowth !== null && licenseeAccountGrowth >= 0 
                    ? 'text-emerald-400' 
                    : 'text-red-400'
                }`}>
                  {licenseeAccountGrowth !== null 
                    ? maskAmount(`${licenseeAccountGrowth >= 0 ? '+' : ''}${licenseeAccountGrowth.toFixed(2)}%`, hiddenCards.growth)
                    : '--'
                  }
                </p>
                <p className="text-[10px] text-zinc-500">
                  From initial {maskAmount(formatCompact(simulatedView?.starting_amount || simulatedView?.startingAmount || 0), hiddenCards.growth)}
                </p>
              </div>
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                licenseeAccountGrowth !== null && licenseeAccountGrowth >= 0
                  ? 'bg-gradient-to-br from-emerald-500 to-emerald-600'
                  : 'bg-gradient-to-br from-red-500 to-red-600'
              }`}>
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
