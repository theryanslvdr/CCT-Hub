import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Sparkles, Eye } from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip } from 'recharts';

export const ProjectionVision = ({
  projectionView, setProjectionView,
  projectionChartData, projectionData,
  effectiveAccountValue, effectiveLotSize, effectiveTotalProfit,
  isLicensee,
  selectedYears, setSelectedYears,
  yearlyGroupedProjection,
  handleOpenDailyProjection,
  formatLargeNumber, formatMoney, truncateTo2Decimals,
  dataHealth, openBalanceVerification, displayAccountValue,
  simulatedView,
  DataHealthBadge,
}) => (
  <Card className="glass-highlight" data-testid="projection-vision-card">
    <CardHeader className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-3">
      <CardTitle className="text-white flex items-center gap-2 text-base sm:text-lg">
        <Sparkles className="w-4 h-4 sm:w-5 sm:h-5 text-orange-400" /> Projection Vision
        {!isLicensee && !simulatedView && dataHealth && DataHealthBadge && (
          <DataHealthBadge healthData={dataHealth} onClick={() => openBalanceVerification(displayAccountValue)} />
        )}
      </CardTitle>
      <div className="flex gap-2 w-full sm:w-auto">
        <Button
          variant={projectionView === 'summary' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setProjectionView('summary')}
          className={`flex-1 sm:flex-none text-xs sm:text-sm ${projectionView === 'summary' ? 'btn-primary' : 'btn-secondary'}`}
          data-testid="projection-summary-tab"
        >
          Summary
        </Button>
        <Button
          variant={projectionView === 'table' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setProjectionView('table')}
          className={`flex-1 sm:flex-none text-xs sm:text-sm ${projectionView === 'table' ? 'btn-primary' : 'btn-secondary'}`}
          data-testid="projection-table-tab"
        >
          <Eye className="w-3 h-3 sm:w-4 sm:h-4 mr-1" /> Monthly Table
        </Button>
      </div>
    </CardHeader>
    <CardContent className="p-3 sm:p-6">
      {projectionView === 'summary' ? (
        <div className="space-y-4 sm:space-y-6">
          <div className={`grid ${isLicensee ? 'grid-cols-2' : 'grid-cols-2 md:grid-cols-4'} gap-2 sm:gap-4 p-3 sm:p-4 rounded-lg bg-[#0d0d0d]/50`}>
            <div>
              <p className="text-[10px] sm:text-xs text-zinc-500">Current Balance</p>
              <p className="font-mono text-sm sm:text-lg text-white truncate">{formatLargeNumber(effectiveAccountValue)}</p>
            </div>
            {!isLicensee && (
              <>
                <div>
                  <p className="text-[10px] sm:text-xs text-zinc-500">LOT Size</p>
                  <p className="font-mono text-sm sm:text-lg text-purple-400">{effectiveLotSize.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-[10px] sm:text-xs text-zinc-500">Daily Profit</p>
                  <p className="font-mono text-sm sm:text-lg text-emerald-400 truncate">{formatMoney(effectiveLotSize * 15)}</p>
                </div>
                <div>
                  <p className="text-[10px] sm:text-xs text-zinc-500">Formula</p>
                  <p className="text-xs sm:text-sm text-zinc-400">Bal ÷ 980 × 15</p>
                </div>
              </>
            )}
            {isLicensee && (
              <div>
                <p className="text-[10px] sm:text-xs text-zinc-500">Total Profit</p>
                <p className={`font-mono text-sm sm:text-lg ${effectiveTotalProfit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {effectiveTotalProfit >= 0 ? '+' : ''}{formatLargeNumber(effectiveTotalProfit)}
                </p>
              </div>
            )}
          </div>

          <div className="h-[180px] sm:h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={projectionChartData}>
                <defs>
                  <linearGradient id="colorProjection" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#F97316" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#F97316" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="name" stroke="#404040" fontSize={10} tickMargin={5} />
                <YAxis
                  stroke="#404040"
                  fontSize={10}
                  width={45}
                  tickFormatter={(v) => {
                    if (v >= 1e12) return `$${(v / 1e12).toFixed(1)}T`;
                    if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
                    if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
                    if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}k`;
                    return `$${v.toFixed(0)}`;
                  }}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#18181B', border: '1px solid #27272A', borderRadius: '8px', fontSize: '12px' }}
                  formatter={(value) => [formatLargeNumber(value), 'Projected Balance']}
                />
                <Line type="monotone" dataKey="balance" stroke="#F97316" strokeWidth={2} dot={{ fill: '#F97316', r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-4">
            {projectionData.slice(1, 4).map((p, i) => (
              <div key={p.period} className={`p-2 sm:p-4 rounded-lg border ${i === 0 ? 'bg-orange-500/10 border-orange-500/20' : 'bg-[#0d0d0d]/50 border-white/[0.06]'}`}>
                <p className={`text-[10px] sm:text-xs ${i === 0 ? 'text-orange-400' : 'text-zinc-500'}`}>{p.period}</p>
                <p className={`font-mono text-sm sm:text-lg ${i === 0 ? 'text-orange-400' : 'text-white'} mt-0.5 sm:mt-1 truncate`}>
                  {formatLargeNumber(p.balance)}
                </p>
                <p className="text-[9px] sm:text-xs text-zinc-500 mt-0.5 sm:mt-1 truncate">
                  LOT: {truncateTo2Decimals(p.lotSize).toFixed(2)}
                </p>
              </div>
            ))}
            <div className="p-2 sm:p-4 rounded-lg border bg-gradient-to-br from-orange-500/10 to-amber-500/10 border-orange-500/20">
              <div className="flex items-center justify-between mb-1 sm:mb-2">
                <p className="text-[10px] sm:text-xs text-purple-400">Year</p>
                <Select value={selectedYears.toString()} onValueChange={(v) => setSelectedYears(parseInt(v))}>
                  <SelectTrigger className="w-14 sm:w-20 h-5 sm:h-6 text-[10px] sm:text-xs bg-[#0d0d0d]/50 border-white/[0.08]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {[1, 2, 3, 4, 5].map(y => (
                      <SelectItem key={y} value={y.toString()}>{y} Year{y > 1 ? 's' : ''}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <p className="font-mono text-sm sm:text-lg text-purple-400 mt-0.5 sm:mt-1 truncate">
                {formatLargeNumber(projectionData[4]?.balance || 0)}
              </p>
              <p className="text-[9px] sm:text-xs text-zinc-500 mt-0.5 sm:mt-1 truncate">
                LOT: {truncateTo2Decimals(projectionData[4]?.lotSize || 0).toFixed(2)}
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-sm text-zinc-400">
            Monthly projection based on compounding (Balance ÷ 980 × 15 per trading day). Weekends excluded.
          </p>
          <div className="max-h-[500px] overflow-y-auto">
            <Accordion type="multiple" className="space-y-2">
              {Object.entries(yearlyGroupedProjection).map(([yearKey, months]) => (
                <AccordionItem
                  key={yearKey}
                  value={`year-${yearKey}`}
                  className="border border-white/[0.06] rounded-lg overflow-hidden"
                >
                  <AccordionTrigger className="px-4 py-3 bg-[#0d0d0d]/50 hover:bg-[#0d0d0d] text-white">
                    <div className="flex items-center justify-between w-full pr-4">
                      <span className="font-medium">
                        {yearKey === 'History' ? (
                          <span className="text-amber-400">History</span>
                        ) : yearKey}
                      </span>
                      <span className="font-mono text-emerald-400">
                        {months[0]?.isPastMonth
                          ? `${months.length} month${months.length > 1 ? 's' : ''} with data`
                          : formatLargeNumber(months[months.length - 1]?.endBalance || 0)}
                      </span>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="bg-[#0a0a0a]/50">
                    <table className="w-full data-table text-sm">
                      <thead>
                        <tr>
                          <th>Month</th>
                          <th>{months[0]?.isPastMonth ? 'Trades' : 'Trading Days'}</th>
                          <th>{months[0]?.isPastMonth ? 'Total Profit' : 'Final Balance'}</th>
                          {months[0]?.isPastMonth && <th>Commission</th>}
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {months.map((m) => (
                          <tr key={m.monthKey} className={m.isCurrentMonth ? 'bg-orange-500/10' : ''}>
                            <td className="font-medium">
                              {m.monthName}
                              {m.isCurrentMonth && <span className="ml-2 text-xs text-orange-400">(Current)</span>}
                            </td>
                            <td className="font-mono text-zinc-400">
                              {m.isPastMonth ? `${m.tradesCount || 0} trades` : `${m.tradingDays} days`}
                            </td>
                            <td className="font-mono text-white">
                              {m.isPastMonth
                                ? <span className={m.totalProfit >= 0 ? 'text-emerald-400' : 'text-red-400'}>{formatLargeNumber(m.totalProfit || 0)}</span>
                                : formatLargeNumber(m.endBalance)}
                            </td>
                            {m.isPastMonth && (
                              <td className="font-mono text-purple-400">
                                {(m.totalCommission || 0) > 0 ? `+${formatLargeNumber(m.totalCommission)}` : '-'}
                              </td>
                            )}
                            <td>
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-7 text-xs text-orange-400 border-orange-400/30 hover:bg-orange-400/10"
                                onClick={() => handleOpenDailyProjection(m)}
                                data-testid={`daily-projection-${m.monthKey}`}
                              >
                                <Eye className="w-3 h-3 mr-1" /> Daily View
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>
        </div>
      )}
    </CardContent>
  </Card>
);
