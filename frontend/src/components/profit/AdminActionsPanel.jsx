import React from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { FolderOpen, FileText, Receipt, Award, RotateCcw, Wallet, Lock } from 'lucide-react';
import { formatLargeNumber } from '@/utils/profitCalculations';

export function AdminActionsPanel({
  // Access Records
  accessRecordsOpen,
  setAccessRecordsOpen,
  setDepositRecordsOpen,
  setWithdrawalRecordsOpen,
  setCommissionRecordsOpen,
  // Reset Dialog
  resetDialogOpen,
  setResetDialogOpen,
  resetStep,
  setResetStep,
  resetPassword,
  setResetPassword,
  resetNewBalance,
  setResetNewBalance,
  handleResetConfirm,
  handleResetWithPassword,
  resetResetDialog,
  summary,
}) {
  return (
    <div className="flex gap-2 w-full md:w-auto md:ml-auto">
      {/* Access Records Button - Combined Popup */}
      <Dialog open={accessRecordsOpen} onOpenChange={setAccessRecordsOpen}>
        <DialogTrigger asChild>
          <Button variant="outline" className="btn-secondary gap-2 flex-1 md:flex-none" data-testid="access-records-button">
            <FolderOpen className="w-4 h-4" /> <span className="hidden sm:inline">Access </span>Records
          </Button>
        </DialogTrigger>
        <DialogContent className="glass-card border-zinc-800 max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <FolderOpen className="w-5 h-5 text-orange-400" /> Access Records
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-3 mt-4">
            <Button 
              variant="outline" 
              className="w-full btn-secondary gap-2 justify-start" 
              onClick={() => { setAccessRecordsOpen(false); setDepositRecordsOpen(true); }}
              data-testid="view-deposits-button"
            >
              <FileText className="w-4 h-4 text-emerald-400" /> Deposit Records
            </Button>
            <Button 
              variant="outline" 
              className="w-full btn-secondary gap-2 justify-start" 
              onClick={() => { setAccessRecordsOpen(false); setWithdrawalRecordsOpen(true); }}
              data-testid="view-withdrawals-button"
            >
              <Receipt className="w-4 h-4 text-amber-400" /> Withdrawal Records
            </Button>
            <Button 
              variant="outline" 
              className="w-full btn-secondary gap-2 justify-start" 
              onClick={() => { setAccessRecordsOpen(false); setCommissionRecordsOpen(true); }}
              data-testid="view-commissions-button"
            >
              <Award className="w-4 h-4 text-purple-400" /> Commission Records
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Reset Button */}
      <Dialog open={resetDialogOpen} onOpenChange={(open) => { if (!open) resetResetDialog(); else setResetDialogOpen(true); }}>
        <DialogTrigger asChild>
          <Button variant="outline" className="btn-secondary gap-2 text-amber-400 hover:text-amber-300 flex-1 md:flex-none" data-testid="reset-tracker-button">
            <RotateCcw className="w-4 h-4" /> Reset<span className="hidden sm:inline"> Tracker</span>
          </Button>
        </DialogTrigger>
        <DialogContent className="glass-card border-zinc-800">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              {resetStep === 'confirm' && <><RotateCcw className="w-5 h-5 text-red-400" /> Reset Profit Tracker</>}
              {resetStep === 'newBalance' && <><Wallet className="w-5 h-5 text-orange-400" /> Set New Account Value</>}
              {resetStep === 'password' && <><Lock className="w-5 h-5 text-amber-400" /> Security Verification</>}
            </DialogTitle>
          </DialogHeader>
          
          {resetStep === 'confirm' && (
            <div className="space-y-4 mt-4">
              <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400">
                <p className="font-medium mb-2">Warning: This action cannot be undone!</p>
                <p className="text-sm">Resetting will delete all your:</p>
                <ul className="list-disc list-inside text-sm mt-2">
                  <li>Deposit records</li>
                  <li>Withdrawal records</li>
                  <li>Trade logs</li>
                  <li>Profit calculations</li>
                </ul>
              </div>
              <div className="flex gap-3">
                <Button variant="outline" className="flex-1" onClick={() => setResetDialogOpen(false)}>
                  Cancel
                </Button>
                <Button className="flex-1 bg-red-500 hover:bg-red-600 text-white" onClick={handleResetConfirm}>
                  Continue
                </Button>
              </div>
            </div>
          )}

          {resetStep === 'password' && (
            <div className="space-y-4 mt-4">
              <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/30">
                <div className="flex items-start gap-3">
                  <Lock className="w-5 h-5 text-amber-400 mt-0.5" />
                  <div>
                    <p className="text-amber-400 font-medium">Security Verification Required</p>
                    <p className="text-sm text-zinc-400 mt-1">
                      Please enter your password to confirm the reset. You&apos;ll be guided through setting up your new tracker.
                    </p>
                  </div>
                </div>
              </div>
              <div>
                <Label className="text-zinc-300">Password</Label>
                <Input
                  type="password"
                  value={resetPassword}
                  onChange={(e) => setResetPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="input-dark mt-1"
                  data-testid="reset-password-input"
                />
              </div>
              <div className="flex gap-3">
                <Button variant="outline" className="flex-1" onClick={() => setResetStep('confirm')}>
                  Back
                </Button>
                <Button className="flex-1 bg-red-500 hover:bg-red-600 text-white" onClick={handleResetWithPassword} data-testid="confirm-reset-button">
                  <Lock className="w-4 h-4 mr-2" /> Confirm Reset
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
