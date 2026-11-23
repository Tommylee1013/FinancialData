import React, { useEffect, useRef, useState } from 'react';
import { Activity, ArrowLeft, Bot, BriefcaseBusiness, CandlestickChart, Check, CircleAlert, CircleDot, Database, Globe2, Loader2, MessageSquarePlus, Network, PanelRightClose, PanelRightOpen, Search, Send, ShieldCheck, Trash2, User } from 'lucide-react';

type AgentId = 'risk' | 'portfolio' | 'trader' | 'research' | 'macro' | 'manager';
type AgentProfile = { id: AgentId; name: string; description: string };
type Message = { id: number; role: 'user' | 'assistant' | 'system'; content: string; created_at?: string };
type Conversation = { id: string; title: string; updated_at: string; message_count?: number; messages?: Message[]; context?: Record<string, any> };
type RunEvent = { id: number; type: string; agentId: string; agentName: string; message: string; detail?: string; tool?: string; createdAt?: string };
type RunEventsResponse = { events: RunEvent[]; status: 'pending' | 'running' | 'complete' | 'failed' };
type Status = { configured: boolean; model: string; chatDatabase: string; financeDatabase: string; agents?: AgentProfile[] };
const agentIcons = { risk: ShieldCheck, portfolio: BriefcaseBusiness, trader: CandlestickChart, research: Search, macro: Globe2, manager: Network };
const fallbackAgents: AgentProfile[] = [
  {id:'risk',name:'Risk Management Agent',description:'VaR, rolling volatility, drawdown and risk controls.'},
  {id:'portfolio',name:'Portfolio Management Agent',description:'Portfolio optimization and data-driven asset allocation.'},
  {id:'trader',name:'Trader Agent',description:'Single-instrument technical analysis and conditional setups.'},
  {id:'research',name:'Research Agent',description:'Single-name outlook with peers, benchmarks and related data.'},
  {id:'macro',name:'Macro Agent',description:'Market, economic, sector and industry outlook.'},
  {id:'manager',name:'Manager',description:'Orchestrate risk, portfolio, trading, research and macro agents; synthesize their evidence into one assessment.'},
];
const agentLabels: Record<AgentId,string> = {risk:'Risk Management',portfolio:'Portfolio Management',trader:'Trader',research:'Research',macro:'Macro',manager:'Manager'};

async function api<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...options });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error ?? `API ${response.status}`);
  return body;
}

export function AIResearchTab() {
  const [status,setStatus]=useState<Status|null>(null),[conversations,setConversations]=useState<Conversation[]>([]),[active,setActive]=useState<Conversation|null>(null);
  const [agentId,setAgentId]=useState<AgentId|null>(null),[input,setInput]=useState(''),[loading,setLoading]=useState(false),[error,setError]=useState('');
  const [activityOpen,setActivityOpen]=useState(false),[runEvents,setRunEvents]=useState<RunEvent[]>([]);
  const bottomRef=useRef<HTMLDivElement>(null);
  const profiles=status?.agents?.length?status.agents:fallbackAgents;
  const profile=profiles.find(item=>item.id===agentId);
  const refreshList=async()=>{const result=await api<{conversations:Conversation[]}>('/api/agent/conversations');setConversations(result.conversations);return result.conversations;};
  const openConversation=async(id:string)=>{const conversation=await api<Conversation>(`/api/agent/conversations/${id}`);setActive(conversation);setAgentId(conversation.context?.agentId??'research');};
  const createConversation=async(nextAgent:AgentId)=>{
    const pending=localStorage.getItem('findash-ai-context');const context={...(pending?JSON.parse(pending):{}),agentId:nextAgent};
    const conversation=await api<Conversation>('/api/agent/conversations',{method:'POST',body:JSON.stringify({title:context.name?`${agentLabels[nextAgent]}: ${context.name}`:`${agentLabels[nextAgent]} session`,context})});
    localStorage.removeItem('findash-ai-context');setActive(conversation);setAgentId(nextAgent);await refreshList();
    if(context.name)setInput(`Analyze ${context.name} using FinDash data. Focus on trend, risk and relevant related series.`);
  };
  useEffect(()=>{Promise.all([api<Status>('/api/agent/status'),refreshList()]).then(async([agentStatus,list])=>{setStatus(agentStatus);const pending=localStorage.getItem('findash-ai-context');if(pending&&list.length)await openConversation(list[0].id);}).catch(err=>setError(err.message));},[]);
  useEffect(()=>{bottomRef.current?.scrollIntoView({behavior:'smooth'});},[active?.messages,loading]);
  const send=async()=>{
    const message=input.trim();if(!message||!active||!agentId||loading)return;
    const runId=globalThis.crypto?.randomUUID?.()??`${Date.now()}-${Math.random().toString(36).slice(2)}`;
    setInput('');setError('');setLoading(true);setRunEvents([]);
    setActive({...active,messages:[...(active.messages??[]),{id:Date.now(),role:'user',content:message}]});
    let polling=true,after=0;
    const pollRun=async()=>{
      while(polling){
        try{
          const update=await api<RunEventsResponse>(`/api/agent/events?runId=${encodeURIComponent(runId)}&after=${after}`);
          if(update.events.length){after=update.events[update.events.length-1].id;setRunEvents(previous=>[...previous,...update.events]);}
          if(update.status==='complete'||update.status==='failed')break;
        }catch{/* The run may not have been registered yet. */}
        await new Promise(resolve=>setTimeout(resolve,450));
      }
    };
    const pollingTask=pollRun();
    try{
      const result=await api<{conversation:Conversation}>('/api/agent/chat',{method:'POST',body:JSON.stringify({conversationId:active.id,message,context:active.context,agentId,runId})});
      setActive(result.conversation);await refreshList();
    }catch(err){setError(err instanceof Error?err.message:String(err));}
    finally{polling=false;await pollingTask;setLoading(false);}
  };
  const remove=async(id:string)=>{await api(`/api/agent/conversations/${id}`,{method:'DELETE'});const list=await refreshList();if(active?.id===id){setActive(null);setAgentId(null);if(list.length)await openConversation(list[0].id);}};

  return <div className={`mx-auto grid min-h-[calc(100vh-8rem)] max-w-screen-2xl grid-cols-1 gap-4 p-4 sm:p-6 ${activityOpen?'lg:grid-cols-[280px_minmax(0,1fr)_360px]':'lg:grid-cols-[280px_minmax(0,1fr)]'}`}>
    <aside className="flex flex-col overflow-hidden rounded-lg border border-border bg-card shadow-sm">
      <div className="border-b border-border p-3"><button onClick={()=>{setActive(null);setAgentId(null);}} className="flex w-full items-center justify-center gap-2 rounded-md bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground"><MessageSquarePlus size={14}/>Choose an agent</button></div>
      <div className="max-h-[520px] flex-1 divide-y divide-border overflow-y-auto">{conversations.map(item=><button key={item.id} onClick={()=>openConversation(item.id)} className={`group w-full p-3 text-left hover:bg-secondary ${active?.id===item.id?'bg-accent':''}`}><div className="flex items-start gap-2"><div className="min-w-0 flex-1"><div className="truncate text-xs font-semibold">{item.title}</div><div className="mt-1 text-[10px] text-muted-foreground">{item.message_count??0} messages · {new Date(item.updated_at).toLocaleDateString()}</div></div><Trash2 onClick={event=>{event.stopPropagation();remove(item.id);}} size={13} className="text-muted-foreground opacity-0 hover:text-down group-hover:opacity-100"/></div></button>)}</div>
      <div className="space-y-1 border-t border-border p-3 text-[10px] text-muted-foreground"><div className="flex items-center gap-1.5"><span className={`h-1.5 w-1.5 rounded-full ${status?.configured?'bg-up':'bg-down'}`}/>{status?.configured?'OpenAI API configured':'API key unavailable'}</div><div className="flex items-center gap-1.5"><Database size={11}/>{status?.model??'Loading model'}</div></div>
    </aside>
    <section className="flex min-h-[650px] flex-col overflow-hidden rounded-lg border border-border bg-card shadow-sm">
      <header className="flex items-center justify-between gap-3 border-b border-border px-5 py-4"><div className="min-w-0"><h2 className="text-base font-semibold">{profile?.name??'FinDash Agent Workspace'}</h2><p className="mt-0.5 text-xs text-muted-foreground">{profile?.description??'Choose a specialist agent to start a data-grounded conversation.'}</p></div><div className="flex shrink-0 items-center gap-2">{agentId&&<button onClick={()=>{setActive(null);setAgentId(null);}} className="rounded-md border border-border px-2 py-1 text-xs text-muted-foreground hover:bg-secondary"><ArrowLeft size={13} className="mr-1 inline"/>Agents</button>}<button onClick={()=>setActivityOpen(value=>!value)} aria-expanded={activityOpen} className={`flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-xs font-medium transition ${activityOpen?'border-primary bg-primary/10 text-primary':'border-border text-muted-foreground hover:bg-secondary hover:text-foreground'}`}><Activity size={14}/><span>Activity</span>{loading&&<span className="h-1.5 w-1.5 animate-pulse rounded-full bg-primary"/>}{activityOpen?<PanelRightClose size={14}/>:<PanelRightOpen size={14}/>}</button></div></header>
      <div className="flex-1 space-y-4 overflow-y-auto p-5">
        {!agentId&&<div className="grid h-full content-center grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">{profiles.map(item=>{const Icon=agentIcons[item.id];return <button key={item.id} onClick={()=>createConversation(item.id)} className="rounded-lg border border-border bg-card p-4 text-left shadow-sm transition hover:border-primary/50 hover:bg-secondary/40"><span className="mb-3 flex h-9 w-9 items-center justify-center rounded-md bg-primary/10 text-primary"><Icon size={18}/></span><span className="block text-sm font-semibold">{item.name}</span><span className="mt-1 block text-xs leading-5 text-muted-foreground">{item.description}</span><span className="mt-3 block text-xs font-medium text-primary">Start session</span></button>;})}</div>}
        {agentId&&!active?.messages?.length&&<div className="flex h-full items-center justify-center"><div className="max-w-lg text-center"><Bot size={34} className="mx-auto mb-3 text-primary"/><h3 className="font-semibold">{profile?.name}</h3><p className="mt-2 text-sm leading-relaxed text-muted-foreground">Agent can inspect read-only FinDash data and use its specialist tools. Results include observation dates where available; analysis is not investment advice.</p></div></div>}
        {active?.messages?.filter(message=>message.role!=='system').map(message=><div key={message.id} className={`flex gap-3 ${message.role==='user'?'justify-end':''}`}>{message.role==='assistant'&&<div className="flex h-7 w-7 shrink-0 items-center justify-center rounded bg-primary/10 text-primary"><Bot size={14}/></div>}<div className={`max-w-[82%] whitespace-pre-wrap rounded-lg px-4 py-3 text-sm leading-relaxed ${message.role==='user'?'bg-primary text-primary-foreground':'bg-secondary text-foreground'}`}>{message.content}</div>{message.role==='user'&&<div className="flex h-7 w-7 shrink-0 items-center justify-center rounded bg-secondary"><User size={14}/></div>}</div>)}
        {loading&&<div className="flex items-center gap-2 text-xs text-muted-foreground"><Loader2 size={14} className="animate-spin"/>Consulting {profile?.name}…</div>}{error&&<div className="rounded border border-down/30 bg-down/5 p-3 text-xs text-down">{error}</div>}<div ref={bottomRef}/>
      </div>
      <footer className="border-t border-border p-4"><div className="flex gap-2"><textarea value={input} onChange={event=>setInput(event.target.value)} onKeyDown={event=>{if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();send();}}} placeholder={agentId?`Ask ${profile?.name??'agent'}…`:'Select an agent to begin'} disabled={!agentId} className="min-h-[48px] max-h-32 flex-1 resize-y rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary disabled:opacity-50"/><button onClick={send} disabled={!input.trim()||loading||!active||!agentId} className="h-12 self-end rounded-md bg-primary px-4 text-primary-foreground disabled:opacity-40"><Send size={16}/></button></div><div className="mt-2 text-[11px] text-muted-foreground">Enter to send · Shift+Enter for a new line · Analysis only, no trade execution</div></footer>
    </section>
    {activityOpen&&<>
      <button aria-label="Close activity panel" onClick={()=>setActivityOpen(false)} className="fixed inset-0 z-40 bg-black/20 lg:hidden"/>
      <aside className="fixed inset-y-0 right-0 z-50 flex w-[min(390px,92vw)] flex-col border-l border-border bg-card shadow-2xl lg:static lg:z-auto lg:h-[calc(100vh-10rem)] lg:min-h-[600px] lg:w-auto lg:rounded-lg lg:border lg:shadow-sm">
        <div className="flex items-start justify-between border-b border-border p-4"><div><div className="flex items-center gap-2 text-sm font-semibold"><Activity size={16} className="text-primary"/>Agent activity</div><p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">Live orchestration and tool trace · private model reasoning is not shown.</p></div><button onClick={()=>setActivityOpen(false)} aria-label="Close activity panel" className="rounded p-1 text-muted-foreground hover:bg-secondary"><PanelRightClose size={16}/></button></div>
        <div className="flex items-center justify-between border-b border-border px-4 py-2.5 text-[11px]"><span className="text-muted-foreground">Framework</span><span className="rounded bg-secondary px-2 py-1 font-medium">LangGraph · FinDash agents</span></div>
        <div className="flex-1 space-y-0 overflow-y-auto p-4">
          {!runEvents.length&&!loading&&<div className="flex h-full min-h-48 flex-col items-center justify-center text-center"><Activity size={24} className="mb-2 text-muted-foreground/50"/><p className="text-sm font-medium">No active run</p><p className="mt-1 max-w-[240px] text-xs leading-relaxed text-muted-foreground">Send a message to watch agent delegation and data tools appear here.</p></div>}
          {runEvents.map((event,index)=>{const failed=event.type.includes('failed');const done=event.type.includes('completed')||event.type==='tool_completed';const Icon=failed?CircleAlert:done?Check:CircleDot;return <div key={event.id} className="relative flex gap-3 pb-5 last:pb-1"><div className="relative flex w-4 shrink-0 justify-center"><span className={`z-10 flex h-4 w-4 items-center justify-center rounded-full ${failed?'bg-down/10 text-down':done?'bg-up/10 text-up':'bg-primary/10 text-primary'}`}><Icon size={11}/></span>{index<runEvents.length-1&&<span className="absolute top-4 h-full w-px bg-border"/>}</div><div className="min-w-0 flex-1"><div className="flex items-center justify-between gap-2"><span className="truncate text-[11px] font-semibold">{event.agentName}{event.tool?` · ${event.tool}`:''}</span><span className="shrink-0 text-[9px] text-muted-foreground">{event.createdAt?new Date(event.createdAt).toLocaleTimeString():''}</span></div><p className="mt-1 text-xs leading-relaxed text-muted-foreground">{event.message}</p>{event.detail&&<p className="mt-1.5 rounded bg-secondary/70 px-2 py-1.5 text-[10px] leading-relaxed text-foreground/75">{event.detail}</p>}</div></div>;})}
          {loading&&<div className="flex items-center gap-2 border-t border-border pt-3 text-[11px] text-muted-foreground"><Loader2 size={13} className="animate-spin"/>Waiting for the next event…</div>}
        </div>
        <div className="border-t border-border p-3 text-[10px] leading-relaxed text-muted-foreground">This trace shows agent handoffs and tool execution summaries, not hidden chain-of-thought.</div>
      </aside>
    </>}
  </div>;
}

export default AIResearchTab;
