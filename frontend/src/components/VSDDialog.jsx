import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ResponsiveContainer, PieChart, Pie, Tooltip } from 'recharts';
import { Loader2, Users, PieChart as PieChartIcon } from 'lucide-react';
import { formatNumber } from '@/lib/utils';

/**
 * VSD (Virtual Share Distribution) Dialog
 * Shows how the Master Admin's Merin balance is distributed between themselves and licensees
 * 
 * @param {boolean} open - Whether the dialog is open
 * @param {function} onOpenChange - Callback when dialog open state changes
 * @param {object} vsdData - VSD data from /api/profit/vsd endpoint
 * @param {boolean} loading - Whether data is loading
 */
export const VSDDialog = ({ open, onOpenChange, vsdData, loading }) => {
  // Colors for pie chart
  const LICENSEE_COLORS = ['#a855f7', '#8b5cf6', '#7c3aed', '#6366f1', '#818cf8'];
  
  // Prepare pie chart data
  const getPieChartData = () => {
    if (!vsdData || vsdData.licensee_count === 0) return [];
    
    return [
      { name: 'Your Portion', value: vsdData.master_admin_portion, fill: '#10b981' },
      ...vsdData.licensee_breakdown.map((l, i) => ({
        name: l.user_name,
        value: l.current_amount,
        fill: LICENSEE_COLORS[i % LICENSEE_COLORS.length]
      }))
    ];
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="glass-card border-zinc-800 max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            <PieChartIcon className="w-5 h-5 text-purple-400" /> Virtual Share Distribution
          </DialogTitle>
        </DialogHeader>
        
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-purple-400" />
          </div>
        ) : vsdData ? (
          <div className="space-y-6 mt-4">
            {/* Summary Header */}
            <div className="p-4 rounded-xl bg-gradient-to-r from-orange-500/10 to-amber-500/10 border border-purple-500/20">
              <div className="text-sm text-zinc-400 mb-1">Total Pool (Merin Balance)</div>
              <div className="text-2xl font-bold text-white">${formatNumber(vsdData.total_pool)}</div>
              <div className="grid grid-cols-2 gap-4 mt-4">
                <div>
                  <div className="text-xs text-zinc-500">Your Portion</div>
                  <div className="text-lg font-semibold text-emerald-400">
                    ${formatNumber(vsdData.master_admin_portion)} 
                    <span className="text-xs text-zinc-500 ml-1">({vsdData.master_admin_share_percentage}%)</span>
                  </div>
                </div>
                <div>
                  <div className="text-xs text-zinc-500">Licensee Portions</div>
                  <div className="text-lg font-semibold text-purple-400">
                    ${formatNumber(vsdData.licensee_funds)} 
                    <span className="text-xs text-zinc-500 ml-1">({vsdData.licensee_share_percentage}%)</span>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Pie Chart */}
            {vsdData.licensee_count > 0 && (
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={getPieChartData()}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={70}
                      paddingAngle={2}
                      dataKey="value"
                      label={({ name, percent }) => `${name} (${(percent * 100).toFixed(1)}%)`}
                      labelLine={{ stroke: '#71717a', strokeWidth: 1 }}
                    />
                    <Tooltip 
                      formatter={(value) => [`$${formatNumber(value)}`, 'Amount']}
                      contentStyle={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', borderRadius: '8px' }}
                      labelStyle={{ color: '#fff' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
            
            {/* Licensee Table */}
            <div>
              <div className="text-sm font-medium text-zinc-300 mb-3 flex items-center gap-2">
                <Users className="w-4 h-4" /> Licensees ({vsdData.licensee_count})
              </div>
              {vsdData.licensee_count === 0 ? (
                <div className="text-center py-8 text-zinc-500">
                  No active licensees
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-zinc-800">
                        <th className="text-left py-2 px-2 text-zinc-400 font-medium">Name</th>
                        <th className="text-right py-2 px-2 text-zinc-400 font-medium">Current Balance</th>
                        <th className="text-right py-2 px-2 text-zinc-400 font-medium">Total Deposit</th>
                        <th className="text-right py-2 px-2 text-zinc-400 font-medium">Total Profit</th>
                        <th className="text-right py-2 px-2 text-zinc-400 font-medium">% Share</th>
                      </tr>
                    </thead>
                    <tbody>
                      {vsdData.licensee_breakdown.map((licensee, idx) => (
                        <tr key={licensee.license_id || idx} className="border-b border-zinc-800/50 hover:bg-zinc-800/30">
                          <td className="py-2 px-2">
                            <div className="font-medium text-white">{licensee.user_name}</div>
                            <div className="text-xs text-zinc-500 capitalize">{licensee.license_type}</div>
                          </td>
                          <td className="text-right py-2 px-2 text-white font-medium">
                            ${formatNumber(licensee.current_amount)}
                          </td>
                          <td className="text-right py-2 px-2 text-zinc-400">
                            ${formatNumber(licensee.starting_amount)}
                          </td>
                          <td className={`text-right py-2 px-2 font-medium ${licensee.total_profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            {licensee.total_profit >= 0 ? '+' : ''}${formatNumber(licensee.total_profit)}
                          </td>
                          <td className="text-right py-2 px-2 text-purple-400">
                            {licensee.share_percentage}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
            
            {/* Info Note */}
            <div className="p-3 rounded-lg bg-zinc-900/50 text-xs text-zinc-400">
              <p>• <span className="text-emerald-400">Your Portion</span> = Funds available for your personal trading/withdrawals</p>
              <p>• <span className="text-purple-400">Licensee Portions</span> = Virtual shares allocated to licensees (they deposited into your Merin account)</p>
              <p>• <span className="text-white">Total Profit</span> = Accumulated projected profits when you (manager) traded</p>
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-zinc-500">
            Failed to load data
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default VSDDialog;
