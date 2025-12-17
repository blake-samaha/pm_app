"use client";

import { useState, useRef, useCallback } from "react";
import { Upload, Link as LinkIcon, X, Image as ImageIcon } from "lucide-react";
import { toast } from "sonner";

interface ImageUploadProps {
    currentUrl?: string | null;
    onUrlChange: (url: string | null) => void;
    onFileSelect: (file: File | null) => void;
    selectedFile?: File | null;
    disabled?: boolean;
}

const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"];
const MAX_SIZE_MB = 2;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

export const ImageUpload = ({
    currentUrl,
    onUrlChange,
    onFileSelect,
    selectedFile,
    disabled = false,
}: ImageUploadProps) => {
    const [showUrlInput, setShowUrlInput] = useState(false);
    const [urlInput, setUrlInput] = useState("");
    const [isDragging, setIsDragging] = useState(false);
    const [imageError, setImageError] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Generate preview URL for selected file
    const filePreviewUrl = selectedFile ? URL.createObjectURL(selectedFile) : null;

    const validateFile = (file: File): boolean => {
        if (!ALLOWED_TYPES.includes(file.type)) {
            toast.error("Invalid file type", {
                description: "Please upload a JPEG, PNG, GIF, or WebP image.",
            });
            return false;
        }
        if (file.size > MAX_SIZE_BYTES) {
            toast.error("File too large", {
                description: `Maximum file size is ${MAX_SIZE_MB}MB.`,
            });
            return false;
        }
        return true;
    };

    const handleFileChange = (file: File | null) => {
        if (file && validateFile(file)) {
            onFileSelect(file);
            onUrlChange(null);
            setUrlInput("");
            setShowUrlInput(false);
            setImageError(false);
        }
    };

    const handleDrop = useCallback(
        (e: React.DragEvent) => {
            e.preventDefault();
            setIsDragging(false);
            if (disabled) return;

            const file = e.dataTransfer.files[0];
            if (file) {
                handleFileChange(file);
            }
        },
        [disabled]
    );

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    // Auto-sync URL to parent when it becomes valid
    const handleUrlInputChange = (value: string) => {
        setUrlInput(value);
        // Automatically update parent when URL is valid
        if (value && (value.startsWith("http://") || value.startsWith("https://"))) {
            onUrlChange(value);
            onFileSelect(null);
        } else if (!value) {
            // Clear if input is emptied
            onUrlChange(null);
        }
    };

    const clearSelection = () => {
        onFileSelect(null);
        onUrlChange(null);
        setUrlInput("");
        setShowUrlInput(false);
        setImageError(false);
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    // Determine what preview to show
    const previewUrl = filePreviewUrl || (urlInput && urlInput.startsWith("http") ? urlInput : null);
    const hasSelection = selectedFile || urlInput;

    // If there's a selection (file or URL entered), show the preview state
    if (hasSelection) {
        return (
            <div className="space-y-3">
                <div className="flex items-center gap-4 rounded-lg border border-gray-200 bg-gray-50 p-4">
                    {previewUrl && !imageError ? (
                        <img
                            src={previewUrl}
                            alt="Logo preview"
                            onError={() => setImageError(true)}
                            className="h-14 w-14 rounded-lg object-cover bg-white shadow-sm"
                        />
                    ) : (
                        <div className="flex h-14 w-14 items-center justify-center rounded-lg bg-gray-200">
                            <ImageIcon className="h-6 w-6 text-gray-400" />
                        </div>
                    )}
                    <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                            {selectedFile ? selectedFile.name : "Image URL"}
                        </p>
                        <p className="text-xs text-gray-500 truncate">
                            {selectedFile 
                                ? `${(selectedFile.size / 1024).toFixed(1)} KB`
                                : urlInput
                            }
                        </p>
                    </div>
                    <button
                        type="button"
                        onClick={clearSelection}
                        disabled={disabled}
                        className="rounded-full p-1.5 text-gray-400 hover:bg-gray-200 hover:text-gray-600 transition-colors"
                    >
                        <X className="h-4 w-4" />
                    </button>
                </div>
                {imageError && urlInput && (
                    <p className="text-xs text-amber-600">
                        Could not preview image, but it may still work.
                    </p>
                )}
            </div>
        );
    }

    // Show current logo if exists and no new selection
    if (currentUrl && !hasSelection) {
        return (
            <div className="space-y-3">
                <div className="flex items-center gap-4 rounded-lg border border-gray-200 bg-gray-50 p-4">
                    <img
                        src={currentUrl.startsWith("/") 
                            ? `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${currentUrl}` 
                            : currentUrl}
                        alt="Current logo"
                        className="h-14 w-14 rounded-lg object-cover bg-white shadow-sm"
                        onError={(e) => {
                            (e.target as HTMLImageElement).src = "";
                            (e.target as HTMLImageElement).className = "h-14 w-14 rounded-lg bg-gray-200";
                        }}
                    />
                    <div className="flex-1">
                        <p className="text-sm font-medium text-gray-700">Current logo</p>
                        <p className="text-xs text-gray-500">Click below to replace</p>
                    </div>
                </div>
                
                {/* Replace options */}
                <div className="flex gap-2">
                    <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={disabled}
                        className="flex-1 flex items-center justify-center gap-2 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
                    >
                        <Upload className="h-4 w-4" />
                        Upload new
                    </button>
                    <button
                        type="button"
                        onClick={() => setShowUrlInput(true)}
                        disabled={disabled}
                        className="flex-1 flex items-center justify-center gap-2 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
                    >
                        <LinkIcon className="h-4 w-4" />
                        Use URL
                    </button>
                </div>
                
                <input
                    ref={fileInputRef}
                    type="file"
                    accept={ALLOWED_TYPES.join(",")}
                    onChange={(e) => handleFileChange(e.target.files?.[0] || null)}
                    disabled={disabled}
                    className="hidden"
                />

                {showUrlInput && (
                    <div className="flex gap-2">
                        <input
                            type="url"
                            value={urlInput}
                            onChange={(e) => handleUrlInputChange(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && e.preventDefault()}
                            placeholder="https://example.com/logo.png"
                            disabled={disabled}
                            autoFocus
                            className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                    </div>
                )}
            </div>
        );
    }

    // Default: no current logo, no selection - show upload zone
    return (
        <div className="space-y-3">
            {/* Drag and drop zone */}
            <div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => !disabled && fileInputRef.current?.click()}
                className={`relative flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 transition-colors ${
                    isDragging
                        ? "border-blue-500 bg-blue-50"
                        : "border-gray-300 hover:border-gray-400 hover:bg-gray-50"
                } ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    accept={ALLOWED_TYPES.join(",")}
                    onChange={(e) => handleFileChange(e.target.files?.[0] || null)}
                    disabled={disabled}
                    className="hidden"
                />
                <div className="rounded-full bg-gray-100 p-3">
                    <Upload className="h-6 w-6 text-gray-400" />
                </div>
                <p className="mt-3 text-sm font-medium text-gray-700">
                    Drop an image here, or click to browse
                </p>
                <p className="mt-1 text-xs text-gray-500">
                    JPEG, PNG, GIF, or WebP up to {MAX_SIZE_MB}MB
                </p>
            </div>

            {/* URL alternative */}
            {!showUrlInput ? (
                <button
                    type="button"
                    onClick={() => setShowUrlInput(true)}
                    disabled={disabled}
                    className="flex w-full items-center justify-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors disabled:opacity-50"
                >
                    <LinkIcon className="h-3.5 w-3.5" />
                    Or paste an image URL
                </button>
            ) : (
                <div className="flex gap-2">
                    <input
                        type="url"
                        value={urlInput}
                        onChange={(e) => handleUrlInputChange(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && e.preventDefault()}
                        placeholder="https://example.com/logo.png"
                        disabled={disabled}
                        autoFocus
                        className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                    <button
                        type="button"
                        onClick={() => {
                            setShowUrlInput(false);
                            handleUrlInputChange("");
                        }}
                        disabled={disabled}
                        className="rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-500 hover:bg-gray-50 transition-colors"
                    >
                        <X className="h-4 w-4" />
                    </button>
                </div>
            )}
        </div>
    );
};

