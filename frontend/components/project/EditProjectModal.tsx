"use client";

import { useUpdateProject } from "@/hooks/useProjects";
import { HealthStatus, Project, ReportingCycle } from "@/types";
import { Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ImageUpload } from "@/components/ui/ImageUpload";
import { uploadLogo } from "@/lib/api";
import { toast } from "sonner";
import { useState, useEffect } from "react";

interface EditProjectModalProps {
    project: Project;
    isOpen: boolean;
    onClose: () => void;
}

export const EditProjectModal = ({ project, isOpen, onClose }: EditProjectModalProps) => {
    const updateProject = useUpdateProject();
    const [activeTab, setActiveTab] = useState<
        "general" | "branding" | "health" | "sprint" | "visibility"
    >("general");
    const [logoFile, setLogoFile] = useState<File | null>(null);
    const [logoUrl, setLogoUrl] = useState<string | null>(null);
    const [isUploading, setIsUploading] = useState(false);

    const [formData, setFormData] = useState({
        name: project.name,
        precursive_url: project.precursive_url,
        jira_url: project.jira_url,
        reporting_cycle: project.reporting_cycle || "",
        health_status_override: project.health_status_override || "",
        is_published: project.is_published,
        sprint_goals: project.sprint_goals || "",
        client_logo_url: project.client_logo_url || "",
    });

    // Reset form data when project changes or modal opens
    useEffect(() => {
        if (isOpen) {
            setFormData({
                name: project.name,
                precursive_url: project.precursive_url,
                jira_url: project.jira_url,
                reporting_cycle: project.reporting_cycle || "",
                health_status_override: project.health_status_override || "",
                is_published: project.is_published,
                sprint_goals: project.sprint_goals || "",
                client_logo_url: project.client_logo_url || "",
            });
            setLogoFile(null);
            setLogoUrl(null);
        }
    }, [project, isOpen]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        // Determine final logo URL
        let finalLogoUrl: string | null = formData.client_logo_url || null;

        // If a new URL was provided, use it
        if (logoUrl) {
            finalLogoUrl = logoUrl;
        }

        // If a file was selected, upload it first
        if (logoFile) {
            try {
                setIsUploading(true);
                finalLogoUrl = await uploadLogo(logoFile);
            } catch (error: any) {
                toast.error("Failed to upload logo", {
                    description: error.response?.data?.detail || "Please try again.",
                });
                setIsUploading(false);
                return;
            }
            setIsUploading(false);
        }

        // Filter out empty strings for optional enums to send null instead
        const payload: any = {
            ...formData,
            reporting_cycle: formData.reporting_cycle || null,
            health_status_override: formData.health_status_override || null,
            sprint_goals: formData.sprint_goals || null,
            client_logo_url: finalLogoUrl,
        };

        updateProject.mutate(
            { id: project.id, data: payload },
            {
                onSuccess: () => {
                    toast.success("Project updated", {
                        description: "Your changes have been saved.",
                    });
                    setLogoFile(null);
                    setLogoUrl(null);
                    onClose();
                },
                onError: (error: any) => {
                    toast.error("Failed to update project", {
                        description:
                            error.response?.data?.detail || "An unexpected error occurred.",
                    });
                },
            }
        );
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
            <div className="w-full max-w-lg overflow-hidden rounded-xl bg-white shadow-2xl">
                {/* Header */}
                <div className="flex items-center justify-between border-b px-6 py-4">
                    <h2 className="text-xl font-semibold text-gray-900">Project Settings</h2>
                    <button
                        onClick={onClose}
                        className="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-500"
                    >
                        <X className="h-5 w-5" />
                    </button>
                </div>

                {/* Tabs */}
                <div className="flex overflow-x-auto border-b px-6">
                    <button
                        onClick={() => setActiveTab("general")}
                        className={`whitespace-nowrap border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
                            activeTab === "general"
                                ? "border-blue-600 text-blue-600"
                                : "border-transparent text-gray-500 hover:text-gray-700"
                        }`}
                    >
                        General
                    </button>
                    <button
                        onClick={() => setActiveTab("branding")}
                        className={`whitespace-nowrap border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
                            activeTab === "branding"
                                ? "border-blue-600 text-blue-600"
                                : "border-transparent text-gray-500 hover:text-gray-700"
                        }`}
                    >
                        Branding
                    </button>
                    <button
                        onClick={() => setActiveTab("health")}
                        className={`whitespace-nowrap border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
                            activeTab === "health"
                                ? "border-blue-600 text-blue-600"
                                : "border-transparent text-gray-500 hover:text-gray-700"
                        }`}
                    >
                        Health
                    </button>
                    <button
                        onClick={() => setActiveTab("sprint")}
                        className={`border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
                            activeTab === "sprint"
                                ? "border-blue-600 text-blue-600"
                                : "border-transparent text-gray-500 hover:text-gray-700"
                        }`}
                    >
                        Sprint
                    </button>
                    <button
                        onClick={() => setActiveTab("visibility")}
                        className={`border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
                            activeTab === "visibility"
                                ? "border-blue-600 text-blue-600"
                                : "border-transparent text-gray-500 hover:text-gray-700"
                        }`}
                    >
                        Visibility
                    </button>
                </div>

                {/* Content */}
                <form onSubmit={handleSubmit} className="p-6">
                    {activeTab === "general" && (
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700">
                                    Project Name
                                </label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) =>
                                        setFormData({ ...formData, name: e.target.value })
                                    }
                                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">
                                    Reporting Cycle
                                </label>
                                <select
                                    value={formData.reporting_cycle}
                                    onChange={(e) =>
                                        setFormData({
                                            ...formData,
                                            reporting_cycle: e.target.value,
                                        })
                                    }
                                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                                >
                                    <option value="">Select cycle...</option>
                                    {Object.values(ReportingCycle).map((cycle) => (
                                        <option key={cycle} value={cycle}>
                                            {cycle}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">
                                    Jira URL
                                </label>
                                <input
                                    type="url"
                                    value={formData.jira_url}
                                    onChange={(e) =>
                                        setFormData({ ...formData, jira_url: e.target.value })
                                    }
                                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">
                                    Precursive URL
                                </label>
                                <input
                                    type="url"
                                    value={formData.precursive_url}
                                    onChange={(e) =>
                                        setFormData({ ...formData, precursive_url: e.target.value })
                                    }
                                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                                />
                            </div>
                        </div>
                    )}

                    {activeTab === "branding" && (
                        <div className="space-y-4">
                            <div className="rounded-md bg-purple-50 p-4">
                                <p className="text-sm text-purple-700">
                                    Add a client logo to personalize this project. You can upload an
                                    image or provide a URL to an existing logo.
                                </p>
                            </div>
                            <div>
                                <label className="mb-2 block text-sm font-medium text-gray-700">
                                    Client Logo
                                </label>
                                <ImageUpload
                                    currentUrl={formData.client_logo_url || null}
                                    onUrlChange={setLogoUrl}
                                    onFileSelect={setLogoFile}
                                    selectedFile={logoFile}
                                    disabled={updateProject.isPending || isUploading}
                                />
                            </div>
                        </div>
                    )}

                    {activeTab === "health" && (
                        <div className="space-y-4">
                            <div className="rounded-md bg-blue-50 p-4">
                                <p className="text-sm text-blue-700">
                                    The system automatically calculates health based on Precursive
                                    data. Use this setting to manually override that status.
                                </p>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">
                                    Health Status Override
                                </label>
                                <select
                                    value={formData.health_status_override}
                                    onChange={(e) =>
                                        setFormData({
                                            ...formData,
                                            health_status_override: e.target.value,
                                        })
                                    }
                                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                                >
                                    <option value="">No Override (Use Automated)</option>
                                    {Object.values(HealthStatus).map((status) => (
                                        <option key={status} value={status}>
                                            {status}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    )}

                    {activeTab === "sprint" && (
                        <div className="space-y-4">
                            <div className="rounded-md bg-indigo-50 p-4">
                                <p className="text-sm text-indigo-700">
                                    Sprint goals are automatically synced from your active Jira
                                    sprint. You can also manually override them here.
                                </p>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">
                                    Current Sprint Goals
                                </label>
                                <textarea
                                    value={formData.sprint_goals}
                                    onChange={(e) =>
                                        setFormData({ ...formData, sprint_goals: e.target.value })
                                    }
                                    rows={5}
                                    placeholder="Enter the goals for the current sprint..."
                                    className="mt-1 block w-full resize-none rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                                />
                                <p className="mt-2 text-xs text-gray-500">
                                    This will be displayed on the project details page.
                                </p>
                            </div>
                        </div>
                    )}

                    {activeTab === "visibility" && (
                        <div className="space-y-4">
                            <div className="flex items-center justify-between rounded-lg border p-4">
                                <div>
                                    <h3 className="font-medium text-gray-900">Publish Project</h3>
                                    <p className="text-sm text-gray-500">
                                        Published projects are visible to assigned Client users.
                                    </p>
                                </div>
                                <label className="relative inline-flex cursor-pointer items-center">
                                    <input
                                        type="checkbox"
                                        checked={formData.is_published}
                                        onChange={(e) =>
                                            setFormData({
                                                ...formData,
                                                is_published: e.target.checked,
                                            })
                                        }
                                        className="peer sr-only"
                                    />
                                    <div className="peer h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-blue-600 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rtl:peer-checked:after:-translate-x-full"></div>
                                </label>
                            </div>
                        </div>
                    )}

                    {/* Footer */}
                    <div className="mt-8 flex justify-end space-x-3 border-t border-gray-100 pt-4">
                        <Button type="button" variant="outline" onClick={onClose}>
                            Cancel
                        </Button>
                        <Button type="submit" disabled={updateProject.isPending || isUploading}>
                            {(updateProject.isPending || isUploading) && (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            )}
                            {isUploading ? "Uploading..." : "Save Changes"}
                        </Button>
                    </div>
                </form>
            </div>
        </div>
    );
};
