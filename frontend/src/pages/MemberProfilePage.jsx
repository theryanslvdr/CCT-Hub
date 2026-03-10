import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { memberAPI } from '@/lib/api';
import { toast } from 'sonner';
import {
  User, Star, Trophy, Flame, Target, MessageSquare, HelpCircle,
  Calendar, ArrowLeft, Shield, Award, Loader2, ChevronRight
} from 'lucide-react';

const LEVEL_STYLES = {
  'Newbie': { badge: 'bg-zinc-500/20', text: 'text-zinc-300' },
  'Apprentice': { badge: 'bg-emerald-500/20', text: 'text-emerald-400' },
  'Journeyman': { badge: 'bg-orange-500/20', text: 'text-orange-400' },
  'Expert': { badge: 'bg-purple-500/20', text: 'text-purple-400' },
  'Master': { badge: 'bg-amber-500/20', text: 'text-amber-400' },
  'Legend': { badge: 'bg-red-500/20', text: 'text-red-400' },
};

const MemberProfilePage = () => {
  const { memberId } = useParams();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const r = await memberAPI.getPublicProfile(memberId);
        setProfile(r.data);
      } catch {
        toast.error('Profile not found');
      }
      setLoading(false);
    };
    load();
  }, [memberId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-zinc-500" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="text-center py-20 text-zinc-500">
        <User className="w-12 h-12 mx-auto mb-3 opacity-30" />
        <p className="text-lg font-medium">Member not found</p>
        <Link to="/forum" className="text-orange-400 text-sm mt-2 inline-block">Back to Forum</Link>
      </div>
    );
  }

  const { profile: p, stats, badges } = profile;
  const level = stats?.level || 'Newbie';
  const ls = LEVEL_STYLES[level] || LEVEL_STYLES['Newbie'];
  const joinDate = p?.created_at ? new Date(p.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long' }) : 'Unknown';

  return (
    <div className="max-w-2xl mx-auto space-y-5" data-testid="member-profile-page">
      <Link to="/forum" className="inline-flex items-center gap-1.5 text-sm text-zinc-500 hover:text-zinc-300 transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back to Forum
      </Link>

      {/* Profile Header Card */}
      <Card className="relative overflow-hidden glass-card rounded-2xl">
        {/* Banner */}
        <div className="h-24 bg-gradient-to-br from-orange-500/20 via-amber-600/10 to-transparent relative">
          <div className="absolute -top-8 -right-8 w-32 h-32 bg-orange-500/[0.1] rounded-full blur-3xl" />
        </div>
        <CardContent className="px-6 pb-6 -mt-10 relative">
          <div className="flex items-end gap-4">
            {/* Avatar */}
            {p?.profile_picture ? (
              <img src={p.profile_picture} alt={p.full_name} className="w-20 h-20 rounded-2xl border-4 border-[#111111] object-cover shadow-lg" />
            ) : (
              <div className="w-20 h-20 rounded-2xl border-4 border-[#111111] bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center shadow-lg">
                <span className="text-2xl font-bold text-white">{p?.full_name?.charAt(0) || '?'}</span>
              </div>
            )}
            <div className="flex-1 pb-1">
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-xl font-bold text-white">{p?.full_name || 'Member'}</h1>
                {p?.role === 'master_admin' && <Shield className="w-4 h-4 text-orange-400" />}
                {p?.role === 'admin' && <Shield className="w-4 h-4 text-purple-400" />}
              </div>
              <div className="flex items-center gap-3 mt-1">
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${ls.badge} ${ls.text}`}>{level}</span>
                <span className="text-xs text-zinc-500 flex items-center gap-1"><Calendar className="w-3 h-3" /> Joined {joinDate}</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { icon: Star, label: 'Points', value: (stats?.lifetime_points || 0).toLocaleString(), color: 'text-amber-400', bg: 'from-amber-500/[0.06]' },
          { icon: Flame, label: 'Best Streak', value: `${stats?.longest_streak || 0} days`, color: 'text-orange-400', bg: 'from-orange-500/[0.06]' },
          { icon: MessageSquare, label: 'Forum Posts', value: stats?.forum_posts || 0, color: 'text-teal-400', bg: 'from-teal-500/[0.06]' },
          { icon: HelpCircle, label: 'Quiz Score', value: stats?.quiz_correct_count || 0, color: 'text-purple-400', bg: 'from-purple-500/[0.06]' },
        ].map((s, i) => {
          const Icon = s.icon;
          return (
            <div key={i} className="relative overflow-hidden p-4 rounded-xl glass-card" data-testid={`profile-stat-${s.label.toLowerCase().replace(/\s/g, '-')}`}>
              <div className={`absolute -top-6 -right-6 w-20 h-20 bg-gradient-to-br ${s.bg} to-transparent rounded-full blur-xl pointer-events-none`} />
              <Icon className={`w-5 h-5 ${s.color} mb-2`} />
              <p className="text-xl font-bold font-mono text-white">{s.value}</p>
              <p className="text-[10px] text-zinc-500 uppercase tracking-wider">{s.label}</p>
            </div>
          );
        })}
      </div>

      {/* Badges */}
      {badges && badges.length > 0 && (
        <Card className="glass-card rounded-xl">
          <CardContent className="p-5">
            <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Award className="w-4 h-4 text-amber-400" /> Badges Earned
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {badges.map((b, i) => (
                <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-white/[0.03] border border-white/[0.04]" data-testid={`badge-${i}`}>
                  <span className="text-2xl">{b.icon || '🏆'}</span>
                  <div>
                    <p className="text-xs font-medium text-white">{b.name || b.badge_name}</p>
                    <p className="text-[10px] text-zinc-500">{b.description || ''}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Activity Summary */}
      <Card className="glass-card rounded-xl">
        <CardContent className="p-5">
          <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3 flex items-center gap-2">
            <Target className="w-4 h-4 text-emerald-400" /> Activity
          </h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02]">
              <span className="text-sm text-zinc-400">Current Streak</span>
              <span className="text-sm font-mono font-bold text-orange-400">{stats?.current_streak || 0} days</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02]">
              <span className="text-sm text-zinc-400">Forum Comments</span>
              <span className="text-sm font-mono font-bold text-white">{stats?.forum_comments || 0}</span>
            </div>
            {p?.referral_code && (
              <div className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02]">
                <span className="text-sm text-zinc-400">Referral Code</span>
                <span className="text-sm font-mono font-bold text-amber-400">{p.referral_code}</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MemberProfilePage;
