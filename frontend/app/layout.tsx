import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/components/providers/AuthProvider";
import { QueryProvider } from "@/components/providers/QueryProvider";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Toaster } from "sonner";

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
                        <ErrorBoundary>
                            {children}
                        </ErrorBoundary>
                    </AuthProvider>
                </QueryProvider>
                <Toaster richColors position="top-right" />
            </body>
        </html>
    );
}
