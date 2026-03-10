import React, { useState, useEffect, useCallback } from 'react';
import { habitAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CheckCircle2, Circle, Lock, Unlock, Send, ExternalLink, ClipboardCopy, Flame, Trophy, Calendar, Sparkles, Loader2, ArrowRight, Instagram, Twitter, Youtube, Linkedin, Facebook, Globe, Zap } from 'lucide-react';
import { toast } from 'sonner';

const PLATFORM_ICONS = {
  Instagram: Instagram,
  Twitter: Twitter,
  YouTube: Youtube,
  LinkedIn: Linkedin,
  Facebook: Facebook,
  TikTok: Globe,
  Any: Globe,
};

const PLATFORM_COLORS = {
  Instagram: 'text-pink-400 bg-pink-500/10 border-pink-500/20',
  Twitter: 'text-sky-400 bg-sky-500/10 border-sky-500/20',
  YouTube: 'text-red-400 bg-red-500/10 border-red-500/20',
  LinkedIn: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  Facebook: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  TikTok: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
  Any: 'text-zinc-400 bg-zinc-500/10 border-zinc-500/20',
};

const LEVEL_CONFIGS = {
  1: { name: 'Getting Started', color: 'text-zinc-400', accent: 'from-zinc-500 to-zinc-400', emoji: 'Seed' },
  2: { name: 'Active Engager', color: 'text-blue-400', accent: 'from-blue-500 to-cyan-400', emoji: 'Sprout' },
  3: { name: 'Content Creator', color: 'text-purple-400', accent: 'from-purple-500 to-pink-400', emoji: 'Bloom' },
  4: { name: 'Thought Leader', color: 'text-amber-400', accent: 'from-amber-500 to-orange-400', emoji: 'Crown' },
};

function SocialGrowthEngine() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(null);

  const loadTasks = useCallback(async () => {
    try {
      const res = await habitAPI.getSocialTasks();
      setData(res.data);
    } catch {
      toast.error('Failed to load social tasks');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadTasks(); }, [loadTasks]);

  const handleToggle = async (taskId, isCompleted) => {
    setCompleting(taskId);
    try {
      if (isCompleted) {
        await habitAPI.uncompleteSocialTask(taskId);
      } else {
        const res = await habitAPI.completeSocialTask(taskId);
        if (res.data.all_done) toast.success('All social tasks done for today!');
        else toast.success('Task completed!');
      }
      await loadTasks();
    } catch {
      toast.error('Failed to update task');
    } finally {
      setCompleting(null);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="w-5 h-5 animate-spin text-blue-400" />
      </div>
    );
  }

  if (!data) return null;

  const { tasks, level, level_name, streak, next_level_at } = data;
  const levelConfig = LEVEL_CONFIGS[level] || LEVEL_CONFIGS[1];
  const completedCount = tasks.filter(t => t.completed).length;
  const progress = tasks.length ? (completedCount / tasks.length) * 100 : 0;

  // Progress to next level
  let levelProgress = 0;
  if (next_level_at) {
    const prevThreshold = level === 1 ? 0 : level === 2 ? 8 : level === 3 ? 22 : 46;
    levelProgress = Math.min(100, ((streak - prevThreshold) / (next_level_at - prevThreshold)) * 100);
  } else {
    levelProgress = 100;
  }

  return (
    <div className="space-y-4" data-testid="social-growth-engine">
      {/* Level & Progress Header */}
      <div className="p-4 rounded-xl bg-gradient-to-br from-zinc-900 to-zinc-900/50 border border-zinc-800">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${levelConfig.accent} flex items-center justify-center`}>
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Social Media Growth</h3>
              <p className={`text-xs ${levelConfig.color}`}>Level {level}: {level_name}</p>
            </div>
          </div>
          {next_level_at && (
            <div className="text-right">
              <p className="text-[10px] text-zinc-500">Next level at {next_level_at} day streak</p>
              <div className="w-24 h-1.5 bg-zinc-800 rounded-full mt-1 overflow-hidden">
                <div
                  className={`h-full rounded-full bg-gradient-to-r ${levelConfig.accent} transition-all duration-500`}
                  style={{ width: `${levelProgress}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Today's progress */}
        <div className="flex items-center gap-3">
          <div className="flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-emerald-500 to-cyan-400 transition-all duration-500 rounded-full"
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="text-xs text-zinc-500 whitespace-nowrap">{completedCount}/{tasks.length} today</span>
        </div>
      </div>

      {/* Task Cards */}
      <div className="space-y-2.5">
        {tasks.map((task) => {
          const PlatformIcon = PLATFORM_ICONS[task.platform] || Globe;
          const platformColor = PLATFORM_COLORS[task.platform] || PLATFORM_COLORS.Any;
          const done = task.completed;

          return (
            <div
              key={task.id}
              className={`p-3.5 rounded-lg border transition-all duration-300 ${
                done
                  ? 'bg-emerald-500/5 border-emerald-500/20'
                  : 'bg-zinc-900/40 border-zinc-800 hover:border-zinc-700'
              }`}
              data-testid={`social-task-${task.id}`}
            >
              <div className="flex items-start gap-3">
                <button
                  onClick={() => handleToggle(task.id, done)}
                  disabled={completing === task.id}
                  className="mt-0.5 shrink-0"
                  data-testid={`social-toggle-${task.id}`}
                >
                  {completing === task.id ? (
                    <Loader2 className="w-5 h-5 animate-spin text-blue-400" />
                  ) : done ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  ) : (
                    <Circle className="w-5 h-5 text-zinc-600 hover:text-zinc-400 transition-colors" />
                  )}
                </button>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <p className={`text-sm font-medium ${done ? 'text-emerald-300 line-through' : 'text-white'}`}>
                      {task.title}
                    </p>
                  </div>
                  <p className="text-xs text-zinc-400 leading-relaxed">{task.description}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className={`text-[10px] px-2 py-0.5 rounded-full border flex items-center gap-1 ${platformColor}`}>
                      <PlatformIcon className="w-2.5 h-2.5" /> {task.platform}
                    </span>
                    <span className="text-[10px] text-zinc-600">{task.time_estimate}</span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Level roadmap */}
      <div className="p-3 rounded-lg bg-zinc-900/40 border border-zinc-800">
        <p className="text-[11px] text-zinc-500 font-medium mb-2 uppercase tracking-wider">Growth Roadmap</p>
        <div className="flex items-center gap-1">
          {[1, 2, 3, 4].map((l) => {
            const cfg = LEVEL_CONFIGS[l];
            const isActive = l === level;
            const isDone = l < level;
            return (
              <React.Fragment key={l}>
                <div className={`flex items-center gap-1.5 px-2 py-1 rounded text-[10px] ${
                  isActive ? `${cfg.color} bg-white/5 font-medium` : isDone ? 'text-emerald-500' : 'text-zinc-600'
                }`}>
                  {isDone ? <CheckCircle2 className="w-3 h-3" /> : isActive ? <Zap className="w-3 h-3" /> : <Circle className="w-3 h-3" />}
                  {cfg.emoji}
                </div>
                {l < 4 && <ArrowRight className="w-3 h-3 text-zinc-700 flex-shrink-0" />}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
}


const HabitTrackerPage = () => {
  const { user } = useAuth();
  const [habits, setHabits] = useState([]);
  const [completions, setCompletions] = useState([]);
  const [gateUnlocked, setGateUnlocked] = useState(true);
  const [gateDeadline, setGateDeadline] = useState(null);
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
      setGateDeadline(res.data.gate_deadline || null);
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
            <div className="text-right">
              <span className="flex items-center gap-1.5 text-sm font-medium text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-full" data-testid="gate-status-unlocked">
                <Unlock className="w-4 h-4" /> Signal Unlocked
              </span>
              {gateDeadline && (
                <p className="text-[10px] text-zinc-500 mt-1 pr-1">
                  Valid until {new Date(gateDeadline).toLocaleDateString()}
                </p>
              )}
            </div>
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

      {/* Social Media Growth Engine */}
      <SocialGrowthEngine />

      {/* Admin-set Habits (if any) */}
      {habits.length > 0 && (
        <>
          <div className="border-t border-zinc-800 pt-4">
            <h2 className="text-base font-semibold text-white mb-1">Platform Tasks</h2>
            <p className="text-xs text-zinc-500 mb-3">{completedCount} of {habits.length} completed</p>
            <div className="h-2 bg-zinc-800 rounded-full overflow-hidden mb-4">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-emerald-500 transition-all duration-500"
                style={{ width: `${habits.length ? (completedCount / habits.length) * 100 : 0}%` }}
              />
            </div>
          </div>

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
                            {(habit.validity_days || 1) > 1 && <span className="text-zinc-500 ml-1">for {habit.validity_days} days</span>}
                          </p>
                        )}
                        {habit.is_gate && done && (habit.validity_days || 1) > 1 && (
                          <p className="text-xs text-emerald-500/70 mt-2">Signal unlocked for {habit.validity_days} days</p>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
};

export default HabitTrackerPage;
