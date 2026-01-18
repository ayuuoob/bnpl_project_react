import { useState, useCallback } from "react";
import Sidebar from "../components/Sidebar";
import ChatPanel from "../components/ChatPanel";
import AnalyticsPanel from "../components/AnalyticsPanel";
import { AppNavbar } from "../components/AppNavbar";
import type { Message, ChatHistory, AnalyticsPayload } from "../types";

const API_URL = "http://localhost:8002";

export default function CopilotPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [analytics, setAnalytics] = useState<AnalyticsPayload | undefined>();
  const [chatHistory, setChatHistory] = useState<ChatHistory[]>([]);
  const [activeChat, setActiveChat] = useState<string | null>(null);
  const [showSidebar, setShowSidebar] = useState(true);
  const [showAnalytics, setShowAnalytics] = useState(false);

  const handleSendMessage = useCallback(
    async (content: string) => {
      const userMsg: Message = {
        id: `user_${Date.now()}`,
        role: "user",
        content,
      };

      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      try {
        const response = await fetch(`${API_URL}/api/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: content }),
        });

        if (!response.ok) {
          throw new Error("API request failed");
        }

        const data = await response.json();

        const assistantMsg: Message = {
          id: data.id || `assistant_${Date.now()}`,
          role: "assistant",
          content: data.content,
          hasAnalytics: data.hasAnalytics,
        };

        setMessages((prev) => [...prev, assistantMsg]);

        if (data.analytics) {
          setAnalytics(data.analytics);
          setShowAnalytics(true);
        }

        if (chatHistory.length === 0 || !activeChat) {
          const newChatId = `chat_${Date.now()}`;
          setChatHistory((prev) => [
            {
              id: newChatId,
              title: content.slice(0, 30) + (content.length > 30 ? "..." : ""),
              date: new Date(),
            },
            ...prev,
          ]);
          setActiveChat(newChatId);
        }
      } catch (error) {
        console.error("Error:", error);
        const errorMsg: Message = {
          id: `error_${Date.now()}`,
          role: "assistant",
          content:
            "Sorry, I encountered an error connecting to the server. Please make sure the backend is running on port 8002.",
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setIsLoading(false);
      }
    },
    [chatHistory, activeChat]
  );

  const handleNewChat = useCallback(() => {
    setMessages([]);
    setAnalytics(undefined);
    setActiveChat(null);
  }, []);

  const handleSelectChat = useCallback((id: string) => {
    setActiveChat(id);
    // In a real app, load the messages for this chat
  }, []);

  return (
    <div className="min-h-screen bg-[#F8F8F8]">
      <AppNavbar />

      {/* Make sure the copilot area fits under the navbar */}
      <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
        {/* Sidebar */}
        {showSidebar && (
          <div className="w-64 flex-shrink-0 transition-all duration-300">
            <Sidebar
              chatHistory={chatHistory}
              activeChat={activeChat}
              onNewChat={handleNewChat}
              onSelectChat={handleSelectChat}
              onToggleSidebar={() => setShowSidebar(false)}
            />
          </div>
        )}

        {/* Chat Panel */}
        <div className="flex-1 min-w-[400px] flex flex-col overflow-hidden">
          <ChatPanel
            messages={messages}
            isLoading={isLoading}
            onSendMessage={handleSendMessage}
            onToggleAnalytics={() => setShowAnalytics(!showAnalytics)}
            onToggleSidebar={() => setShowSidebar(!showSidebar)}
            showAnalyticsToggle={true}
            showSidebarToggle={!showSidebar}
          />
        </div>

        {/* Analytics Panel */}
        {showAnalytics && (
          <div className="w-[550px] flex-shrink-0 border-l border-border overflow-hidden">
            <AnalyticsPanel
              data={analytics}
              onClose={() => setShowAnalytics(false)}
            />
          </div>
        )}
      </div>
    </div>
  );
}
