import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Edit3 } from 'lucide-react';

export const AdjustTradeDialog = ({
  open,
  onOpenChange,
  isMobile,
  enterAPDate,
  adjustmentType, setAdjustmentType,
  adjustmentAmount, setAdjustmentAmount,
  adjustedBalance, setAdjustedBalance,
  enterAPValue, setEnterAPValue,
  enterAPCommission, setEnterAPCommission,
  enterAPLoading,
  handleSubmitEnterAP,
  formatLargeNumber,
  formatMoney,
  truncateTo2Decimals,
}) => (
  <Dialog open={open && !isMobile} onOpenChange={onOpenChange}>
    <DialogContent className="glass-card border-[#222222] max-w-md">
      <DialogHeader>
        <DialogTitle className="text-white flex items-center gap-2">
          <Edit3 className="w-5 h-5 text-amber-400" /> Adjust Trade
        </DialogTitle>
      </DialogHeader>
      {enterAPDate && (
        <div className="space-y-5 py-4">
          <p className="text-zinc-400 text-sm">
            Adjust your trade data for <span className="text-white font-medium">{enterAPDate.dateStr}</span>
          </p>

          <div className="p-3 rounded-lg bg-[#0d0d0d]/50 space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-zinc-400">Calculated Balance Before</span>
              <span className="font-mono text-white">{formatLargeNumber(enterAPDate.balanceBefore || 0)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-zinc-400">Calculated Lot Size</span>
              <span className="font-mono text-purple-400">{truncateTo2Decimals(enterAPDate.lotSize || (enterAPDate.balanceBefore || 0) / 980).toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-zinc-400">Target Profit</span>
              <span className="font-mono text-zinc-400">{formatMoney(enterAPDate.targetProfit || truncateTo2Decimals((enterAPDate.lotSize || (enterAPDate.balanceBefore || 0) / 980) * 15))}</span>
            </div>
          </div>

          <div className="space-y-2">
            <Label className="text-zinc-300">Did you deposit or withdraw on this day?</Label>
            <Select value={adjustmentType} onValueChange={setAdjustmentType}>
              <SelectTrigger className="input-dark"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="profit_only">No, just enter profit</SelectItem>
                <SelectItem value="with_deposit">Yes, I made a deposit</SelectItem>
                <SelectItem value="with_withdrawal">Yes, I made a withdrawal</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {adjustmentType !== 'profit_only' && (
            <div className="space-y-2">
              <Label className="text-zinc-300">
                {adjustmentType === 'with_deposit' ? 'Deposit' : 'Withdrawal'} Amount (USD)
              </Label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                <Input
                  type="number" step="0.01" value={adjustmentAmount}
                  onChange={(e) => setAdjustmentAmount(e.target.value)}
                  placeholder="0.00" className="input-dark pl-7 font-mono"
                  data-testid="adjustment-amount-input"
                />
              </div>
            </div>
          )}

          <div className="space-y-2">
            <Label className="text-zinc-300">Adjusted Balance Before Trade (optional)</Label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
              <Input
                type="number" step="0.01" value={adjustedBalance}
                onChange={(e) => setAdjustedBalance(e.target.value)}
                placeholder={enterAPDate.balanceBefore?.toString() || '0'}
                className="input-dark pl-7 font-mono"
                data-testid="adjusted-balance-input"
              />
            </div>
            <p className="text-xs text-zinc-500">
              If the calculated balance is incorrect, enter the actual balance you had before this trade
            </p>
          </div>

          <div className="space-y-2">
            <Label className="text-zinc-300">Actual Profit (USD)</Label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
              <Input
                type="number" step="0.01" value={enterAPValue}
                onChange={(e) => setEnterAPValue(e.target.value)}
                placeholder="Enter your actual profit"
                className="input-dark pl-7 text-lg font-mono"
                data-testid="enter-ap-input"
              />
            </div>
            <p className="text-xs text-zinc-500">Enter positive for profit, negative for loss</p>
          </div>

          <div className="space-y-2">
            <Label className="text-zinc-300">Commission for the Day (USD) - Optional</Label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
              <Input
                type="number" step="0.01" value={enterAPCommission}
                onChange={(e) => setEnterAPCommission(e.target.value)}
                placeholder="0.00" className="input-dark pl-7 font-mono"
                data-testid="enter-ap-commission-input"
              />
            </div>
            <p className="text-xs text-zinc-500">Enter any referral commission you earned on this day</p>
          </div>

          {(enterAPValue || adjustmentAmount || adjustedBalance || enterAPCommission) && (
            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 space-y-2 text-sm">
              <p className="text-amber-400 font-medium">Adjustment Summary:</p>
              {adjustedBalance && adjustedBalance !== enterAPDate.balanceBefore?.toString() && (
                <div className="flex items-center justify-between">
                  <span className="text-zinc-400">New Balance Before</span>
                  <span className="font-mono text-white">${parseFloat(adjustedBalance).toLocaleString()}</span>
                </div>
              )}
              {adjustmentType !== 'profit_only' && adjustmentAmount && (
                <div className="flex items-center justify-between">
                  <span className="text-zinc-400">{adjustmentType === 'with_deposit' ? 'Deposit' : 'Withdrawal'}</span>
                  <span className={`font-mono ${adjustmentType === 'with_deposit' ? 'text-emerald-400' : 'text-red-400'}`}>
                    {adjustmentType === 'with_deposit' ? '+' : '-'}${parseFloat(adjustmentAmount).toLocaleString()}
                  </span>
                </div>
              )}
              {enterAPValue && (
                <div className="flex items-center justify-between">
                  <span className="text-zinc-400">Actual Profit</span>
                  <span className={`font-mono ${parseFloat(enterAPValue) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {parseFloat(enterAPValue) >= 0 ? '+' : ''}${parseFloat(enterAPValue).toLocaleString()}
                  </span>
                </div>
              )}
              {enterAPCommission && parseFloat(enterAPCommission) > 0 && (
                <div className="flex items-center justify-between">
                  <span className="text-zinc-400">Commission</span>
                  <span className="font-mono text-cyan-400">+${parseFloat(enterAPCommission).toLocaleString()}</span>
                </div>
              )}
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <Button variant="outline" className="flex-1 btn-secondary" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button
              className="flex-1 btn-primary"
              onClick={handleSubmitEnterAP}
              disabled={enterAPLoading || !enterAPValue}
              data-testid="submit-enter-ap"
            >
              {enterAPLoading ? 'Saving...' : 'Save Adjustment'}
            </Button>
          </div>
        </div>
      )}
    </DialogContent>
  </Dialog>
);
