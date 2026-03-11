import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { storeAPI, rewardsAPI } from '@/lib/api';
import { ShoppingBag, Shield, Snowflake, TrendingUp, Flame, Loader2, ShieldCheck, Minus, Plus, Coins, Tag } from 'lucide-react';
import { toast } from 'sonner';

const HubStorePage = () => {
  const [items, setItems] = useState([]);
  const [credits, setCredits] = useState(null);
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState(null);
  // Streak freeze state
  const [freezeData, setFreezeData] = useState(null);
  const [freezeQty, setFreezeQty] = useState({ trade: 1, habit: 1 });
  const [freezePurchasing, setFreezePurchasing] = useState(null);

  const loadData = useCallback(async () => {
    try {
      const [itemsRes, creditsRes, freezeRes] = await Promise.all([
        storeAPI.getItems(),
        storeAPI.getMyCredits(),
        rewardsAPI.getStreakFreezes().catch(() => ({ data: null })),
      ]);
      setItems(itemsRes.data?.items || itemsRes.data || []);
      setCredits(creditsRes.data);
      setFreezeData(freezeRes.data);
    } catch {
      toast.error('Failed to load store');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handlePurchase = async (itemId) => {
    setPurchasing(itemId);
    try {
      await storeAPI.purchase(itemId);
      toast.success('Purchase successful!');
      loadData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Purchase failed');
    } finally {
      setPurchasing(null);
    }
  };

  const handleFreezePurchase = async (type) => {
    setFreezePurchasing(type);
    try {
      await rewardsAPI.purchaseStreakFreeze(type, freezeQty[type]);
      toast.success(`Purchased ${freezeQty[type]} ${type} streak freeze${freezeQty[type] > 1 ? 's' : ''}!`);
      setFreezeQty(prev => ({ ...prev, [type]: 1 }));
      loadData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to purchase');
    } finally {
      setFreezePurchasing(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-6 h-6 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const freezeTypes = [
    { key: 'trade', label: 'Trade Streak Freeze', desc: 'Protects your trading streak when you miss a trading day', icon: TrendingUp, available: freezeData?.trade_freezes || 0, used: freezeData?.trade_freezes_used || 0, cost: freezeData?.costs?.trade || 200, color: 'blue' },
    { key: 'habit', label: 'Habit Streak Freeze', desc: 'Protects your daily habit streak when you miss a day', icon: Flame, available: freezeData?.habit_freezes || 0, used: freezeData?.habit_freezes_used || 0, cost: freezeData?.costs?.habit || 150, color: 'orange' },
  ];

  return (
    <div className="space-y-6 max-w-4xl mx-auto" data-testid="hub-store-page">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <ShoppingBag className="w-6 h-6 text-orange-400" /> Hub Store
        </h1>
        <p className="text-sm text-zinc-400 mt-1">Purchase items to enhance your Hub experience</p>
      </div>

      {/* Credits summary */}
      {(credits || freezeData) && (
        <div className="flex items-center gap-4 text-xs text-zinc-400">
          {credits && <span className="flex items-center gap-1"><Shield className="w-3 h-3 text-cyan-400" /> Active Credits: <strong className="text-cyan-400 font-mono">{credits.active_credits?.length || 0}</strong></span>}
          {freezeData && <span className="flex items-center gap-1"><Coins className="w-3 h-3 text-amber-400" /> Reward Points: <strong className="text-amber-400 font-mono">{freezeData.available_points || 0}</strong></span>}
        </div>
      )}

      {/* Signal Gate Immunity & Other Items */}
      {items.length > 0 && (
        <Card className="glass-card border-cyan-500/20" data-testid="immunity-section">
          <CardHeader className="pb-2">
            <CardTitle className="text-white text-base flex items-center gap-2">
              <Shield className="w-4 h-4 text-cyan-400" /> Signal Gate Immunity
              <Tag className="w-3 h-3 text-zinc-600 ml-auto" />
            </CardTitle>
            <p className="text-xs text-zinc-500 mt-1">Bypass the signal gate when you miss a trade — your access stays open</p>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {items.map(item => (
                <div key={item.id || item.name} className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04] hover:border-cyan-500/30 transition-all" data-testid={`store-item-${item.name?.replace(/\s/g, '-')}`}>
                  <div className="flex items-center gap-3 mb-3">
                    <div className="p-2 rounded-lg bg-cyan-500/10">
                      <Shield className="w-5 h-5 text-cyan-400" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-white">{item.name}</p>
                      <p className="text-[11px] text-zinc-400">{item.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-mono text-amber-400">{item.cost || item.price} pts</span>
                    <Button
                      size="sm"
                      onClick={() => handlePurchase(item.id)}
                      disabled={purchasing === item.id}
                      className="bg-cyan-600 hover:bg-cyan-500 text-white text-xs h-8"
                      data-testid={`buy-${item.name?.replace(/\s/g, '-')}`}
                    >
                      {purchasing === item.id ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <ShoppingBag className="w-3 h-3 mr-1" />}
                      Purchase
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Streak Freezes Section */}
      {freezeData && (
        <Card className="glass-card border-blue-500/20" data-testid="streak-freeze-section">
          <CardHeader className="pb-2">
            <CardTitle className="text-white text-base flex items-center gap-2">
              <Snowflake className="w-4 h-4 text-cyan-400" /> Streak Freezes
              <Tag className="w-3 h-3 text-zinc-600 ml-auto" />
            </CardTitle>
            <p className="text-xs text-zinc-500 mt-1">Purchase with reward points. When you miss a day, a freeze is automatically applied to keep your streak alive.</p>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {freezeTypes.map((ft) => {
                const Icon = ft.icon;
                const qty = freezeQty[ft.key];
                const totalCost = ft.cost * qty;
                const canAfford = (freezeData?.available_points || 0) >= totalCost;
                return (
                  <div key={ft.key} className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04] hover:border-blue-500/30 transition-all" data-testid={`streak-freeze-${ft.key}`}>
                    <div className="flex items-center gap-3 mb-3">
                      <div className={`p-2 rounded-lg bg-${ft.color}-500/10`}>
                        <Icon className={`w-5 h-5 text-${ft.color}-400`} />
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-white">{ft.label}</p>
                        <p className="text-[11px] text-zinc-400">{ft.desc}</p>
                      </div>
                    </div>
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-4">
                        <div>
                          <p className="text-[10px] text-zinc-500 uppercase">Available</p>
                          <p className="text-lg font-bold font-mono text-cyan-400">{ft.available}</p>
                        </div>
                        <div>
                          <p className="text-[10px] text-zinc-500 uppercase">Used</p>
                          <p className="text-lg font-bold font-mono text-zinc-400">{ft.used}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-[10px] text-zinc-500 uppercase">Cost Each</p>
                        <p className="text-sm font-mono text-amber-400">{ft.cost} pts</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-1 bg-[#1a1a1a] rounded-lg px-1 py-1">
                        <button onClick={() => setFreezeQty(p => ({ ...p, [ft.key]: Math.max(1, qty - 1) }))} className="p-1 rounded hover:bg-white/[0.08] text-zinc-400 hover:text-white transition-colors"><Minus className="w-3.5 h-3.5" /></button>
                        <span className="text-sm font-mono text-white w-6 text-center">{qty}</span>
                        <button onClick={() => setFreezeQty(p => ({ ...p, [ft.key]: Math.min(10, qty + 1) }))} className="p-1 rounded hover:bg-white/[0.08] text-zinc-400 hover:text-white transition-colors"><Plus className="w-3.5 h-3.5" /></button>
                      </div>
                      <Button
                        onClick={() => handleFreezePurchase(ft.key)}
                        disabled={!canAfford || freezePurchasing === ft.key}
                        className={`flex-1 bg-${ft.color}-600 hover:bg-${ft.color}-500 text-white text-sm disabled:opacity-40`}
                        data-testid={`buy-${ft.key}-freeze-btn`}
                      >
                        {freezePurchasing === ft.key ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <ShieldCheck className="w-4 h-4 mr-1" />}
                        Buy for {totalCost} pts
                      </Button>
                    </div>
                    {!canAfford && <p className="text-[10px] text-red-400 mt-1.5">Not enough points ({freezeData?.available_points || 0} available)</p>}
                  </div>
                );
              })}
            </div>

            {/* Usage History */}
            {freezeData?.usage_history?.length > 0 && (
              <div className="mt-4 pt-4 border-t border-white/[0.06]">
                <p className="text-xs text-zinc-400 font-medium mb-2">Recent Freeze Usage</p>
                <div className="space-y-1.5">
                  {freezeData.usage_history.slice(0, 5).map((u, i) => (
                    <div key={i} className="flex items-center justify-between text-xs py-1.5 px-2 rounded bg-[#0d0d0d]/40">
                      <div className="flex items-center gap-2">
                        <Snowflake className="w-3 h-3 text-cyan-400" />
                        <span className="text-zinc-300 capitalize">{u.freeze_type} freeze</span>
                      </div>
                      <span className="text-zinc-500 font-mono">{u.date}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {items.length === 0 && !freezeData && (
        <Card className="glass-card">
          <CardContent className="py-16 text-center">
            <ShoppingBag className="w-12 h-12 mx-auto mb-3 text-zinc-600" />
            <p className="text-zinc-400 text-lg">Coming Soon</p>
            <p className="text-sm text-zinc-500 mt-1">New items will be available for purchase shortly</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default HubStorePage;
