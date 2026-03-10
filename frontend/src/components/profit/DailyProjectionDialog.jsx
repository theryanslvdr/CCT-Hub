/**
 * DailyProjectionDialog - Shows daily projection table for a selected month
 * Extracted from ProfitTrackerPage.jsx for maintainability
 */
import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import {
  Tooltip as ShadcnTooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Calendar, Check, X, Edit3, AlertTriangle, TreePine, Loader2 } from 'lucide-react';
import { formatNumber } from '@/lib/utils';
import { truncateTo2Decimals, formatMoney, formatLargeNumber } from '@/utils/profitCalculations';

export const DailyProjectionDialog = ({
  open,
  onOpenChange,
  selectedMonth,
  dailyData,
  isLicensee,
  isMasterAdmin,
  simulatedView,
  globalHolidays,
  tradeLogs,
  togglingTrade,
  onToggleTradeOverride,
  onOpenEnterAP,
  onDidNotTrade,
  onOpenAdjustCommission,
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="glass-card border-zinc-800 max-w-5xl max-h-[80vh]">
        <DialogHeader className="text-left">
          <DialogTitle className="text-white flex flex-col md:flex-row md:items-center gap-2">
            <div className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-orange-400" />
              <span className="hidden md:inline">Daily Projection - </span>
              <span className="md:hidden text-left">{selectedMonth?.monthName}</span>
              <span className="hidden md:inline">{selectedMonth?.monthName}</span>
            </div>
            {selectedMonth?.isCurrentMonth && (
              <span className="text-xs bg-orange-500/10 text-orange-400 px-2 py-0.5 rounded-full md:ml-2 w-fit">
                <span className="hidden md:inline">{dailyData.filter(day => day.actualProfit === undefined && day.status !== 'completed').length} Days remaining</span>
                <span className="md:hidden">{dailyData.filter(day => day.actualProfit === undefined && day.status !== 'completed').length} Days</span>
              </span>
            )}
          </DialogTitle>
        </DialogHeader>
        
        {/* Monthly Summary Card */}
        {dailyData.length > 0 && (
          <div className={`grid ${isLicensee ? 'grid-cols-2' : 'grid-cols-3'} gap-3 mt-4`}>
            <div className="p-3 rounded-lg bg-gradient-to-r from-orange-500/10 to-amber-500/5 border border-orange-500/15">
              <p className="text-xs text-orange-400 uppercase tracking-wider">Monthly Target</p>
              <p className="text-lg font-bold font-mono text-orange-400 mt-1">
                ${formatNumber(
                  dailyData.reduce((sum, day) => sum + (day.targetProfit || 0), 0)
                )}
              </p>
              <p className="text-[10px] text-zinc-500 mt-0.5">
                {dailyData.length} trading days
              </p>
            </div>
            <div className="p-3 rounded-lg bg-gradient-to-r from-emerald-500/10 to-emerald-500/5 border border-emerald-500/20">
              <p className="text-xs text-emerald-400 uppercase tracking-wider">Current Profit</p>
              <p className={`text-lg font-bold font-mono mt-1 ${
                dailyData
                  .filter(day => day.managerTraded === true || (day.status === 'completed' && day.actualProfit !== undefined))
                  .reduce((sum, day) => sum + (day.actualProfit || day.targetProfit || 0), 0) >= 0
                  ? 'text-emerald-400' : 'text-red-400'
              }`}>
                ${formatNumber(
                  dailyData
                    .filter(day => day.managerTraded === true || (day.status === 'completed' && day.actualProfit !== undefined))
                    .reduce((sum, day) => sum + (day.actualProfit || day.targetProfit || 0), 0)
                )}
              </p>
              <p className="text-[10px] text-zinc-500 mt-0.5">
                {dailyData.filter(day => day.managerTraded === true || (day.status === 'completed' && day.actualProfit !== undefined)).length} trades completed
              </p>
            </div>
            {!isLicensee && (
              <div className="p-3 rounded-lg bg-gradient-to-r from-cyan-500/10 to-amber-500/5 border border-cyan-500/20">
                <p className="text-xs text-cyan-400 uppercase tracking-wider">Total Commission</p>
                <p className="text-lg font-bold font-mono text-cyan-400 mt-1">
                  ${formatNumber(
                    dailyData
                      .reduce((sum, day) => sum + (day.commission || 0), 0)
                  )}
                </p>
                <p className="text-[10px] text-zinc-500 mt-0.5">
                  From referral bonuses
                </p>
              </div>
            )}
          </div>
        )}
        
        <div className="mt-4 max-h-[50vh] overflow-y-auto">
          {dailyData.length > 0 ? (
            <table className="w-full data-table text-sm">
              <thead className="sticky top-0 bg-zinc-900">
                <tr>
                  <th>Date</th>
                  <th>Balance Before</th>
                  {!isLicensee && <th>LOT Size</th>}
                  <th>Target Profit</th>
                  {isLicensee ? (
                    <th>Manager Traded</th>
                  ) : (
                    <>
                      <th>Actual Profit</th>
                      <th>Commission</th>
                      <th>P/L Diff</th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody>
                {dailyData.map((day) => {
                  const plDiff = day.status === 'completed' && day.actualProfit !== undefined 
                    ? day.actualProfit - day.targetProfit 
                    : null;
                  const masterTraded = day.managerTraded;
                  const isGlobalHoliday = globalHolidays.some(h => h.date === day.dateKey);
                  
                  let rowClass = '';
                  if (isGlobalHoliday) {
                    rowClass = 'bg-emerald-500/10 border-l-2 border-l-emerald-500';
                  } else if (day.isToday) {
                    rowClass = 'bg-orange-500/10 border-l-2 border-l-orange-500';
                  } else if (day.status === 'completed') {
                    rowClass = 'bg-emerald-500/5';
                  } else if (day.status === 'missed') {
                    rowClass = 'bg-zinc-800/30 opacity-75';
                  }
                  
                  if (isGlobalHoliday) {
                    return (
                      <tr key={day.dateKey} className={rowClass}>
                        <td className="font-medium">
                          <div className="flex items-center gap-2">
                            <TreePine className="w-4 h-4 text-emerald-400" />
                            {day.dateStr}
                          </div>
                        </td>
                        <td colSpan={isLicensee ? 4 : 6} className="text-center">
                          <span className="text-emerald-400 font-medium flex items-center justify-center gap-2">
                            <TreePine className="w-4 h-4" />
                            HOLIDAY
                            <TreePine className="w-4 h-4" />
                          </span>
                        </td>
                      </tr>
                    );
                  }
                  
                  return (
                    <tr key={day.dateKey} className={rowClass}>
                      <td className="font-medium">
                        {day.dateStr}
                        {day.isToday && (
                          <span className="ml-2 text-xs bg-orange-500 text-white px-1.5 py-0.5 rounded">TODAY</span>
                        )}
                        {day.status === 'completed' && !day.isToday && (
                          <span className="ml-2 text-xs bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded">&#10003;</span>
                        )}
                        {!isLicensee && tradeLogs[day.dateKey]?.is_manual_adjustment && (
                          <span className="ml-1 text-xs bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded" title="Manually Adjusted">
                            &#9998;
                          </span>
                        )}
                      </td>
                      <td className="font-mono text-white">{formatLargeNumber(day.balanceBefore)}</td>
                      {!isLicensee && (
                        <td className="font-mono text-purple-400">{truncateTo2Decimals(day.lotSize).toFixed(2)}</td>
                      )}
                      
                      <td className="font-mono text-zinc-400">
                        {isLicensee && day.status !== 'future' && !masterTraded ? (
                          <span className="text-zinc-500">--</span>
                        ) : (
                          formatMoney(day.targetProfit)
                        )}
                      </td>
                      
                      {/* Licensee: Manager Traded column */}
                      {isLicensee && (
                        <td className="text-center">
                          {day.status === 'future' ? (
                            <span className="text-zinc-500 text-xs">-</span>
                          ) : isMasterAdmin && simulatedView?.licenseId ? (
                            <div className="flex items-center justify-center gap-2">
                              <Switch
                                checked={masterTraded || false}
                                onCheckedChange={() => onToggleTradeOverride(day.dateKey, masterTraded)}
                                disabled={togglingTrade === day.dateKey}
                                className="data-[state=checked]:bg-emerald-500 data-[state=unchecked]:bg-red-500"
                                data-testid={`trade-toggle-${day.dateKey}`}
                              />
                              {togglingTrade === day.dateKey && (
                                <Loader2 className="w-3 h-3 animate-spin text-zinc-400" />
                              )}
                            </div>
                          ) : masterTraded ? (
                            <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-emerald-500/20" title="Manager traded - profit added">
                              <Check className="w-4 h-4 text-emerald-400" />
                            </span>
                          ) : (
                            <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-red-500/20" title="Manager did not trade - balance carried forward">
                              <X className="w-4 h-4 text-red-400" />
                            </span>
                          )}
                        </td>
                      )}
                      
                      {/* Non-licensee: Actual Profit column */}
                      {!isLicensee && (
                        <td>
                          {day.status === 'completed' ? (
                            day.isErrorTrade ? (
                              <TooltipProvider>
                                <ShadcnTooltip>
                                  <TooltipTrigger asChild>
                                    <span className="font-mono text-orange-400 inline-flex items-center gap-1 cursor-help">
                                      <AlertTriangle className="w-3.5 h-3.5" />
                                      {day.actualProfit >= 0 ? '+' : ''}{formatMoney(day.actualProfit)}
                                    </span>
                                  </TooltipTrigger>
                                  <TooltipContent side="top" className="max-w-[250px] bg-zinc-900 border border-orange-500/30 text-orange-200">
                                    <p className="font-semibold text-orange-400 mb-1">Error Trade Correction</p>
                                    {day.errorType && <p className="text-xs text-zinc-400">Type: {day.errorType}</p>}
                                    {day.errorExplanation && <p className="text-xs">{day.errorExplanation}</p>}
                                  </TooltipContent>
                                </ShadcnTooltip>
                              </TooltipProvider>
                            ) : (
                              <span className={`font-mono ${day.actualProfit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                {day.actualProfit >= 0 ? '+' : ''}{formatMoney(day.actualProfit)}
                              </span>
                            )
                          ) : day.status === 'active' ? (
                            <Button
                              size="sm"
                              className="h-6 text-xs btn-primary"
                              onClick={() => window.location.href = '/trade-monitor'}
                              data-testid="trade-now-daily"
                            >
                              Trade Now
                            </Button>
                          ) : day.status === 'missed' ? (
                            <div className="flex flex-col md:flex-row gap-1">
                              <TooltipProvider>
                                <ShadcnTooltip>
                                  <TooltipTrigger asChild>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      className="h-6 w-6 md:w-auto text-xs border-amber-500/50 text-amber-400 hover:bg-amber-500/20 p-0 md:px-2"
                                      onClick={() => onOpenEnterAP(day)}
                                      data-testid={`enter-ap-${day.dateKey}`}
                                    >
                                      <Edit3 className="w-3 h-3 md:mr-1" />
                                      <span className="hidden md:inline">Adjust Trade</span>
                                    </Button>
                                  </TooltipTrigger>
                                  <TooltipContent side="top" className="md:hidden bg-zinc-800 text-white">
                                    Adjust Trade
                                  </TooltipContent>
                                </ShadcnTooltip>
                              </TooltipProvider>
                              <TooltipProvider>
                                <ShadcnTooltip>
                                  <TooltipTrigger asChild>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      className="h-6 w-6 md:w-auto text-xs border-red-500/50 text-red-400 hover:bg-red-500/20 p-0 md:px-2"
                                      onClick={() => onDidNotTrade(day)}
                                      data-testid={`did-not-trade-${day.dateKey}`}
                                    >
                                      <X className="w-3 h-3 md:mr-1" />
                                      <span className="hidden md:inline">Did Not Trade</span>
                                    </Button>
                                  </TooltipTrigger>
                                  <TooltipContent side="top" className="md:hidden bg-zinc-800 text-white">
                                    Did Not Trade
                                  </TooltipContent>
                                </ShadcnTooltip>
                              </TooltipProvider>
                            </div>
                          ) : day.status === 'future' ? (
                            <span className="text-zinc-500 text-xs">-</span>
                          ) : day.isToday ? (
                            <TooltipProvider>
                              <ShadcnTooltip>
                                <TooltipTrigger asChild>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    className="h-6 w-6 md:w-auto text-xs border-amber-500/50 text-amber-400 hover:bg-amber-500/20 p-0 md:px-2"
                                    onClick={() => onOpenEnterAP(day)}
                                    data-testid={`enter-ap-${day.dateKey}`}
                                  >
                                    <Edit3 className="w-3 h-3 md:mr-1" />
                                    <span className="hidden md:inline">Adjust Trade</span>
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent side="top" className="md:hidden bg-zinc-800 text-white">
                                  Adjust Trade
                                </TooltipContent>
                              </ShadcnTooltip>
                            </TooltipProvider>
                          ) : (
                            <TooltipProvider>
                              <ShadcnTooltip>
                                <TooltipTrigger asChild>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    className="h-6 w-6 md:w-auto text-xs border-amber-500/50 text-amber-400 hover:bg-amber-500/20 p-0 md:px-2"
                                    onClick={() => onOpenEnterAP(day)}
                                    data-testid={`enter-ap-${day.dateKey}`}
                                  >
                                    <Edit3 className="w-3 h-3 md:mr-1" />
                                    <span className="hidden md:inline">Adjust Trade</span>
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent side="top" className="md:hidden bg-zinc-800 text-white">
                                  Adjust Trade
                                </TooltipContent>
                              </ShadcnTooltip>
                            </TooltipProvider>
                          )}
                        </td>
                      )}
                      
                      {/* Commission column */}
                      {!isLicensee && (
                        <td>
                          {day.status === 'completed' || day.status === 'active' || day.isToday ? (
                            <button
                              onClick={() => onOpenAdjustCommission(day)}
                              className="font-mono text-cyan-400 hover:text-cyan-300 hover:underline cursor-pointer"
                              data-testid={`adjust-commission-${day.dateKey}`}
                            >
                              {day.commission > 0 ? `+${formatMoney(day.commission)}` : '-'}
                            </button>
                          ) : day.status === 'missed' ? (
                            <button
                              onClick={() => onOpenAdjustCommission(day)}
                              className={`hover:underline cursor-pointer ${day.commission > 0 ? 'font-mono text-cyan-400 hover:text-cyan-300' : 'text-zinc-500 text-xs hover:text-cyan-400'}`}
                              data-testid={`adjust-commission-${day.dateKey}`}
                            >
                              {day.commission > 0 ? `+${formatMoney(day.commission)}` : 'Add'}
                            </button>
                          ) : (
                            <span className="text-zinc-500 text-xs">-</span>
                          )}
                        </td>
                      )}
                      
                      {/* P/L Diff column */}
                      {!isLicensee && (
                        <td>
                          {plDiff !== null ? (
                            <span className={`font-mono ${plDiff >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                              {plDiff >= 0 ? '+' : ''}{formatMoney(plDiff)}
                            </span>
                          ) : (
                            <span className="text-zinc-500 text-xs">-</span>
                          )}
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            <div className="text-center py-8 text-zinc-500">
              No trading days in this period.
            </div>
          )}
        </div>
        <div className="mt-4 p-3 md:p-4 rounded-lg bg-zinc-900/50 text-xs text-zinc-400 max-w-full overflow-hidden">
          <p className="break-words">&#8226; Weekends and holidays are excluded from projections</p>
          {isLicensee ? (
            <>
              <p className="break-words">&#8226; <span className="text-emerald-400"><Check className="w-3 h-3 inline" /></span> = Manager traded - profit added to your balance</p>
              <p className="break-words">&#8226; <span className="text-red-400"><X className="w-3 h-3 inline" /></span> = Manager did not trade - balance carried forward (no profit)</p>
              <p className="break-words">&#8226; &quot;--&quot; in Target Profit means no trade was made that day</p>
              {isMasterAdmin && simulatedView?.licenseId && (
                <p className="mt-1 text-amber-400 break-words">&#8226; Toggle switch to override &quot;Manager Traded&quot; status for any day</p>
              )}
            </>
          ) : (
            <>
              <p className="break-words">&#8226; <span className="text-amber-400">Adjust Trade</span> = Click to enter your actual profit for missed trades</p>
              <p className="break-words">&#8226; <span className="text-orange-400">Trade Now</span> = Active signal available</p>
              <p className="break-words">&#8226; Actual profits update your Account Value when recorded</p>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default DailyProjectionDialog;
