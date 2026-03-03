import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useWebSocket } from '@/contexts/WebSocketContext';
import { forumAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { toast } from 'sonner';
import ForumImageUpload from '@/components/ForumImageUpload';
import {
  ArrowLeft, CheckCircle2, Clock, Eye, MessageCircle,
  Award, Star, Loader2, Send, Trash2, Users,
  ThumbsUp, ThumbsDown, ChevronDown, ChevronUp, ImageIcon, X
} from 'lucide-react';

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
            className="w-24 h-24 rounded-lg overflow-hidden border border-zinc-700 hover:border-blue-500 transition-colors"
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
                      idx === activeIndex ? 'bg-blue-500' : 'bg-zinc-600 hover:bg-zinc-500'
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
  if (role === 'basic_admin') return <span className="text-[9px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 font-medium">Admin</span>;
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

  const loadPost = useCallback(async () => {
    try {
      const res = await forumAPI.getPost(postId);
      setPost(res.data);
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
    <div className="space-y-5 pb-20 md:pb-6 max-w-4xl" data-testid="forum-post-page">
      {/* Back button */}
      <button
        onClick={() => navigate('/forum')}
        className="flex items-center gap-1.5 text-sm text-zinc-400 hover:text-white transition-colors"
        data-testid="back-to-forum"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Forum
      </button>

      {/* Post */}
      <div className="p-5 rounded-lg bg-zinc-900/60 border border-zinc-800">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${
                post.status === 'open'
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  : 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'
              }`}>
                {post.status === 'open' ? 'Open' : 'Solved'}
              </span>
              {post.best_answer_id && (
                <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  Has Best Answer
                </span>
              )}
            </div>
            <h1 className="text-lg md:text-xl font-bold text-white">{post.title}</h1>
          </div>
          {canManage && (
            <div className="flex gap-2 flex-shrink-0">
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

        <div className="mt-4 text-sm text-zinc-300 whitespace-pre-wrap">{post.content}</div>

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
        <h2 className="text-sm font-semibold text-zinc-400 mb-3 flex items-center gap-1.5">
          <MessageCircle className="w-4 h-4" /> {post.comments?.length || 0} Comments
        </h2>

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
                <p className="text-sm text-zinc-300 whitespace-pre-wrap">{c.content}</p>

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
                    {c.score !== 0 && (
                      <span className={`font-medium ${c.score > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {c.score > 0 ? '+' : ''}{c.score} score
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1">
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
          <Textarea
            value={comment}
            onChange={e => setComment(e.target.value)}
            placeholder="Write your answer..."
            rows={3}
            className="input-dark resize-none mb-3"
            data-testid="comment-input"
          />
          <div className="mb-3">
            <ForumImageUpload
              images={commentImages}
              onChange={setCommentImages}
              folder="forum/comments"
              maxImages={4}
              disabled={submitting}
            />
          </div>
          <div className="flex justify-end">
            <Button
              onClick={handleComment}
              disabled={submitting || !comment.trim()}
              className="gap-2 bg-blue-600 hover:bg-blue-700"
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
                <Users className="w-4 h-4 text-blue-400" /> Active Collaborators (+15 pts each)
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
                            ? 'bg-blue-500/10 border-blue-500/30 text-blue-400'
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
    </div>
  );
}
