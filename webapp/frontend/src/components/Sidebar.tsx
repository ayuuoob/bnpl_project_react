import React, { useState } from 'react';
import { Plus, Search, MessageSquare, PanelLeftClose, ChevronLeft } from 'lucide-react';
import type { ChatHistory } from '../types';

interface Props {
    chatHistory: ChatHistory[];
    activeChat: string | null;
    onNewChat: () => void;
    onSelectChat: (id: string) => void;
    onToggleSidebar?: () => void;
}

const Sidebar: React.FC<Props> = ({ chatHistory, activeChat, onNewChat, onSelectChat, onToggleSidebar }) => {
    const [searchQuery, setSearchQuery] = useState('');

    const filteredChats = chatHistory.filter(chat =>
        chat.title.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const weekAgo = new Date(today);
    weekAgo.setDate(weekAgo.getDate() - 7);

    const groupedChats = {
        today: filteredChats.filter(c => new Date(c.date) >= today),
        yesterday: filteredChats.filter(c => new Date(c.date) >= yesterday && new Date(c.date) < today),
        week: filteredChats.filter(c => new Date(c.date) >= weekAgo && new Date(c.date) < yesterday),
        older: filteredChats.filter(c => new Date(c.date) < weekAgo)
    };

    const ChatGroup = ({ title, chats }: { title: string; chats: ChatHistory[] }) => {
        if (chats.length === 0) return null;
        return (
            <div className="mb-4">
                <h3 className="text-xs font-semibold text-[#505050] uppercase tracking-wider px-3 mb-2">{title}</h3>
                <div className="space-y-1">
                    {chats.map(chat => (
                        <button
                            key={chat.id}
                            onClick={() => onSelectChat(chat.id)}
                            className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-sm transition-colors ${activeChat === chat.id
                                ? 'bg-[#582098]/10 text-[#582098]'
                                : 'text-[#303848] hover:bg-[#F8F8F8]'
                                }`}
                        >
                            <MessageSquare size={14} className="shrink-0 opacity-60" />
                            <span className="truncate">{chat.title}</span>
                        </button>
                    ))}
                </div>
            </div>
        );
    };

    return (
        <div className="flex flex-col h-full bg-white border-r border-border">
            {/* Header with toggle */}
            <div className="flex items-center justify-between p-3 border-b border-border">
                <button
                    onClick={onNewChat}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2.5 bg-[#582098] text-white rounded-lg hover:bg-[#582098]/90 transition-colors text-sm font-medium"
                >
                    <Plus size={16} />
                    <span>New Chat</span>
                </button>
                {onToggleSidebar && (
                    <button
                        onClick={onToggleSidebar}
                        className="ml-2 p-2 rounded-lg text-[#505050] hover:bg-[#F8F8F8] hover:text-[#582098] transition-colors"
                        title="Close sidebar"
                    >
                        <ChevronLeft size={18} />
                    </button>
                )}
            </div>

            {/* Search */}
            <div className="p-3 border-b border-border">
                <div className="relative">
                    <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#505050]" />
                    <input
                        type="text"
                        placeholder="Search chats..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-9 pr-3 py-2 text-sm border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#582098]/20 focus:border-[#582098] bg-[#F8F8F8]"
                    />
                </div>
            </div>

            {/* Chat History */}
            <div className="flex-1 overflow-y-auto p-2">
                <ChatGroup title="Today" chats={groupedChats.today} />
                <ChatGroup title="Yesterday" chats={groupedChats.yesterday} />
                <ChatGroup title="This Week" chats={groupedChats.week} />
                <ChatGroup title="Older" chats={groupedChats.older} />

                {filteredChats.length === 0 && (
                    <div className="text-center text-[#505050] text-sm py-8">
                        {searchQuery ? 'No matching chats' : 'No chat history'}
                    </div>
                )}
            </div>
        </div>
    );
};

export default Sidebar;
