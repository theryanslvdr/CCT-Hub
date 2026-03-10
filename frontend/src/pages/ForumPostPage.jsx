import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useWebSocket } from '@/contexts/WebSocketContext';
import { forumAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { toast } from 'sonner';
import ForumImageUpload from '@/components/ForumImageUpload';
import {
  ArrowLeft, CheckCircle2, Clock, Eye, MessageCircle,
  Award, Star, Loader2, Send, Trash2, Users,
  ThumbsUp, ThumbsDown, ChevronDown, ChevronUp, ImageIcon, X,
  Edit3, Pin, MoreHorizontal, Merge, ShieldCheck, Calendar, Search
} from 'lucide-react';
import { AIForumSummary, AIAnswerSuggestion } from '@/components/AIFeatures';

// Image gallery lightbox component
function ImageGallery({ images }) {
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);

  if (!images || images.length === 0) return null;

  return (
    <>
      <div className="flex flex-wrap gap-2 mt-3">
        {images.map((url, idx) => (
          <button
            key={idx}
            onClick={() => { setActiveIndex(idx); setLightboxOpen(true); }}
            className="w-24 h-24 rounded-lg overflow-hidden border border-zinc-700 hover:border-orange-500 transition-colors"
          >
            <img src={url} alt={`Image ${idx + 1}`} className="w-full h-full object-cover" />
          </button>
        ))}
      </div>

      {/* Lightbox */}
      <Dialog open={lightboxOpen} onOpenChange={setLightboxOpen}>
        <DialogContent className="bg-zinc-900 border-zinc-800 max-w-4xl p-0 overflow-hidden">
          <div className="relative">
            <button
              onClick={() => setLightboxOpen(false)}
              className="absolute top-2 right-2 z-10 w-8 h-8 rounded-full bg-black/60 flex items-center justify-center text-white hover:bg-black/80"
            >
              <X className="w-5 h-5" />
            </button>
            <img 
              src={images[activeIndex]} 
              alt="Full size"
              className="w-full max-h-[80vh] object-contain"
            />
            {images.length > 1 && (
              <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
                {images.map((_, idx) => (
                  <button
                    key={idx}
                    onClick={() => setActiveIndex(idx)}
                    className={`w-2 h-2 rounded-full transition-colors ${
                      idx === activeIndex ? 'bg-orange-500' : 'bg-zinc-600 hover:bg-zinc-500'
                    }`}
                  />
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

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

function RoleBadge({ role }) {
  if (role === 'master_admin') return <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400 font-medium">Admin</span>;
  if (role === 'super_admin') return <span className="text-[9px] px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-400 font-medium">Super</span>;
  if (role === 'basic_admin') return <span className="text-[9px] px-1.5 py-0.5 rounded bg-orange-500/10 text-orange-400 font-medium">Admin</span>;
  return null;
}

function VoterList({ voters, type }) {
  if (!voters || voters.length === 0) return null;
  return (
    <div className="mt-1.5 flex flex-wrap gap-1">
      {voters.map(v => (
        <span
          key={v.user_id}
          className={`text-[10px] px-1.5 py-0.5 rounded ${
            type === 'up' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
          }`}
        >
          {v.name}
        </span>
      ))}
    </div>
  );
}

function VoteButtons({ comment, userId, onVote }) {
  const [expandVoters, setExpandVoters] = useState(false);
  const isOwn = comment.author_id === userId;

  return (
    <div className="flex items-center gap-1">
      <button
        onClick={() => !isOwn && onVote(comment.id, 'up')}
        disabled={isOwn}
        className={`flex items-center gap-1 px-2 py-1 rounded text-xs transition-all ${
          comment.my_vote === 'up'
            ? 'bg-emerald-500/20 text-emerald-400'
            : isOwn
            ? 'text-zinc-600 cursor-not-allowed'
            : 'text-zinc-500 hover:bg-zinc-800 hover:text-emerald-400'
        }`}
        data-testid={`upvote-${comment.id}`}
      >
        <ThumbsUp className="w-3.5 h-3.5" />
        <span>{comment.upvotes || 0}</span>
      </button>
      <button
        onClick={() => !isOwn && onVote(comment.id, 'down')}
        disabled={isOwn}
        className={`flex items-center gap-1 px-2 py-1 rounded text-xs transition-all ${
          comment.my_vote === 'down'
            ? 'bg-red-500/20 text-red-400'
            : isOwn
            ? 'text-zinc-600 cursor-not-allowed'
            : 'text-zinc-500 hover:bg-zinc-800 hover:text-red-400'
        }`}
        data-testid={`downvote-${comment.id}`}
      >
        <ThumbsDown className="w-3.5 h-3.5" />
        <span>{comment.downvotes || 0}</span>
      </button>
      {(comment.upvotes > 0 || comment.downvotes > 0) && (
        <button
          onClick={() => setExpandVoters(!expandVoters)}
          className="text-zinc-600 hover:text-zinc-400 p-1 transition-colors"
          data-testid={`toggle-voters-${comment.id}`}
        >
          {expandVoters ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </button>
      )}
      {expandVoters && (
        <div className="absolute z-10 mt-1 top-full left-0 bg-zinc-800 border border-zinc-700 rounded-lg p-2 min-w-[140px] shadow-xl">
          {comment.up_voters?.length > 0 && (
            <div className="mb-1">
              <p className="text-[9px] text-emerald-400 font-medium mb-0.5">Upvoted</p>
              <VoterList voters={comment.up_voters} type="up" />
            </div>
          )}
          {comment.down_voters?.length > 0 && (
            <div>
              <p className="text-[9px] text-red-400 font-medium mb-0.5">Downvoted</p>
              <VoterList voters={comment.down_voters} type="down" />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ForumPostPage() {
  const { postId } = useParams();
  const { user, isAdmin } = useAuth();
  const { lastForumEvent } = useWebSocket();
  const navigate = useNavigate();

  const [post, setPost] = useState(null);
  const [loading, setLoading] = useState(true);
  const [comment, setComment] = useState('');
  const [commentImages, setCommentImages] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [closing, setClosing] = useState(false);
  const [closeDialogOpen, setCloseDialogOpen] = useState(false);
  const [selectedBestAnswer, setSelectedBestAnswer] = useState(null);
  const [selectedCollaborators, setSelectedCollaborators] = useState([]);
  const [deleting, setDeleting] = useState(false);
  const [editingPost, setEditingPost] = useState(false);
  const [editPostData, setEditPostData] = useState({ title: '', content: '' });
  const [editingCommentId, setEditingCommentId] = useState(null);
  const [editCommentContent, setEditCommentContent] = useState('');
  const [mentionQuery, setMentionQuery] = useState('');
  const [mentionResults, setMentionResults] = useState([]);
  const [showMentions, setShowMentions] = useState(false);
  const commentInputRef = React.useRef(null);

  // Sidebar details
  const [postDetails, setPostDetails] = useState(null);

  // Merge dialog state
  const [mergeDialogOpen, setMergeDialogOpen] = useState(false);
  const [mergeSearchQuery, setMergeSearchQuery] = useState('');
  const [mergeSearchResults, setMergeSearchResults] = useState([]);
  const [mergeTargetId, setMergeTargetId] = useState(null);
  const [merging, setMerging] = useState(false);
  const [mergeSearching, setMergeSearching] = useState(false);

  // Validating solution state
  const [validating, setValidating] = useState(false);

  const isMergeAdmin = user?.role === 'master_admin' || user?.role === 'super_admin';

  const loadPost = useCallback(async () => {
    try {
      const res = await forumAPI.getPost(postId);
      setPost(res.data);
      // Load sidebar details
      forumAPI.getPostDetails(postId).then(r => setPostDetails(r.data)).catch(() => {});
    } catch (e) {
      toast.error('Failed to load post');
      navigate('/forum');
    } finally {
      setLoading(false);
    }
  }, [postId, navigate]);

  useEffect(() => { loadPost(); }, [loadPost]);

  // Real-time: auto-refresh when a WebSocket forum event matches this post
  useEffect(() => {
    if (lastForumEvent && lastForumEvent.post_id === postId) {
      loadPost();
    }
  }, [lastForumEvent, postId, loadPost]);

  const isOP = post?.author_id === user?.id;
  const canManage = isOP || isAdmin();

  const handleComment = async () => {
    if (!comment.trim()) return;
    setSubmitting(true);
    try {
      const images = commentImages.map(img => img.url);
      await forumAPI.createComment(postId, { content: comment, images });
      setComment('');
      setCommentImages([]);
      toast.success('Comment posted');
      loadPost();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to post comment');
    } finally {
      setSubmitting(false);
    }
  };

  const handleVote = async (commentId, voteType) => {
    try {
      await forumAPI.voteComment(commentId, voteType);
      loadPost();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to vote');
    }
  };

  const handleMarkBestAnswer = async (commentId) => {
    try {
      await forumAPI.markBestAnswer(postId, commentId);
      toast.success('Best answer marked!');
      loadPost();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to mark best answer');
    }
  };

  const openCloseDialog = () => {
    setSelectedBestAnswer(post?.best_answer_id || null);
    setSelectedCollaborators([]);
    setCloseDialogOpen(true);
  };

  const handleClosePost = async () => {
    setClosing(true);
    try {
      const res = await forumAPI.closePost(postId, {
        best_answer_id: selectedBestAnswer,
        active_collaborator_ids: selectedCollaborators,
      });
      const awarded = res.data.points_awarded || [];
      if (awarded.length > 0) {
        const summary = awarded.map(a => `${a.name}: +${a.points}pts (${a.reason})`).join(', ');
        toast.success(`Post closed! Points awarded: ${summary}`);
      } else {
        toast.success('Post closed!');
      }
      setCloseDialogOpen(false);
      loadPost();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to close post');
    } finally {
      setClosing(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this post and all its comments?')) return;
    setDeleting(true);
    try {
      await forumAPI.deletePost(postId);
      toast.success('Post deleted');
      navigate('/forum');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to delete post');
    } finally {
      setDeleting(false);
    }
  };

  const handleEditPost = async () => {
    try {
      await forumAPI.editPost(postId, { title: editPostData.title, content: editPostData.content });
      toast.success('Post updated');
      setEditingPost(false);
      loadPost();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to edit post');
    }
  };

  const handleEditComment = async (commentId) => {
    if (!editCommentContent.trim()) return;
    try {
      await forumAPI.editComment(commentId, { content: editCommentContent });
      toast.success('Comment updated');
      setEditingCommentId(null);
      setEditCommentContent('');
      loadPost();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to edit comment');
    }
  };

  const handleDeleteComment = async (commentId) => {
    if (!window.confirm('Delete this comment?')) return;
    try {
      await forumAPI.deleteComment(commentId);
      toast.success('Comment deleted');
      loadPost();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to delete comment');
    }
  };

  const handlePinPost = async () => {
    try {
      await forumAPI.pinPost(postId, !post.pinned);
      toast.success(post.pinned ? 'Post unpinned' : 'Post pinned');
      loadPost();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to pin post');
    }
  };

  // Merge post handlers
  const handleMergeSearch = async (q) => {
    setMergeSearchQuery(q);
    if (q.trim().length < 2) { setMergeSearchResults([]); return; }
    setMergeSearching(true);
    try {
      const res = await forumAPI.searchSimilar(q.trim());
      setMergeSearchResults((res.data.results || []).filter(r => r.id !== postId));
    } catch { setMergeSearchResults([]); }
    finally { setMergeSearching(false); }
  };

  const handleMergePosts = async () => {
    if (!mergeTargetId) { toast.error('Select a target post'); return; }
    if (!window.confirm('Merge this post into the selected target? All comments will be moved. This cannot be undone.')) return;
    setMerging(true);
    try {
      const res = await forumAPI.mergePosts(postId, mergeTargetId);
      toast.success(res.data.message);
      setMergeDialogOpen(false);
      navigate(`/forum/${mergeTargetId}`);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to merge posts');
    } finally { setMerging(false); }
  };

  const handleValidateSolution = async () => {
    setValidating(true);
    try {
      await forumAPI.validateSolution(postId);
      toast.success('Solution marked as still valid');
      loadPost();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to validate solution');
    } finally { setValidating(false); }
  };

  const canEditPost = (isOP && ((Date.now() - new Date(post?.created_at).getTime()) < 86400000)) || isAdmin();
  const canEditComment = (c) => {
    const isAuthor = c.author_id === user?.id;
    const within24h = (Date.now() - new Date(c.created_at).getTime()) < 86400000;
    return (isAuthor && within24h) || isAdmin();
  };

  // @Mention search
  const handleCommentChange = async (e) => {
    const val = e.target.value;
    setComment(val);
    
    const cursorPos = e.target.selectionStart;
    const textBefore = val.substring(0, cursorPos);
    const atMatch = textBefore.match(/@(\w{1,20})$/);
    
    if (atMatch) {
      setMentionQuery(atMatch[1]);
      try {
        const res = await forumAPI.searchUsers(atMatch[1]);
        setMentionResults(res.data.users || []);
        setShowMentions(true);
      } catch { setMentionResults([]); }
    } else {
      setShowMentions(false);
    }
  };

  const insertMention = (userName) => {
    const input = commentInputRef.current;
    if (!input) return;
    const cursorPos = input.selectionStart;
    const textBefore = comment.substring(0, cursorPos);
    const textAfter = comment.substring(cursorPos);
    const newBefore = textBefore.replace(/@\w{1,20}$/, `@${userName} `);
    setComment(newBefore + textAfter);
    setShowMentions(false);
  };

  const getCommenters = () => {
    if (!post?.comments) return [];
    const seen = new Set();
    return post.comments
      .filter(c => c.author_id !== post.author_id && !seen.has(c.author_id) && (seen.add(c.author_id), true))
      .map(c => ({ user_id: c.author_id, name: c.author_name || 'Unknown' }));
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="w-6 h-6 animate-spin text-zinc-500" />
      </div>
    );
  }

  if (!post) return null;

  const commenters = getCommenters();

  return (
    <div className="flex gap-5 pb-20 md:pb-6" data-testid="forum-post-page">
      {/* Main content */}
      <div className="flex-1 min-w-0 space-y-5 max-w-4xl">
      {/* Back button */}
      <button
        onClick={() => navigate('/forum')}
        className="flex items-center gap-1.5 text-sm text-zinc-400 hover:text-white transition-colors"
        data-testid="back-to-forum"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Forum
      </button>

      {/* Post */}
      <div className={`p-5 rounded-lg border ${post.pinned ? 'bg-amber-500/5 border-amber-500/30' : 'bg-zinc-900/60 border-zinc-800'}`}>
        {post.pinned && (
          <div className="flex items-center gap-1.5 mb-2 text-amber-400 text-xs font-medium">
            <Pin className="w-3.5 h-3.5" /> Pinned Post
          </div>
        )}
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${
                post.status === 'open'
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  : 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'
              }`}>
                {post.status === 'open' ? 'Open' : 'Solved'}
              </span>
              {post.category && post.category !== 'general' && (
                <span className="text-[10px] font-medium px-2 py-0.5 rounded-full border bg-orange-500/10 text-orange-400 border-orange-500/15">
                  {post.category}
                </span>
              )}
              {post.best_answer_id && (
                <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  Has Best Answer
                </span>
              )}
              {post.edited && (
                <span className="text-[10px] text-zinc-600 italic">edited</span>
              )}
            </div>
            {editingPost ? (
              <div className="space-y-2">
                <input
                  value={editPostData.title}
                  onChange={e => setEditPostData(p => ({ ...p, title: e.target.value }))}
                  className="w-full rounded-md border border-zinc-700 bg-zinc-800 text-white px-3 py-2 text-sm"
                  data-testid="edit-post-title"
                />
                <Textarea
                  value={editPostData.content}
                  onChange={e => setEditPostData(p => ({ ...p, content: e.target.value }))}
                  rows={5}
                  className="input-dark resize-none"
                  data-testid="edit-post-content"
                />
                <div className="flex gap-2">
                  <Button size="sm" onClick={handleEditPost} className="bg-orange-600 hover:bg-orange-700" data-testid="save-post-edit-btn">Save</Button>
                  <Button size="sm" variant="outline" onClick={() => setEditingPost(false)} className="btn-secondary">Cancel</Button>
                </div>
              </div>
            ) : (
              <h1 className="text-lg md:text-xl font-bold text-white">{post.title}</h1>
            )}
          </div>
          {canManage && !editingPost && (
            <div className="flex gap-2 flex-shrink-0">
              {isMergeAdmin && (
                <Button size="sm" variant="outline" onClick={() => { setMergeDialogOpen(true); setMergeSearchQuery(''); setMergeSearchResults([]); setMergeTargetId(null); }} className="btn-secondary text-orange-400" data-testid="merge-post-btn" title="Merge into another post">
                  <Merge className="w-3.5 h-3.5" />
                </Button>
              )}
              {isAdmin() && (
                <Button size="sm" variant="outline" onClick={handlePinPost} className={`btn-secondary ${post.pinned ? 'text-amber-400' : 'text-zinc-400'}`} data-testid="pin-post-btn" title={post.pinned ? 'Unpin' : 'Pin'}>
                  <Pin className="w-3.5 h-3.5" />
                </Button>
              )}
              {canEditPost && (
                <Button size="sm" variant="outline" onClick={() => { setEditPostData({ title: post.title, content: post.content }); setEditingPost(true); }} className="btn-secondary text-orange-400" data-testid="edit-post-btn">
                  <Edit3 className="w-3.5 h-3.5" />
                </Button>
              )}
              {post.status === 'open' && (
                <Button size="sm" onClick={openCloseDialog} className="gap-1.5 bg-emerald-600 hover:bg-emerald-700" data-testid="close-post-btn">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Close
                </Button>
              )}
              <Button size="sm" variant="outline" onClick={handleDelete} disabled={deleting} className="btn-secondary text-red-400 hover:text-red-300" data-testid="delete-post-btn">
                <Trash2 className="w-3.5 h-3.5" />
              </Button>
            </div>
          )}
        </div>

        {!editingPost && <div className="mt-4 text-sm text-zinc-300 whitespace-pre-wrap">{post.content}</div>}

        {/* Post images */}
        <ImageGallery images={post.images} />

        <div className="flex items-center gap-4 mt-4 text-[11px] text-zinc-500 border-t border-zinc-800 pt-3">
          <span className="flex items-center gap-1">
            <span className="font-medium text-zinc-300">{post.author_name}</span>
            <RoleBadge role={post.author_role} />
          </span>
          <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{timeSince(post.created_at)}</span>
          <span className="flex items-center gap-1"><MessageCircle className="w-3 h-3" />{post.comments?.length || 0} comments</span>
          <span className="flex items-center gap-1"><Eye className="w-3 h-3" />{post.views} views</span>
        </div>

        {post.tags?.length > 0 && (
          <div className="flex gap-1.5 mt-2">
            {post.tags.map(t => (
              <span key={t} className="text-[10px] px-2 py-0.5 rounded bg-zinc-800 text-zinc-400">{t}</span>
            ))}
          </div>
        )}
      </div>

      {/* Comments */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-zinc-400 flex items-center gap-1.5">
            <MessageCircle className="w-4 h-4" /> {post.comments?.length || 0} Comments
          </h2>
          <AIForumSummary postId={postId} commentCount={post.comments?.length || 0} />
        </div>

        {(!post.comments || post.comments.length === 0) ? (
          <p className="text-center text-zinc-600 py-8 text-sm">No comments yet. Be the first to help!</p>
        ) : (
          <div className="space-y-3">
            {post.comments.map(c => (
              <div
                key={c.id}
                className={`p-4 rounded-lg border transition-all ${
                  c.is_best_answer
                    ? 'bg-amber-500/5 border-amber-500/30'
                    : 'bg-zinc-900/40 border-zinc-800'
                }`}
                data-testid={`comment-${c.id}`}
              >
                {c.is_best_answer && (
                  <div className="flex items-center gap-1.5 mb-2 text-amber-400 text-xs font-medium">
                    <Award className="w-3.5 h-3.5" /> Best Answer
                  </div>
                )}

                {editingCommentId === c.id ? (
                  <div className="space-y-2">
                    <Textarea
                      value={editCommentContent}
                      onChange={e => setEditCommentContent(e.target.value)}
                      rows={3}
                      className="input-dark resize-none"
                      data-testid={`edit-comment-input-${c.id}`}
                    />
                    <div className="flex gap-2">
                      <Button size="sm" onClick={() => handleEditComment(c.id)} className="bg-orange-600 hover:bg-orange-700" data-testid={`save-comment-edit-${c.id}`}>Save</Button>
                      <Button size="sm" variant="outline" onClick={() => { setEditingCommentId(null); setEditCommentContent(''); }} className="btn-secondary">Cancel</Button>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-zinc-300 whitespace-pre-wrap">{c.content}</p>
                )}

                {/* Comment images */}
                <ImageGallery images={c.images} />

                {/* Vote + Meta row */}
                <div className="flex items-center justify-between mt-3">
                  <div className="flex items-center gap-3 text-[11px] text-zinc-500">
                    <span className="flex items-center gap-1">
                      <span className="text-zinc-300">{c.author_name}</span>
                      <RoleBadge role={c.author_role} />
                    </span>
                    <span>{timeSince(c.created_at)}</span>
                    {c.edited && <span className="italic text-zinc-600">edited</span>}
                    {c.score !== 0 && (
                      <span className={`font-medium ${c.score > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {c.score > 0 ? '+' : ''}{c.score} score
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1">
                    {/* Edit/Delete Comment */}
                    {canEditComment(c) && editingCommentId !== c.id && (
                      <>
                        <Button
                          size="sm" variant="ghost"
                          onClick={() => { setEditingCommentId(c.id); setEditCommentContent(c.content); }}
                          className="text-xs text-zinc-500 hover:text-orange-400 h-7 px-2"
                          data-testid={`edit-comment-${c.id}`}
                        >
                          <Edit3 className="w-3 h-3" />
                        </Button>
                        <Button
                          size="sm" variant="ghost"
                          onClick={() => handleDeleteComment(c.id)}
                          className="text-xs text-zinc-500 hover:text-red-400 h-7 px-2"
                          data-testid={`delete-comment-${c.id}`}
                        >
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      </>
                    )}
                    {/* Voting */}
                    <div className="relative">
                      <VoteButtons comment={c} userId={user?.id} onVote={handleVote} />
                    </div>
                    {/* Mark best */}
                    {canManage && post.status === 'open' && !c.is_best_answer && c.author_id !== post.author_id && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleMarkBestAnswer(c.id)}
                        className="text-xs text-amber-400 hover:text-amber-300 h-7 px-2"
                        data-testid={`mark-best-${c.id}`}
                      >
                        <Star className="w-3 h-3 mr-1" /> Mark Best
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* New comment box */}
      {post.status === 'open' && (
        <div className="p-4 rounded-lg bg-zinc-900/60 border border-zinc-800">
          <div className="relative">
            <Textarea
              ref={commentInputRef}
              value={comment}
              onChange={handleCommentChange}
              placeholder="Write your answer... Use @name to mention someone"
              rows={3}
              className="input-dark resize-none mb-3"
              data-testid="comment-input"
            />
            {/* @Mention dropdown */}
            {showMentions && mentionResults.length > 0 && (
              <div className="absolute bottom-full left-0 mb-1 w-64 bg-zinc-800 border border-zinc-700 rounded-lg shadow-xl z-20 max-h-40 overflow-y-auto" data-testid="mention-dropdown">
                {mentionResults.map(u => (
                  <button
                    key={u.id}
                    onClick={() => insertMention(u.name || u.email)}
                    className="w-full text-left px-3 py-2 hover:bg-zinc-700 text-sm text-zinc-300 flex items-center gap-2"
                  >
                    <span className="font-medium">{u.name || u.email}</span>
                    {u.role && u.role !== 'member' && <RoleBadge role={u.role} />}
                  </button>
                ))}
              </div>
            )}
          </div>
          <div className="mb-3">
            <ForumImageUpload
              images={commentImages}
              onChange={setCommentImages}
              folder="forum/comments"
              maxImages={4}
              disabled={submitting}
            />
          </div>
          <div className="flex items-center justify-between">
            <AIAnswerSuggestion postId={postId} />
            <Button
              onClick={handleComment}
              disabled={submitting || !comment.trim()}
              className="gap-2 bg-orange-600 hover:bg-orange-700"
              data-testid="submit-comment-btn"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              Reply
            </Button>
          </div>
        </div>
      )}

      {post.status === 'closed' && (
        <div className="text-center py-4 text-sm text-zinc-500 border border-zinc-800 rounded-lg">
          This post has been closed. No new comments can be added.
        </div>
      )}

      </div>{/* end main content */}

      {/* Right Sidebar — Post Details */}
      <aside className="hidden lg:block w-72 flex-shrink-0 space-y-4" data-testid="post-details-sidebar">
        {/* Post Info */}
        <div className="p-4 rounded-lg bg-zinc-900/60 border border-zinc-800">
          <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">Post Info</h3>
          <div className="space-y-2.5 text-xs">
            <div className="flex items-center gap-2 text-zinc-400">
              <Calendar className="w-3.5 h-3.5 flex-shrink-0" />
              <span>Posted {post.created_at ? new Date(post.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : 'Unknown'}</span>
            </div>
            <div className="flex items-center gap-2 text-zinc-400">
              <Eye className="w-3.5 h-3.5 flex-shrink-0" />
              <span>{post.views || 0} views</span>
            </div>
            <div className="flex items-center gap-2 text-zinc-400">
              <MessageCircle className="w-3.5 h-3.5 flex-shrink-0" />
              <span>{post.comments?.length || 0} comments</span>
            </div>
            {post.merged_from && (
              <div className="flex items-center gap-2 text-orange-400">
                <Merge className="w-3.5 h-3.5 flex-shrink-0" />
                <span>Has merged content</span>
              </div>
            )}
          </div>
        </div>

        {/* Solution Validation */}
        {post.status === 'closed' && post.best_answer_id && (
          <div className="p-4 rounded-lg bg-zinc-900/60 border border-zinc-800">
            <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">Solution Status</h3>
            {postDetails?.solution_validated_at ? (
              <p className="text-[11px] text-emerald-400 mb-2 flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5" />
                Validated {timeSince(postDetails.solution_validated_at)}
              </p>
            ) : (
              <p className="text-[11px] text-zinc-500 mb-2">Not yet validated</p>
            )}
            <Button
              size="sm"
              variant="outline"
              onClick={handleValidateSolution}
              disabled={validating}
              className="w-full gap-1.5 text-xs btn-secondary text-emerald-400 hover:text-emerald-300 border-emerald-500/20 hover:border-emerald-500/40"
              data-testid="validate-solution-btn"
            >
              {validating ? <Loader2 className="w-3 h-3 animate-spin" /> : <ShieldCheck className="w-3 h-3" />}
              Solution still valid
            </Button>
          </div>
        )}

        {/* Contributors */}
        {postDetails?.contributors?.length > 0 && (
          <div className="p-4 rounded-lg bg-zinc-900/60 border border-zinc-800">
            <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <Users className="w-3.5 h-3.5" /> Contributors ({postDetails.contributors.length})
            </h3>
            <div className="space-y-1.5">
              {postDetails.contributors.map(c => (
                <div key={c.user_id} className="flex items-center gap-2 text-xs">
                  <span className="text-zinc-300">{c.name}</span>
                  <RoleBadge role={c.role} />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Awards */}
        {postDetails?.awards?.length > 0 && (
          <div className="p-4 rounded-lg bg-zinc-900/60 border border-zinc-800">
            <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <Award className="w-3.5 h-3.5 text-amber-400" /> Awards
            </h3>
            <div className="space-y-1.5">
              {postDetails.awards.map((a, i) => (
                <div key={i} className="flex items-center justify-between text-xs">
                  <span className="text-zinc-300">{a.name}</span>
                  <span className="text-amber-400 font-medium">+{a.points} pts</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </aside>

      {/* Close Post Dialog */}
      <Dialog open={closeDialogOpen} onOpenChange={setCloseDialogOpen}>
        <DialogContent className="bg-zinc-900 border-zinc-800 max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-white">Close Post & Award Points</DialogTitle>
          </DialogHeader>
          <div className="space-y-5">
            {/* Best Answer Selection */}
            <div>
              <p className="text-sm font-medium text-zinc-300 mb-2 flex items-center gap-1.5">
                <Award className="w-4 h-4 text-amber-400" /> Best Answer (+50 pts)
              </p>
              {post.comments?.filter(c => c.author_id !== post.author_id).length === 0 ? (
                <p className="text-xs text-zinc-500">No eligible comments for best answer.</p>
              ) : (
                <div className="space-y-1.5 max-h-40 overflow-y-auto">
                  {post.comments.filter(c => c.author_id !== post.author_id).map(c => (
                    <button
                      key={c.id}
                      onClick={() => setSelectedBestAnswer(selectedBestAnswer === c.id ? null : c.id)}
                      className={`w-full text-left p-2.5 rounded border text-xs transition-all ${
                        selectedBestAnswer === c.id
                          ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                          : 'bg-zinc-800/50 border-zinc-700 text-zinc-400 hover:border-zinc-600'
                      }`}
                      data-testid={`select-best-${c.id}`}
                    >
                      <span className="font-medium text-zinc-300">{c.author_name}</span>
                      {c.score > 0 && <span className="text-emerald-400 ml-1.5">+{c.score}</span>}
                      : {c.content.slice(0, 80)}{c.content.length > 80 ? '...' : ''}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Active Collaborators */}
            <div>
              <p className="text-sm font-medium text-zinc-300 mb-2 flex items-center gap-1.5">
                <Users className="w-4 h-4 text-orange-400" /> Active Collaborators (+15 pts each)
              </p>
              {commenters.length === 0 ? (
                <p className="text-xs text-zinc-500">No collaborators to select.</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {commenters.map(c => {
                    const isBestAuthor = selectedBestAnswer && post.comments.find(
                      cm => cm.id === selectedBestAnswer
                    )?.author_id === c.user_id;
                    return (
                      <button
                        key={c.user_id}
                        onClick={() => {
                          if (isBestAuthor) return;
                          setSelectedCollaborators(prev =>
                            prev.includes(c.user_id)
                              ? prev.filter(id => id !== c.user_id)
                              : [...prev, c.user_id]
                          );
                        }}
                        disabled={isBestAuthor}
                        className={`px-3 py-1.5 rounded-full text-xs border transition-all ${
                          isBestAuthor
                            ? 'bg-amber-500/10 border-amber-500/30 text-amber-400 cursor-not-allowed'
                            : selectedCollaborators.includes(c.user_id)
                            ? 'bg-orange-500/10 border-orange-500/20 text-orange-400'
                            : 'bg-zinc-800 border-zinc-700 text-zinc-400 hover:border-zinc-600'
                        }`}
                        data-testid={`select-collab-${c.user_id}`}
                      >
                        {c.name} {isBestAuthor ? '(Best Answer)' : ''}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Summary */}
            <div className="text-xs text-zinc-500 bg-zinc-800/50 p-3 rounded">
              <p className="font-medium text-zinc-300 mb-1">Points Summary:</p>
              {selectedBestAnswer && <p>Best Answer: +50 pts</p>}
              {selectedCollaborators.length > 0 && <p>Collaborators: +{selectedCollaborators.length * 15} pts ({selectedCollaborators.length} people)</p>}
              {!selectedBestAnswer && selectedCollaborators.length === 0 && <p>No points will be awarded.</p>}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCloseDialogOpen(false)} className="btn-secondary">Cancel</Button>
            <Button onClick={handleClosePost} disabled={closing} className="gap-2 bg-emerald-600 hover:bg-emerald-700" data-testid="confirm-close-btn">
              {closing ? <><Loader2 className="w-4 h-4 animate-spin" /> Closing...</> : <><CheckCircle2 className="w-4 h-4" /> Close & Award Points</>}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Merge Post Dialog */}
      <Dialog open={mergeDialogOpen} onOpenChange={setMergeDialogOpen}>
        <DialogContent className="bg-zinc-900 border-zinc-800 max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Merge className="w-5 h-5 text-orange-400" /> Merge Post
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-xs text-zinc-400">
              Merge "<span className="text-zinc-200">{post.title}</span>" into another post.
              All comments will be moved to the target. The original poster gets 8 pts.
            </p>
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
              <Input
                value={mergeSearchQuery}
                onChange={e => handleMergeSearch(e.target.value)}
                placeholder="Search for target post..."
                className="pl-9 input-dark"
                data-testid="merge-search-input"
              />
            </div>
            {mergeSearching && (
              <div className="flex justify-center py-3"><Loader2 className="w-4 h-4 animate-spin text-zinc-500" /></div>
            )}
            {mergeSearchResults.length > 0 && (
              <div className="max-h-48 overflow-y-auto space-y-1.5">
                {mergeSearchResults.map(r => (
                  <button
                    key={r.id}
                    onClick={() => setMergeTargetId(mergeTargetId === r.id ? null : r.id)}
                    className={`w-full text-left p-3 rounded border text-xs transition-all ${
                      mergeTargetId === r.id
                        ? 'bg-orange-500/10 border-orange-500/30 text-orange-300'
                        : 'bg-zinc-800/50 border-zinc-700 text-zinc-400 hover:border-zinc-600'
                    }`}
                    data-testid={`merge-target-${r.id}`}
                  >
                    <div className="flex items-center gap-2">
                      <span className={`text-[9px] px-1.5 py-0.5 rounded-full border ${r.status === 'open' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'}`}>
                        {r.status === 'open' ? 'Open' : 'Solved'}
                      </span>
                      <span className="text-zinc-200 truncate flex-1">{r.title}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-zinc-500">
                      <span className="flex items-center gap-0.5"><MessageCircle className="w-2.5 h-2.5" />{r.comment_count || 0}</span>
                      <span>{timeSince(r.created_at)}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setMergeDialogOpen(false)} className="btn-secondary">Cancel</Button>
            <Button onClick={handleMergePosts} disabled={merging || !mergeTargetId} className="gap-2 bg-orange-600 hover:bg-orange-700" data-testid="confirm-merge-btn">
              {merging ? <><Loader2 className="w-4 h-4 animate-spin" /> Merging...</> : <><Merge className="w-4 h-4" /> Merge</>}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
