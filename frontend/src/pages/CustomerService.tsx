import { useState, useEffect } from 'react';
import { customerServiceAPI } from '../lib/api';
import { Loading, SkeletonTable } from '../components/Loading';
import { ErrorDisplay, EmptyState } from '../components/ErrorDisplay';
import { toast } from '../hooks/useToast';
import { 
  MessageCircle, 
  Send, 
  User, 
  Bot, 
  AlertTriangle,
  Hand,
  Clock
} from 'lucide-react';

interface Session {
  id: string;
  customer_id: string;
  channel: string;
  status: string;
  priority: string;
  last_message: string;
  agent_id?: string;
  created_at: string;
}

export default function CustomerService() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSession, setActiveSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSessions = async () => {
    try {
      setLoading(true);
      const response = await customerServiceAPI.sessions();
      setSessions(response?.sessions || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load sessions');
    } finally {
      setLoading(false);
    }
  };

  const fetchMessages = async (sessionId: string) => {
    try {
      const response = await customerServiceAPI.getSession(sessionId);
      setMessages(response?.messages || []);
    } catch (err: any) {
      toast.error('Failed to load messages');
    }
  };

  useEffect(() => {
    fetchSessions();
    const interval = setInterval(fetchSessions, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (activeSession) {
      fetchMessages(activeSession.id);
    }
  }, [activeSession]);

  const handleSendMessage = async () => {
    if (!activeSession || !newMessage.trim()) return;
    
    try {
      await customerServiceAPI.sendMessage(activeSession.id, {
        content: newMessage,
        agent_id: activeSession.agent_id,
      });
      setNewMessage('');
      fetchMessages(activeSession.id);
      toast.success('Message sent');
    } catch (err: any) {
      toast.error('Failed to send message');
    }
  };

  const handleHandoff = async (reason: string) => {
    if (!activeSession) return;
    
    try {
      await customerServiceAPI.handoff(activeSession.id, { reason });
      toast.success('Handoff initiated');
      fetchSessions();
    } catch (err: any) {
      toast.error('Handoff failed');
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-gray-200 rounded w-48 animate-pulse" />
        <SkeletonTable rows={5} />
      </div>
    );
  }

  if (error) {
    return <ErrorDisplay message={error} onRetry={fetchSessions} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Customer Service</h1>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <MessageCircle className="w-5 h-5" />
          {sessions.length} active sessions
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sessions List */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="p-4 border-b border-gray-200">
            <h2 className="font-semibold text-gray-900">Sessions</h2>
          </div>
          
          {sessions.length > 0 ? (
            <div className="divide-y divide-gray-100">
              {sessions.map((session) => (
                <button
                  key={session.id}
                  onClick={() => setActiveSession(session)}
                  className={`w-full text-left p-4 hover:bg-gray-50 transition-colors ${
                    activeSession?.id === session.id ? 'bg-blue-50 border-l-4 border-blue-600' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {session.customer_id.slice(0, 12)}...
                      </p>
                      <p className="text-xs text-gray-500">{session.channel}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        session.priority === 'urgent' ? 'bg-red-100 text-red-700' :
                        session.priority === 'high' ? 'bg-orange-100 text-orange-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {session.priority}
                      </span>
                      <span className={`w-2 h-2 rounded-full ${
                        session.status === 'active' ? 'bg-green-500' : 'bg-gray-300'
                      }`} />
                    </div>
                  </div>
                  
                  <p className="text-sm text-gray-600 mt-2 truncate">{session.last_message}</p>
                </button>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No sessions"
              message="Customer sessions will appear here."
            />
          )}
        </div>

        {/* Chat Area */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 flex flex-col">
          {activeSession ? (
            <>
              <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                    <User className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{activeSession.customer_id.slice(0, 12)}...</p>
                    <p className="text-sm text-gray-500">{activeSession.channel} • {activeSession.status}</p>
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <button
                    onClick={() => handleHandoff('Customer requested human')}
                    className="flex items-center gap-2 px-3 py-2 bg-orange-50 text-orange-700 text-sm rounded-lg hover:bg-orange-100 transition-colors"
                  >
                    <Hand className="w-4 h-4" />
                    Handoff
                  </button>
                  
                  {activeSession.priority === 'urgent' && (
                    <span className="flex items-center gap-1 px-3 py-2 bg-red-50 text-red-700 text-sm rounded-lg">
                      <AlertTriangle className="w-4 h-4" />
                      Urgent
                    </span>
                  )}
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[300px]">
                {messages.length > 0 ? (
                  messages.map((msg, index) => (
                    <div
                      key={index}
                      className={`flex gap-3 ${msg.is_agent ? 'flex-row' : 'flex-row-reverse'}`}
                    >
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        msg.is_agent ? 'bg-blue-100' : 'bg-gray-100'
                      }`}>
                        {msg.is_agent ? (
                          <Bot className="w-4 h-4 text-blue-600" />
                        ) : (
                          <User className="w-4 h-4 text-gray-600" />
                        )}
                      </div>
                      
                      <div className={`max-w-[70%] px-4 py-2 rounded-lg ${
                        msg.is_agent 
                          ? 'bg-blue-50 text-blue-900' 
                          : 'bg-gray-100 text-gray-900'
                      }`}>
                        <p className="text-sm">{msg.content}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {new Date(msg.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <p className="text-gray-400">No messages yet. Start the conversation!</p>
                  </div>
                )}
              </div>

              {/* Input */}
              <div className="p-4 border-t border-gray-200">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Type a message..."
                    className="flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={!newMessage.trim()}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <MessageCircle className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">Select a session to view messages</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
