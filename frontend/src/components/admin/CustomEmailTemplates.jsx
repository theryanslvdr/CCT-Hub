import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import api from '@/lib/api';
import { toast } from 'sonner';
import { 
  Plus, Edit2, Trash2, Save, X, Loader2, FileText, 
  Code, Eye, Mail, Send, CheckCircle
} from 'lucide-react';
import ReactQuill from 'react-quill-new';
import 'react-quill-new/dist/quill.snow.css';

// Available shortcodes for email templates
const SHORTCODES = [
  { code: '{user_name}', description: "Recipient's name" },
  { code: '{user_email}', description: "Recipient's email" },
  { code: '{missed_count}', description: 'Number of missed trades' },
  { code: '{team_profit}', description: "Today's team profit" },
  { code: '{team_commission}', description: "Today's team commission" },
  { code: '{profit_tracker_url}', description: 'Link to Profit Tracker' },
  { code: '{current_date}', description: "Today's date" },
  { code: '{account_value}', description: "User's account value" },
  { code: '{lot_size}', description: "User's LOT size" },
];

const CATEGORIES = [
  { value: 'general', label: 'General' },
  { value: 'reminder', label: 'Reminder' },
  { value: 'announcement', label: 'Announcement' },
  { value: 'welcome', label: 'Welcome' },
  { value: 'notification', label: 'Notification' },
];

export const CustomEmailTemplates = () => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [saving, setSaving] = useState(false);
  
  // Form state
  const [templateName, setTemplateName] = useState('');
  const [templateSubject, setTemplateSubject] = useState('');
  const [templateBody, setTemplateBody] = useState('');
  const [templateCategory, setTemplateCategory] = useState('general');
  const [editorMode, setEditorMode] = useState('visual'); // 'visual' or 'code'

  // Quill modules
  const quillModules = useMemo(() => ({
    toolbar: [
      [{ 'header': [1, 2, 3, false] }],
      ['bold', 'italic', 'underline', 'strike'],
      [{ 'color': [] }, { 'background': [] }],
      [{ 'list': 'ordered'}, { 'list': 'bullet' }],
      [{ 'align': [] }],
      ['link', 'image'],
      ['clean']
    ],
  }), []);

  const quillFormats = [
    'header', 'bold', 'italic', 'underline', 'strike',
    'color', 'background', 'list', 'bullet', 'align', 'link', 'image'
  ];

  const fetchTemplates = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.get('/admin/email-templates');
      setTemplates(res.data.templates || []);
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const resetForm = () => {
    setTemplateName('');
    setTemplateSubject('');
    setTemplateBody('');
    setTemplateCategory('general');
    setEditorMode('visual');
    setSelectedTemplate(null);
    setIsEditing(false);
    setIsCreating(false);
  };

  const handleSelectTemplate = (template) => {
    setSelectedTemplate(template);
    setTemplateName(template.name);
    setTemplateSubject(template.subject);
    setTemplateBody(template.body);
    setTemplateCategory(template.category || 'general');
    setEditorMode(template.is_html ? 'code' : 'visual');
    setIsEditing(true);
    setIsCreating(false);
  };

  const handleCreateNew = () => {
    resetForm();
    setIsCreating(true);
    setIsEditing(false);
  };

  const handleSave = async () => {
    if (!templateName.trim()) {
      toast.error('Please enter a template name');
      return;
    }
    if (!templateSubject.trim()) {
      toast.error('Please enter a subject');
      return;
    }
    if (!templateBody.trim()) {
      toast.error('Please enter email body');
      return;
    }

    setSaving(true);
    try {
      const data = {
        name: templateName,
        subject: templateSubject,
        body: templateBody,
        category: templateCategory,
        is_html: editorMode === 'code'
      };

      if (isCreating) {
        await api.post('/admin/email-templates', data);
        toast.success('Template created successfully');
      } else if (selectedTemplate) {
        await api.put(`/admin/email-templates/${selectedTemplate.id}`, data);
        toast.success('Template updated successfully');
      }
      
      fetchTemplates();
      resetForm();
    } catch (error) {
      toast.error('Failed to save template');
      console.error(error);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (templateId) => {
    if (!window.confirm('Are you sure you want to delete this template?')) return;
    
    try {
      await api.delete(`/admin/email-templates/${templateId}`);
      toast.success('Template deleted');
      if (selectedTemplate?.id === templateId) {
        resetForm();
      }
      fetchTemplates();
    } catch (error) {
      toast.error('Failed to delete template');
    }
  };

  const insertShortcode = (code) => {
    setTemplateBody(prev => prev + code);
  };

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="w-8 h-8 animate-spin text-purple-400" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with Create button */}
      <div className="flex justify-between items-center">
        <p className="text-sm text-zinc-400">
          {templates.length} custom template{templates.length !== 1 ? 's' : ''}
        </p>
        <Button
          onClick={handleCreateNew}
          className="btn-primary"
          size="sm"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Template
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Template List */}
        <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
          {templates.length === 0 && !isCreating ? (
            <div className="text-center py-8 text-zinc-500">
              <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No custom templates yet</p>
              <p className="text-xs mt-1">Create your first reusable email template</p>
            </div>
          ) : (
            templates.map((template) => (
              <div
                key={template.id}
                className={`p-4 rounded-lg border transition-all cursor-pointer ${
                  selectedTemplate?.id === template.id
                    ? 'bg-purple-500/10 border-purple-500/30'
                    : 'bg-zinc-900/50 border-zinc-800 hover:border-zinc-700'
                }`}
                onClick={() => handleSelectTemplate(template)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-white font-medium truncate">{template.name}</p>
                      {template.is_html && (
                        <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/30 text-xs shrink-0">
                          HTML
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-zinc-500 mt-0.5 truncate">{template.subject}</p>
                    <Badge variant="outline" className="bg-zinc-800/50 text-zinc-400 border-zinc-700 text-xs mt-1">
                      {template.category}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-1 ml-2 shrink-0">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSelectTemplate(template);
                      }}
                      className="h-8 w-8 p-0 text-blue-400 hover:text-blue-300"
                    >
                      <Edit2 className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(template.id);
                      }}
                      className="h-8 w-8 p-0 text-red-400 hover:text-red-300"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Edit/Create Panel */}
        <div className="lg:border-l lg:border-zinc-800 lg:pl-6">
          {(isEditing || isCreating) ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-white font-medium">
                  {isCreating ? 'Create New Template' : `Edit: ${selectedTemplate?.name}`}
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={resetForm}
                  className="text-zinc-400"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>

              {/* Template Name */}
              <div>
                <Label className="text-zinc-300">Template Name</Label>
                <Input
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                  className="input-dark mt-1"
                  placeholder="e.g., Weekly Trade Reminder"
                />
              </div>

              {/* Category */}
              <div>
                <Label className="text-zinc-300">Category</Label>
                <Select value={templateCategory} onValueChange={setTemplateCategory}>
                  <SelectTrigger className="input-dark mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-zinc-900 border-zinc-800">
                    {CATEGORIES.map((cat) => (
                      <SelectItem key={cat.value} value={cat.value}>
                        {cat.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Subject */}
              <div>
                <Label className="text-zinc-300">Subject Line</Label>
                <Input
                  value={templateSubject}
                  onChange={(e) => setTemplateSubject(e.target.value)}
                  className="input-dark mt-1"
                  placeholder="Email subject with {shortcodes}"
                />
              </div>

              {/* Shortcodes */}
              <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
                <p className="text-xs text-purple-400 mb-2">Available Shortcodes (click to insert):</p>
                <div className="flex flex-wrap gap-2">
                  {SHORTCODES.map((sc) => (
                    <code
                      key={sc.code}
                      className="px-2 py-1 rounded bg-zinc-800 text-xs text-zinc-300 cursor-pointer hover:bg-zinc-700 hover:text-white transition-colors"
                      onClick={() => insertShortcode(sc.code)}
                      title={sc.description}
                    >
                      {sc.code}
                    </code>
                  ))}
                </div>
              </div>

              {/* Editor Mode Toggle */}
              <div className="flex items-center justify-between">
                <Label className="text-zinc-300">Email Body</Label>
                <Tabs value={editorMode} onValueChange={setEditorMode} className="w-auto">
                  <TabsList className="bg-zinc-800 h-8">
                    <TabsTrigger value="visual" className="text-xs h-7 px-3">
                      <Eye className="w-3 h-3 mr-1" /> Visual
                    </TabsTrigger>
                    <TabsTrigger value="code" className="text-xs h-7 px-3">
                      <Code className="w-3 h-3 mr-1" /> HTML
                    </TabsTrigger>
                  </TabsList>
                </Tabs>
              </div>

              {/* Editor */}
              {editorMode === 'visual' ? (
                <div className="rounded-lg overflow-hidden border border-zinc-800 bg-white">
                  <ReactQuill
                    theme="snow"
                    value={templateBody}
                    onChange={setTemplateBody}
                    modules={quillModules}
                    formats={quillFormats}
                    className="bg-white text-black"
                    style={{ minHeight: '200px' }}
                  />
                </div>
              ) : (
                <Textarea
                  value={templateBody}
                  onChange={(e) => setTemplateBody(e.target.value)}
                  className="input-dark font-mono text-sm min-h-[250px]"
                  placeholder="<html>...</html>"
                />
              )}
              <p className="text-xs text-zinc-500">
                Shortcodes like {'{user_name}'} will be replaced with actual values when sent.
              </p>

              {/* Save Button */}
              <div className="flex gap-2">
                <Button
                  onClick={handleSave}
                  disabled={saving}
                  className="btn-primary flex-1"
                >
                  {saving ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="w-4 h-4 mr-2" />
                      {isCreating ? 'Create Template' : 'Save Changes'}
                    </>
                  )}
                </Button>
                <Button
                  variant="outline"
                  onClick={resetForm}
                  className="border-zinc-700"
                >
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full min-h-[300px] text-center">
              <div>
                <FileText className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-500">Select a template to edit</p>
                <p className="text-xs text-zinc-600 mt-1">or create a new one</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Custom styles for Quill editor */}
      <style>{`
        .ql-toolbar.ql-snow {
          border-color: #3f3f46 !important;
          background: #18181b !important;
        }
        .ql-toolbar.ql-snow .ql-stroke {
          stroke: #a1a1aa !important;
        }
        .ql-toolbar.ql-snow .ql-fill {
          fill: #a1a1aa !important;
        }
        .ql-toolbar.ql-snow .ql-picker-label {
          color: #a1a1aa !important;
        }
        .ql-toolbar.ql-snow button:hover .ql-stroke,
        .ql-toolbar.ql-snow .ql-picker-label:hover .ql-stroke {
          stroke: #fff !important;
        }
        .ql-toolbar.ql-snow button:hover .ql-fill,
        .ql-toolbar.ql-snow .ql-picker-label:hover .ql-fill {
          fill: #fff !important;
        }
        .ql-container.ql-snow {
          border-color: #3f3f46 !important;
          min-height: 200px;
        }
        .ql-editor {
          min-height: 200px;
          font-size: 14px;
        }
      `}</style>
    </div>
  );
};

export default CustomEmailTemplates;
