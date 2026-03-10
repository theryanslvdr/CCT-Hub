import React, { useRef, useState } from 'react';
import { Share2, Download, Copy, Check, TrendingUp, Calendar, DollarSign, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { toast } from 'sonner';

const ShareTradeCard = ({ isOpen, onClose, data }) => {
  const cardRef = useRef(null);
  const [copied, setCopied] = useState(false);

  if (!data) return null;

  const {
    accountValue = 0,
    totalProfit = 0,
    totalDeposits = 0,
    tradingDays = 0,
    currentStreak = 0,
    dateRange = '',
    userName = 'Trader',
  } = data;

  const profitPercent = totalDeposits > 0 ? ((totalProfit / totalDeposits) * 100).toFixed(1) : '0.0';
  const isPositive = totalProfit >= 0;

  const handleCopyText = () => {
    const text = [
      `${userName}'s Trading Performance`,
      `Period: ${dateRange}`,
      `Account Value: $${accountValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
      `Total Profit: ${isPositive ? '+' : ''}$${totalProfit.toLocaleString(undefined, { minimumFractionDigits: 2 })} (${profitPercent}%)`,
      `Trading Days: ${tradingDays}`,
      `Current Streak: ${currentStreak} days`,
      ``,
      `Powered by CrossCurrent Finance Hub`,
    ].join('\n');

    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      toast.success('Trade summary copied!');
      setTimeout(() => setCopied(false), 2000);
    }).catch(() => toast.error('Copy failed'));
  };

  const handleDownload = async () => {
    try {
      const el = cardRef.current;
      if (!el) return;
      // Use html2canvas if available, otherwise copy text
      if (window.html2canvas) {
        const canvas = await window.html2canvas(el, { backgroundColor: '#0a0a0a', scale: 2 });
        const link = document.createElement('a');
        link.download = `trade-card-${Date.now()}.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();
        toast.success('Card downloaded!');
      } else {
        handleCopyText();
      }
    } catch {
      handleCopyText();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-[#111111] border-white/[0.08] max-w-md p-0 overflow-hidden" data-testid="share-trade-dialog">
        <DialogHeader className="p-4 pb-0">
          <DialogTitle className="text-white flex items-center gap-2">
            <Share2 className="w-5 h-5 text-orange-400" /> Share Your Performance
          </DialogTitle>
        </DialogHeader>

        {/* The shareable card */}
        <div className="p-4">
          <div
            ref={cardRef}
            className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#0a0a0a] via-[#111111] to-[#0d0d0d] border border-white/[0.08] p-6"
            data-testid="share-trade-card"
          >
            {/* Decorative glow */}
            <div className="absolute -top-12 -right-12 w-40 h-40 bg-orange-500/[0.08] rounded-full blur-3xl pointer-events-none" />
            <div className="absolute -bottom-8 -left-8 w-32 h-32 bg-amber-500/[0.05] rounded-full blur-2xl pointer-events-none" />

            {/* Header */}
            <div className="flex items-center justify-between mb-5 relative">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center">
                  <TrendingUp className="w-4 h-4 text-white" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">{userName}</p>
                  <p className="text-[10px] text-zinc-500">CrossCurrent</p>
                </div>
              </div>
              <div className="flex items-center gap-1 text-[10px] text-zinc-500">
                <Calendar className="w-3 h-3" />
                {dateRange}
              </div>
            </div>

            {/* Account Value - Hero number */}
            <div className="mb-5 relative">
              <p className="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Account Value</p>
              <p className="text-4xl font-bold font-mono text-white">
                ${Math.floor(accountValue).toLocaleString()}
                <span className="text-xl opacity-40">.{(accountValue % 1).toFixed(2).slice(2)}</span>
              </p>
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-3 gap-3 mb-5 relative">
              <div className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.04]">
                <p className="text-[9px] text-zinc-500 uppercase tracking-wider">Profit</p>
                <p className={`text-lg font-bold font-mono mt-0.5 ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                  {isPositive ? '+' : ''}{profitPercent}%
                </p>
              </div>
              <div className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.04]">
                <p className="text-[9px] text-zinc-500 uppercase tracking-wider">Days</p>
                <p className="text-lg font-bold font-mono text-white mt-0.5">{tradingDays}</p>
              </div>
              <div className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.04]">
                <p className="text-[9px] text-zinc-500 uppercase tracking-wider">Streak</p>
                <p className="text-lg font-bold font-mono text-orange-400 mt-0.5">{currentStreak}</p>
              </div>
            </div>

            {/* Profit amount */}
            <div className="flex items-center gap-2 p-3 rounded-xl bg-white/[0.03] border border-white/[0.04] relative">
              <DollarSign className={`w-5 h-5 ${isPositive ? 'text-emerald-400' : 'text-red-400'}`} />
              <div>
                <p className="text-[9px] text-zinc-500 uppercase tracking-wider">Total Profit</p>
                <p className={`text-xl font-bold font-mono ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                  {isPositive ? '+' : ''}${Math.abs(totalProfit).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </p>
              </div>
            </div>

            {/* Footer branding */}
            <div className="mt-4 pt-3 border-t border-white/[0.04] flex items-center justify-between relative">
              <p className="text-[9px] text-zinc-600">Powered by CrossCurrent Finance Hub</p>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded bg-gradient-to-br from-orange-500 to-amber-600" />
                <span className="text-[9px] text-zinc-500 font-semibold">CC</span>
              </div>
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex gap-2 px-4 pb-4">
          <Button
            onClick={handleCopyText}
            className="flex-1 gap-2 bg-white/[0.06] hover:bg-white/[0.1] border border-white/[0.08] text-zinc-300"
            data-testid="copy-trade-btn"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
            {copied ? 'Copied!' : 'Copy Text'}
          </Button>
          <Button
            onClick={handleDownload}
            className="flex-1 gap-2 bg-orange-500 hover:bg-orange-400 text-white"
            data-testid="download-trade-btn"
          >
            <Download className="w-4 h-4" /> Download
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ShareTradeCard;
