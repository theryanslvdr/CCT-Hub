import React, { useState, useEffect, useCallback } from 'react';
import { storeAPI } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Shield, Coins, Clock, CheckCircle2, Loader2, Zap, ShoppingBag } from 'lucide-react';
import { toast } from 'sonner';

const StorePage = () => {
  const [items, setItems] = useState([]);
  const [points, setPoints] = useState(0);
  const [activeImmunity, setActiveImmunity] = useState(null);
  const [credits, setCredits] = useState([]);
  const [purchasing, setPurchasing] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadStore = useCallback(async () => {
    try {
      const [itemsRes, creditsRes] = await Promise.all([
        storeAPI.getItems(),
        storeAPI.getMyCredits(),
      ]);
      setItems(itemsRes.data.items || []);
      setPoints(itemsRes.data.user_points || 0);
      setActiveImmunity(itemsRes.data.active_immunity);
      setCredits(creditsRes.data.active_credits || []);
    } catch {
      toast.error('Failed to load store');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadStore(); }, [loadStore]);

  const handlePurchase = async (itemId) => {
    setPurchasing(itemId);
    try {
      const res = await storeAPI.purchase(itemId);
      toast.success(res.data.message);
      setPoints(res.data.remaining_points);
      loadStore();
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Purchase failed');
    }
    setPurchasing(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-6 h-6 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto" data-testid="store-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <ShoppingBag className="w-6 h-6 text-orange-400" /> Store
          </h1>
          <p className="text-sm text-zinc-400 mt-1">Spend your reward points on useful items</p>
        </div>
        <div className="flex items-center gap-2 bg-amber-500/10 border border-amber-500/20 rounded-xl px-4 py-2" data-testid="points-balance">
          <Coins className="w-5 h-5 text-amber-400" />
          <span className="text-lg font-bold text-amber-400 font-mono">{points}</span>
          <span className="text-xs text-zinc-500">points</span>
        </div>
      </div>

      {/* Active immunity status */}
      {credits.length > 0 && (
        <Card className="glass-card border-emerald-500/20">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
                <Shield className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-emerald-400">Gate Immunity Active</p>
                <p className="text-xs text-zinc-500">
                  Expires: {new Date(credits[0].expires_at).toLocaleDateString()} {new Date(credits[0].expires_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Store Items */}
      <div className="grid gap-4 md:grid-cols-3">
        {items.map(item => {
          const canAfford = points >= item.cost;
          return (
            <Card key={item.id} className={`glass-card transition-all ${canAfford ? 'hover:border-orange-500/30' : 'opacity-60'}`} data-testid={`store-item-${item.id}`}>
              <CardContent className="p-5 flex flex-col h-full">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-10 h-10 rounded-xl bg-orange-500/15 flex items-center justify-center">
                    <Zap className="w-5 h-5 text-orange-400" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-white">{item.name}</p>
                    <div className="flex items-center gap-1 text-xs text-zinc-500">
                      <Clock className="w-3 h-3" /> {item.duration_days} day{item.duration_days > 1 ? 's' : ''}
                    </div>
                  </div>
                </div>
                <p className="text-xs text-zinc-400 flex-1 leading-relaxed mb-4">{item.description}</p>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1">
                    <Coins className="w-4 h-4 text-amber-400" />
                    <span className="text-sm font-bold text-amber-400 font-mono">{item.cost}</span>
                  </div>
                  <Button
                    size="sm"
                    disabled={!canAfford || purchasing === item.id}
                    onClick={() => handlePurchase(item.id)}
                    className="bg-orange-500 hover:bg-orange-600 text-white h-8 text-xs disabled:opacity-40"
                    data-testid={`buy-${item.id}`}
                  >
                    {purchasing === item.id ? <Loader2 className="w-3 h-3 animate-spin" /> : canAfford ? 'Purchase' : 'Not enough'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* How it works */}
      <Card className="glass-card">
        <CardHeader className="pb-2">
          <CardTitle className="text-white text-sm">How Gate Immunity Works</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-xs text-zinc-400 leading-relaxed">
            Signal Gate Immunity Credits let you access trading signals without completing your daily habits.
            Perfect for days when you're traveling, busy, or just need a break.
          </p>
          <div className="flex items-start gap-2 text-xs text-zinc-500">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 mt-0.5 shrink-0" />
            <span>Once purchased, immunity activates immediately</span>
          </div>
          <div className="flex items-start gap-2 text-xs text-zinc-500">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 mt-0.5 shrink-0" />
            <span>Your streak is preserved during immunity periods</span>
          </div>
          <div className="flex items-start gap-2 text-xs text-zinc-500">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 mt-0.5 shrink-0" />
            <span>Earn points by completing habits, quizzes, and referring members</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default StorePage;
