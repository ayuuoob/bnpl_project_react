import React, { useState, useRef, useEffect } from 'react';
import type { Message } from '../types';
import { Send, Bot, User, Loader2, BarChart3, PanelLeft } from 'lucide-react';

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
            <div className="flex items-center justify-between p-4 border-b border-gray-100">
                <div className="flex items-center gap-3">
                    {showSidebarToggle && (
                        <button
                            onClick={onToggleSidebar}
                            className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-500 hover:text-indigo-600"
                            title="Show sidebar"
                        >
                            <PanelLeft size={20} />
                        </button>
                    )}
                    <div>
                        <h1 className="text-xl font-bold text-gray-800">BNPL Copilot</h1>
                        <p className="text-xs text-gray-500">Powered by Gemini & Local Pandas</p>
                    </div>
                </div>
                {showAnalyticsToggle && (
                    <button
                        onClick={onToggleAnalytics}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-500 hover:text-indigo-600"
                        title="Toggle Analytics Panel"
                    >
                        <BarChart3 size={20} />
                    </button>
                )}
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 && (
                    <div className="mt-4">
                        <div className="flex gap-3 mb-6">
                            <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center shrink-0 text-indigo-600">
                                <Bot size={16} />
                            </div>
                            <div className="bg-gray-50 p-4 rounded-xl rounded-tl-none text-sm text-gray-700 leading-relaxed max-w-[85%]">
                                <p className="font-medium text-gray-800 mb-2">Hello! I'm your BNPL Copilot.</p>
                                <p>I can help you analyze payment trends, approval rates, risk metrics, and more. Try asking me questions like "What's today's approval rate?" or "Who is the most risky user?"</p>
                            </div>
                        </div>

                        <p className="text-gray-500 text-sm mb-3">Try a sample query:</p>
                        <div className="grid grid-cols-1 gap-2">
                            {suggestions.map((s) => (
                                <button
                                    key={s}
                                    onClick={() => onSendMessage(s)}
                                    className="text-left text-sm p-3 rounded-xl border border-gray-200 hover:border-indigo-300 hover:bg-indigo-50/50 transition-all text-gray-700"
                                >
                                    {s}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {messages.map((m) => (
                    <div key={m.id} className={`flex gap-3 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${m.role === 'user'
                            ? 'bg-indigo-600 text-white'
                            : 'bg-indigo-100 text-indigo-600'
                            }`}>
                            {m.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                        </div>
                        <div className={`max-w-[80%] p-3 rounded-xl text-sm leading-relaxed ${m.role === 'user'
                            ? 'bg-indigo-600 text-white rounded-tr-none'
                            : 'bg-gray-100 text-gray-800 rounded-tl-none'
                            }`}>
                            {m.content}
                            {m.hasAnalytics && m.role === 'assistant' && (
                                <div className="mt-2 pt-2 border-t border-gray-200/50">
                                    <span className="inline-flex items-center gap-1 text-xs text-indigo-600 bg-indigo-50 px-2 py-1 rounded-full">
                                        <BarChart3 size={12} />
                                        View analysis
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="flex gap-3">
                        <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center shrink-0 text-indigo-600">
                            <Bot size={16} />
                        </div>
                        <div className="flex items-center gap-2 text-gray-400 text-sm p-3 bg-gray-50 rounded-xl rounded-tl-none">
                            <Loader2 className="animate-spin" size={14} /> Analyzing...
                        </div>
                    </div>
                )}
                <div ref={scrollRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-gray-100 bg-white">
                <form onSubmit={handleSubmit} className="relative">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask about GMV, users, merchants, or risk..."
                        className="w-full pl-4 pr-12 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all text-sm bg-gray-50"
                    />
                    <button
                        type="submit"
                        disabled={isLoading || !input.trim()}
                        className="absolute right-2 top-2 p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        <Send size={16} />
                    </button>
                </form>
            </div>
        </div>
    );
};

export default ChatPanel;
