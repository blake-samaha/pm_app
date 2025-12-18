"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import { Home, Folder, LogOut, Laptop } from "lucide-react";
import { useAuthStore } from "@/store/authStore";

export function CommandMenu() {
    const [open, setOpen] = React.useState(false);
    const router = useRouter();
    const { logout, user } = useAuthStore();

    React.useEffect(() => {
        const down = (e: KeyboardEvent) => {
            if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                setOpen((open) => !open);
            }
        };
        document.addEventListener("keydown", down);
        return () => document.removeEventListener("keydown", down);
    }, []);

    return (
        <Command.Dialog
            open={open}
            onOpenChange={setOpen}
            label="Global Command Menu"
            className="fixed inset-0 z-50 flex items-start justify-center bg-slate-900/20 p-4 pt-[20vh] backdrop-blur-sm transition-all"
        >
            <div className="w-full max-w-lg overflow-hidden rounded-xl border border-slate-200 bg-white shadow-2xl ring-1 ring-slate-900/5">
                <Command.Input
                    className="w-full border-b border-slate-100 p-4 text-base text-slate-900 outline-none placeholder:text-slate-400"
                    placeholder="Type a command or search..."
                />
                <Command.List className="max-h-[300px] scroll-py-2 overflow-y-auto p-2">
                    <Command.Empty className="py-6 text-center text-sm text-slate-500">
                        No results found.
                    </Command.Empty>

                    <Command.Group
                        heading="Navigation"
                        className="px-2 py-1.5 text-xs font-medium uppercase tracking-wider text-slate-400"
                    >
                        <Command.Item
                            onSelect={() => {
                                setOpen(false);
                                router.push("/");
                            }}
                            className="flex cursor-pointer items-center rounded-md px-2 py-2.5 text-sm text-slate-700 transition-colors aria-selected:bg-slate-100 aria-selected:text-slate-900"
                        >
                            <Home className="mr-2 h-4 w-4 text-slate-500" />
                            Home
                        </Command.Item>
                        <Command.Item
                            onSelect={() => {
                                setOpen(false);
                                router.push("/");
                            }}
                            className="flex cursor-pointer items-center rounded-md px-2 py-2.5 text-sm text-slate-700 transition-colors aria-selected:bg-slate-100 aria-selected:text-slate-900"
                        >
                            <Folder className="mr-2 h-4 w-4 text-slate-500" />
                            Projects
                        </Command.Item>
                    </Command.Group>

                    <Command.Group
                        heading="Account"
                        className="mt-2 px-2 py-1.5 text-xs font-medium uppercase tracking-wider text-slate-400"
                    >
                        {user && (
                            <div className="flex items-center px-2 py-1.5 text-sm text-slate-500">
                                <Laptop className="mr-2 h-4 w-4 opacity-50" />
                                Signed in as {user.name}
                            </div>
                        )}
                        <Command.Item
                            onSelect={() => {
                                setOpen(false);
                                logout();
                                router.push("/login");
                            }}
                            className="flex cursor-pointer items-center rounded-md px-2 py-2.5 text-sm text-red-600 transition-colors aria-selected:bg-red-50 aria-selected:text-red-700"
                        >
                            <LogOut className="mr-2 h-4 w-4" />
                            Logout
                        </Command.Item>
                    </Command.Group>
                </Command.List>
            </div>
        </Command.Dialog>
    );
}
