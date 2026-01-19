import { useState } from "react";
import { ThumbsUp, ThumbsDown, Check } from "lucide-react";

interface FeedbackButtonsProps {
    query: string;
    response: string;
}

export function FeedbackButtons({ query, response }: FeedbackButtonsProps) {
    const [submitted, setSubmitted] = useState(false);
    const [rating, setRating] = useState<"positive" | "negative" | null>(null);

    const handleFeedback = async (type: "positive" | "negative") => {
        if (submitted) return;

        setRating(type);

        try {
            await fetch("http://localhost:8002/api/feedback", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query: query,
                    response_snippet: response.substring(0, 300),
                    rating: type,
                }),
            });
            setSubmitted(true);
        } catch (error) {
            console.error("Failed to submit feedback:", error);
        }
    };

    if (submitted) {
        return (
            <div className="flex items-center gap-1 text-xs text-green-600">
                <Check className="h-3 w-3" />
                <span>Thanks for your feedback!</span>
            </div>
        );
    }

    return (
        <div className="flex items-center gap-2 mt-1">
            <span className="text-xs text-gray-400">Was this helpful?</span>
            <button
                onClick={() => handleFeedback("positive")}
                className={`p-1 rounded hover:bg-green-50 transition-colors ${rating === "positive" ? "text-green-600" : "text-gray-400 hover:text-green-600"
                    }`}
                title="Helpful"
            >
                <ThumbsUp className="h-4 w-4" />
            </button>
            <button
                onClick={() => handleFeedback("negative")}
                className={`p-1 rounded hover:bg-red-50 transition-colors ${rating === "negative" ? "text-red-600" : "text-gray-400 hover:text-red-600"
                    }`}
                title="Not helpful"
            >
                <ThumbsDown className="h-4 w-4" />
            </button>
        </div>
    );
}
