import React, { useEffect, useRef, useState } from 'react';
import { Bot, Database, Loader2, MessageSquarePlus, Send, Trash2, User } from 'lucide-react';

type Message = { id: number; role: 'user' | 'assistant' | 'system'; content: string; created_at?: string };
type Conversation = { id: string; title: string; updated_at: string; message_count?: number; messages?: Message[]; context?: Record<string, unknown> };
type Status = { configured: boolean; model: string; chatDatabase: string; financeDatabase: string };

async function api<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...options });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error ?? `API ${response.status}`);
  return body;
}

export function AIResearchTab() {
  const [status, setStatus] = useState<Status | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [active, setActive] = useState<Conversation | null>(null);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  const refreshList = async () => {
    const result = await api<{ conversations: Conversation[] }>('/api/agent/conversations');
    setConversations(result.conversations);
    return result.conversations;
  };

  const openConversation = async (id: string) => {
    const conversation = await api<Conversation>(`/api/agent/conversations/${id}`);
    setActive(conversation);
  };

  const createConversation = async () => {
    const pending = localStorage.getItem('findash-ai-context');
    const context = pending ? JSON.parse(pending) : {};
    const conversation = await api<Conversation>('/api/agent/conversations', {
      method: 'POST', body: JSON.stringify({ title: context.name ? `Research: ${context.name}` : 'New research', context }),
    });
    localStorage.removeItem('findash-ai-context');
    setActive(conversation);
    await refreshList();
    if (context.name) setInput(`Analyze ${context.name} using the current FinDash data. Focus on trend, risk, and related indicators.`);
  };

  useEffect(() => {
    Promise.all([api<Status>('/api/agent/status'), refreshList()]).then(async ([agentStatus, list]) => {
      setStatus(agentStatus);
      const pending = localStorage.getItem('findash-ai-context');
      if (pending || !list.length) await createConversation();
      else await openConversation(list[0].id);
    }).catch(err => setError(err.message));
  }, []);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [active?.messages, loading]);

  const send = async () => {
    const message = input.trim();
    if (!message || !active || loading) return;
    setInput(''); setError(''); setLoading(true);
    setActive({ ...active, messages: [...(active.messages ?? []), { id: Date.now(), role: 'user', content: message }] });
    try {
      const result = await api<{ conversation: Conversation }>('/api/agent/chat', {
        method: 'POST', body: JSON.stringify({ conversationId: active.id, message, context: active.context }),
      });
      setActive(result.conversation);
      await refreshList();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally { setLoading(false); }
  };

  const remove = async (id: string) => {
    await api(`/api/agent/conversations/${id}`, { method: 'DELETE' });
    const list = await refreshList();
    if (active?.id === id) list.length ? await openConversation(list[0].id) : await createConversation();
  };

  return <div className="max-w-screen-2xl mx-auto p-4 grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-4 min-h-[calc(100vh-8rem)]">
    <aside className="bg-card border border-border rounded-lg overflow-hidden flex flex-col">
      <div className="p-3 border-b border-border"><button onClick={createConversation} className="w-full flex items-center justify-center gap-2 bg-primary text-primary-foreground rounded px-3 py-2 text-xs font-semibold"><MessageSquarePlus size={14}/>New research</button></div>
      <div className="max-h-[520px] flex-1 overflow-y-auto divide-y divide-border">
        {conversations.map(item => <button key={item.id} onClick={() => openConversation(item.id)} className={`w-full text-left p-3 group hover:bg-secondary ${active?.id === item.id ? 'bg-accent' : ''}`}>
          <div className="flex items-start gap-2"><div className="flex-1 min-w-0"><div className="text-xs font-semibold truncate">{item.title}</div><div className="text-[10px] text-muted-foreground mt-1">{item.message_count ?? 0} messages · {new Date(item.updated_at).toLocaleDateString()}</div></div><Trash2 onClick={event => { event.stopPropagation(); remove(item.id); }} size={13} className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-down"/></div>
        </button>)}
      </div>
      <div className="p-3 border-t border-border text-[10px] text-muted-foreground space-y-1">
        <div className="flex items-center gap-1.5"><span className={`w-1.5 h-1.5 rounded-full ${status?.configured ? 'bg-up' : 'bg-down'}`}/>{status?.configured ? 'OpenAI API configured' : 'API key unavailable'}</div>
        <div className="flex items-center gap-1.5"><Database size={11}/>{status?.model ?? 'Loading configuration'}</div>
      </div>
    </aside>

    <section className="bg-card border border-border rounded-lg flex flex-col min-h-[650px] overflow-hidden">
      <header className="px-5 py-4 border-b border-border flex items-center justify-between"><div><h2 className="text-base font-bold">{active?.title ?? 'AI Research'}</h2><p className="text-[10px] text-muted-foreground mt-0.5">Read-only financial data tools · Locally persisted conversation history</p></div><Bot size={20} className="text-primary"/></header>
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {!active?.messages?.length && <div className="h-full flex items-center justify-center"><div className="max-w-lg text-center"><Bot size={34} className="mx-auto text-primary mb-3"/><h3 className="font-bold">FinDash Research Agent</h3><p className="text-xs text-muted-foreground mt-2 leading-relaxed">Ask about market indices, macro releases, rates, volatility, freight, industry data, or relationships between series. The agent can inspect your read-only DuckDB and will report observation dates.</p></div></div>}
        {active?.messages?.filter(message => message.role !== 'system').map(message => <div key={message.id} className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : ''}`}>
          {message.role === 'assistant' && <div className="w-7 h-7 rounded bg-primary/10 text-primary flex items-center justify-center shrink-0"><Bot size={14}/></div>}
          <div className={`max-w-[82%] rounded-lg px-4 py-3 text-xs leading-relaxed whitespace-pre-wrap ${message.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-secondary text-foreground'}`}>{message.content}</div>
          {message.role === 'user' && <div className="w-7 h-7 rounded bg-secondary flex items-center justify-center shrink-0"><User size={14}/></div>}
        </div>)}
        {loading && <div className="flex items-center gap-2 text-xs text-muted-foreground"><Loader2 size={14} className="animate-spin"/>Reviewing FinDash data…</div>}
        {error && <div className="rounded border border-down/30 bg-down/5 text-down text-xs p-3">{error}</div>}
        <div ref={bottomRef}/>
      </div>
      <footer className="p-4 border-t border-border"><div className="flex gap-2"><textarea value={input} onChange={event => setInput(event.target.value)} onKeyDown={event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); send(); } }} placeholder="Ask FinDash Research…" className="flex-1 min-h-[48px] max-h-32 resize-y rounded border border-border bg-background px-3 py-2 text-xs outline-none focus:border-primary"/><button onClick={send} disabled={!input.trim() || loading || !active} className="self-end h-12 px-4 rounded bg-primary text-primary-foreground disabled:opacity-40"><Send size={16}/></button></div><div className="text-[9px] text-muted-foreground mt-2">Enter to send · Shift+Enter for a new line · Research output is not investment advice.</div></footer>
    </section>
  </div>;
}
