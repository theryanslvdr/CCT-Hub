import React, { useState } from 'react';
import { aiAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Loader2, Sparkles, TrendingUp, Brain, BookOpen, Target, AlertTriangle, Zap } from 'lucide-react';

export function AITradeCoach({ tradeId }) {
  const [coaching, setCoaching] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadCoaching = async () => {
    setLoading(true);
    try {
      const res = await aiAPI.getTradeCoach(tradeId);
      setCoaching(res.data.coaching);
    } catch {
      setCoaching('Unable to load coaching feedback.');
    } finally {
      setLoading(false);
    }
  };

  if (coaching) {
    return (
      <div className="p-3 rounded-lg bg-blue-500/5 border border-blue-500/20 text-xs text-zinc-300 space-y-1.5" data-testid="ai-trade-coach">
        <div className="flex items-center gap-1.5 text-blue-400 font-medium text-[11px] uppercase tracking-wider">
          <Brain className="w-3.5 h-3.5" /> AI Coach
        </div>
        <div className="whitespace-pre-wrap leading-relaxed">{coaching}</div>
      </div>
    );
  }

  return (
    <Button
      size="sm"
      variant="ghost"
      onClick={loadCoaching}
      disabled={loading}
      className="text-[11px] text-blue-400 hover:text-blue-300 gap-1 h-6 px-2"
      data-testid={`ai-coach-btn-${tradeId}`}
    >
      {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Brain className="w-3 h-3" />}
      AI Coach
    </Button>
  );
}

export function AIFinancialSummary() {
  const [summary, setSummary] = useState(null);
  const [stats, setStats] = useState(null);
  const [period, setPeriod] = useState('weekly');
  const [loading, setLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);

  const loadSummary = async (p) => {
    setLoading(true);
    setPeriod(p);
    try {
      const res = await aiAPI.getFinancialSummary(p);
      setSummary(res.data.summary);
      setStats(res.data.stats);
      setLoaded(true);
    } catch {
      setSummary('Unable to generate summary.');
    } finally {
      setLoading(false);
    }
  };

  if (!loaded) {
    return (
      <div className="p-4 rounded-lg bg-gradient-to-br from-zinc-900 to-zinc-900/50 border border-zinc-800 hover:border-blue-500/20 transition-colors" data-testid="ai-financial-summary">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-blue-400" /> AI Financial Summary
          </h3>
        </div>
        <p className="text-xs text-zinc-500 mb-3">Get an AI-powered analysis of your trading performance.</p>
        <div className="flex gap-2">
          <Button size="sm" onClick={() => loadSummary('weekly')} disabled={loading} className="text-xs gap-1 bg-blue-600 hover:bg-blue-700 h-7" data-testid="ai-summary-weekly-btn">
            {loading && period === 'weekly' ? <Loader2 className="w-3 h-3 animate-spin" /> : <Sparkles className="w-3 h-3" />} Weekly
          </Button>
          <Button size="sm" variant="outline" onClick={() => loadSummary('monthly')} disabled={loading} className="text-xs gap-1 btn-secondary h-7" data-testid="ai-summary-monthly-btn">
            {loading && period === 'monthly' ? <Loader2 className="w-3 h-3 animate-spin" /> : null} Monthly
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 rounded-lg bg-gradient-to-br from-zinc-900 to-zinc-900/50 border border-blue-500/20" data-testid="ai-financial-summary">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-blue-400" /> AI Financial Summary
          <span className="text-[9px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">{period}</span>
        </h3>
        <div className="flex gap-1">
          <Button size="sm" variant="ghost" onClick={() => loadSummary('weekly')} disabled={loading} className={`text-[10px] h-6 px-2 ${period === 'weekly' ? 'text-blue-400' : 'text-zinc-500'}`}>Week</Button>
          <Button size="sm" variant="ghost" onClick={() => loadSummary('monthly')} disabled={loading} className={`text-[10px] h-6 px-2 ${period === 'monthly' ? 'text-blue-400' : 'text-zinc-500'}`}>Month</Button>
        </div>
      </div>
      {loading ? (
        <div className="flex justify-center py-4"><Loader2 className="w-4 h-4 animate-spin text-blue-400" /></div>
      ) : (
        <div className="text-xs text-zinc-300 whitespace-pre-wrap leading-relaxed">{summary}</div>
      )}
    </div>
  );
}

export function AIBalanceForecast() {
  const [forecast, setForecast] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);

  const loadForecast = async () => {
    setLoading(true);
    try {
      const res = await aiAPI.getBalanceForecast();
      setForecast(res.data.forecast);
      setData(res.data);
      setLoaded(true);
    } catch {
      setForecast('Unable to generate forecast.');
    } finally {
      setLoading(false);
    }
  };

  if (!loaded) {
    return (
      <div className="p-4 rounded-lg bg-gradient-to-br from-zinc-900 to-zinc-900/50 border border-zinc-800 hover:border-emerald-500/20 transition-colors" data-testid="ai-balance-forecast">
        <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2 mb-2">
          <TrendingUp className="w-4 h-4 text-emerald-400" /> AI Balance Forecast
        </h3>
        <p className="text-xs text-zinc-500 mb-3">See where your balance is headed based on your trading history.</p>
        <Button size="sm" onClick={loadForecast} disabled={loading} className="text-xs gap-1 bg-emerald-600 hover:bg-emerald-700 h-7" data-testid="ai-forecast-btn">
          {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <TrendingUp className="w-3 h-3" />} Generate Forecast
        </Button>
      </div>
    );
  }

  return (
    <div className="p-4 rounded-lg bg-gradient-to-br from-zinc-900 to-zinc-900/50 border border-emerald-500/20" data-testid="ai-balance-forecast">
      <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2 mb-2">
        <TrendingUp className="w-4 h-4 text-emerald-400" /> AI Balance Forecast
        {data?.ai_powered && <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">AI</span>}
      </h3>
      {data?.current_balance && (
        <p className="text-[11px] text-zinc-500 mb-2">Current balance: <span className="text-emerald-400 font-mono">${data.current_balance.toLocaleString()}</span></p>
      )}
      {loading ? (
        <div className="flex justify-center py-4"><Loader2 className="w-4 h-4 animate-spin text-emerald-400" /></div>
      ) : (
        <div className="text-xs text-zinc-300 whitespace-pre-wrap leading-relaxed">{forecast}</div>
      )}
      <Button size="sm" variant="ghost" onClick={loadForecast} disabled={loading} className="text-[10px] text-zinc-500 mt-2 h-6 px-2" data-testid="ai-forecast-refresh">
        Refresh
      </Button>
    </div>
  );
}

export function AIForumSummary({ postId, commentCount }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);

  if (commentCount < 3) return null;

  const loadSummary = async () => {
    setLoading(true);
    try {
      const res = await aiAPI.getForumSummary(postId);
      setSummary(res.data.summary);
      setLoaded(true);
    } catch {
      setSummary('Unable to generate summary.');
    } finally {
      setLoading(false);
    }
  };

  if (!loaded) {
    return (
      <Button
        size="sm"
        variant="outline"
        onClick={loadSummary}
        disabled={loading}
        className="text-[11px] gap-1.5 btn-secondary text-blue-400 hover:text-blue-300 border-blue-500/20 h-7"
        data-testid="ai-summary-btn"
      >
        {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Sparkles className="w-3 h-3" />}
        AI Summary
      </Button>
    );
  }

  if (!summary) return null;

  return (
    <div className="p-3 rounded-lg bg-blue-500/5 border border-blue-500/20 text-xs" data-testid="ai-forum-summary">
      <div className="flex items-center gap-1.5 text-blue-400 font-medium text-[11px] uppercase tracking-wider mb-2">
        <Sparkles className="w-3.5 h-3.5" /> AI Summary
      </div>
      <div className="text-zinc-300 whitespace-pre-wrap leading-relaxed">{summary}</div>
    </div>
  );
}


// ─── Phase 2 Components ───

export function AISignalInsights({ signalId }) {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await aiAPI.getSignalInsights(signalId);
      setInsights(res.data.insights);
    } catch {
      setInsights('Unable to load signal insights.');
    } finally {
      setLoading(false);
    }
  };

  if (insights) {
    return (
      <div className="p-3 rounded-lg bg-purple-500/5 border border-purple-500/20 text-xs space-y-1.5" data-testid="ai-signal-insights">
        <div className="flex items-center gap-1.5 text-purple-400 font-medium text-[11px] uppercase tracking-wider">
          <Zap className="w-3.5 h-3.5" /> AI Signal Insights
        </div>
        <div className="text-zinc-300 whitespace-pre-wrap leading-relaxed">{insights}</div>
      </div>
    );
  }

  return (
    <Button
      size="sm"
      variant="outline"
      onClick={load}
      disabled={loading}
      className="text-[11px] gap-1.5 btn-secondary text-purple-400 hover:text-purple-300 border-purple-500/20 h-7"
      data-testid={`ai-insights-btn-${signalId}`}
    >
      {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Zap className="w-3 h-3" />}
      AI Insights
    </Button>
  );
}

export function AITradeJournal() {
  const [journal, setJournal] = useState(null);
  const [stats, setStats] = useState(null);
  const [period, setPeriod] = useState('daily');
  const [loading, setLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);

  const load = async (p) => {
    setLoading(true);
    setPeriod(p);
    try {
      const res = await aiAPI.getTradeJournal(p);
      setJournal(res.data.journal);
      setStats(res.data.stats);
      setLoaded(true);
    } catch {
      setJournal('Unable to generate journal.');
    } finally {
      setLoading(false);
    }
  };

  if (!loaded) {
    return (
      <div className="p-4 rounded-lg bg-gradient-to-br from-zinc-900 to-zinc-900/50 border border-zinc-800 hover:border-amber-500/20 transition-colors" data-testid="ai-trade-journal">
        <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2 mb-2">
          <BookOpen className="w-4 h-4 text-amber-400" /> AI Trade Journal
        </h3>
        <p className="text-xs text-zinc-500 mb-3">AI-generated reflections on your trading patterns and discipline.</p>
        <div className="flex gap-2">
          <Button size="sm" onClick={() => load('daily')} disabled={loading} className="text-xs gap-1 bg-amber-600 hover:bg-amber-700 h-7" data-testid="ai-journal-daily-btn">
            {loading && period === 'daily' ? <Loader2 className="w-3 h-3 animate-spin" /> : <BookOpen className="w-3 h-3" />} Today
          </Button>
          <Button size="sm" variant="outline" onClick={() => load('weekly')} disabled={loading} className="text-xs gap-1 btn-secondary h-7" data-testid="ai-journal-weekly-btn">
            This Week
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 rounded-lg bg-gradient-to-br from-zinc-900 to-zinc-900/50 border border-amber-500/20" data-testid="ai-trade-journal">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-amber-400" /> AI Trade Journal
          <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">{period}</span>
        </h3>
        <div className="flex gap-1">
          <Button size="sm" variant="ghost" onClick={() => load('daily')} disabled={loading} className={`text-[10px] h-6 px-2 ${period === 'daily' ? 'text-amber-400' : 'text-zinc-500'}`}>Day</Button>
          <Button size="sm" variant="ghost" onClick={() => load('weekly')} disabled={loading} className={`text-[10px] h-6 px-2 ${period === 'weekly' ? 'text-amber-400' : 'text-zinc-500'}`}>Week</Button>
        </div>
      </div>
      {stats && (
        <div className="flex gap-3 mb-2 text-[10px] text-zinc-500">
          <span>Profit: <span className="text-amber-400 font-mono">${stats.total_profit}</span></span>
          <span>Streak: <span className="text-zinc-300">{stats.streak}d</span></span>
          <span>Exceeded: <span className="text-emerald-400">{stats.exceeded}</span></span>
        </div>
      )}
      {loading ? (
        <div className="flex justify-center py-4"><Loader2 className="w-4 h-4 animate-spin text-amber-400" /></div>
      ) : (
        <div className="text-xs text-zinc-300 whitespace-pre-wrap leading-relaxed">{journal}</div>
      )}
    </div>
  );
}

export function AIGoalAdvisor({ goalId, goalName }) {
  const [advice, setAdvice] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await aiAPI.getGoalAdvisor(goalId);
      setAdvice(res.data.advice);
      setData(res.data);
    } catch {
      setAdvice('Unable to generate goal advice.');
    } finally {
      setLoading(false);
    }
  };

  if (advice) {
    return (
      <div className="p-3 rounded-lg bg-cyan-500/5 border border-cyan-500/20 text-xs space-y-1.5" data-testid="ai-goal-advisor">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-cyan-400 font-medium text-[11px] uppercase tracking-wider">
            <Target className="w-3.5 h-3.5" /> AI Goal Advisor
          </div>
          {data?.days_to_goal && (
            <span className="text-[10px] text-zinc-500">~{data.days_to_goal} days at current pace</span>
          )}
        </div>
        <div className="text-zinc-300 whitespace-pre-wrap leading-relaxed">{advice}</div>
      </div>
    );
  }

  return (
    <Button
      size="sm"
      variant="outline"
      onClick={load}
      disabled={loading}
      className="text-[11px] gap-1.5 btn-secondary text-cyan-400 hover:text-cyan-300 border-cyan-500/20 h-7"
      data-testid={`ai-goal-btn-${goalId}`}
    >
      {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Target className="w-3 h-3" />}
      AI Advisor
    </Button>
  );
}

export function AIAnomalyAlert() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await aiAPI.getAnomalyCheck();
      setData(res.data);
      setLoaded(true);
    } catch {
      setData({ status: 'error', message: 'Unable to check for anomalies.' });
    } finally {
      setLoading(false);
    }
  };

  if (!loaded) {
    return (
      <div className="p-4 rounded-lg bg-gradient-to-br from-zinc-900 to-zinc-900/50 border border-zinc-800 hover:border-red-500/20 transition-colors" data-testid="ai-anomaly-alert">
        <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2 mb-2">
          <AlertTriangle className="w-4 h-4 text-red-400" /> AI Anomaly Detection
        </h3>
        <p className="text-xs text-zinc-500 mb-3">Check for unusual patterns in your trading performance.</p>
        <Button size="sm" onClick={load} disabled={loading} className="text-xs gap-1 bg-red-600/80 hover:bg-red-600 h-7" data-testid="ai-anomaly-btn">
          {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <AlertTriangle className="w-3 h-3" />} Check Now
        </Button>
      </div>
    );
  }

  const isHealthy = data?.status === 'healthy';

  return (
    <div className={`p-4 rounded-lg bg-gradient-to-br from-zinc-900 to-zinc-900/50 border ${isHealthy ? 'border-emerald-500/20' : 'border-red-500/20'}`} data-testid="ai-anomaly-alert">
      <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2 mb-2">
        <AlertTriangle className={`w-4 h-4 ${isHealthy ? 'text-emerald-400' : 'text-red-400'}`} />
        AI Anomaly Detection
        <span className={`text-[9px] px-1.5 py-0.5 rounded border ${isHealthy ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}`}>
          {isHealthy ? 'All Clear' : 'Attention'}
        </span>
      </h3>
      {isHealthy ? (
        <p className="text-xs text-emerald-400">{data.message}</p>
      ) : (
        <>
          {data.flags && (
            <div className="mb-2 space-y-1">
              {data.flags.map((f, i) => (
                <div key={i} className="text-[11px] text-red-400/80 flex items-start gap-1.5">
                  <span className="text-red-500 mt-0.5">*</span> {f}
                </div>
              ))}
            </div>
          )}
          <div className="text-xs text-zinc-300 whitespace-pre-wrap leading-relaxed">{data.anomalies}</div>
        </>
      )}
      <Button size="sm" variant="ghost" onClick={load} disabled={loading} className="text-[10px] text-zinc-500 mt-2 h-6 px-2" data-testid="ai-anomaly-refresh">
        Re-check
      </Button>
    </div>
  );
}
