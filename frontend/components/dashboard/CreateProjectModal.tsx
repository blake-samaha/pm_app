"use client";

import { useState } from "react";
import { useCreateProject } from "@/hooks/useProjects";
import { ProjectType, ReportingCycle } from "@/types";
import { X, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ImageUpload } from "@/components/ui/ImageUpload";
import { uploadLogo } from "@/lib/api";
import { toast } from "sonner";

interface CreateProjectModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export const CreateProjectModal = ({ isOpen, onClose }: CreateProjectModalProps) => {
    const createProject = useCreateProject();
    const [logoFile, setLogoFile] = useState<File | null>(null);
    const [logoUrl, setLogoUrl] = useState<string | null>(null);
    const [isUploading, setIsUploading] = useState(false);

    const resetForm = () => {
        setLogoFile(null);
        setLogoUrl(null);
        setIsUploading(false);
    };

    const handleClose = () => {
        resetForm();
        onClose();
    };

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();

        const formData = new FormData(e.currentTarget);

        // Determine final logo URL
        let finalLogoUrl: string | null = logoUrl;

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

        const data = {
            name: formData.get("name") as string,
            precursive_url: formData.get("precursive_url") as string,
            jira_url: formData.get("jira_url") as string,
            type: formData.get("type") as string,
            reporting_cycle: formData.get("reporting_cycle") as string,
            client_logo_url: finalLogoUrl,
        };

        createProject.mutate(data, {
            onSuccess: () => {
                toast.success("Project created", {
                    description: `"${data.name}" has been created successfully.`,
                });
                resetForm();
                onClose();
            },
            onError: (error: any) => {
                toast.error("Failed to create project", {
                    description: error.response?.data?.detail || "An unexpected error occurred.",
                });
            },
        });
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
            <div className="w-full max-w-lg rounded-xl bg-white shadow-2xl">
                <div className="flex items-center justify-between border-b p-6">
                    <h2 className="text-xl font-semibold text-gray-900">Create New Project</h2>
                    <button onClick={handleClose} className="text-gray-400 hover:text-gray-500">
                        <X className="h-6 w-6" />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4 p-6">
                    {createProject.isError && (
                        <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">
                            {(createProject.error as any)?.response?.data?.detail ||
                                "Failed to create project"}
                        </div>
                    )}

                    <div>
                        <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                            Project Name
                        </label>
                        <input
                            type="text"
                            name="name"
                            id="name"
                            required
                            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                    </div>

                    <div>
                        <label
                            htmlFor="precursive_url"
                            className="block text-sm font-medium text-gray-700"
                        >
                            Precursive URL
                        </label>
                        <input
                            type="url"
                            name="precursive_url"
                            id="precursive_url"
                            required
                            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                    </div>

                    <div>
                        <label
                            htmlFor="jira_url"
                            className="block text-sm font-medium text-gray-700"
                        >
                            Jira URL
                        </label>
                        <input
                            type="url"
                            name="jira_url"
                            id="jira_url"
                            required
                            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label
                                htmlFor="type"
                                className="block text-sm font-medium text-gray-700"
                            >
                                Project Type
                            </label>
                            <select
                                name="type"
                                id="type"
                                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            >
                                {Object.values(ProjectType).map((type) => (
                                    <option key={type} value={type}>
                                        {type}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label
                                htmlFor="reporting_cycle"
                                className="block text-sm font-medium text-gray-700"
                            >
                                Reporting Cycle
                            </label>
                            <select
                                name="reporting_cycle"
                                id="reporting_cycle"
                                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            >
                                {Object.values(ReportingCycle).map((cycle) => (
                                    <option key={cycle} value={cycle}>
                                        {cycle}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <div>
                        <label className="mb-2 block text-sm font-medium text-gray-700">
                            Client Logo
                        </label>
                        <ImageUpload
                            currentUrl={null}
                            onUrlChange={setLogoUrl}
                            onFileSelect={setLogoFile}
                            selectedFile={logoFile}
                            disabled={createProject.isPending || isUploading}
                        />
                    </div>

                    <div className="mt-6 flex justify-end space-x-3">
                        <Button type="button" variant="outline" onClick={handleClose}>
                            Cancel
                        </Button>
                        <Button type="submit" disabled={createProject.isPending || isUploading}>
                            {(createProject.isPending || isUploading) && (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            )}
                            {isUploading ? "Uploading..." : "Create Project"}
                        </Button>
                    </div>
                </form>
            </div>
        </div>
    );
};
