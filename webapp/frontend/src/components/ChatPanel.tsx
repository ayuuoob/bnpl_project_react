import React, { useState, useRef, useEffect } from 'react';
import type { Message } from '../types';
import { Send, Bot, User, Loader2, BarChart3, PanelLeftOpen } from 'lucide-react';
import { FeedbackButtons } from './FeedbackButtons';

interface Props {
    messages: Message[];
    isLoading: boolean;
    onSendMessage: (msg: string) => void;
    onToggleAnalytics?: () => void;
    onToggleSidebar?: () => void;
    showAnalyticsToggle?: boolean;
    showSidebarToggle?: boolean;
}

const suggestions = [
    "What is the total GMV?",
    "Show all users in Rabat",
    "Give me the user with highest risk",
    "Show me risk overview"
];

const ChatPanel: React.FC<Props> = ({ messages, isLoading, onSendMessage, onToggleAnalytics, onToggleSidebar, showAnalyticsToggle, showSidebarToggle }) => {
    const [input, setInput] = useState('');
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSubmit = (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!input.trim() || isLoading) return;
        onSendMessage(input);
        setInput('');
    };

    return (
        <div className="flex flex-col h-full max-h-full bg-white overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border">
                <div className="flex items-center gap-3">
                    {showSidebarToggle && (
                        <button
                            onClick={onToggleSidebar}
                            className="p-2 hover:bg-[#F8F8F8] rounded-lg transition-colors text-[#505050] hover:text-[#582098]"
                            title="Show sidebar"
                        >
                            <PanelLeftOpen size={20} />
                        </button>
                    )}
                    <div>
                        <h1 className="text-xl font-semibold text-[#303848]">BNPL Copilot</h1>
                        <p className="text-xs text-[#505050]">Powered by Gemini & Local Pandas</p>
                    </div>
                </div>
                {showAnalyticsToggle && (
                    <button
                        onClick={onToggleAnalytics}
                        className="p-2 hover:bg-[#F8F8F8] rounded-lg transition-colors text-[#505050] hover:text-[#582098]"
                        title="Toggle Analytics Panel"
                    >
                        <BarChart3 size={20} />
                    </button>
                )}
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-[65%] mx-auto space-y-4">
                    {messages.length === 0 && (
                        <div className="mt-4">
                            <div className="flex gap-3 mb-6">
                                <div className="w-10 h-10 rounded-full bg-[#582098]/10 flex items-center justify-center shrink-0">
                                    <img src="/logo.png" alt="BNPL Copilot" className="w-10 h-10 object-contain" />
                                </div>
                                <div className="bg-[#F8F8F8] p-4 rounded-xl rounded-tl-none text-sm text-[#505050] leading-relaxed border border-border">
                                    <p className="font-medium text-[#303848] mb-2">Hello! I'm your BNPL Copilot.</p>
                                    <p>I can help you analyze payment trends, approval rates, risk metrics, and more. Try asking me questions like "What's today's approval rate?" or "Who is the most risky user?"</p>
                                </div>
                            </div>

                            <p className="text-[#505050] text-sm mb-3 ml-13">Try a sample query:</p>
                            <div className="grid grid-cols-1 gap-2 ml-13">
                                {suggestions.map((s) => (
                                    <button
                                        key={s}
                                        onClick={() => onSendMessage(s)}
                                        className="text-left text-sm p-3 rounded-xl border border-border hover:border-[#582098]/50 hover:bg-[#582098]/5 transition-all text-[#303848]"
                                    >
                                        {s}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {messages.map((m) => (
                        <div key={m.id} className={`flex gap-3 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${m.role === 'user'
                                ? 'bg-[#582098] text-white'
                                : 'bg-[#582098]/10'
                                }`}>
                                {m.role === 'user' ? <User size={18} /> : <img src="/logo.png" alt="BNPL Copilot" className="w-10 h-10 object-contain" />}
                            </div>
                            <div className={`p-4 rounded-xl text-sm leading-relaxed ${m.role === 'user'
                                ? 'bg-[#582098] text-white rounded-tr-none'
                                : 'bg-[#F8F8F8] text-[#303848] rounded-tl-none border border-border'
                                }`}>
                                {m.content}
                                {m.hasAnalytics && m.role === 'assistant' && (
                                    <div className="mt-2 pt-2 border-t border-border">
                                        <span className="inline-flex items-center gap-1 text-xs text-[#582098] bg-[#582098]/10 px-2 py-1 rounded-full">
                                            <BarChart3 size={12} />
                                            View analysis
                                        </span>
                                    </div>
                                )}
                                {m.role === 'assistant' && (
                                    <FeedbackButtons
                                        query={messages.find(msg => msg.id < m.id && msg.role === 'user')?.content || ''}
                                        response={m.content}
                                    />
                                )}
                            </div>
                        </div>
                    ))}

                    {isLoading && (
                        <div className="flex gap-3">
                            <div className="w-10 h-10 rounded-full bg-[#582098]/10 flex items-center justify-center shrink-0">
                                <img src="/logo.png" alt="BNPL Copilot" className="w-10 h-10 object-contain" />
                            </div>
                            <div className="flex items-center gap-2 text-[#505050] text-sm p-4 bg-[#F8F8F8] rounded-xl rounded-tl-none border border-border">
                                <Loader2 className="animate-spin" size={14} /> Analyzing...
                            </div>
                        </div>
                    )}
                    <div ref={scrollRef} />
                </div>
            </div>

            {/* Input */}
            <div className="p-4 border-t border-border bg-white">
                <form onSubmit={handleSubmit} className="relative max-w-[65%] mx-auto">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask about GMV, users, merchants, or risk..."
                        className="w-full pl-4 pr-14 py-3 rounded-xl border border-border focus:outline-none focus:ring-2 focus:ring-[#582098]/20 focus:border-[#582098] transition-all text-sm bg-[#F8F8F8]"
                    />
                    <button
                        type="submit"
                        disabled={isLoading || !input.trim()}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-2.5 bg-[#582098] text-white rounded-lg hover:bg-[#582098]/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        <Send size={16} />
                    </button>
                </form>
            </div>
        </div>
    );
};

export default ChatPanel;
