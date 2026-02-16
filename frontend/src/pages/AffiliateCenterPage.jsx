import React, { useState, useEffect, useCallback } from 'react';
import { affiliateAPI } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MessageSquare, BookOpen, Image, HelpCircle, Bot, ClipboardCopy, ChevronDown, ChevronUp } from 'lucide-react';
import { toast } from 'sonner';

const CATEGORIES = [
  { key: 'conversation_starters', label: 'Conversation Starters', icon: MessageSquare, color: 'text-blue-400', desc: 'Ready-to-use messages to start inviting conversations' },
  { key: 'story_templates', label: 'Story Templates', icon: BookOpen, color: 'text-purple-400', desc: 'Social media and story templates to share' },
  { key: 'marketing', label: 'Marketing Materials', icon: Image, color: 'text-amber-400', desc: 'Graphics, images, and promotional content' },
  { key: 'faqs', label: 'FAQs', icon: HelpCircle, color: 'text-emerald-400', desc: 'Common questions and answers for prospects' },
];

const ResourceCard = ({ resource }) => {
  const [expanded, setExpanded] = useState(false);
  const isLong = resource.content.length > 200;

  const handleCopy = () => {
    navigator.clipboard.writeText(resource.content).then(() => toast.success('Copied to clipboard!'));
  };

  return (
    <div className="p-4 rounded-lg bg-zinc-900/60 border border-zinc-800 hover:border-zinc-700 transition-colors" data-testid={`resource-${resource.id}`}>
      <div className="flex items-start justify-between gap-2">
        <h4 className="text-sm font-medium text-white">{resource.title}</h4>
        <Button variant="ghost" size="sm" onClick={handleCopy} className="shrink-0 text-zinc-400 hover:text-blue-400" data-testid={`copy-resource-${resource.id}`}>
          <ClipboardCopy className="w-3.5 h-3.5" />
        </Button>
      </div>
      <div className={`text-sm text-zinc-400 mt-2 whitespace-pre-wrap ${!expanded && isLong ? 'line-clamp-3' : ''}`}>
        {resource.content}
      </div>
      {isLong && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-blue-400 hover:text-blue-300 mt-1.5 flex items-center gap-1"
        >
          {expanded ? <><ChevronUp className="w-3 h-3" /> Show less</> : <><ChevronDown className="w-3 h-3" /> Show more</>}
        </button>
      )}
    </div>
  );
};

const AffiliateCenterPage = () => {
  const [resources, setResources] = useState({});
  const [chatbase, setChatbase] = useState({ enabled: false, bot_id: '' });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('conversation_starters');

  const loadData = useCallback(async () => {
    try {
      const [resRes, cbRes] = await Promise.all([
        affiliateAPI.getResources(),
        affiliateAPI.getChatbase(),
      ]);
      setResources(resRes.data.resources || {});
      setChatbase(cbRes.data);
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
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

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-zinc-900/60 border border-zinc-800 w-full flex flex-wrap h-auto gap-1 p-1">
          {CATEGORIES.map(cat => {
            const Icon = cat.icon;
            const count = (resources[cat.key] || []).length;
            return (
              <TabsTrigger
                key={cat.key}
                value={cat.key}
                className="flex-1 min-w-[120px] text-xs data-[state=active]:bg-zinc-800 gap-1.5"
                data-testid={`affiliate-tab-${cat.key}`}
              >
                <Icon className={`w-3.5 h-3.5 ${cat.color}`} />
                {cat.label}
                {count > 0 && <span className="text-[10px] text-zinc-500 ml-0.5">({count})</span>}
              </TabsTrigger>
            );
          })}
          {chatbase.enabled && (
            <TabsTrigger
              value="consim"
              className="flex-1 min-w-[120px] text-xs data-[state=active]:bg-zinc-800 gap-1.5"
              data-testid="affiliate-tab-consim"
            >
              <Bot className="w-3.5 h-3.5 text-cyan-400" />
              ConSim
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
                {(resources[cat.key] || []).length === 0 ? (
                  <p className="text-sm text-zinc-500 text-center py-6">No {cat.label.toLowerCase()} available yet.</p>
                ) : (
                  (resources[cat.key] || []).map(r => <ResourceCard key={r.id} resource={r} />)
                )}
              </CardContent>
            </Card>
          </TabsContent>
        ))}

        {chatbase.enabled && (
          <TabsContent value="consim" className="mt-4">
            <Card className="glass-card">
              <CardHeader className="pb-3">
                <CardTitle className="text-white text-base flex items-center gap-2">
                  <Bot className="w-5 h-5 text-cyan-400" />
                  ConSim - Conversation Simulator
                </CardTitle>
                <p className="text-xs text-zinc-500">Practice your invitation conversations with an AI chatbot</p>
              </CardHeader>
              <CardContent>
                <div className="rounded-lg overflow-hidden border border-zinc-800" style={{ height: '500px' }} data-testid="chatbase-embed">
                  <iframe
                    src={`https://www.chatbase.co/chatbot-iframe/${chatbase.bot_id}`}
                    title="ConSim Chatbot"
                    width="100%"
                    height="100%"
                    style={{ border: 'none' }}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>

      {totalResources === 0 && !chatbase.enabled && (
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
