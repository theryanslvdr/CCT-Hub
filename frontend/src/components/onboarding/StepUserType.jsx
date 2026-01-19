import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { User, TrendingUp, Check, Sparkles } from 'lucide-react';

/**
 * Step 1: User Type Selection
 * Allows user to choose between 'new' (new trader/start fresh) or 'experienced' (import history)
 */
export const StepUserType = ({ userType, setUserType, isReset }) => {
  return (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
          <Sparkles className="w-10 h-10 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">
          {isReset ? 'Reset Your Tracker' : 'Welcome to CrossCurrent!'}
        </h2>
        <p className="text-zinc-400">
          Let&apos;s set up your profit tracker. Are you new to Merin trading?
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card 
          className={`cursor-pointer transition-all hover:border-blue-500/50 ${userType === 'new' ? 'border-blue-500 bg-blue-500/10' : 'glass-card'}`}
          onClick={() => setUserType('new')}
          data-testid="user-type-new"
        >
          <CardContent className="p-6 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-emerald-500/20 flex items-center justify-center">
              <User className="w-8 h-8 text-emerald-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">New Trader / Start Fresh</h3>
            <p className="text-sm text-zinc-400">
              {isReset ? 'Start over with a clean slate.' : 'Just starting my trading journey.'} Set up a fresh tracker.
            </p>
            {userType === 'new' && (
              <div className="mt-4">
                <Check className="w-6 h-6 text-emerald-400 mx-auto" />
              </div>
            )}
          </CardContent>
        </Card>
        
        <Card 
          className={`cursor-pointer transition-all hover:border-blue-500/50 ${userType === 'experienced' ? 'border-blue-500 bg-blue-500/10' : 'glass-card'}`}
          onClick={() => setUserType('experienced')}
          data-testid="user-type-experienced"
        >
          <CardContent className="p-6 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-purple-500/20 flex items-center justify-center">
              <TrendingUp className="w-8 h-8 text-purple-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Experienced Trader</h3>
            <p className="text-sm text-zinc-400">
              Already trading on Merin. Import my trading history.
            </p>
            {userType === 'experienced' && (
              <div className="mt-4">
                <Check className="w-6 h-6 text-purple-400 mx-auto" />
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default StepUserType;
