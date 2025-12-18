import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/components/providers/AuthProvider";
import { AuthGuard } from "@/components/providers/AuthGuard";
import { QueryProvider } from "@/components/providers/QueryProvider";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Toaster } from "sonner";
import { CommandMenu } from "@/components/ui/command-menu";
import { ImpersonationBar } from "@/components/ImpersonationBar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "Automated Project Management Tool",
    description: "Project management for Cognite",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
            <body className={inter.className}>
                <QueryProvider>
                    <AuthProvider>
                        <AuthGuard>
                            <ErrorBoundary>
                                <ImpersonationBar />
                                <CommandMenu />
                                {children}
                            </ErrorBoundary>
                        </AuthGuard>
                    </AuthProvider>
                </QueryProvider>
                <Toaster richColors position="top-right" />
            </body>
        </html>
    );
}
