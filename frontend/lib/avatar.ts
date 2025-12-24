/**
 * Get initials from a name (up to 2 characters).
 */
export const getInitials = (name: string): string => {
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) {
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
};

/**
 * Generate a consistent color based on a string (for avatar backgrounds).
 */
export const getAvatarColor = (str: string): string => {
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
