import React, { useState, useRef } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { referralAPI } from '@/lib/api';
import { toast } from 'sonner';
import { Search, Loader2, UserPlus, CheckCircle2 } from 'lucide-react';

const InviterModal = ({ open, onComplete }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [selected, setSelected] = useState(null);
  const debounce = useRef(null);

  const handleSearch = (value) => {
    setQuery(value);
    setSelected(null);
    if (debounce.current) clearTimeout(debounce.current);
    if (value.trim().length < 1) { setResults([]); return; }
    setSearching(true);
    debounce.current = setTimeout(async () => {
      try {
        const res = await referralAPI.lookupMembers(value.trim());
        setResults(res.data.results || []);
      } catch { setResults([]); }
      setSearching(false);
    }, 300);
  };

  const handleSelect = (member) => {
    setSelected(member);
    setResults([]);
    setQuery(member.name);
  };

  const handleConfirm = async () => {
    if (!selected) return;
    setSubmitting(true);
    try {
      const res = await referralAPI.setInviter(selected.id);
      toast.success(`Linked to ${res.data.inviter_name} as your inviter!`);
      onComplete(res.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to set inviter');
    }
    setSubmitting(false);
  };

  return (
    <Dialog open={open} onOpenChange={() => {}}>
      <DialogContent className="bg-[#111111] border-white/[0.06] max-w-md [&>button]:hidden" data-testid="inviter-modal">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-orange-400" />
            Who invited you?
          </DialogTitle>
          <DialogDescription className="text-zinc-400">
            Search for the member who invited you to CrossCurrent. This is required to complete your referral link.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 mt-2">
          {!selected ? (
            <>
              <div className="relative">
                <Input
                  value={query}
                  onChange={(e) => handleSearch(e.target.value)}
                  placeholder="Type their name or email..."
                  className="bg-[#0a0a0a] border-white/[0.06] text-white text-sm pl-9"
                  autoFocus
                  data-testid="inviter-search-input"
                />
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                {searching && <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 animate-spin" />}
              </div>

              {results.length > 0 && (
                <div className="rounded-lg border border-white/[0.06] overflow-hidden divide-y divide-white/[0.04] max-h-[240px] overflow-y-auto" data-testid="inviter-search-results">
                  {results.map((r) => (
                    <button
                      key={r.id}
                      onClick={() => handleSelect(r)}
                      className="w-full flex items-center gap-3 px-3 py-2.5 bg-[#0a0a0a]/60 hover:bg-orange-500/[0.06] transition-colors text-left"
                      data-testid={`inviter-option-${r.id}`}
                    >
                      <div className="w-8 h-8 rounded-full bg-[#1a1a1a] flex items-center justify-center shrink-0">
                        <span className="text-xs font-medium text-zinc-400">{r.name?.charAt(0)?.toUpperCase() || '?'}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white truncate">{r.name}</p>
                        <p className="text-[11px] text-zinc-500 truncate">{r.masked_email}</p>
                      </div>
                      <span className="text-[10px] font-mono text-orange-400/70 shrink-0">{r.merin_code}</span>
                    </button>
                  ))}
                </div>
              )}

              {query.trim().length > 0 && !searching && results.length === 0 && (
                <p className="text-xs text-zinc-500 text-center py-2" data-testid="inviter-no-results">
                  No members found matching "{query}"
                </p>
              )}
            </>
          ) : (
            <div className="p-4 rounded-lg bg-orange-500/[0.06] border border-orange-500/20">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-orange-500/10 flex items-center justify-center">
                  <span className="text-sm font-bold text-orange-400">{selected.name?.charAt(0)?.toUpperCase()}</span>
                </div>
                <div className="flex-1">
                  <p className="text-white font-medium">{selected.name}</p>
                  <p className="text-xs text-zinc-500">{selected.masked_email}</p>
                </div>
                <button
                  onClick={() => { setSelected(null); setQuery(''); }}
                  className="text-xs text-zinc-500 hover:text-white transition-colors"
                >
                  Change
                </button>
              </div>
            </div>
          )}

          <Button
            onClick={handleConfirm}
            disabled={!selected || submitting}
            className="w-full bg-orange-500 hover:bg-orange-600 text-white"
            data-testid="inviter-confirm-btn"
          >
            {submitting ? (
              <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Confirming...</>
            ) : (
              <><CheckCircle2 className="w-4 h-4 mr-2" /> Confirm Inviter</>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default InviterModal;
