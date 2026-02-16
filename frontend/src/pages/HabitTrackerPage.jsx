import React, { useState, useEffect, useCallback } from 'react';
import { habitAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CheckCircle2, Circle, Lock, Unlock, Send, ExternalLink, ClipboardCopy, Flame, Trophy, Calendar } from 'lucide-react';
import { toast } from 'sonner';

const HabitTrackerPage = () => {
  const { user } = useAuth();
  const [habits, setHabits] = useState([]);
  const [completions, setCompletions] = useState([]);
  const [gateUnlocked, setGateUnlocked] = useState(true);
  const [date, setDate] = useState('');
  const [streak, setStreak] = useState({ current_streak: 0, longest_streak: 0, total_days: 0 });
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(null);

  const loadHabits = useCallback(async () => {
    try {
      const res = await habitAPI.getHabits();
      setHabits(res.data.habits || []);
      setCompletions(res.data.completions_today || []);
      setGateUnlocked(res.data.gate_unlocked);
      setDate(res.data.date);
      if (res.data.streak) setStreak(res.data.streak);
    } catch {
      toast.error('Failed to load habits');
    }
    setLoading(false);
  }, []);

  useEffect(() => { loadHabits(); }, [loadHabits]);

  const handleToggle = async (habitId) => {
    const isCompleted = completions.includes(habitId);
    setCompleting(habitId);
    try {
      if (isCompleted) {
        await habitAPI.uncompleteHabit(habitId);
        toast.info('Habit unmarked');
      } else {
        const res = await habitAPI.completeHabit(habitId);
        if (!res.data.already) toast.success('Habit completed!');
      }
      await loadHabits();
    } catch {
      toast.error('Failed to update habit');
    }
    setCompleting(null);
  };

  const handleCopyAction = (text) => {
    navigator.clipboard.writeText(text).then(() => toast.success('Copied to clipboard!'));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (habits.length === 0) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-white">Daily Habits</h1>
        <Card className="glass-card">
          <CardContent className="p-8 text-center text-zinc-400">
            <p>No habits configured yet. Your admin will add daily tasks soon.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const completedCount = habits.filter(h => completions.includes(h.id)).length;

  return (
    <div className="space-y-6" data-testid="habit-tracker-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Daily Habits</h1>
          <p className="text-sm text-zinc-400 mt-1">{date}</p>
        </div>
        <div className="flex items-center gap-2">
          {gateUnlocked ? (
            <span className="flex items-center gap-1.5 text-sm font-medium text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-full" data-testid="gate-status-unlocked">
              <Unlock className="w-4 h-4" /> Signal Unlocked
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-sm font-medium text-orange-400 bg-orange-500/10 px-3 py-1.5 rounded-full" data-testid="gate-status-locked">
              <Lock className="w-4 h-4" /> Complete a task to unlock
            </span>
          )}
        </div>
      </div>

      {/* Streak badges */}
      <div className="grid grid-cols-3 gap-3" data-testid="streak-badges">
        <div className="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800 text-center">
          <div className="flex items-center justify-center gap-1.5 mb-1">
            <Flame className={`w-5 h-5 ${streak.current_streak > 0 ? 'text-orange-400' : 'text-zinc-600'}`} />
          </div>
          <p className="text-2xl font-bold text-white">{streak.current_streak}</p>
          <p className="text-[11px] text-zinc-500">Current Streak</p>
        </div>
        <div className="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800 text-center">
          <div className="flex items-center justify-center gap-1.5 mb-1">
            <Trophy className={`w-5 h-5 ${streak.longest_streak > 0 ? 'text-amber-400' : 'text-zinc-600'}`} />
          </div>
          <p className="text-2xl font-bold text-white">{streak.longest_streak}</p>
          <p className="text-[11px] text-zinc-500">Best Streak</p>
        </div>
        <div className="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800 text-center">
          <div className="flex items-center justify-center gap-1.5 mb-1">
            <Calendar className="w-5 h-5 text-blue-400" />
          </div>
          <p className="text-2xl font-bold text-white">{streak.total_days}</p>
          <p className="text-[11px] text-zinc-500">Total Days</p>
        </div>
      </div>

      {/* Progress */}
      <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-blue-500 to-emerald-500 transition-all duration-500"
          style={{ width: `${habits.length ? (completedCount / habits.length) * 100 : 0}%` }}
        />
      </div>
      <p className="text-xs text-zinc-500">{completedCount} of {habits.length} completed</p>

      {/* Habits list */}
      <div className="space-y-3">
        {habits.map(habit => {
          const done = completions.includes(habit.id);
          return (
            <Card
              key={habit.id}
              className={`glass-card transition-all duration-300 ${done ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-zinc-800'}`}
              data-testid={`habit-card-${habit.id}`}
            >
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <button
                    onClick={() => handleToggle(habit.id)}
                    disabled={completing === habit.id}
                    className="mt-0.5 shrink-0"
                    data-testid={`habit-toggle-${habit.id}`}
                  >
                    {completing === habit.id ? (
                      <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                    ) : done ? (
                      <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                    ) : (
                      <Circle className="w-6 h-6 text-zinc-600 hover:text-zinc-400 transition-colors" />
                    )}
                  </button>
                  <div className="flex-1 min-w-0">
                    <p className={`font-medium ${done ? 'text-emerald-300 line-through' : 'text-white'}`}>
                      {habit.title}
                    </p>
                    {habit.description && (
                      <p className="text-sm text-zinc-400 mt-1">{habit.description}</p>
                    )}

                    {/* Action data: show pre-written message or link */}
                    {habit.action_type === 'send_invite' && habit.action_data && (
                      <div className="mt-3 p-3 bg-zinc-900/60 rounded-lg border border-zinc-800">
                        <p className="text-xs text-zinc-500 mb-1.5">Pre-written message:</p>
                        <p className="text-sm text-zinc-300 whitespace-pre-wrap">{habit.action_data}</p>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="mt-2 text-blue-400 hover:text-blue-300 gap-1.5"
                          onClick={() => handleCopyAction(habit.action_data)}
                          data-testid={`copy-invite-${habit.id}`}
                        >
                          <ClipboardCopy className="w-3.5 h-3.5" /> Copy Message
                        </Button>
                      </div>
                    )}

                    {habit.action_type === 'link_click' && habit.action_data && (
                      <a
                        href={habit.action_data}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-2 inline-flex items-center gap-1 text-sm text-blue-400 hover:text-blue-300"
                      >
                        <ExternalLink className="w-3.5 h-3.5" /> Open Link
                      </a>
                    )}

                    {habit.is_gate && !done && (
                      <p className="text-xs text-orange-400 mt-2 flex items-center gap-1">
                        <Lock className="w-3 h-3" /> Completing this unlocks your daily signal
                      </p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
};

export default HabitTrackerPage;
