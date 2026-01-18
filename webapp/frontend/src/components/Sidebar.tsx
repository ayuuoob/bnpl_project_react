import React, { useState } from 'react';
import { Plus, Search, MessageSquare, PanelLeftClose } from 'lucide-react';
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
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-3 mb-2">{title}</h3>
                <div className="space-y-1">
                    {chats.map(chat => (
                        <button
                            key={chat.id}
                            onClick={() => onSelectChat(chat.id)}
                            className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-sm transition-colors ${activeChat === chat.id
                                ? 'bg-indigo-50 text-indigo-700'
                                : 'text-gray-600 hover:bg-gray-100'
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
        <div className="flex flex-col h-full bg-white border-r border-gray-200">
            {/* Header with toggle */}
            <div className="flex items-center justify-between p-2 border-b border-gray-100">
                <button
                    onClick={onNewChat}
                    className="flex-1 flex items-center justify-center gap-1 px-2 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-xs font-medium"
                >
                    <Plus size={14} />
                    <span className="hidden sm:inline">New</span>
                </button>
            </div>

            {/* Search */}
            <div className="p-2 border-b border-gray-100">
                <div className="relative">
                    <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Search..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-8 pr-2 py-1.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                    />
                </div>
            </div>

            {/* Chat History */}
            <div className="flex-1 overflow-y-auto p-1">
                <ChatGroup title="Today" chats={groupedChats.today} />
                <ChatGroup title="Yest." chats={groupedChats.yesterday} />
                <ChatGroup title="Week" chats={groupedChats.week} />
                <ChatGroup title="Older" chats={groupedChats.older} />

                {filteredChats.length === 0 && (
                    <div className="text-center text-gray-400 text-xs py-4">
                        {searchQuery ? 'No match' : 'Empty'}
                    </div>
                )}
            </div>
        </div>
    );
};

export default Sidebar;
