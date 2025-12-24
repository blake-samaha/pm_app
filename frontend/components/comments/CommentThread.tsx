"use client";

import type { Comment } from "@/lib/api/types";
import { Loader2, Send, MessageSquare } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useEffect, useRef, useState } from "react";

interface CommentThreadProps {
    comments: Comment[] | undefined;
    isLoading: boolean;
    onAddComment: (content: string) => Promise<void>;
    isAddingComment: boolean;
}

/**
 * Get author display name: name first, fallback to email
 */
const getAuthorDisplay = (comment: Comment): string => {
    if (comment.author_name && comment.author_name.trim()) {
        return comment.author_name;
    }
    if (comment.author_email && comment.author_email.trim()) {
        return comment.author_email;
    }
    return "Unknown";
};

/**
 * Get initials from a name or email
 */
const getInitials = (str: string): string => {
    if (!str) return "?";
    // If it's an email, use first letter
    if (str.includes("@")) {
        return str[0].toUpperCase();
    }
    // For names, use first letters of first and last name
    const parts = str.trim().split(/\s+/);
    if (parts.length >= 2) {
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return str.slice(0, 2).toUpperCase();
};

/**
 * Generate a consistent color based on a string
 */
const getAvatarColor = (str: string): string => {
    const colors = [
        "bg-blue-500",
        "bg-emerald-500",
        "bg-amber-500",
        "bg-rose-500",
        "bg-violet-500",
        "bg-cyan-500",
        "bg-fuchsia-500",
        "bg-lime-500",
    ];
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
};

/**
 * Shared comment thread component for both Risks and Actions.
 * Displays comments with author identity (name/email fallback) + timestamp.
 * Ordered oldest → newest with auto-scroll to bottom.
 */
export const CommentThread = ({
    comments,
    isLoading,
    onAddComment,
    isAddingComment,
}: CommentThreadProps) => {
    const [newComment, setNewComment] = useState("");
    const scrollContainerRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom when comments change or on initial load
    useEffect(() => {
        if (scrollContainerRef.current && comments && comments.length > 0) {
            scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
        }
    }, [comments]);

    const handleSubmit = async () => {
        if (!newComment.trim()) return;
        try {
            await onAddComment(newComment.trim());
            setNewComment("");
        } catch (error) {
            console.error("Failed to add comment:", error);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    return (
        <div className="flex h-full flex-col">
            {/* Header */}
            <div className="mb-4 flex items-center">
                <MessageSquare className="mr-2 h-4 w-4 text-slate-500" />
                <h4 className="text-sm font-bold text-slate-900">Comments</h4>
                {comments && comments.length > 0 && (
                    <span className="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                        {comments.length}
                    </span>
                )}
            </div>

            {/* Comment List */}
            <div
                ref={scrollContainerRef}
                className="mb-4 flex-1 space-y-3 overflow-y-auto"
                style={{ maxHeight: "300px" }}
            >
                {isLoading ? (
                    <div className="flex justify-center py-8">
                        <Loader2 className="h-5 w-5 animate-spin text-slate-400" />
                    </div>
                ) : comments && comments.length > 0 ? (
                    comments.map((comment) => {
                        const authorDisplay = getAuthorDisplay(comment);
                        const initials = getInitials(authorDisplay);
                        const avatarColor = getAvatarColor(
                            comment.author_email || comment.author_name || "unknown"
                        );

                        return (
                            <div key={comment.id} className="flex gap-3">
                                {/* Avatar */}
                                <div
                                    className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full text-xs font-bold text-white ${avatarColor}`}
                                >
                                    {initials}
                                </div>
                                {/* Content */}
                                <div className="flex-1 rounded-lg bg-slate-50 p-3">
                                    <div className="mb-1 flex items-center justify-between">
                                        <span className="text-xs font-semibold text-slate-700">
                                            {authorDisplay}
                                        </span>
                                        <span className="text-[10px] text-slate-400">
                                            {new Date(comment.created_at).toLocaleString()}
                                        </span>
                                    </div>
                                    <p className="text-sm text-slate-600">{comment.content}</p>
                                </div>
                            </div>
                        );
                    })
                ) : (
                    <div className="flex flex-col items-center justify-center py-8 text-center">
                        <MessageSquare className="mb-2 h-8 w-8 text-slate-200" />
                        <p className="text-sm text-slate-400">No comments yet</p>
                        <p className="text-xs text-slate-300">Be the first to add one!</p>
                    </div>
                )}
            </div>

            {/* Add Comment Input */}
            <div className="flex gap-2 border-t border-slate-100 pt-4">
                <Input
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    placeholder="Add a comment..."
                    className="flex-1"
                    onKeyDown={handleKeyDown}
                    disabled={isAddingComment}
                />
                <Button
                    size="sm"
                    onClick={handleSubmit}
                    disabled={!newComment.trim() || isAddingComment}
                >
                    {isAddingComment ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                        <Send className="h-4 w-4" />
                    )}
                </Button>
            </div>
        </div>
    );
};
