import React, { useState, useEffect, useCallback } from 'react';
import { quizAPI } from '../../lib/api';
import { useAuth } from '../../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { toast } from 'sonner';
import {
  Loader2, Sparkles, Check, X, Send, HelpCircle, RefreshCw,
  BookOpen, Filter, CheckCircle2, XCircle, Eye, Pencil, Save, AlertTriangle
} from 'lucide-react';

const TOPICS = ['Rewards', 'Hub', 'Website', 'Merin', 'MOIL10'];
const STATUS_COLORS = {
  pending: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  approved: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  rejected: 'text-red-400 bg-red-500/10 border-red-500/20',
};

const QuizManagementPage = () => {
  const { isMasterAdmin } = useAuth();
  const [pool, setPool] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [statusFilter, setStatusFilter] = useState('pending');
  const [topicFilter, setTopicFilter] = useState('');
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState(new Set());
  const [genTopic, setGenTopic] = useState('');
  const [genCount, setGenCount] = useState(5);
  const [genDifficulty, setGenDifficulty] = useState(1);
  const [publishDate, setPublishDate] = useState(new Date().toISOString().split('T')[0]);

  // Published quizzes for today
  const [published, setPublished] = useState([]);
  const [viewingPublished, setViewingPublished] = useState(false);

  // Edit modal
  const [editQuiz, setEditQuiz] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [saving, setSaving] = useState(false);
  const [verification, setVerification] = useState(null);

  const loadPool = useCallback(async () => {
    setLoading(true);
    try {
      const res = await quizAPI.getPool({
        status: statusFilter || undefined,
        topic: topicFilter || undefined,
        page,
        page_size: 20,
      });
      setPool(res.data.quizzes);
      setTotal(res.data.total);
    } catch {
      toast.error('Failed to load quiz pool');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, topicFilter, page]);

  const loadPublished = useCallback(async () => {
    try {
      const res = await quizAPI.getPublished(publishDate);
      setPublished(res.data.quizzes);
    } catch {
      toast.error('Failed to load published quizzes');
    }
  }, [publishDate]);

  useEffect(() => { loadPool(); }, [loadPool]);
  useEffect(() => { loadPublished(); }, [loadPublished]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const res = await quizAPI.generate({
        count: genCount,
        topic: genTopic || null,
        difficulty: genDifficulty,
      });
      toast.success(`Generated ${res.data.count} quiz questions`);
      setStatusFilter('pending');
      loadPool();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Generation failed');
    } finally {
      setGenerating(false);
    }
  };

  const handleApprove = async () => {
    if (selected.size === 0) return;
    try {
      const res = await quizAPI.approve([...selected]);
      toast.success(`Approved ${res.data.approved} questions`);
      setSelected(new Set());
      loadPool();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Approval failed');
    }
  };

  const handleReject = async () => {
    if (selected.size === 0) return;
    try {
      const res = await quizAPI.reject([...selected]);
      toast.success(`Rejected ${res.data.rejected} questions`);
      setSelected(new Set());
      loadPool();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Rejection failed');
    }
  };

  const handlePublish = async () => {
    if (selected.size === 0) {
      toast.error('Select approved quizzes to publish');
      return;
    }
    setPublishing(true);
    try {
      const res = await quizAPI.publish([...selected], publishDate);
      toast.success(`Published ${res.data.published} quizzes for ${publishDate}`);
      setSelected(new Set());
      loadPool();
      loadPublished();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Publishing failed');
    } finally {
      setPublishing(false);
    }
  };

  const toggleSelect = (id) => {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const openEdit = (quiz, e) => {
    e.stopPropagation();
    setEditQuiz(quiz);
    setEditForm({
      question: quiz.question,
      correct_answer: quiz.correct_answer,
      wrong_answers: [...(quiz.wrong_answers || [])],
      explanation: quiz.explanation || '',
      platform_topic: quiz.platform_topic || 'Hub',
    });
    setVerification(null);
  };

  const handleSaveEdit = async () => {
    if (!editQuiz) return;
    setSaving(true);
    setVerification(null);
    try {
      const res = await quizAPI.edit(editQuiz.id, editForm);
      setVerification(res.data.verification);
      if (res.data.verification?.verified) {
        toast.success('Quiz saved & AI verified');
        setEditQuiz(null);
        loadPool();
        loadPublished();
      } else {
        toast.warning('Saved but AI flagged issues — review the note below');
        loadPool();
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const selectAll = () => {
    if (selected.size === pool.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(pool.map(q => q.id)));
    }
  };

  return (
    <div className="space-y-6" data-testid="quiz-management-page">
      {/* Generate Section */}
      <Card className="glass-card">
        <CardHeader className="pb-3">
          <CardTitle className="text-white flex items-center gap-2 text-lg">
            <Sparkles className="w-5 h-5 text-blue-400" /> Generate Quiz Questions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3 items-end">
            <div>
              <label className="text-xs text-zinc-400 mb-1 block">Topic</label>
              <select
                value={genTopic}
                onChange={e => setGenTopic(e.target.value)}
                className="h-9 px-3 rounded-md bg-zinc-800 border border-zinc-700 text-white text-sm"
                data-testid="gen-topic-select"
              >
                <option value="">All Topics</option>
                {TOPICS.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-zinc-400 mb-1 block">Count</label>
              <Input
                type="number"
                min={1}
                max={10}
                value={genCount}
                onChange={e => setGenCount(parseInt(e.target.value) || 5)}
                className="w-20 h-9 bg-zinc-800 border-zinc-700 text-white"
                data-testid="gen-count-input"
              />
            </div>
            <div>
              <label className="text-xs text-zinc-400 mb-1 block">Difficulty</label>
              <select
                value={genDifficulty}
                onChange={e => setGenDifficulty(parseInt(e.target.value))}
                className="h-9 px-3 rounded-md bg-zinc-800 border border-zinc-700 text-white text-sm"
                data-testid="gen-difficulty-select"
              >
                {[1,2,3,4,5,6,7].map(d => <option key={d} value={d}>Level {d}</option>)}
              </select>
            </div>
            <Button
              onClick={handleGenerate}
              disabled={generating}
              className="btn-primary h-9 gap-2"
              data-testid="generate-quiz-btn"
            >
              {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              Generate
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Published for today */}
      <Card className="glass-card">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-white flex items-center gap-2 text-base">
              <Send className="w-4 h-4 text-emerald-400" /> Published Quizzes
            </CardTitle>
            <div className="flex items-center gap-2">
              <Input
                type="date"
                value={publishDate}
                onChange={e => setPublishDate(e.target.value)}
                className="h-8 w-36 bg-zinc-800 border-zinc-700 text-white text-xs"
                data-testid="publish-date-input"
              />
              <Button
                size="sm"
                variant="outline"
                onClick={() => setViewingPublished(!viewingPublished)}
                className="h-8 text-xs gap-1"
                data-testid="toggle-published-btn"
              >
                <Eye className="w-3 h-3" /> {viewingPublished ? 'Hide' : 'Show'} ({published.length})
              </Button>
            </div>
          </div>
        </CardHeader>
        {viewingPublished && (
          <CardContent>
            {published.length === 0 ? (
              <p className="text-sm text-zinc-500">No quizzes published for {publishDate}</p>
            ) : (
              <div className="space-y-2">
                {published.map((q, i) => (
                  <div key={q.id} className="p-3 rounded-lg bg-zinc-900/40 border border-zinc-800">
                    <p className="text-sm text-white font-medium">{i+1}. {q.question}</p>
                    <p className="text-xs text-emerald-400 mt-1">Answer: {q.correct_answer}</p>
                    <p className="text-xs text-zinc-500 mt-0.5">{q.explanation}</p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        )}
      </Card>

      {/* Quiz Pool */}
      <Card className="glass-card">
        <CardHeader className="pb-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <CardTitle className="text-white flex items-center gap-2 text-base">
              <BookOpen className="w-4 h-4 text-purple-400" /> Quiz Pool
              <span className="text-xs text-zinc-500 font-normal">({total} total)</span>
            </CardTitle>
            <div className="flex items-center gap-2 flex-wrap">
              {/* Filters */}
              <div className="flex rounded-lg overflow-hidden border border-zinc-700">
                {['pending', 'approved', 'rejected', ''].map(s => (
                  <button
                    key={s || 'all'}
                    onClick={() => { setStatusFilter(s); setPage(1); }}
                    className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                      statusFilter === s ? 'bg-blue-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-white'
                    }`}
                    data-testid={`filter-${s || 'all'}-btn`}
                  >
                    {s || 'All'}
                  </button>
                ))}
              </div>
              <select
                value={topicFilter}
                onChange={e => { setTopicFilter(e.target.value); setPage(1); }}
                className="h-8 px-2 rounded-md bg-zinc-800 border border-zinc-700 text-white text-xs"
              >
                <option value="">All Topics</option>
                {TOPICS.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Bulk actions */}
          {selected.size > 0 && (
            <div className="flex items-center gap-2 mb-3 p-2 rounded-lg bg-blue-500/10 border border-blue-500/20">
              <span className="text-xs text-blue-300">{selected.size} selected</span>
              <div className="flex gap-1.5 ml-auto">
                {isMasterAdmin() && (
                  <Button size="sm" onClick={handleApprove} className="h-7 text-xs bg-emerald-600 hover:bg-emerald-700 gap-1" data-testid="bulk-approve-btn">
                    <CheckCircle2 className="w-3 h-3" /> Approve
                  </Button>
                )}
                <Button size="sm" onClick={handleReject} variant="outline" className="h-7 text-xs border-red-500/50 text-red-400 hover:bg-red-500/20 gap-1" data-testid="bulk-reject-btn">
                  <XCircle className="w-3 h-3" /> Reject
                </Button>
                {statusFilter === 'approved' && (
                  <Button size="sm" onClick={handlePublish} disabled={publishing} className="h-7 text-xs bg-blue-600 hover:bg-blue-700 gap-1" data-testid="bulk-publish-btn">
                    {publishing ? <Loader2 className="w-3 h-3 animate-spin" /> : <Send className="w-3 h-3" />}
                    Publish for {publishDate}
                  </Button>
                )}
              </div>
            </div>
          )}

          {loading ? (
            <div className="flex justify-center py-8"><Loader2 className="w-5 h-5 animate-spin text-blue-400" /></div>
          ) : pool.length === 0 ? (
            <div className="text-center py-8 text-zinc-500">
              <HelpCircle className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p className="text-sm">No quizzes found. Generate some above!</p>
            </div>
          ) : (
            <>
              <div className="flex items-center mb-2">
                <button
                  onClick={selectAll}
                  className="text-xs text-zinc-400 hover:text-white transition-colors"
                  data-testid="select-all-btn"
                >
                  {selected.size === pool.length ? 'Deselect All' : 'Select All'}
                </button>
              </div>
              <div className="space-y-2">
                {pool.map((quiz) => (
                  <div
                    key={quiz.id}
                    className={`p-3 rounded-lg border transition-all cursor-pointer ${
                      selected.has(quiz.id) ? 'bg-blue-500/10 border-blue-500/30' : 'bg-zinc-900/40 border-zinc-800 hover:border-zinc-700'
                    }`}
                    onClick={() => toggleSelect(quiz.id)}
                    data-testid={`quiz-pool-${quiz.id}`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`w-5 h-5 mt-0.5 rounded border-2 flex items-center justify-center shrink-0 transition-colors ${
                        selected.has(quiz.id) ? 'border-blue-400 bg-blue-500' : 'border-zinc-600'
                      }`}>
                        {selected.has(quiz.id) && <Check className="w-3 h-3 text-white" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-sm text-white font-medium">{quiz.question}</p>
                          <button
                            onClick={(e) => openEdit(quiz, e)}
                            className="shrink-0 p-1.5 rounded-md hover:bg-zinc-700 text-zinc-400 hover:text-white transition-colors"
                            data-testid={`edit-quiz-${quiz.id}`}
                            title="Edit quiz"
                          >
                            <Pencil className="w-3.5 h-3.5" />
                          </button>
                        </div>
                        <p className="text-xs text-emerald-400 mt-1">Correct: {quiz.correct_answer}</p>
                        <p className="text-xs text-zinc-500 mt-0.5">{quiz.explanation}</p>
                        {quiz.ai_verification && !quiz.ai_verification.verified && (
                          <div className="flex items-center gap-1 mt-1 text-[10px] text-amber-400">
                            <AlertTriangle className="w-3 h-3" /> AI flagged: {quiz.ai_verification.note}
                          </div>
                        )}
                        <div className="flex items-center gap-2 mt-2 flex-wrap">
                          <span className={`text-[10px] px-2 py-0.5 rounded-full border ${STATUS_COLORS[quiz.status]}`}>
                            {quiz.status}
                          </span>
                          <span className="text-[10px] px-2 py-0.5 rounded-full border text-blue-400 bg-blue-500/10 border-blue-500/20">
                            {quiz.platform_topic}
                          </span>
                          <span className="text-[10px] text-zinc-600">Lvl {quiz.difficulty}</span>
                          {quiz.wrong_answers?.map((wa, i) => (
                            <span key={i} className="text-[10px] text-zinc-600">{String.fromCharCode(66 + i)}: {wa}</span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              {total > 20 && (
                <div className="flex justify-between items-center mt-4 text-sm text-zinc-400">
                  <span>Page {page} of {Math.ceil(total / 20)}</span>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>Prev</Button>
                    <Button size="sm" variant="outline" onClick={() => setPage(p => p + 1)} disabled={page >= Math.ceil(total / 20)}>Next</Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Edit Quiz Modal */}
      {editQuiz && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setEditQuiz(null)}>
          <div
            className="w-full max-w-lg mx-4 p-5 rounded-xl bg-zinc-900 border border-zinc-700 space-y-4 max-h-[80vh] overflow-y-auto"
            onClick={e => e.stopPropagation()}
            data-testid="edit-quiz-modal"
          >
            <div className="flex items-center justify-between">
              <h3 className="text-white font-semibold flex items-center gap-2">
                <Pencil className="w-4 h-4 text-blue-400" /> Edit Quiz Question
              </h3>
              <button onClick={() => setEditQuiz(null)} className="text-zinc-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <label className="text-xs text-zinc-400 mb-1 block">Question</label>
              <textarea
                value={editForm.question || ''}
                onChange={e => setEditForm(p => ({ ...p, question: e.target.value }))}
                className="w-full h-20 px-3 py-2 rounded-md bg-zinc-800 border border-zinc-700 text-white text-sm resize-none"
                data-testid="edit-question-input"
              />
            </div>

            <div>
              <label className="text-xs text-zinc-400 mb-1 block">Correct Answer</label>
              <Input
                value={editForm.correct_answer || ''}
                onChange={e => setEditForm(p => ({ ...p, correct_answer: e.target.value }))}
                className="bg-zinc-800 border-zinc-700 text-white"
                data-testid="edit-correct-answer-input"
              />
            </div>

            <div>
              <label className="text-xs text-zinc-400 mb-1 block">Wrong Answers</label>
              {(editForm.wrong_answers || []).map((wa, i) => (
                <Input
                  key={i}
                  value={wa}
                  onChange={e => {
                    const updated = [...(editForm.wrong_answers || [])];
                    updated[i] = e.target.value;
                    setEditForm(p => ({ ...p, wrong_answers: updated }));
                  }}
                  className="bg-zinc-800 border-zinc-700 text-white mb-1.5"
                  placeholder={`Wrong answer ${i + 1}`}
                  data-testid={`edit-wrong-answer-${i}`}
                />
              ))}
            </div>

            <div>
              <label className="text-xs text-zinc-400 mb-1 block">Explanation</label>
              <textarea
                value={editForm.explanation || ''}
                onChange={e => setEditForm(p => ({ ...p, explanation: e.target.value }))}
                className="w-full h-16 px-3 py-2 rounded-md bg-zinc-800 border border-zinc-700 text-white text-sm resize-none"
                data-testid="edit-explanation-input"
              />
            </div>

            <div>
              <label className="text-xs text-zinc-400 mb-1 block">Platform Topic</label>
              <select
                value={editForm.platform_topic || 'Hub'}
                onChange={e => setEditForm(p => ({ ...p, platform_topic: e.target.value }))}
                className="h-9 w-full px-3 rounded-md bg-zinc-800 border border-zinc-700 text-white text-sm"
              >
                {TOPICS.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>

            {/* AI Verification Result */}
            {verification && (
              <div className={`p-3 rounded-lg text-xs ${
                verification.verified
                  ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-300'
                  : 'bg-amber-500/10 border border-amber-500/20 text-amber-300'
              }`}>
                <div className="flex items-center gap-1.5 font-medium mb-1">
                  {verification.verified
                    ? <><CheckCircle2 className="w-3.5 h-3.5" /> AI Verified</>
                    : <><AlertTriangle className="w-3.5 h-3.5" /> AI Flagged Issues</>
                  }
                </div>
                {verification.note && <p>{verification.note}</p>}
              </div>
            )}

            <div className="flex gap-2 pt-1">
              <Button
                variant="outline"
                onClick={() => setEditQuiz(null)}
                className="flex-1 h-9"
              >
                Cancel
              </Button>
              <Button
                onClick={handleSaveEdit}
                disabled={saving}
                className="flex-1 h-9 btn-primary gap-2"
                data-testid="save-edit-btn"
              >
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                Save & Verify
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QuizManagementPage;
