/**
 * Shared Admin Components
 * Reusable UI components for admin pages
 */

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Search, ChevronLeft, ChevronRight, Users, ShieldCheck, ShieldAlert, 
  Crown, Loader2, RefreshCw 
} from 'lucide-react';

/**
 * Stats Card - Displays a single metric with icon
 */
export const StatsCard = ({ 
  title, 
  value, 
  icon: Icon, 
  iconColor = 'from-orange-500 to-amber-600',
  valueColor = 'text-white',
  testId
}) => (
  <Card className="glass-card" data-testid={testId}>
    <CardContent className="p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-zinc-400">{title}</p>
          <p className={`text-3xl font-bold font-mono mt-2 ${valueColor}`}>{value}</p>
        </div>
        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${iconColor} flex items-center justify-center`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </CardContent>
  </Card>
);

/**
 * Search and Filter Bar
 */
export const SearchFilterBar = ({
  searchQuery,
  onSearchChange,
  searchPlaceholder = 'Search...',
  filters = [],
  onRefresh,
  refreshing,
  children
}) => (
  <Card className="glass-card">
    <CardContent className="p-4">
      <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
          <Input
            placeholder={searchPlaceholder}
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="input-dark pl-10"
            data-testid="search-input"
          />
        </div>
        
        <div className="flex flex-wrap gap-2 items-center">
          {filters.map((filter, index) => (
            <Select key={index} value={filter.value} onValueChange={filter.onChange}>
              <SelectTrigger className="w-[140px] bg-[#0d0d0d]/50 border-white/[0.06] text-white" data-testid={filter.testId}>
                <SelectValue placeholder={filter.placeholder} />
              </SelectTrigger>
              <SelectContent className="bg-[#0d0d0d] border-white/[0.06]">
                {filter.options.map((option) => (
                  <SelectItem key={option.value} value={option.value} className="text-white hover:bg-[#1a1a1a]">
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ))}
          
          {onRefresh && (
            <Button
              variant="outline"
              size="icon"
              onClick={onRefresh}
              disabled={refreshing}
              className="border-white/[0.08] hover:bg-[#1a1a1a]"
              data-testid="refresh-button"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            </Button>
          )}
          
          {children}
        </div>
      </div>
    </CardContent>
  </Card>
);

/**
 * Pagination Controls
 */
export const Pagination = ({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
  itemName = 'items'
}) => {
  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  return (
    <div className="flex items-center justify-between mt-4">
      <p className="text-sm text-zinc-400">
        Showing {startItem}-{endItem} of {totalItems} {itemName}
      </p>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="icon"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="border-white/[0.08] hover:bg-[#1a1a1a]"
          data-testid="prev-page"
        >
          <ChevronLeft className="w-4 h-4" />
        </Button>
        <span className="text-sm text-zinc-300 px-2">
          Page {currentPage} of {totalPages}
        </span>
        <Button
          variant="outline"
          size="icon"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="border-white/[0.08] hover:bg-[#1a1a1a]"
          data-testid="next-page"
        >
          <ChevronRight className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
};

/**
 * Role Badge Component
 */
export const RoleBadge = ({ role }) => {
  const getRoleConfig = (role) => {
    switch (role) {
      case 'master_admin':
        return { 
          icon: Crown, 
          label: 'Master Admin',
          className: 'bg-purple-500/20 text-purple-400 border-orange-500/20' 
        };
      case 'super_admin':
        return { 
          icon: ShieldAlert, 
          label: 'Super Admin',
          className: 'bg-amber-500/20 text-amber-400 border-amber-500/30' 
        };
      case 'basic_admin':
        return { 
          icon: ShieldCheck, 
          label: 'Admin',
          className: 'bg-orange-500/10 text-orange-400 border-orange-500/20' 
        };
      default:
        return { 
          icon: Users, 
          label: 'Member',
          className: 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30' 
        };
    }
  };

  const config = getRoleConfig(role);
  const Icon = config.icon;

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium border ${config.className}`}>
      <Icon className="w-3 h-3" />
      {config.label}
    </span>
  );
};

/**
 * License Type Badge
 */
export const LicenseBadge = ({ type }) => {
  if (!type) return null;
  
  const config = type === 'extended' 
    ? { label: 'EXT', className: 'bg-purple-500/20 text-purple-400 border-orange-500/20' }
    : { label: 'HON', className: 'bg-amber-500/20 text-amber-400 border-amber-500/30' };

  return (
    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium border ${config.className}`}>
      {config.label}
    </span>
  );
};

/**
 * Status Badge
 */
export const StatusBadge = ({ status, type = 'default' }) => {
  const getStatusConfig = () => {
    if (type === 'transaction') {
      switch (status) {
        case 'completed':
          return { label: 'Completed', className: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' };
        case 'pending':
          return { label: 'Pending', className: 'bg-amber-500/20 text-amber-400 border-amber-500/30' };
        case 'processing':
          return { label: 'Processing', className: 'bg-orange-500/10 text-orange-400 border-orange-500/20' };
        case 'awaiting_confirmation':
          return { label: 'Awaiting Confirm', className: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30' };
        case 'rejected':
          return { label: 'Rejected', className: 'bg-red-500/20 text-red-400 border-red-500/30' };
        default:
          return { label: status, className: 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30' };
      }
    }
    
    // Default status types
    switch (status) {
      case 'active':
        return { label: 'Active', className: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' };
      case 'inactive':
        return { label: 'Inactive', className: 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30' };
      case 'suspended':
        return { label: 'Suspended', className: 'bg-red-500/20 text-red-400 border-red-500/30' };
      default:
        return { label: status, className: 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30' };
    }
  };

  const config = getStatusConfig();
  
  return (
    <span className={`px-2 py-1 rounded text-xs font-medium border ${config.className}`}>
      {config.label}
    </span>
  );
};

/**
 * Loading Spinner
 */
export const LoadingSpinner = ({ size = 'default', text = 'Loading...' }) => {
  const sizeClass = size === 'small' ? 'w-6 h-6' : size === 'large' ? 'w-12 h-12' : 'w-8 h-8';
  
  return (
    <div className="flex flex-col items-center justify-center h-64 gap-3">
      <Loader2 className={`${sizeClass} text-orange-500 animate-spin`} />
      {text && <p className="text-zinc-400 text-sm">{text}</p>}
    </div>
  );
};

/**
 * Empty State
 */
export const EmptyState = ({ 
  icon: Icon = Users, 
  title = 'No data found', 
  description = 'Try adjusting your search or filters',
  action
}) => (
  <div className="flex flex-col items-center justify-center py-16 text-center">
    <div className="w-16 h-16 rounded-full bg-[#1a1a1a] flex items-center justify-center mb-4">
      <Icon className="w-8 h-8 text-zinc-500" />
    </div>
    <h3 className="text-lg font-medium text-white mb-2">{title}</h3>
    <p className="text-zinc-400 text-sm max-w-md mb-4">{description}</p>
    {action}
  </div>
);

/**
 * Action Button Group
 */
export const ActionButtons = ({ actions, size = 'sm' }) => (
  <div className="flex items-center gap-1">
    {actions.map((action, index) => (
      <Button
        key={index}
        variant={action.variant || 'ghost'}
        size={size}
        onClick={action.onClick}
        disabled={action.disabled}
        className={action.className || 'text-zinc-400 hover:text-white hover:bg-[#1a1a1a]'}
        title={action.title}
        data-testid={action.testId}
      >
        {action.icon && <action.icon className="w-4 h-4" />}
        {action.label && <span className="ml-1">{action.label}</span>}
      </Button>
    ))}
  </div>
);

export default {
  StatsCard,
  SearchFilterBar,
  Pagination,
  RoleBadge,
  LicenseBadge,
  StatusBadge,
  LoadingSpinner,
  EmptyState,
  ActionButtons
};
