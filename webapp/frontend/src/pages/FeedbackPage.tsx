import { useEffect, useState } from "react";
import { ThumbsUp, ThumbsDown, MessageSquare, TrendingUp } from "lucide-react";

interface FeedbackEntry {
    timestamp: string;
    query: string;
    response_snippet: string;
    rating: string;
    comment: string;
}

interface FeedbackStats {
    total: number;
    positive_pct: number;
    entries: FeedbackEntry[];
}

export default function FeedbackPage() {
    const [stats, setStats] = useState<FeedbackStats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch("http://localhost:8002/api/feedback")
            .then((res) => res.json())
            .then((data) => {
                setStats(data);
                setLoading(false);
            })
            .catch((err) => {
                console.error("Failed to fetch feedback:", err);
                setLoading(false);
            });
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#582098]"></div>
            </div>
        );
    }

    return (
        <div className="p-8 max-w-6xl mx-auto">
            <h1 className="text-2xl font-bold text-[#303848] mb-6">Feedback Dashboard</h1>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                <div className="bg-white rounded-xl border border-border p-6">
                    <div className="flex items-center gap-3">
                        <div className="p-3 bg-[#582098]/10 rounded-lg">
                            <MessageSquare className="h-6 w-6 text-[#582098]" />
                        </div>
                        <div>
                            <p className="text-sm text-[#505050]">Total Feedback</p>
                            <p className="text-2xl font-bold text-[#303848]">{stats?.total || 0}</p>
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-xl border border-border p-6">
                    <div className="flex items-center gap-3">
                        <div className="p-3 bg-green-100 rounded-lg">
                            <ThumbsUp className="h-6 w-6 text-green-600" />
                        </div>
                        <div>
                            <p className="text-sm text-[#505050]">Positive Rate</p>
                            <p className="text-2xl font-bold text-green-600">{stats?.positive_pct || 0}%</p>
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-xl border border-border p-6">
                    <div className="flex items-center gap-3">
                        <div className="p-3 bg-red-100 rounded-lg">
                            <ThumbsDown className="h-6 w-6 text-red-600" />
                        </div>
                        <div>
                            <p className="text-sm text-[#505050]">Negative Rate</p>
                            <p className="text-2xl font-bold text-red-600">{100 - (stats?.positive_pct || 0)}%</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Feedback Table */}
            <div className="bg-white rounded-xl border border-border overflow-hidden">
                <div className="px-6 py-4 border-b border-border">
                    <h2 className="font-semibold text-[#303848]">Recent Feedback</h2>
                </div>

                {stats?.entries && stats.entries.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-[#F8F8F8]">
                                <tr>
                                    <th className="text-left px-6 py-3 text-xs font-medium text-[#505050] uppercase">Time</th>
                                    <th className="text-left px-6 py-3 text-xs font-medium text-[#505050] uppercase">Query</th>
                                    <th className="text-left px-6 py-3 text-xs font-medium text-[#505050] uppercase">Response</th>
                                    <th className="text-left px-6 py-3 text-xs font-medium text-[#505050] uppercase">Rating</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border">
                                {stats.entries.slice().reverse().map((entry, idx) => (
                                    <tr key={idx} className="hover:bg-[#F8F8F8]/50">
                                        <td className="px-6 py-4 text-sm text-[#505050] whitespace-nowrap">
                                            {new Date(entry.timestamp).toLocaleString()}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-[#303848] max-w-xs truncate">
                                            {entry.query}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-[#505050] max-w-xs truncate">
                                            {entry.response_snippet}
                                        </td>
                                        <td className="px-6 py-4">
                                            {entry.rating === "positive" ? (
                                                <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs">
                                                    <ThumbsUp className="h-3 w-3" /> Helpful
                                                </span>
                                            ) : (
                                                <span className="inline-flex items-center gap-1 px-2 py-1 bg-red-100 text-red-700 rounded-full text-xs">
                                                    <ThumbsDown className="h-3 w-3" /> Not Helpful
                                                </span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="p-12 text-center text-[#505050]">
                        <MessageSquare className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                        <p>No feedback collected yet.</p>
                        <p className="text-sm">Use the chat and click 👍 or 👎 on AI responses.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
