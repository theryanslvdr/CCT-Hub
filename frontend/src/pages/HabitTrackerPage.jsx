import React, { useState, useEffect, useCallback } from 'react';
import { habitAPI, quizAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CheckCircle2, Circle, Lock, Unlock, Send, ExternalLink, ClipboardCopy, Flame, Trophy, Calendar, Sparkles, Loader2, ArrowRight, Zap, HelpCircle, Check, X, BookOpen } from 'lucide-react';
import { toast } from 'sonner';

const LEVEL_CONFIGS = {
  1: { name: 'Getting Started', color: 'text-zinc-400', accent: 'from-zinc-500 to-zinc-400', emoji: 'Seed' },
  2: { name: 'Active Engager', color: 'text-orange-400', accent: 'from-orange-500 to-amber-400', emoji: 'Sprout' },
  3: { name: 'Content Creator', color: 'text-purple-400', accent: 'from-purple-500 to-pink-400', emoji: 'Bloom' },
  4: { name: 'Thought Leader', color: 'text-amber-400', accent: 'from-amber-500 to-orange-400', emoji: 'Crown' },
  5: { name: 'Brand Ambassador', color: 'text-rose-400', accent: 'from-rose-500 to-red-400', emoji: 'Star' },
  6: { name: 'Growth Hacker', color: 'text-emerald-400', accent: 'from-emerald-500 to-teal-400', emoji: 'Rocket' },
  7: { name: 'Community Leader', color: 'text-yellow-400', accent: 'from-yellow-500 to-amber-300', emoji: 'Diamond' },
};

const TOPIC_COLORS = {
  Rewards: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  Hub: 'text-orange-400 bg-orange-500/10 border-orange-500/15',
  Website: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  Merin: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
  MOIL10: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
};

function SocialGrowthEngine() {
  const { isAdmin } = useAuth();
  const [quizData, setQuizData] = useState(null);
  const [streakData, setStreakData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [answering, setAnswering] = useState(null);
  const [selectedAnswer, setSelectedAnswer] = useState({});

  const loadData = useCallback(async () => {
    try {
      const [quizRes, streakRes] = await Promise.all([
        quizAPI.getToday(),
        habitAPI.getSocialTasks(),
      ]);
      setQuizData(quizRes.data);
      setStreakData(streakRes.data);
    } catch {
      toast.error('Failed to load growth tasks');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleAnswer = async (quizId) => {
    const answer = selectedAnswer[quizId];
    if (!answer) {
      toast.error('Please select an answer');
      return;
    }
    setAnswering(quizId);
    try {
      const res = await quizAPI.answer(quizId, answer);
      if (res.data.is_correct) {
        const bonusMsg = res.data.correct_bonus ? ` (+${res.data.correct_bonus} bonus pts)` : '';
        toast.success(`Correct!${bonusMsg}`);
      } else {
        toast.error('Incorrect — see the explanation below');
      }
      if (res.data.reward) {
        toast.success(`+${res.data.reward.points} streak reward points! (Day ${res.data.reward.streak} streak)`);
      }
      await loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to submit answer');
    } finally {
      setAnswering(null);
    }
  };

  if (loading) {
    return <div className="flex justify-center py-8"><Loader2 className="w-5 h-5 animate-spin text-orange-400" /></div>;
  }

  const level = streakData?.level || 1;
  const levelName = streakData?.level_name || 'Getting Started';
  const streak = streakData?.streak || 0;
  const nextLevelAt = streakData?.next_level_at;
  const levelConfig = LEVEL_CONFIGS[level] || LEVEL_CONFIGS[1];

  const quizzes = quizData?.quizzes || [];
  const answeredCount = quizzes.filter(q => q.answered).length;
  const correctCount = quizzes.filter(q => q.is_correct).length;
  const progress = quizzes.length ? (answeredCount / quizzes.length) * 100 : 0;

  let levelProgress = 0;
  if (nextLevelAt) {
    const prevThresholds = { 1: 0, 2: 8, 3: 22, 4: 46, 5: 60, 6: 80, 7: 100 };
    const prev = prevThresholds[level] || 0;
    levelProgress = Math.min(100, ((streak - prev) / (nextLevelAt - prev)) * 100);
  } else {
    levelProgress = 100;
  }

  return (
    <div className="space-y-4" data-testid="social-growth-engine">
      {/* Level & Progress Header */}
      <div className="p-4 rounded-xl bg-gradient-to-br from-zinc-900 to-zinc-900/50 border border-white/[0.06]">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${levelConfig.accent} flex items-center justify-center`}>
              <BookOpen className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Community Knowledge</h3>
              <p className={`text-xs ${levelConfig.color}`}>Level {level}: {levelName}</p>
            </div>
          </div>
          {nextLevelAt && (
            <div className="text-right">
              <p className="text-[10px] text-zinc-500">Next level at {nextLevelAt} day streak</p>
              <div className="w-24 h-1.5 bg-[#1a1a1a] rounded-full mt-1 overflow-hidden">
                <div className={`h-full rounded-full bg-gradient-to-r ${levelConfig.accent} transition-all duration-500`} style={{ width: `${levelProgress}%` }} />
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          <div className="flex-1 h-2 bg-[#1a1a1a] rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-emerald-500 to-amber-400 transition-all duration-500 rounded-full" style={{ width: `${progress}%` }} />
          </div>
          <span className="text-xs text-zinc-500 whitespace-nowrap">
            {answeredCount}/{quizzes.length} answered {correctCount > 0 && `(${correctCount} correct)`}
          </span>
        </div>
      </div>

      {/* Quiz Cards */}
      {quizzes.length === 0 ? (
        <div className="p-6 rounded-lg bg-[#0d0d0d]/40 border border-white/[0.06] text-center">
          <HelpCircle className="w-10 h-10 mx-auto mb-3 text-zinc-600" />
          <p className="text-sm text-zinc-400">No quizzes published for today yet.</p>
          <p className="text-xs text-zinc-600 mt-1">Check back later — your admin is preparing today's knowledge challenges.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {quizzes.map((quiz, idx) => (
            <QuizCard
              key={quiz.id}
              quiz={quiz}
              index={idx}
              selectedAnswer={selectedAnswer[quiz.id]}
              onSelectAnswer={(ans) => setSelectedAnswer(prev => ({ ...prev, [quiz.id]: ans }))}
              onSubmit={() => handleAnswer(quiz.id)}
              submitting={answering === quiz.id}
            />
          ))}
        </div>
      )}

      {/* Level roadmap */}
      <div className="p-3 rounded-lg bg-[#0d0d0d]/40 border border-white/[0.06]">
        <p className="text-[11px] text-zinc-500 font-medium mb-2 uppercase tracking-wider">Growth Roadmap</p>
        <div className="flex items-center gap-1 flex-wrap">
          {[1, 2, 3, 4, 5, 6, 7].map((l) => {
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
                {l < 7 && <ArrowRight className="w-3 h-3 text-zinc-700 flex-shrink-0" />}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function QuizCard({ quiz, index, selectedAnswer, onSelectAnswer, onSubmit, submitting }) {
  const topicColor = TOPIC_COLORS[quiz.platform_topic] || TOPIC_COLORS.Hub;

  return (
    <div
      className={`p-4 rounded-lg border transition-all ${
        quiz.answered
          ? quiz.is_correct ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-red-500/5 border-red-500/20'
          : 'bg-[#0d0d0d]/40 border-white/[0.06]'
      }`}
      data-testid={`quiz-card-${quiz.id}`}
    >
      {/* Question header */}
      <div className="flex items-start gap-3 mb-3">
        <div className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold shrink-0 ${
          quiz.answered ? (quiz.is_correct ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400') : 'bg-orange-500/10 text-orange-400'
        }`}>
          {quiz.answered ? (quiz.is_correct ? <Check className="w-4 h-4" /> : <X className="w-4 h-4" />) : index + 1}
        </div>
        <div className="flex-1">
          <p className="text-sm font-medium text-white leading-snug">{quiz.question}</p>
          <div className="flex items-center gap-2 mt-1.5">
            <span className={`text-[10px] px-2 py-0.5 rounded-full border ${topicColor}`}>{quiz.platform_topic}</span>
          </div>
        </div>
      </div>

      {/* Answer options */}
      <div className="space-y-1.5 ml-10">
        {quiz.options.map((option, oi) => {
          const isSelected = selectedAnswer === option;
          const isAnswered = quiz.answered;
          const isCorrectAnswer = isAnswered && option === quiz.correct_answer;
          const isWrongPick = isAnswered && option === quiz.user_answer && !quiz.is_correct;

          let optClasses = 'bg-white/[0.04] border-white/[0.08] text-zinc-300 hover:border-zinc-500 cursor-pointer';
          if (isAnswered) {
            if (isCorrectAnswer) optClasses = 'bg-emerald-500/10 border-emerald-500/40 text-emerald-300';
            else if (isWrongPick) optClasses = 'bg-red-500/10 border-red-500/40 text-red-300';
            else optClasses = 'bg-white/[0.03] border-white/[0.06] text-zinc-500';
          } else if (isSelected) {
            optClasses = 'bg-orange-500/10 border-orange-500/40 text-orange-300 ring-1 ring-orange-500/30';
          }

          return (
            <button
              key={oi}
              onClick={() => !isAnswered && onSelectAnswer(option)}
              disabled={isAnswered}
              className={`w-full text-left px-3 py-2 rounded-md border text-xs transition-all ${optClasses}`}
              data-testid={`quiz-option-${quiz.id}-${oi}`}
            >
              <span className="font-mono mr-2 opacity-50">{String.fromCharCode(65 + oi)}.</span>
              {option}
              {isCorrectAnswer && <Check className="w-3.5 h-3.5 inline ml-2 text-emerald-400" />}
              {isWrongPick && <X className="w-3.5 h-3.5 inline ml-2 text-red-400" />}
            </button>
          );
        })}
      </div>

      {/* Submit or Explanation */}
      <div className="ml-10 mt-3">
        {quiz.answered ? (
          <div className={`p-2.5 rounded-md text-xs leading-relaxed ${
            quiz.is_correct ? 'bg-emerald-500/10 text-emerald-300' : 'bg-amber-500/10 text-amber-300'
          }`}>
            <span className="font-semibold">{quiz.is_correct ? 'Correct!' : 'Explanation:'}</span>{' '}
            {quiz.explanation}
          </div>
        ) : (
          <Button
            size="sm"
            onClick={onSubmit}
            disabled={!selectedAnswer || submitting}
            className="h-7 text-xs btn-primary gap-1"
            data-testid={`quiz-submit-${quiz.id}`}
          >
            {submitting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Send className="w-3 h-3" />}
            Submit Answer
          </Button>
        )}
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
        if (res.data.reward) {
          toast.success(`+${res.data.reward.points} reward points! (Day ${res.data.reward.streak} streak)`);
        } else if (!res.data.already) {
          toast.success('Habit completed!');
        }
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
        <div className="w-6 h-6 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
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
        <div className="p-3 rounded-xl bg-[#0d0d0d]/60 border border-white/[0.06] text-center">
          <div className="flex items-center justify-center gap-1.5 mb-1">
            <Flame className={`w-5 h-5 ${streak.current_streak > 0 ? 'text-orange-400' : 'text-zinc-600'}`} />
          </div>
          <p className="text-2xl font-bold text-white">{streak.current_streak}</p>
          <p className="text-[11px] text-zinc-500">Current Streak</p>
        </div>
        <div className="p-3 rounded-xl bg-[#0d0d0d]/60 border border-white/[0.06] text-center">
          <div className="flex items-center justify-center gap-1.5 mb-1">
            <Trophy className={`w-5 h-5 ${streak.longest_streak > 0 ? 'text-amber-400' : 'text-zinc-600'}`} />
          </div>
          <p className="text-2xl font-bold text-white">{streak.longest_streak}</p>
          <p className="text-[11px] text-zinc-500">Best Streak</p>
        </div>
        <div className="p-3 rounded-xl bg-[#0d0d0d]/60 border border-white/[0.06] text-center">
          <div className="flex items-center justify-center gap-1.5 mb-1">
            <Calendar className="w-5 h-5 text-orange-400" />
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
          <div className="border-t border-white/[0.06] pt-4">
            <h2 className="text-base font-semibold text-white mb-1">Platform Tasks</h2>
            <p className="text-xs text-zinc-500 mb-3">{completedCount} of {habits.length} completed</p>
            <div className="h-2 bg-[#1a1a1a] rounded-full overflow-hidden mb-4">
              <div
                className="h-full bg-gradient-to-r from-orange-500 to-emerald-500 transition-all duration-500"
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
                  className={`glass-card transition-all duration-300 ${done ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-white/[0.06]'}`}
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
                          <div className="w-6 h-6 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
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
                          <div className="mt-3 p-3 bg-[#0d0d0d]/60 rounded-lg border border-white/[0.06]">
                            <p className="text-xs text-zinc-500 mb-1.5">Pre-written message:</p>
                            <p className="text-sm text-zinc-300 whitespace-pre-wrap">{habit.action_data}</p>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="mt-2 text-orange-400 hover:text-orange-300 gap-1.5"
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
                            className="mt-2 inline-flex items-center gap-1 text-sm text-orange-400 hover:text-orange-300"
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
