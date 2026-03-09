import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { forumAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { toast } from 'sonner';
import ForumImageUpload from '@/components/ForumImageUpload';
import {
  MessageSquare, Plus, Search, Clock, CheckCircle2,
  Eye, MessageCircle, Loader2, ChevronLeft, ChevronRight,
  Award, ThumbsUp, Trophy, Star, ImageIcon, Pin, Tag, AlertTriangle
} from 'lucide-react';

const STATUS_COLORS = {
  open: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  closed: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20',
};

function timeSince(dateStr) {
  const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (seconds < 60) return 'just now';
  const mins = Math.floor(seconds / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(dateStr).toLocaleDateString();
}

const CATEGORY_COLORS = {
  general: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20',
  trading: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  technical: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  announcements: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
};

function PostCard({ post, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-4 rounded-lg bg-zinc-900/60 border transition-all group ${
        post.pinned ? 'border-amber-500/30 bg-amber-500/5' : 'border-zinc-800 hover:border-zinc-600'
      }`}
      data-testid={`forum-post-${post.id}`}
    >
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            {post.pinned && (
              <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center gap-0.5">
                <Pin className="w-2.5 h-2.5" /> Pinned
              </span>
            )}
            <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${STATUS_COLORS[post.status]}`}>
              {post.status === 'open' ? 'Open' : 'Solved'}
            </span>
            {post.category && post.category !== 'general' && (
              <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${CATEGORY_COLORS[post.category] || CATEGORY_COLORS.general}`}>
                {post.category}
              </span>
            )}
            {post.best_answer_id && (
              <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                Best Answer
              </span>
            )}
            {post.edited && (
              <span className="text-[10px] text-zinc-600 italic">edited</span>
            )}
          </div>
          <h3 className="text-sm font-semibold text-white group-hover:text-blue-400 transition-colors truncate">
            {post.title}
          </h3>
          <p className="text-xs text-zinc-500 mt-1 line-clamp-2">{post.content}</p>
          <div className="flex items-center gap-4 mt-2 text-[11px] text-zinc-500">
            <span>{post.author_name || 'Unknown'}</span>
            <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{timeSince(post.created_at)}</span>
            <span className="flex items-center gap-1"><MessageCircle className="w-3 h-3" />{post.comment_count || 0}</span>
            <span className="flex items-center gap-1"><Eye className="w-3 h-3" />{post.views || 0}</span>
          </div>
        </div>
        {post.tags?.length > 0 && (
          <div className="flex flex-wrap gap-1 max-w-[120px]">
            {post.tags.slice(0, 3).map(t => (
              <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">
                {t}
              </span>
            ))}
          </div>
        )}
      </div>
    </button>
  );
}

function SimilarPostsSuggestion({ query, navigate, onSelect }) {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!query || query.trim().length < 3) {
      setResults([]);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await forumAPI.searchSimilar(query.trim());
        setResults(res.data.results || []);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 400);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [query]);

  if (!query || query.trim().length < 3) return null;

  return (
    <div className="mt-2 rounded-lg border border-zinc-700 bg-zinc-800/80 overflow-hidden" data-testid="similar-posts-suggestions">
      <div className="px-3 py-2 border-b border-zinc-700 flex items-center gap-1.5">
        <Search className="w-3 h-3 text-blue-400" />
        <span className="text-[11px] text-zinc-400 font-medium">Similar existing posts</span>
        {loading && <Loader2 className="w-3 h-3 animate-spin text-zinc-500 ml-auto" />}
      </div>
      {results.length === 0 && !loading ? (
        <div className="px-3 py-2 text-xs text-zinc-500">No similar posts found. Your question looks unique!</div>
      ) : (
        <div className="max-h-40 overflow-y-auto">
          {results.map(r => (
            <button
              key={r.id}
              onClick={() => { onSelect(); navigate(`/forum/${r.id}`); }}
              className="w-full text-left px-3 py-2 hover:bg-zinc-700/50 transition-colors border-b border-zinc-700/50 last:border-0"
              data-testid={`similar-post-${r.id}`}
            >
              <div className="flex items-center gap-2">
                <span className={`text-[9px] px-1.5 py-0.5 rounded-full border ${STATUS_COLORS[r.status]}`}>
                  {r.status === 'open' ? 'Open' : 'Solved'}
                </span>
                {r.best_answer_id && (
                  <Award className="w-3 h-3 text-amber-400" />
                )}
                <span className="text-xs text-zinc-300 truncate flex-1">{r.title}</span>
                <span className="text-[10px] text-zinc-500 flex items-center gap-0.5">
                  <MessageCircle className="w-2.5 h-2.5" />{r.comment_count || 0}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function TopContributorsCard({ contributors }) {
  if (!contributors || contributors.length === 0) return null;

  const medals = ['text-amber-400', 'text-zinc-400', 'text-amber-700'];

  return (
    <div className="p-4 rounded-lg bg-zinc-900/60 border border-zinc-800" data-testid="top-contributors-section">
      <p className="text-xs font-semibold text-zinc-300 mb-3 flex items-center gap-1.5">
        <Trophy className="w-4 h-4 text-amber-400" /> Top Contributors
      </p>
      <div className="space-y-2">
        {contributors.map((c, i) => (
          <div
            key={c.user_id}
            className={`flex items-center gap-3 p-2 rounded-lg ${i < 3 ? 'bg-zinc-800/50' : ''}`}
          >
            <span className={`text-sm font-bold w-6 text-center ${medals[i] || 'text-zinc-500'}`}>
              {i + 1}
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-zinc-200 truncate">{c.name}</p>
              <div className="flex items-center gap-3 mt-0.5">
                {c.best_answers > 0 && (
                  <span className="text-[10px] text-amber-400 flex items-center gap-0.5">
                    <Star className="w-2.5 h-2.5" /> {c.best_answers} best
                  </span>
                )}
                {c.upvotes_received > 0 && (
                  <span className="text-[10px] text-emerald-400 flex items-center gap-0.5">
                    <ThumbsUp className="w-2.5 h-2.5" /> {c.upvotes_received} upvotes
                  </span>
                )}
                <span className="text-[10px] text-zinc-500 flex items-center gap-0.5">
                  <MessageCircle className="w-2.5 h-2.5" /> {c.comments_count}
                </span>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm font-bold text-blue-400">{c.reputation}</p>
              <p className="text-[9px] text-zinc-500">rep</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ForumListPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [posts, setPosts] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [stats, setStats] = useState(null);
  const [newPostOpen, setNewPostOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newPost, setNewPost] = useState({ title: '', content: '', tags: '', images: [], category: 'general' });
  const [categoryFilter, setCategoryFilter] = useState('');
  const [similarWarning, setSimilarWarning] = useState(null);

  const pageSize = 20;

  const loadPosts = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, page_size: pageSize };
      if (statusFilter) params.status = statusFilter;
      if (categoryFilter) params.category = categoryFilter;
      if (searchQuery.trim()) params.search = searchQuery.trim();
      const res = await forumAPI.listPosts(params);
      setPosts(res.data.posts || []);
      setTotal(res.data.total || 0);
    } catch (e) {
      toast.error('Failed to load posts');
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter, categoryFilter, searchQuery]);

  useEffect(() => { loadPosts(); }, [loadPosts]);
  useEffect(() => {
    forumAPI.getStats().then(r => setStats(r.data)).catch(() => {});
  }, []);

  const handleCreatePost = async () => {
    if (!newPost.title.trim() || !newPost.content.trim()) {
      toast.error('Title and content are required');
      return;
    }

    // Pre-submission AI-powered duplicate check
    if (!newPost._confirmedDuplicate) {
      try {
        const res = await forumAPI.aiCheckDuplicate(newPost.title.trim(), newPost.content.trim());
        if (res.data.has_similar && res.data.results?.length > 0) {
          setSimilarWarning({ results: res.data.results, ai: res.data.ai_powered });
          return;
        }
      } catch {
        try {
          const res = await forumAPI.searchSimilarFull(newPost.title.trim(), newPost.content.trim());
          if (res.data.has_similar && res.data.results?.length > 0) {
            setSimilarWarning({ results: res.data.results, ai: false });
            return;
          }
        } catch { /* proceed */ }
      }
    }

    setCreating(true);
    try {
      const tags = newPost.tags ? newPost.tags.split(',').map(t => t.trim()).filter(Boolean) : [];
      const images = newPost.images.map(img => img.url);
      const res = await forumAPI.createPost({ title: newPost.title, content: newPost.content, tags, images, category: newPost.category });
      toast.success('Post created!');
      setNewPostOpen(false);
      setNewPost({ title: '', content: '', tags: '', images: [], category: 'general' });
      setSimilarWarning(null);
      navigate(`/forum/${res.data.id}`);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to create post');
    } finally {
      setCreating(false);
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-5 pb-20 md:pb-6" data-testid="forum-list-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white flex items-center gap-2">
            <MessageSquare className="w-5 h-5 md:w-6 md:h-6 text-blue-400" /> Community Forum
          </h1>
          <p className="text-sm text-zinc-500 mt-0.5">Ask questions, share knowledge, earn points</p>
        </div>
        <Button
          onClick={() => setNewPostOpen(true)}
          className="gap-2 bg-blue-600 hover:bg-blue-700 w-full sm:w-auto"
          data-testid="new-post-btn"
        >
          <Plus className="w-4 h-4" /> New Post
        </Button>
      </div>

      {/* Stats bar */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: 'Total Posts', value: stats.total_posts, color: 'text-white' },
            { label: 'Open', value: stats.open_posts, color: 'text-emerald-400' },
            { label: 'Solved', value: stats.closed_posts, color: 'text-zinc-400' },
            { label: 'Comments', value: stats.total_comments, color: 'text-blue-400' },
          ].map(s => (
            <div key={s.label} className="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800 text-center">
              <p className={`text-xl font-bold ${s.color}`}>{s.value}</p>
              <p className="text-[10px] text-zinc-500 uppercase">{s.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Top Contributors */}
      <TopContributorsCard contributors={stats?.top_contributors} />

      {/* Filters */}
      <div className="flex flex-col gap-2">
        <div className="flex flex-col sm:flex-row gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
            <Input
              placeholder="Search posts..."
              value={searchQuery}
              onChange={e => { setSearchQuery(e.target.value); setPage(1); }}
              className="pl-9 input-dark"
              data-testid="forum-search-input"
            />
          </div>
          <div className="flex gap-2">
            {['', 'open', 'closed'].map(s => (
              <Button
                key={s}
                variant={statusFilter === s ? 'default' : 'outline'}
                size="sm"
                onClick={() => { setStatusFilter(s); setPage(1); }}
                className={statusFilter === s ? 'bg-blue-600 text-white' : 'btn-secondary'}
                data-testid={`filter-${s || 'all'}`}
              >
                {s === '' ? 'All' : s === 'open' ? 'Open' : 'Solved'}
              </Button>
            ))}
          </div>
        </div>
        {/* Category Filter */}
        <div className="flex gap-2 flex-wrap">
          <span className="text-xs text-zinc-500 flex items-center gap-1 mr-1"><Tag className="w-3 h-3" /> Category:</span>
          {['', 'general', 'trading', 'technical', 'announcements'].map(c => (
            <Button
              key={c}
              variant={categoryFilter === c ? 'default' : 'outline'}
              size="sm"
              onClick={() => { setCategoryFilter(c); setPage(1); }}
              className={`h-7 text-xs ${categoryFilter === c ? 'bg-blue-600 text-white' : 'btn-secondary'}`}
              data-testid={`category-${c || 'all'}`}
            >
              {c === '' ? 'All' : c.charAt(0).toUpperCase() + c.slice(1)}
            </Button>
          ))}
        </div>
      </div>

      {/* Posts list */}
      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-zinc-500" /></div>
      ) : posts.length === 0 ? (
        <div className="text-center py-12 text-zinc-500">
          <MessageSquare className="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p className="text-sm">No posts yet. Be the first to ask a question!</p>
        </div>
      ) : (
        <div className="space-y-2">
          {posts.map(p => (
            <PostCard key={p.id} post={p} onClick={() => navigate(`/forum/${p.id}`)} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 pt-2">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="btn-secondary">
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <span className="text-xs text-zinc-400">Page {page} of {totalPages}</span>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)} className="btn-secondary">
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      )}

      {/* New Post Dialog with Similar Posts */}
      <Dialog open={newPostOpen} onOpenChange={setNewPostOpen}>
        <DialogContent className="bg-zinc-900 border-zinc-800 max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-white">New Post</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-zinc-300">Title</Label>
              <Input
                value={newPost.title}
                onChange={e => setNewPost(p => ({ ...p, title: e.target.value }))}
                placeholder="What's your question?"
                className="input-dark mt-1"
                data-testid="new-post-title"
              />
              {/* Live similar posts search */}
              <SimilarPostsSuggestion
                query={newPost.title}
                navigate={navigate}
                onSelect={() => setNewPostOpen(false)}
              />
            </div>
            <div>
              <Label className="text-zinc-300">Content</Label>
              <Textarea
                value={newPost.content}
                onChange={e => setNewPost(p => ({ ...p, content: e.target.value }))}
                placeholder="Describe your question in detail..."
                rows={5}
                className="input-dark mt-1 resize-none"
                data-testid="new-post-content"
              />
            </div>
            <div>
              <Label className="text-zinc-300">Category</Label>
              <select
                value={newPost.category}
                onChange={e => setNewPost(p => ({ ...p, category: e.target.value }))}
                className="w-full mt-1 rounded-md border border-zinc-700 bg-zinc-800 text-zinc-200 px-3 py-2 text-sm"
                data-testid="new-post-category"
              >
                <option value="general">General</option>
                <option value="trading">Trading</option>
                <option value="technical">Technical</option>
                <option value="announcements">Announcements</option>
              </select>
            </div>
            <div>
              <Label className="text-zinc-300">Tags (comma separated)</Label>
              <Input
                value={newPost.tags}
                onChange={e => setNewPost(p => ({ ...p, tags: e.target.value }))}
                placeholder="e.g. trading, signals, lot-size"
                className="input-dark mt-1"
                data-testid="new-post-tags"
              />
            </div>
            <div>
              <Label className="text-zinc-300 flex items-center gap-1.5">
                <ImageIcon className="w-3.5 h-3.5" /> Attach Images (optional)
              </Label>
              <div className="mt-2">
                <ForumImageUpload
                  images={newPost.images}
                  onChange={(imgs) => setNewPost(p => ({ ...p, images: imgs }))}
                  folder="forum/posts"
                  maxImages={4}
                  disabled={creating}
                />
              </div>
            </div>
          </div>
          {/* Duplicate post warning */}
          {similarWarning && (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-3 space-y-2" data-testid="duplicate-warning">
              <p className="text-xs font-medium text-amber-400 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5" /> Similar posts found — your question may already be answered!
                {similarWarning.ai && <span className="ml-1 text-[9px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">AI-powered</span>}
              </p>
              <div className="max-h-32 overflow-y-auto space-y-1">
                {(similarWarning.results || similarWarning).map(r => (
                  <button
                    key={r.id}
                    onClick={() => { setNewPostOpen(false); setSimilarWarning(null); navigate(`/forum/${r.id}`); }}
                    className="w-full text-left px-3 py-2 rounded bg-zinc-800/50 border border-zinc-700 hover:border-amber-500/30 text-xs text-zinc-300 transition-all"
                    data-testid={`warning-post-${r.id}`}
                  >
                    <div className="flex items-center gap-2">
                      <span className={`text-[9px] px-1.5 py-0.5 rounded-full border ${STATUS_COLORS[r.status]}`}>
                        {r.status === 'open' ? 'Open' : 'Solved'}
                      </span>
                      {r.best_answer_id && <Award className="w-3 h-3 text-amber-400" />}
                      <span className="truncate">{r.title}</span>
                    </div>
                  </button>
                ))}
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={() => { setSimilarWarning(null); setNewPost(p => ({ ...p, _confirmedDuplicate: true })); }}
                className="w-full text-xs btn-secondary text-zinc-400"
                data-testid="continue-posting-btn"
              >
                My question is different — continue posting
              </Button>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setNewPostOpen(false)} className="btn-secondary">Cancel</Button>
            <Button onClick={handleCreatePost} disabled={creating} className="bg-blue-600 hover:bg-blue-700 gap-2" data-testid="submit-post-btn">
              {creating ? <><Loader2 className="w-4 h-4 animate-spin" /> Posting...</> : 'Post'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
