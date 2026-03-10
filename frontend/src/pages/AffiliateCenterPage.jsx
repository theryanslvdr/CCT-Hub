import React, { useState, useEffect, useCallback } from 'react';
import { affiliateAPI, adminAffiliateAPI, referralAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MessageSquare, BookOpen, Image, HelpCircle, Bot, ClipboardCopy, ChevronDown, ChevronUp, Plus, X, Loader2, Trash2, UserPlus, Link2, ExternalLink, CheckCircle2, Search } from 'lucide-react';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

const CATEGORIES = [
  { key: 'conversation_starters', label: 'Conversation Starters', icon: MessageSquare, color: 'text-orange-400', desc: 'Ready-to-use messages to start inviting conversations' },
  { key: 'story_templates', label: 'Story Templates', icon: BookOpen, color: 'text-purple-400', desc: 'Social media and story templates to share' },
  { key: 'marketing', label: 'Marketing Materials', icon: Image, color: 'text-amber-400', desc: 'Graphics, images, and promotional content' },
  { key: 'faqs', label: 'FAQs', icon: HelpCircle, color: 'text-emerald-400', desc: 'Common questions and answers for prospects' },
];

const ResourceCard = ({ resource, isAdmin, onDelete }) => {
  const [expanded, setExpanded] = useState(false);
  const isLong = resource.content.length > 200;

  const handleCopy = () => {
    navigator.clipboard.writeText(resource.content).then(() => toast.success('Copied to clipboard!'));
  };

  return (
    <div className="p-4 rounded-lg bg-[#0d0d0d]/60 border border-white/[0.06] hover:border-white/[0.08] transition-colors" data-testid={`resource-${resource.id}`}>
      <div className="flex items-start justify-between gap-2">
        <h4 className="text-sm font-medium text-white">{resource.title}</h4>
        <div className="flex gap-1 shrink-0">
          <Button variant="ghost" size="sm" onClick={handleCopy} className="text-zinc-400 hover:text-orange-400" data-testid={`copy-resource-${resource.id}`}>
            <ClipboardCopy className="w-3.5 h-3.5" />
          </Button>
          {isAdmin && onDelete && (
            <Button variant="ghost" size="sm" onClick={() => onDelete(resource.id)} className="text-zinc-400 hover:text-red-400" data-testid={`delete-resource-${resource.id}`}>
              <Trash2 className="w-3.5 h-3.5" />
            </Button>
          )}
        </div>
      </div>
      <div className={`text-sm text-zinc-400 mt-2 whitespace-pre-wrap ${!expanded && isLong ? 'line-clamp-3' : ''}`}>
        {resource.content}
      </div>
      {isLong && (
        <button onClick={() => setExpanded(!expanded)} className="text-xs text-orange-400 hover:text-orange-300 mt-1.5 flex items-center gap-1">
          {expanded ? <><ChevronUp className="w-3 h-3" /> Show less</> : <><ChevronDown className="w-3 h-3" /> Show more</>}
        </button>
      )}
    </div>
  );
};

const InlineAddForm = ({ category, onSaved }) => {
  const [show, setShow] = useState(false);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!title.trim() || !content.trim()) { toast.error('Title and content required'); return; }
    setSaving(true);
    try {
      await adminAffiliateAPI.createResource({ category, title, content, order: 0 });
      toast.success('Resource added');
      setTitle(''); setContent(''); setShow(false);
      onSaved();
    } catch { toast.error('Failed to save'); }
    setSaving(false);
  };

  if (!show) {
    return (
      <Button variant="ghost" size="sm" onClick={() => setShow(true)} className="w-full border border-dashed border-white/[0.08] text-zinc-500 hover:text-white hover:border-zinc-500 gap-1.5" data-testid={`add-resource-inline-${category}`}>
        <Plus className="w-4 h-4" /> Add Resource
      </Button>
    );
  }

  return (
    <div className="p-3 rounded-lg border border-cyan-500/30 bg-[#0d0d0d]/60 space-y-2" data-testid={`inline-form-${category}`}>
      <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Title" className="input-dark text-sm" data-testid={`inline-title-${category}`} />
      <Textarea value={content} onChange={(e) => setContent(e.target.value)} placeholder="Content (members can copy this)" className="input-dark text-sm" rows={3} data-testid={`inline-content-${category}`} />
      <div className="flex gap-2 justify-end">
        <Button variant="ghost" size="sm" onClick={() => { setShow(false); setTitle(''); setContent(''); }}><X className="w-3.5 h-3.5" /></Button>
        <Button size="sm" onClick={handleSave} disabled={saving} className="bg-cyan-600 hover:bg-cyan-700 gap-1" data-testid={`inline-save-${category}`}>
          {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Save'}
        </Button>
      </div>
    </div>
  );
};

const AffiliateCenterPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const isAdmin = ['admin', 'basic_admin', 'super_admin', 'master_admin'].includes(user?.role);
  const [resources, setResources] = useState({});
  const [chatbase, setChatbase] = useState({ enabled: false, bot_id: '' });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('conversation_starters');
  const [inviteData, setInviteData] = useState(null);
  const [copied, setCopied] = useState(false);
  const [lookupQuery, setLookupQuery] = useState('');
  const [lookupResults, setLookupResults] = useState([]);
  const [lookupLoading, setLookupLoading] = useState(false);
  const lookupTimeout = React.useRef(null);

  const loadData = useCallback(async () => {
    try {
      const [resRes, cbRes, trackRes] = await Promise.all([
        affiliateAPI.getResources(),
        affiliateAPI.getChatbase(),
        referralAPI.getTracking().catch(() => ({ data: null })),
      ]);
      setResources(resRes.data.resources || {});
      setChatbase(cbRes.data);
      setInviteData(trackRes.data);
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleDeleteResource = async (id) => {
    try {
      await adminAffiliateAPI.deleteResource(id);
      toast.success('Resource deleted');
      loadData();
    } catch { toast.error('Failed to delete'); }
  };

  const handleCopyInviteLink = () => {
    const link = inviteData?.onboarding_invite_link;
    if (link) {
      navigator.clipboard.writeText(link);
      setCopied(true);
      toast.success('Invite link copied!');
      setTimeout(() => setCopied(false), 2500);
    }
  };

  const handleLookupChange = (value) => {
    setLookupQuery(value);
    if (lookupTimeout.current) clearTimeout(lookupTimeout.current);
    if (value.trim().length < 1) {
      setLookupResults([]);
      return;
    }
    setLookupLoading(true);
    lookupTimeout.current = setTimeout(async () => {
      try {
        const res = await referralAPI.lookupMembers(value.trim());
        setLookupResults(res.data.results || []);
      } catch {
        setLookupResults([]);
      }
      setLookupLoading(false);
    }, 300);
  };

  const handleCopyMerinCode = (code) => {
    navigator.clipboard.writeText(code);
    toast.success(`Merin code ${code} copied!`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-6 h-6 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const totalResources = Object.values(resources).flat().length;

  return (
    <div className="space-y-6" data-testid="affiliate-center-page">
      <div>
        <h1 className="text-2xl font-bold text-white">Affiliate Center</h1>
        <p className="text-sm text-zinc-400 mt-1">Resources to help you invite and onboard new members</p>
      </div>

      {/* Invite Someone Card */}
      <Card className="border-orange-500/20 bg-gradient-to-r from-orange-500/[0.06] to-amber-500/[0.02] overflow-hidden" data-testid="invite-someone-card">
        <CardContent className="p-5">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-orange-500/10 flex items-center justify-center shrink-0">
              <UserPlus className="w-6 h-6 text-orange-400" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold text-white">Invite Someone</h3>
              <p className="text-xs text-zinc-400 mt-1 mb-3">
                Share this link with prospects. It takes them to the onboarding wizard with your Merin code 
                <span className="text-orange-400 font-mono ml-1">{inviteData?.merin_code || '—'}</span> pre-filled.
              </p>
              {inviteData?.onboarding_invite_link ? (
                <div className="space-y-3">
                  <div className="flex gap-2">
                    <Input
                      value={inviteData.onboarding_invite_link}
                      readOnly
                      className="bg-[#0a0a0a] border-white/[0.06] text-white font-mono text-xs"
                      data-testid="onboarding-invite-link-input"
                    />
                    <Button
                      onClick={handleCopyInviteLink}
                      className={`shrink-0 transition-all ${copied ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-orange-500 hover:bg-orange-600'} text-white`}
                      data-testid="copy-onboarding-invite-link"
                    >
                      {copied ? (
                        <><CheckCircle2 className="w-4 h-4 mr-1.5" /> Copied</>
                      ) : (
                        <><ClipboardCopy className="w-4 h-4 mr-1.5" /> Copy</>
                      )}
                    </Button>
                  </div>
                  <div className="flex items-center gap-4 text-[11px] text-zinc-500">
                    <button
                      onClick={() => navigate('/referral-tracking')}
                      className="flex items-center gap-1 text-orange-400/70 hover:text-orange-400 transition-colors"
                      data-testid="view-referral-tracking-link"
                    >
                      <Link2 className="w-3 h-3" /> View referral stats
                    </button>
                    {inviteData?.invite_link && (
                      <a
                        href={inviteData.invite_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-zinc-500 hover:text-zinc-300 transition-colors"
                        data-testid="direct-merin-link"
                      >
                        <ExternalLink className="w-3 h-3" /> Direct Merin signup link
                      </a>
                    )}
                  </div>
                </div>
              ) : (
                <p className="text-sm text-amber-400">
                  Set your Merin referral code in{' '}
                  <button onClick={() => navigate('/profile')} className="underline hover:text-amber-300">Profile</button>
                  {' '}to generate your invite link.
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Member Lookup Card */}
      <Card className="glass-card" data-testid="member-lookup-card">
        <CardContent className="p-5">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-cyan-500/10 flex items-center justify-center shrink-0">
              <Search className="w-6 h-6 text-cyan-400" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold text-white">Find a Member</h3>
              <p className="text-xs text-zinc-400 mt-1 mb-3">
                Look up a member by name or email to find their Merin referral code.
              </p>
              <div className="relative">
                <Input
                  value={lookupQuery}
                  onChange={(e) => handleLookupChange(e.target.value)}
                  placeholder="Type a name or email..."
                  className="bg-[#0a0a0a] border-white/[0.06] text-white text-sm pl-9"
                  data-testid="member-lookup-input"
                />
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                {lookupLoading && (
                  <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 animate-spin" />
                )}
              </div>
              {lookupResults.length > 0 && (
                <div className="mt-2 rounded-lg border border-white/[0.06] overflow-hidden divide-y divide-white/[0.04]" data-testid="member-lookup-results">
                  {lookupResults.map((r) => (
                    <div key={r.id} className="flex items-center gap-3 px-3 py-2.5 bg-[#0a0a0a]/60 hover:bg-white/[0.03] transition-colors">
                      <div className="w-8 h-8 rounded-full bg-[#1a1a1a] flex items-center justify-center shrink-0">
                        <span className="text-xs font-medium text-zinc-400">{r.name?.charAt(0)?.toUpperCase() || '?'}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white truncate">{r.name}</p>
                        <p className="text-[11px] text-zinc-500 truncate">{r.masked_email}</p>
                      </div>
                      <button
                        onClick={() => handleCopyMerinCode(r.merin_code)}
                        className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-orange-500/10 text-orange-400 text-xs font-mono hover:bg-orange-500/20 transition-colors shrink-0"
                        data-testid={`copy-merin-code-${r.id}`}
                      >
                        <ClipboardCopy className="w-3 h-3" />
                        {r.merin_code}
                      </button>
                    </div>
                  ))}
                </div>
              )}
              {lookupQuery.trim().length > 0 && !lookupLoading && lookupResults.length === 0 && (
                <p className="text-xs text-zinc-500 mt-2" data-testid="member-lookup-no-results">No members found matching "{lookupQuery}"</p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-[#0d0d0d]/60 border border-white/[0.06] w-full flex flex-wrap h-auto gap-1 p-1">
          {CATEGORIES.map(cat => {
            const Icon = cat.icon;
            const count = (resources[cat.key] || []).length;
            return (
              <TabsTrigger
                key={cat.key}
                value={cat.key}
                className="flex-1 min-w-[120px] text-xs data-[state=active]:bg-[#1a1a1a] gap-1.5"
                data-testid={`affiliate-tab-${cat.key}`}
              >
                <Icon className={`w-3.5 h-3.5 ${cat.color}`} />
                {cat.label}
                {count > 0 && <span className="text-[10px] text-zinc-500 ml-0.5">({count})</span>}
              </TabsTrigger>
            );
          })}
          {chatbase.enabled && (
            <TabsTrigger value="consim" className="flex-1 min-w-[120px] text-xs data-[state=active]:bg-[#1a1a1a] gap-1.5" data-testid="affiliate-tab-consim">
              <Bot className="w-3.5 h-3.5 text-cyan-400" /> ConSim
            </TabsTrigger>
          )}
        </TabsList>

        {CATEGORIES.map(cat => (
          <TabsContent key={cat.key} value={cat.key} className="mt-4">
            <Card className="glass-card">
              <CardHeader className="pb-3">
                <CardTitle className="text-white text-base flex items-center gap-2">
                  <cat.icon className={`w-5 h-5 ${cat.color}`} />
                  {cat.label}
                </CardTitle>
                <p className="text-xs text-zinc-500">{cat.desc}</p>
              </CardHeader>
              <CardContent className="space-y-3">
                {(resources[cat.key] || []).length === 0 && !isAdmin ? (
                  <p className="text-sm text-zinc-500 text-center py-6">No {cat.label.toLowerCase()} available yet.</p>
                ) : (
                  (resources[cat.key] || []).map(r => (
                    <ResourceCard key={r.id} resource={r} isAdmin={isAdmin} onDelete={handleDeleteResource} />
                  ))
                )}
                {isAdmin && <InlineAddForm category={cat.key} onSaved={loadData} />}
              </CardContent>
            </Card>
          </TabsContent>
        ))}

        {chatbase.enabled && (
          <TabsContent value="consim" className="mt-4">
            <Card className="glass-card">
              <CardHeader className="pb-3">
                <CardTitle className="text-white text-base flex items-center gap-2">
                  <Bot className="w-5 h-5 text-cyan-400" /> ConSim - Conversation Simulator
                </CardTitle>
                <p className="text-xs text-zinc-500">Practice your invitation conversations with an AI chatbot</p>
              </CardHeader>
              <CardContent>
                <div className="rounded-lg overflow-hidden border border-white/[0.06]" style={{ height: '500px' }} data-testid="chatbase-embed">
                  <iframe src={`https://www.chatbase.co/chatbot-iframe/${chatbase.bot_id}`} title="ConSim Chatbot" width="100%" height="100%" style={{ border: 'none' }} />
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>

      {totalResources === 0 && !chatbase.enabled && !isAdmin && (
        <Card className="glass-card">
          <CardContent className="p-8 text-center text-zinc-400">
            <p>The affiliate center is being set up. Check back soon for resources!</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AffiliateCenterPage;
