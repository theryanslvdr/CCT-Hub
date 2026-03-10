import React, { useState, useEffect, useCallback } from 'react';
import { Users, Trophy, Copy, Link2, Crown, UserPlus, ChevronRight, Loader2, CheckCircle2, ExternalLink } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { referralAPI } from '@/lib/api';
import { toast } from 'sonner';

const ReferralTrackingPage = () => {
  const [tracking, setTracking] = useState(null);
  const [leaderboard, setLeaderboard] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      const [trackRes, lbRes] = await Promise.all([
        referralAPI.getTracking(),
        referralAPI.getLeaderboard(),
      ]);
      setTracking(trackRes.data);
      setLeaderboard(lbRes.data);
    } catch {
      toast.error('Failed to load referral data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const copyLink = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-orange-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto" data-testid="referral-tracking-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Invite & Earn</h1>
        <p className="text-sm text-zinc-500 mt-1">Invite members, earn rewards, and climb the leaderboard.</p>
      </div>

      {/* Invite Link Card */}
      <Card className="border-orange-500/20 bg-gradient-to-r from-orange-500/[0.04] to-transparent">
        <CardContent className="p-5">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-orange-500/10 flex items-center justify-center shrink-0">
              <Link2 className="w-6 h-6 text-orange-400" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-white">Your Invite Link</h3>
              <p className="text-xs text-zinc-500 mt-1 mb-3">
                Share this link with people you want to invite. Your Merin code <span className="text-orange-400 font-mono">{tracking?.merin_code || tracking?.referral_code || '—'}</span> is embedded.
              </p>
              {tracking?.onboarding_invite_link ? (
                <div className="space-y-3">
                  <div className="flex gap-2">
                    <Input
                      value={tracking.onboarding_invite_link}
                      readOnly
                      className="bg-[#0a0a0a] border-white/[0.06] text-white font-mono text-xs"
                      data-testid="invite-link-display"
                    />
                    <Button
                      onClick={() => copyLink(tracking.onboarding_invite_link)}
                      className="bg-orange-500 hover:bg-orange-600 text-white shrink-0"
                      data-testid="copy-invite-link"
                    >
                      <Copy className="w-4 h-4 mr-1.5" />
                      Copy
                    </Button>
                  </div>
                  {tracking?.invite_link && (
                    <div className="flex items-center gap-1 text-[11px] text-zinc-500">
                      <ExternalLink className="w-3 h-3" />
                      <span>Direct Merin signup:</span>
                      <a href={tracking.invite_link} target="_blank" rel="noopener noreferrer" className="text-zinc-400 hover:text-zinc-300 underline truncate max-w-[300px]" data-testid="direct-merin-link-referral">
                        {tracking.invite_link}
                      </a>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-sm text-amber-400">Set your Merin referral code in Profile to generate an invite link.</p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
              <UserPlus className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{tracking?.direct_count || 0}</p>
              <p className="text-xs text-zinc-500">Direct Referrals</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center">
              <Trophy className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">
                {tracking?.milestones?.filter(m => m.achieved).length || 0}/{tracking?.milestones?.length || 6}
              </p>
              <p className="text-xs text-zinc-500">Milestones Achieved</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
              <Crown className="w-5 h-5 text-orange-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">
                #{leaderboard?.leaderboard?.find(l => l.is_current_user)?.rank || leaderboard?.current_user_rank || '—'}
              </p>
              <p className="text-xs text-zinc-500">Your Rank</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="milestones" className="w-full">
        <TabsList className="bg-[#111111] border border-white/[0.06]">
          <TabsTrigger value="milestones">Milestones</TabsTrigger>
          <TabsTrigger value="leaderboard">Leaderboard</TabsTrigger>
          <TabsTrigger value="referrals">My Referrals</TabsTrigger>
        </TabsList>

        <TabsContent value="milestones" className="mt-4">
          <div className="space-y-3" data-testid="referral-milestones">
            {tracking?.milestones?.map((m, i) => (
              <Card key={i} className={m.achieved ? 'border-emerald-500/20 bg-emerald-500/[0.02]' : ''}>
                <CardContent className="p-4">
                  <div className="flex items-center gap-4">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${m.achieved ? 'bg-emerald-500/10' : 'bg-white/[0.03]'}`}>
                      {m.achieved ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                      ) : (
                        <Users className="w-5 h-5 text-zinc-600" />
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <p className={`text-sm font-medium ${m.achieved ? 'text-emerald-400' : 'text-white'}`}>{m.title}</p>
                        <span className="text-xs text-orange-400 font-mono">+{m.points} pts</span>
                      </div>
                      <p className="text-xs text-zinc-500 mt-0.5">
                        {m.achieved ? `Achieved! (${m.threshold} referrals)` : `${tracking?.direct_count || 0} / ${m.threshold} referrals`}
                      </p>
                      {!m.achieved && (
                        <Progress value={m.progress * 100} className="h-1.5 mt-2 bg-[#1a1a1a]" />
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="leaderboard" className="mt-4">
          <Card>
            <CardContent className="p-0" data-testid="referral-leaderboard">
              {leaderboard?.leaderboard?.length > 0 ? (
                <div className="divide-y divide-white/[0.04]">
                  {leaderboard.leaderboard.map((entry) => (
                    <div
                      key={entry.user_id}
                      className={`flex items-center gap-3 px-4 py-3 ${entry.is_current_user ? 'bg-orange-500/[0.04]' : ''}`}
                    >
                      <span className={`w-8 text-center font-bold text-sm ${
                        entry.rank === 1 ? 'text-amber-400' :
                        entry.rank === 2 ? 'text-zinc-300' :
                        entry.rank === 3 ? 'text-orange-700' :
                        'text-zinc-500'
                      }`}>
                        {entry.rank <= 3 ? ['', '1st', '2nd', '3rd'][entry.rank] : `#${entry.rank}`}
                      </span>
                      <div className="w-8 h-8 rounded-full bg-[#1a1a1a] flex items-center justify-center">
                        <span className="text-xs font-medium text-zinc-400">
                          {entry.name?.charAt(0)?.toUpperCase() || '?'}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white truncate">
                          {entry.name}
                          {entry.is_current_user && <span className="text-orange-400 ml-1.5 text-xs">(you)</span>}
                        </p>
                        {entry.badge && <p className="text-[10px] text-zinc-500">{entry.badge}</p>}
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-bold text-white">{entry.referral_count}</p>
                        <p className="text-[10px] text-zinc-500">referrals</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-12 text-center text-zinc-500">
                  <Trophy className="w-8 h-8 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">No referrals yet. Be the first!</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="referrals" className="mt-4">
          <Card>
            <CardContent className="p-0" data-testid="my-referrals-list">
              {tracking?.referrals?.length > 0 ? (
                <div className="divide-y divide-white/[0.04]">
                  {tracking.referrals.map((r, i) => (
                    <div key={i} className="flex items-center gap-3 px-4 py-3">
                      <div className="w-8 h-8 rounded-full bg-[#1a1a1a] flex items-center justify-center">
                        <span className="text-xs font-medium text-zinc-400">{r.name?.charAt(0)?.toUpperCase() || '?'}</span>
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-white">{r.name}</p>
                        <p className="text-[10px] text-zinc-500">
                          Joined {new Date(r.joined).toLocaleDateString()}
                        </p>
                      </div>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full ${r.onboarded ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
                        {r.onboarded ? 'Onboarded' : 'Pending'}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-12 text-center text-zinc-500">
                  <UserPlus className="w-8 h-8 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">No referrals yet. Share your invite link to get started!</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Next Milestone CTA */}
      {tracking?.next_milestone && (
        <Card className="border-orange-500/10">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
                <ChevronRight className="w-5 h-5 text-orange-400" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-white">
                  Next: {tracking.next_milestone.title}
                </p>
                <p className="text-xs text-zinc-500">
                  {tracking.next_milestone.threshold - (tracking?.direct_count || 0)} more referral{tracking.next_milestone.threshold - (tracking?.direct_count || 0) !== 1 ? 's' : ''} to earn <span className="text-orange-400">+{tracking.next_milestone.points} pts</span>
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ReferralTrackingPage;
