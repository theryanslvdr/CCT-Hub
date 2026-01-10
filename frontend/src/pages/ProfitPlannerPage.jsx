import React, { useState, useEffect } from 'react';
import { goalsAPI } from '@/lib/api';
import { formatCurrency, formatNumber } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { toast } from 'sonner';
import { Plus, Target, Sparkles, Gift, Home, Car, Plane, GraduationCap, DollarSign, TrendingUp, Calendar } from 'lucide-react';

const goalIcons = {
  default: Target,
  gift: Gift,
  home: Home,
  car: Car,
  travel: Plane,
  education: GraduationCap,
};

export const ProfitPlannerPage = () => {
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [contributeDialogOpen, setContributeDialogOpen] = useState(false);
  const [selectedGoal, setSelectedGoal] = useState(null);
  const [goalPlan, setGoalPlan] = useState(null);
  const [contributionAmount, setContributionAmount] = useState('');
  const [newGoal, setNewGoal] = useState({
    name: '',
    target_amount: '',
    current_amount: '0',
    target_date: '',
    price_type: 'fixed',
    market_item: '',
    currency: 'USD',
    icon: 'default',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const res = await goalsAPI.getAll();
      setGoals(res.data);
    } catch (error) {
      console.error('Failed to load goals:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGoal = async () => {
    if (!newGoal.name || !newGoal.target_amount) {
      toast.error('Please fill in required fields');
      return;
    }

    try {
      await goalsAPI.create({
        name: newGoal.name,
        target_amount: parseFloat(newGoal.target_amount),
        current_amount: parseFloat(newGoal.current_amount) || 0,
        target_date: newGoal.target_date ? new Date(newGoal.target_date).toISOString() : null,
        price_type: newGoal.price_type,
        market_item: newGoal.market_item,
        currency: newGoal.currency,
      });
      toast.success('Goal created!');
      setDialogOpen(false);
      setNewGoal({ name: '', target_amount: '', current_amount: '0', target_date: '', price_type: 'fixed', market_item: '', currency: 'USD', icon: 'default' });
      loadData();
    } catch (error) {
      toast.error('Failed to create goal');
    }
  };

  const handleContribute = async () => {
    if (!contributionAmount || parseFloat(contributionAmount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    try {
      const res = await goalsAPI.contribute(selectedGoal.id, parseFloat(contributionAmount));
      if (res.data.completed) {
        toast.success('🎉 Congratulations! You reached your goal!');
      } else {
        toast.success('Contribution added!');
      }
      setContributeDialogOpen(false);
      setContributionAmount('');
      setSelectedGoal(null);
      loadData();
    } catch (error) {
      toast.error('Failed to add contribution');
    }
  };

  const loadGoalPlan = async (goal) => {
    try {
      const res = await goalsAPI.getPlan(goal.id);
      setGoalPlan(res.data);
      setSelectedGoal(goal);
    } catch (error) {
      console.error('Failed to load goal plan:', error);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" /></div>;
  }

  const totalTarget = goals.reduce((sum, g) => sum + g.target_amount, 0);
  const totalCurrent = goals.reduce((sum, g) => sum + g.current_amount, 0);
  const completedGoals = goals.filter(g => g.current_amount >= g.target_amount).length;

  return (
    <div className="space-y-6">
      {/* Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="glass-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Total Goals</p>
                <p className="text-3xl font-bold font-mono text-white mt-2">{goals.length}</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center">
                <Target className="w-6 h-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Completed</p>
                <p className="text-3xl font-bold font-mono text-emerald-400 mt-2">{completedGoals}</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Total Target</p>
                <p className="text-3xl font-bold font-mono text-white mt-2">${formatNumber(totalTarget)}</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
                <DollarSign className="w-6 h-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Total Saved</p>
                <p className="text-3xl font-bold font-mono text-cyan-400 mt-2">${formatNumber(totalCurrent)}</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-cyan-600 flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Add Goal Button */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogTrigger asChild>
          <Button className="btn-primary gap-2" data-testid="add-goal-button">
            <Plus className="w-4 h-4" /> Add Goal
          </Button>
        </DialogTrigger>
        <DialogContent className="glass-card border-zinc-800 max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-white">Create New Goal</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <Label className="text-zinc-300">Goal Name</Label>
              <Input
                value={newGoal.name}
                onChange={(e) => setNewGoal({ ...newGoal, name: e.target.value })}
                placeholder="e.g., New MacBook, Emergency Fund, Dream Vacation"
                className="input-dark mt-1"
                data-testid="goal-name-input"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-zinc-300">Target Amount</Label>
                <Input
                  type="number"
                  value={newGoal.target_amount}
                  onChange={(e) => setNewGoal({ ...newGoal, target_amount: e.target.value })}
                  placeholder="0.00"
                  className="input-dark mt-1"
                  data-testid="goal-target-input"
                />
              </div>
              <div>
                <Label className="text-zinc-300">Starting Amount</Label>
                <Input
                  type="number"
                  value={newGoal.current_amount}
                  onChange={(e) => setNewGoal({ ...newGoal, current_amount: e.target.value })}
                  placeholder="0.00"
                  className="input-dark mt-1"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-zinc-300">Target Date (optional)</Label>
                <Input
                  type="date"
                  value={newGoal.target_date}
                  onChange={(e) => setNewGoal({ ...newGoal, target_date: e.target.value })}
                  className="input-dark mt-1"
                />
              </div>
              <div>
                <Label className="text-zinc-300">Currency</Label>
                <Select value={newGoal.currency} onValueChange={(v) => setNewGoal({ ...newGoal, currency: v })}>
                  <SelectTrigger className="input-dark mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="USD">USD</SelectItem>
                    <SelectItem value="PHP">PHP</SelectItem>
                    <SelectItem value="EUR">EUR</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <Button onClick={handleCreateGoal} className="w-full btn-primary" data-testid="confirm-create-goal">
              Create Goal
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Goals Grid */}
      {goals.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {goals.map((goal) => {
            const isCompleted = goal.current_amount >= goal.target_amount;
            const remaining = goal.target_amount - goal.current_amount;
            
            return (
              <Card key={goal.id} className={`glass-card hover:border-blue-500/30 transition-all ${isCompleted ? 'border-emerald-500/30 neon-success' : ''}`}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <p className="font-bold text-white text-lg">{goal.name}</p>
                      {goal.target_date && (
                        <p className="text-xs text-zinc-500 flex items-center gap-1 mt-1">
                          <Calendar className="w-3 h-3" />
                          Target: {new Date(goal.target_date).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                    {isCompleted && (
                      <div className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-medium">
                        Completed!
                      </div>
                    )}
                  </div>

                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-zinc-400">${formatNumber(goal.current_amount)}</span>
                      <span className="text-zinc-400">${formatNumber(goal.target_amount)}</span>
                    </div>
                    <Progress value={goal.progress_percentage} className="h-3" />
                    <p className="text-center text-lg font-bold text-gradient">{formatNumber(goal.progress_percentage, 1)}%</p>
                  </div>

                  {!isCompleted && (
                    <div className="mt-4 p-3 rounded-lg bg-zinc-900/50">
                      <p className="text-xs text-zinc-500">Remaining</p>
                      <p className="text-xl font-mono font-bold text-white">${formatNumber(remaining)}</p>
                    </div>
                  )}

                  <div className="mt-4 flex gap-2">
                    <Button
                      className="flex-1 btn-secondary"
                      onClick={() => loadGoalPlan(goal)}
                      data-testid={`view-plan-${goal.id}`}
                    >
                      View Plan
                    </Button>
                    {!isCompleted && (
                      <Button
                        className="flex-1 btn-primary"
                        onClick={() => { setSelectedGoal(goal); setContributeDialogOpen(true); }}
                        data-testid={`contribute-${goal.id}`}
                      >
                        Contribute
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : (
        <Card className="glass-card">
          <CardContent className="p-12 text-center">
            <Target className="w-16 h-16 text-zinc-700 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-white mb-2">No Goals Yet</h3>
            <p className="text-zinc-500 mb-6">Start planning your financial future by creating your first goal!</p>
            <Button className="btn-primary" onClick={() => setDialogOpen(true)}>
              <Plus className="w-4 h-4 mr-2" /> Create Your First Goal
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Contribute Dialog */}
      <Dialog open={contributeDialogOpen} onOpenChange={setContributeDialogOpen}>
        <DialogContent className="glass-card border-zinc-800">
          <DialogHeader>
            <DialogTitle className="text-white">Contribute to {selectedGoal?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="p-4 rounded-lg bg-zinc-900/50">
              <div className="flex justify-between mb-2">
                <span className="text-zinc-400">Current Progress</span>
                <span className="text-white font-mono">${formatNumber(selectedGoal?.current_amount || 0)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Remaining</span>
                <span className="text-emerald-400 font-mono">${formatNumber((selectedGoal?.target_amount || 0) - (selectedGoal?.current_amount || 0))}</span>
              </div>
            </div>
            <div>
              <Label className="text-zinc-300">Contribution Amount</Label>
              <Input
                type="number"
                value={contributionAmount}
                onChange={(e) => setContributionAmount(e.target.value)}
                placeholder="Enter amount"
                className="input-dark mt-1"
                data-testid="contribution-amount-input"
              />
            </div>
            <Button onClick={handleContribute} className="w-full btn-primary" data-testid="confirm-contribute">
              Add Contribution
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Goal Plan Dialog */}
      <Dialog open={!!goalPlan} onOpenChange={() => setGoalPlan(null)}>
        <DialogContent className="glass-card border-zinc-800 max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-white">Plan for {goalPlan?.goal_name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-lg bg-zinc-900/50">
                <p className="text-xs text-zinc-500">Target</p>
                <p className="text-xl font-mono font-bold text-white">${formatNumber(goalPlan?.target || 0)}</p>
              </div>
              <div className="p-4 rounded-lg bg-zinc-900/50">
                <p className="text-xs text-zinc-500">Current</p>
                <p className="text-xl font-mono font-bold text-cyan-400">${formatNumber(goalPlan?.current || 0)}</p>
              </div>
              <div className="p-4 rounded-lg bg-zinc-900/50">
                <p className="text-xs text-zinc-500">Remaining</p>
                <p className="text-xl font-mono font-bold text-amber-400">${formatNumber(goalPlan?.remaining || 0)}</p>
              </div>
              <div className="p-4 rounded-lg bg-zinc-900/50">
                <p className="text-xs text-zinc-500">Account Balance</p>
                <p className="text-xl font-mono font-bold text-white">${formatNumber(goalPlan?.account_value || 0)}</p>
              </div>
            </div>

            <div className={`p-4 rounded-lg ${goalPlan?.suggestion?.type === 'ready' ? 'bg-emerald-500/10 border border-emerald-500/30' : 'bg-blue-500/10 border border-blue-500/30'}`}>
              <p className={`text-sm ${goalPlan?.suggestion?.type === 'ready' ? 'text-emerald-400' : 'text-blue-400'}`}>
                {goalPlan?.suggestion?.message}
              </p>
              {goalPlan?.suggestion?.trades_needed && (
                <p className="text-xs text-zinc-500 mt-2">
                  Estimated trades needed: {goalPlan.suggestion.trades_needed}
                </p>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};
