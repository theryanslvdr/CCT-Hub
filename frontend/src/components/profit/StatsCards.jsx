import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { ValueTooltip } from '@/components/ui/value-tooltip';
import { Wallet, ArrowDownToLine, TrendingUp, Calculator, Eye, EyeOff } from 'lucide-react';
import { formatFullCurrency, formatLargeNumber, formatCompact, MASKED_VALUE, maskAmount } from '@/utils/profitCalculations';
import { formatNumber } from '@/lib/utils';

/** Render a large number with cents dimmed */
function DimmedNumber({ value, hidden, compact, prefix = '', className = '' }) {
  if (hidden) return <span className={className}>****</span>;
  const formatted = compact ? formatCompact(value) : formatLargeNumber(value);
  const str = `${prefix}${formatted}`;
  const dotIdx = str.indexOf('.');
  if (dotIdx === -1) return <span className={className}>{str}</span>;
  return (
    <span className={className}>
      {str.slice(0, dotIdx)}
      <span className="opacity-40">{str.slice(dotIdx)}</span>
    </span>
  );
}

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
  const cards = [
    {
      id: 'accountValue',
      label: 'Account Value',
      value: displayAccountValue,
      icon: Wallet,
      gradient: 'from-orange-500 to-amber-600',
      bgGlow: 'from-orange-500/[0.06] to-transparent',
      show: true,
      extras: (
        <>
          {!isLicensee && !simulatedView && (
            <button
              onClick={() => openBalanceVerification(displayAccountValue)}
              className="text-[10px] px-1.5 py-0.5 rounded bg-orange-500/10 text-orange-400 hover:bg-orange-500/20 transition-colors"
              data-testid="sync-balance-btn"
            >
              Sync
            </button>
          )}
        </>
      ),
    },
    {
      id: 'deposits',
      label: 'Deposits',
      value: effectiveTotalDeposits,
      icon: ArrowDownToLine,
      gradient: 'from-teal-500 to-teal-600',
      bgGlow: 'from-teal-500/[0.06] to-transparent',
      show: true,
      isCurrency: true,
    },
    {
      id: 'profit',
      label: 'Total Profit',
      value: effectiveTotalProfit,
      icon: TrendingUp,
      gradient: effectiveTotalProfit >= 0 ? 'from-emerald-500 to-emerald-600' : 'from-red-500 to-red-600',
      bgGlow: effectiveTotalProfit >= 0 ? 'from-emerald-500/[0.06] to-transparent' : 'from-red-500/[0.06] to-transparent',
      show: true,
      coloredValue: true,
    },
    {
      id: 'lotSize',
      label: 'LOT Size',
      icon: Calculator,
      gradient: 'from-purple-500 to-purple-600',
      bgGlow: 'from-purple-500/[0.06] to-transparent',
      show: !isLicensee,
      isLot: true,
    },
    {
      id: 'growth',
      label: 'Account Growth',
      icon: TrendingUp,
      gradient: licenseeAccountGrowth >= 0 ? 'from-emerald-500 to-emerald-600' : 'from-red-500 to-red-600',
      bgGlow: licenseeAccountGrowth >= 0 ? 'from-emerald-500/[0.06] to-transparent' : 'from-red-500/[0.06] to-transparent',
      show: isLicensee,
      isGrowth: true,
    },
  ];

  return (
    <div className={`grid gap-3 ${isLicensee ? 'grid-cols-2 sm:grid-cols-4' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4'}`}>
      {cards.filter(c => c.show).map(card => {
        const Icon = card.icon;
        const isHidden = hiddenCards[card.id];

        return (
          <Card
            key={card.id}
            className="relative overflow-hidden bg-[#111111]/80 border border-white/[0.06] hover:border-white/[0.1] transition-all rounded-xl"
            data-testid={`${card.id}-card`}
          >
            {/* Subtle glow */}
            <div className={`absolute -top-8 -right-8 w-32 h-32 bg-gradient-to-br ${card.bgGlow} rounded-full blur-2xl pointer-events-none`} />

            <CardContent className="p-4 relative">
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-[11px] text-zinc-500 uppercase tracking-wider font-medium">{card.label}</p>
                    {card.id === 'deposits' && (
                      <Select value={selectedCurrency} onValueChange={setSelectedCurrency}>
                        <SelectTrigger className="w-16 h-5 text-[10px] bg-transparent border-white/[0.06]">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="USD">USD</SelectItem>
                          <SelectItem value="PHP">PHP</SelectItem>
                          <SelectItem value="EUR">EUR</SelectItem>
                          <SelectItem value="GBP">GBP</SelectItem>
                        </SelectContent>
                      </Select>
                    )}
                    {card.extras}
                    <button
                      onClick={() => toggleCardVisibility(card.id)}
                      className="text-zinc-600 hover:text-zinc-400 transition-colors"
                      data-testid={`toggle-${card.id}`}
                    >
                      {isHidden ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                    </button>
                  </div>

                  {/* Value display with decimal dimming */}
                  <div className="mt-1.5">
                    {card.isLot ? (
                      <p className="text-2xl font-bold font-mono text-purple-400">
                        {maskAmount(effectiveLotSize.toFixed(2), isHidden)}
                      </p>
                    ) : card.isGrowth ? (
                      <p className={`text-2xl font-bold font-mono ${licenseeAccountGrowth >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {licenseeAccountGrowth !== null
                          ? maskAmount(`${licenseeAccountGrowth >= 0 ? '+' : ''}${licenseeAccountGrowth.toFixed(2)}%`, isHidden)
                          : '--'
                        }
                      </p>
                    ) : card.isCurrency && card.id === 'deposits' ? (
                      <ValueTooltip exactValue={isHidden ? MASKED_VALUE : `${getCurrencySymbol(selectedCurrency)}${formatNumber(convertAmount(effectiveTotalDeposits, selectedCurrency))} (${formatFullCurrency(effectiveTotalDeposits)} USDT)`}>
                        <p className="text-2xl font-bold font-mono text-white">
                          <span className="hidden md:inline">{maskAmount(`${getCurrencySymbol(selectedCurrency)}${formatNumber(convertAmount(effectiveTotalDeposits, selectedCurrency))}`, isHidden)}</span>
                          <span className="md:hidden">
                            <DimmedNumber value={effectiveTotalDeposits} hidden={isHidden} compact />
                          </span>
                        </p>
                      </ValueTooltip>
                    ) : (
                      <ValueTooltip exactValue={isHidden ? MASKED_VALUE : formatFullCurrency(card.value)}>
                        <p className={`text-2xl font-bold font-mono ${card.coloredValue ? (card.value >= 0 ? 'text-emerald-400' : 'text-red-400') : 'text-white'}`}>
                          <span className="hidden md:inline">
                            <DimmedNumber
                              value={Math.abs(card.value)}
                              hidden={isHidden}
                              prefix={card.coloredValue ? (card.value >= 0 ? '+' : '-') : ''}
                            />
                          </span>
                          <span className="md:hidden">
                            <DimmedNumber
                              value={Math.abs(card.value)}
                              hidden={isHidden}
                              compact
                              prefix={card.coloredValue ? (card.value >= 0 ? '+' : '-') : ''}
                            />
                          </span>
                        </p>
                      </ValueTooltip>
                    )}
                  </div>

                  {/* Subtext */}
                  {card.id === 'deposits' && !isHidden && (
                    <p className="text-[10px] text-zinc-600 hidden md:block mt-0.5">
                      ≈ {formatFullCurrency(effectiveTotalDeposits)} USDT
                    </p>
                  )}
                  {card.isLot && (
                    <p className="text-[10px] text-zinc-600 mt-0.5">Balance / 980</p>
                  )}
                  {card.isGrowth && (
                    <p className="text-[10px] text-zinc-600 mt-0.5">
                      From initial {maskAmount(formatCompact(simulatedView?.starting_amount || simulatedView?.startingAmount || 0), isHidden)}
                    </p>
                  )}
                </div>

                {/* Icon */}
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${card.gradient} flex items-center justify-center flex-shrink-0 shadow-lg`}>
                  <Icon className="w-5 h-5 text-white" />
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
