import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../lib/api';
import { CheckCircle, XCircle, Play, Loader2, Shield } from 'lucide-react';

export default function SystemCheckPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const runCheck = async () => {
    setLoading(true);
    setResult(null);
    try {
      const res = await api.post('/rewards/system-check');
      setResult(res.data);
    } catch (err) {
      setResult({
        overall: 'fail',
        message: err?.response?.data?.detail || 'Failed to run system check',
        results: [],
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="system-check-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Shield className="w-6 h-6 text-orange-400" />
            Rewards System Check
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            One-click health check for the rewards engine
          </p>
        </div>
        <Button
          onClick={runCheck}
          disabled={loading}
          className="bg-orange-600 hover:bg-orange-700"
          data-testid="run-system-check-btn"
        >
          {loading ? (
            <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Running...</>
          ) : (
            <><Play className="w-4 h-4 mr-2" /> Run System Check</>
          )}
        </Button>
      </div>

      {result && (
        <Card className={`border ${result.overall === 'pass' ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-red-500/30 bg-red-500/5'}`}>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              {result.overall === 'pass' ? (
                <CheckCircle className="w-5 h-5 text-emerald-400" />
              ) : (
                <XCircle className="w-5 h-5 text-red-400" />
              )}
              <span className={result.overall === 'pass' ? 'text-emerald-400' : 'text-red-400'}>
                {result.message}
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2" data-testid="system-check-results">
              {result.results?.map((r, i) => (
                <div
                  key={i}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg ${
                    r.status === 'pass'
                      ? 'bg-white/[0.04] text-zinc-200'
                      : 'bg-red-900/20 text-red-300'
                  }`}
                  data-testid={`check-step-${i}`}
                >
                  {r.status === 'pass' ? (
                    <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-400 shrink-0" />
                  )}
                  <span className="font-medium">{r.step}</span>
                  {r.points !== undefined && (
                    <span className="text-xs text-zinc-400 ml-auto">{r.points} pts</span>
                  )}
                  {r.error && (
                    <span className="text-xs text-red-400 ml-auto">{r.error}</span>
                  )}
                </div>
              ))}
            </div>
            {result.timestamp && (
              <p className="text-xs text-zinc-500 mt-4">
                Ran at {new Date(result.timestamp).toLocaleString()}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {!result && !loading && (
        <Card className="border border-white/[0.08]/50">
          <CardContent className="py-12 text-center text-zinc-500">
            <Shield className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>Click "Run System Check" to validate the rewards engine.</p>
            <p className="text-xs mt-2">Tests: sign-up, deposit, trade, referral, summary, leaderboard, redeem, credit</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
