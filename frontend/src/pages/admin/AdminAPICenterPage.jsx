import React, { useState, useEffect } from 'react';
import { apiCenterAPI } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Textarea } from '../ui/textarea';
import { Switch } from '../ui/switch';
import { toast } from 'sonner';
import { Plus, Link2, Send, Trash2, ExternalLink, Webhook } from 'lucide-react';

export const AdminAPICenterPage = () => {
  const [connections, setConnections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [sendDialogOpen, setSendDialogOpen] = useState(false);
  const [selectedConnection, setSelectedConnection] = useState(null);
  const [payload, setPayload] = useState('{\n  "action": "test",\n  "data": {}\n}');
  const [sendResult, setSendResult] = useState(null);
  const [newConnection, setNewConnection] = useState({
    name: '',
    endpoint_url: '',
    api_key: '',
    is_active: true,
  });

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    loadConnections();
  }, []);

  const loadConnections = async () => {
    try {
      const res = await apiCenterAPI.getConnections();
      setConnections(res.data);
    } catch (error) {
      console.error('Failed to load connections:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateConnection = async () => {
    if (!newConnection.name || !newConnection.endpoint_url) {
      toast.error('Please fill in required fields');
      return;
    }

    try {
      await apiCenterAPI.createConnection(newConnection);
      toast.success('API connection created!');
      setDialogOpen(false);
      setNewConnection({ name: '', endpoint_url: '', api_key: '', is_active: true });
      loadConnections();
    } catch (error) {
      toast.error('Failed to create connection');
    }
  };

  const handleDeleteConnection = async (id) => {
    if (!window.confirm('Are you sure you want to delete this connection?')) return;
    
    try {
      await apiCenterAPI.deleteConnection(id);
      toast.success('Connection deleted');
      loadConnections();
    } catch (error) {
      toast.error('Failed to delete connection');
    }
  };

  const handleSendToConnection = async () => {
    try {
      const parsedPayload = JSON.parse(payload);
      const res = await apiCenterAPI.sendToConnection(selectedConnection.id, parsedPayload);
      setSendResult(res.data);
      toast.success('Request sent successfully!');
    } catch (error) {
      if (error instanceof SyntaxError) {
        toast.error('Invalid JSON payload');
      } else {
        setSendResult({ error: error.response?.data?.detail || 'Request failed' });
        toast.error('Request failed');
      }
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" /></div>;
  }

  return (
    <div className="space-y-6">
      {/* Info Card */}
      <Card className="glass-highlight">
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center flex-shrink-0">
              <Webhook className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Webhook Receiver</h3>
              <p className="text-zinc-400 text-sm mt-1">External apps can send data to this endpoint:</p>
              <code className="block mt-2 p-3 rounded-lg bg-zinc-900 text-blue-400 font-mono text-sm">
                POST {BACKEND_URL}/api/api-center/receive
              </code>
              <p className="text-xs text-zinc-500 mt-2">
                Send JSON payload with "action" and "data" fields. Supported actions: "update_signal"
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Create Connection Button */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogTrigger asChild>
          <Button className="btn-primary gap-2" data-testid="create-connection-button">
            <Plus className="w-4 h-4" /> Add Connection
          </Button>
        </DialogTrigger>
        <DialogContent className="glass-card border-zinc-800">
          <DialogHeader>
            <DialogTitle className="text-white">Add API Connection</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <Label className="text-zinc-300">Connection Name</Label>
              <Input
                value={newConnection.name}
                onChange={(e) => setNewConnection({ ...newConnection, name: e.target.value })}
                placeholder="e.g., Heartbeat App, Rewards System"
                className="input-dark mt-1"
                data-testid="connection-name-input"
              />
            </div>
            <div>
              <Label className="text-zinc-300">Endpoint URL</Label>
              <Input
                value={newConnection.endpoint_url}
                onChange={(e) => setNewConnection({ ...newConnection, endpoint_url: e.target.value })}
                placeholder="https://api.example.com/webhook"
                className="input-dark mt-1"
                data-testid="connection-url-input"
              />
            </div>
            <div>
              <Label className="text-zinc-300">API Key (optional)</Label>
              <Input
                type="password"
                value={newConnection.api_key}
                onChange={(e) => setNewConnection({ ...newConnection, api_key: e.target.value })}
                placeholder="Bearer token or API key"
                className="input-dark mt-1"
              />
            </div>
            <div className="flex items-center justify-between">
              <Label className="text-zinc-300">Active</Label>
              <Switch
                checked={newConnection.is_active}
                onCheckedChange={(v) => setNewConnection({ ...newConnection, is_active: v })}
              />
            </div>
            <Button onClick={handleCreateConnection} className="w-full btn-primary" data-testid="confirm-create-connection">
              Create Connection
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Connections List */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-white">API Connections</CardTitle>
        </CardHeader>
        <CardContent>
          {connections.length > 0 ? (
            <div className="space-y-4">
              {connections.map((conn) => (
                <div key={conn.id} className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800 hover:border-zinc-700 transition-colors">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${conn.is_active ? 'bg-blue-500/20' : 'bg-zinc-700/50'}`}>
                        <Link2 className={`w-5 h-5 ${conn.is_active ? 'text-blue-400' : 'text-zinc-500'}`} />
                      </div>
                      <div>
                        <p className="font-medium text-white">{conn.name}</p>
                        <p className="text-xs text-zinc-500 truncate max-w-[300px]">{conn.endpoint_url}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`status-badge ${conn.is_active ? 'status-success' : 'bg-zinc-700/50 text-zinc-400'}`}>
                        {conn.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="btn-secondary"
                      onClick={() => { setSelectedConnection(conn); setSendDialogOpen(true); setSendResult(null); }}
                      data-testid={`send-to-${conn.id}`}
                    >
                      <Send className="w-4 h-4 mr-1" /> Send
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteConnection(conn.id)}
                      className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                      data-testid={`delete-connection-${conn.id}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                  {conn.last_used && (
                    <p className="text-xs text-zinc-500 mt-2">
                      Last used: {new Date(conn.last_used).toLocaleString()}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-zinc-500">
              No API connections yet. Add a connection to communicate with external apps!
            </div>
          )}
        </CardContent>
      </Card>

      {/* Send Dialog */}
      <Dialog open={sendDialogOpen} onOpenChange={setSendDialogOpen}>
        <DialogContent className="glass-card border-zinc-800 max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-white">Send to {selectedConnection?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <Label className="text-zinc-300">Endpoint</Label>
              <p className="text-sm text-zinc-400 font-mono mt-1 truncate">{selectedConnection?.endpoint_url}</p>
            </div>
            <div>
              <Label className="text-zinc-300">JSON Payload</Label>
              <Textarea
                value={payload}
                onChange={(e) => setPayload(e.target.value)}
                rows={8}
                className="input-dark mt-1 font-mono text-sm"
                data-testid="payload-textarea"
              />
            </div>
            <Button onClick={handleSendToConnection} className="w-full btn-primary" data-testid="send-request-button">
              <Send className="w-4 h-4 mr-2" /> Send Request
            </Button>

            {sendResult && (
              <div className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                <p className="text-xs text-zinc-500 mb-2">Response:</p>
                <pre className="text-sm text-zinc-300 font-mono overflow-auto max-h-40">
                  {JSON.stringify(sendResult, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};
