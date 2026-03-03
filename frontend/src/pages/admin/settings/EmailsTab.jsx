import React, { useState, useEffect } from 'react';
import { settingsAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { toast } from 'sonner';
import {
  Mail, FileText, Loader2, Code, Eye as EyePreview, Send, Trash2,
  ChevronLeft, ChevronRight, Clock, XCircle
} from 'lucide-react';

export function EmailsTab() {
  const { user } = useAuth();
  const [emailTemplates, setEmailTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [savingTemplate, setSavingTemplate] = useState(false);
  const [editorMode, setEditorMode] = useState('code');
  const [testEmailDialogOpen, setTestEmailDialogOpen] = useState(false);
  const [testEmailAddress, setTestEmailAddress] = useState('');
  const [sendingTestEmail, setSendingTestEmail] = useState(false);
  const [testVariableValues, setTestVariableValues] = useState({});
  const [emailHistory, setEmailHistory] = useState([]);
  const [emailHistoryPage, setEmailHistoryPage] = useState(1);
  const [emailHistoryTotal, setEmailHistoryTotal] = useState(0);
  const [emailHistoryLoading, setEmailHistoryLoading] = useState(false);
  const [clearingHistory, setClearingHistory] = useState(false);

  useEffect(() => {
    loadEmailTemplates();
    loadEmailHistory();
  }, []);

  const loadEmailTemplates = async () => {
    try {
      const res = await settingsAPI.getEmailTemplates();
      setEmailTemplates(res.data.templates || []);
    } catch (error) {
      console.error('Failed to load email templates:', error);
    }
  };

  const loadEmailHistory = async (page = 1) => {
    setEmailHistoryLoading(true);
    try {
      const res = await settingsAPI.getEmailHistory(page);
      setEmailHistory(res.data.emails || []);
      setEmailHistoryTotal(res.data.total || 0);
      setEmailHistoryPage(page);
    } catch (error) {
      console.error('Failed to load email history:', error);
    } finally {
      setEmailHistoryLoading(false);
    }
  };

  const handleClearEmailHistory = async () => {
    if (!window.confirm('Are you sure you want to clear all email history? This cannot be undone.')) return;
    setClearingHistory(true);
    try {
      await settingsAPI.clearEmailHistory();
      toast.success('Email history cleared');
      loadEmailHistory();
    } catch (error) {
      toast.error('Failed to clear email history');
    } finally {
      setClearingHistory(false);
    }
  };

  const handleSaveTemplate = async () => {
    if (!editingTemplate) return;
    setSavingTemplate(true);
    try {
      await settingsAPI.updateEmailTemplate(editingTemplate.type, {
        subject: editingTemplate.subject,
        body: editingTemplate.body,
        variables: editingTemplate.variables,
      });
      toast.success('Email template saved!');
      setEditingTemplate(null);
      loadEmailTemplates();
    } catch (error) {
      toast.error('Failed to save template');
    } finally {
      setSavingTemplate(false);
    }
  };

  const handleOpenTestEmail = () => {
    if (!editingTemplate) return;
    const sampleValues = {};
    (editingTemplate.variables || []).forEach((v) => {
      if (v.includes('name')) sampleValues[v] = 'John Doe';
      else if (v.includes('email')) sampleValues[v] = 'john@example.com';
      else if (v.includes('amount') || v.includes('balance')) sampleValues[v] = '$1,250.00';
      else if (v.includes('date')) sampleValues[v] = new Date().toLocaleDateString();
      else if (v.includes('link') || v.includes('url')) sampleValues[v] = 'https://example.com/action';
      else if (v.includes('code')) sampleValues[v] = 'ABC123';
      else if (v.includes('profit')) sampleValues[v] = '$150.00';
      else if (v.includes('product')) sampleValues[v] = 'MOIL10';
      else if (v.includes('direction')) sampleValues[v] = 'BUY';
      else if (v.includes('time')) sampleValues[v] = '14:00 PHT';
      else sampleValues[v] = `Sample ${v}`;
    });
    setTestVariableValues(sampleValues);
    setTestEmailAddress(user?.email || '');
    setTestEmailDialogOpen(true);
  };

  const getPreviewContent = (content, variables = {}) => {
    let result = content;
    Object.entries(variables).forEach(([key, value]) => {
      result = result.replace(new RegExp(`\\{\\{${key}\\}\\}`, 'g'), value);
    });
    return result;
  };

  const handleSendTestEmail = async () => {
    if (!editingTemplate || !testEmailAddress) return;
    setSendingTestEmail(true);
    try {
      const processedSubject = getPreviewContent(editingTemplate.subject, testVariableValues);
      const processedBody = getPreviewContent(editingTemplate.body, testVariableValues);
      await settingsAPI.sendTestEmail({
        to: testEmailAddress,
        subject: processedSubject,
        body: processedBody,
        template_type: editingTemplate.type,
      });
      toast.success('Test email sent successfully!');
      setTestEmailDialogOpen(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send test email');
    } finally {
      setSendingTestEmail(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-cyan-400" /> Email Templates
          </CardTitle>
          <p className="text-sm text-zinc-500">Customize email templates for notifications and communications</p>
        </CardHeader>
        <CardContent>
          {emailTemplates.length === 0 ? (
            <div className="text-center py-8">
              <Mail className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
              <p className="text-zinc-500">No email templates configured</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Template List */}
              <div className="space-y-3 max-h-[500px] overflow-y-auto">
                {emailTemplates.map((template) => (
                  <div
                    key={template.type}
                    className={`p-4 rounded-lg border transition-all cursor-pointer ${
                      selectedTemplate?.type === template.type
                        ? 'bg-blue-500/10 border-blue-500/30'
                        : 'bg-zinc-900/50 border-zinc-800 hover:border-zinc-700'
                    }`}
                    onClick={() => {
                      setSelectedTemplate(template);
                      setEditingTemplate({ ...template });
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-white font-medium capitalize">{template.type.replace(/_/g, ' ')}</p>
                        <p className="text-xs text-zinc-500 mt-0.5 truncate max-w-[200px]">{template.subject}</p>
                      </div>
                      <Button variant="ghost" size="sm" className="text-blue-400 hover:text-blue-300 shrink-0">
                        Edit
                      </Button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Edit Template Panel */}
              <div className="lg:border-l lg:border-zinc-800 lg:pl-6">
                {editingTemplate ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-white font-medium capitalize">Edit: {editingTemplate.type.replace(/_/g, ' ')}</h3>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant={editorMode === 'code' ? 'default' : 'outline'}
                          onClick={() => setEditorMode('code')}
                          className={editorMode === 'code' ? 'bg-blue-600' : 'btn-secondary'}
                        >
                          <Code className="w-3 h-3 mr-1" /> Code
                        </Button>
                        <Button
                          size="sm"
                          variant={editorMode === 'preview' ? 'default' : 'outline'}
                          onClick={() => setEditorMode('preview')}
                          className={editorMode === 'preview' ? 'bg-blue-600' : 'btn-secondary'}
                        >
                          <EyePreview className="w-3 h-3 mr-1" /> Preview
                        </Button>
                      </div>
                    </div>

                    <div>
                      <Label className="text-zinc-400">Subject</Label>
                      <Input
                        value={editingTemplate.subject}
                        onChange={(e) => setEditingTemplate((prev) => ({ ...prev, subject: e.target.value }))}
                        className="input-dark mt-1"
                      />
                    </div>

                    {editorMode === 'code' ? (
                      <div>
                        <Label className="text-zinc-400">Body (HTML)</Label>
                        <textarea
                          value={editingTemplate.body}
                          onChange={(e) => setEditingTemplate((prev) => ({ ...prev, body: e.target.value }))}
                          className="w-full h-64 mt-1 rounded-lg border border-zinc-700 bg-zinc-900 text-zinc-300 p-3 font-mono text-xs resize-none focus:outline-none focus:border-blue-500"
                        />
                      </div>
                    ) : (
                      <div>
                        <Label className="text-zinc-400">Preview</Label>
                        <div
                          className="mt-1 p-4 rounded-lg border border-zinc-700 bg-white min-h-[256px] max-h-[400px] overflow-y-auto"
                          dangerouslySetInnerHTML={{ __html: editingTemplate.body }}
                        />
                      </div>
                    )}

                    {editingTemplate.variables?.length > 0 && (
                      <div className="p-3 rounded-lg bg-zinc-800/50 border border-zinc-700">
                        <p className="text-xs text-zinc-400 mb-1">Available Variables:</p>
                        <div className="flex flex-wrap gap-1">
                          {editingTemplate.variables.map((v) => (
                            <code key={v} className="text-[10px] bg-zinc-700 text-cyan-400 px-1.5 py-0.5 rounded">
                              {`{{${v}}}`}
                            </code>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="flex gap-2">
                      <Button onClick={handleSaveTemplate} disabled={savingTemplate} className="btn-primary gap-2 flex-1">
                        {savingTemplate ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                        Save Template
                      </Button>
                      <Button onClick={handleOpenTestEmail} variant="outline" className="btn-secondary gap-2">
                        <Send className="w-4 h-4" /> Test
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full text-zinc-500">
                    <p className="text-sm">Select a template to edit</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Email History */}
      <Card className="glass-card">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-zinc-400" /> Email History
            </CardTitle>
            <Button
              onClick={handleClearEmailHistory}
              disabled={clearingHistory || emailHistory.length === 0}
              variant="outline"
              size="sm"
              className="btn-secondary text-red-400 hover:text-red-300 gap-2"
            >
              {clearingHistory ? <Loader2 className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3" />}
              Clear
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {emailHistoryLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-zinc-400" />
            </div>
          ) : emailHistory.length === 0 ? (
            <p className="text-center text-zinc-500 py-8">No emails sent yet</p>
          ) : (
            <>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {emailHistory.map((email, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-zinc-900/50 border border-zinc-800 flex items-center justify-between">
                    <div className="min-w-0 flex-1">
                      <p className="text-sm text-white truncate">{email.subject}</p>
                      <p className="text-xs text-zinc-500">
                        To: {email.to} &bull; {new Date(email.sent_at).toLocaleString()}
                      </p>
                    </div>
                    {email.status === 'sent' ? (
                      <span className="text-xs text-emerald-400 shrink-0 ml-2">Sent</span>
                    ) : (
                      <span className="text-xs text-red-400 shrink-0 ml-2">Failed</span>
                    )}
                  </div>
                ))}
              </div>
              {emailHistoryTotal > 10 && (
                <div className="flex items-center justify-center gap-2 mt-4">
                  <Button
                    size="sm"
                    variant="outline"
                    className="btn-secondary"
                    disabled={emailHistoryPage <= 1}
                    onClick={() => loadEmailHistory(emailHistoryPage - 1)}
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </Button>
                  <span className="text-xs text-zinc-400">
                    Page {emailHistoryPage} of {Math.ceil(emailHistoryTotal / 10)}
                  </span>
                  <Button
                    size="sm"
                    variant="outline"
                    className="btn-secondary"
                    disabled={emailHistoryPage >= Math.ceil(emailHistoryTotal / 10)}
                    onClick={() => loadEmailHistory(emailHistoryPage + 1)}
                  >
                    <ChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Test Email Dialog */}
      <Dialog open={testEmailDialogOpen} onOpenChange={setTestEmailDialogOpen}>
        <DialogContent className="bg-zinc-900 border-zinc-800 max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-white">Send Test Email</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-zinc-400">Recipient Email</Label>
              <Input value={testEmailAddress} onChange={(e) => setTestEmailAddress(e.target.value)} className="input-dark mt-1" />
            </div>
            {Object.keys(testVariableValues).length > 0 && (
              <div className="space-y-2">
                <Label className="text-zinc-400">Template Variables</Label>
                {Object.entries(testVariableValues).map(([key, value]) => (
                  <div key={key} className="flex items-center gap-2">
                    <code className="text-[10px] bg-zinc-700 text-cyan-400 px-1.5 py-0.5 rounded shrink-0">{`{{${key}}}`}</code>
                    <Input
                      value={value}
                      onChange={(e) => setTestVariableValues((prev) => ({ ...prev, [key]: e.target.value }))}
                      className="input-dark flex-1"
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setTestEmailDialogOpen(false)} className="btn-secondary">
              Cancel
            </Button>
            <Button onClick={handleSendTestEmail} disabled={sendingTestEmail} className="btn-primary gap-2">
              {sendingTestEmail ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              Send Test
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
