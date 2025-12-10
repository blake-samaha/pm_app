"use client";

import { useRouter } from "next/navigation";
import { signInWithPopup } from "firebase/auth";
import {
    auth,
    googleProvider,
    signInWithEmailAndPassword,
    createUserWithEmailAndPassword,
    sendPasswordResetEmail,
} from "@/lib/firebase";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { useState } from "react";
import { Loader2, Mail, Lock, Eye, EyeOff } from "lucide-react";

export default function LoginPage() {
    const router = useRouter();
    const setAuth = useAuthStore((state) => state.setAuth);
    
    // Form state
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    
    // UI state
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [isRegistering, setIsRegistering] = useState(false);
    const [showForgotPassword, setShowForgotPassword] = useState(false);
    const [forgotEmail, setForgotEmail] = useState("");

    /**
     * Completes the login flow by sending the Firebase token to the backend
     * and storing the resulting JWT token.
     */
    const completeLogin = async (firebaseUser: any) => {
        const idToken = await firebaseUser.getIdToken();
        
        // Send token to backend for verification and JWT creation
        const response = await api.post("/auth/login", { token: idToken });
        const { access_token } = response.data;

        // Set token in localStorage for API interceptor
        localStorage.setItem("accessToken", access_token);

        // Get user info from backend
        const userResponse = await api.get("/auth/me");
        const user = userResponse.data;

        // Store in Zustand
        setAuth(user, access_token);
        router.push("/");
    };

    /**
     * Handle Google Sign-In
     */
    const handleGoogleSignIn = async () => {
        setLoading(true);
        setError(null);
        setSuccess(null);

        try {
            const result = await signInWithPopup(auth, googleProvider);
            await completeLogin(result.user);
        } catch (err: any) {
            console.error("Google login failed", err);
            
            if (err.code === "auth/popup-closed-by-user") {
                setError("Sign-in was cancelled. Please try again.");
            } else if (err.code === "auth/popup-blocked") {
                setError("Pop-up was blocked. Please allow pop-ups for this site.");
            } else if (err.code === "auth/configuration-not-found") {
                setError("Google Sign-In is not configured. Please contact support.");
            } else {
                setError(err.message || "Google login failed. Please try again.");
            }
            
            localStorage.removeItem("accessToken");
        } finally {
            setLoading(false);
        }
    };

    /**
     * Handle Email/Password Sign-In or Registration
     */
    const handleEmailSignIn = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setSuccess(null);

        try {
            let userCredential;
            
            if (isRegistering) {
                // Create new account
                userCredential = await createUserWithEmailAndPassword(auth, email, password);
            } else {
                // Sign in existing user
                userCredential = await signInWithEmailAndPassword(auth, email, password);
            }

            await completeLogin(userCredential.user);
        } catch (err: any) {
            console.error("Email login failed", err);
            
            // Handle Firebase auth errors with user-friendly messages
            switch (err.code) {
                case "auth/user-not-found":
                    setError("No account found with this email. Click 'Create Account' to register.");
                    break;
                case "auth/wrong-password":
                    setError("Incorrect password. Please try again.");
                    break;
                case "auth/invalid-credential":
                    setError("Invalid email or password. Please check and try again.");
                    break;
                case "auth/email-already-in-use":
                    setError("An account with this email already exists. Try signing in instead.");
                    break;
                case "auth/weak-password":
                    setError("Password should be at least 6 characters.");
                    break;
                case "auth/invalid-email":
                    setError("Please enter a valid email address.");
                    break;
                case "auth/too-many-requests":
                    setError("Too many failed attempts. Please try again later.");
                    break;
                default:
                    setError(err.message || "Authentication failed. Please try again.");
            }
            
            localStorage.removeItem("accessToken");
        } finally {
            setLoading(false);
        }
    };

    /**
     * Handle Password Reset
     */
    const handleForgotPassword = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setSuccess(null);

        try {
            await sendPasswordResetEmail(auth, forgotEmail);
            setSuccess("Password reset email sent! Check your inbox.");
            setShowForgotPassword(false);
            setForgotEmail("");
        } catch (err: any) {
            console.error("Password reset failed", err);
            
            switch (err.code) {
                case "auth/user-not-found":
                    setError("No account found with this email address.");
                    break;
                case "auth/invalid-email":
                    setError("Please enter a valid email address.");
                    break;
                default:
                    setError(err.message || "Failed to send reset email. Please try again.");
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
            <div className="w-full max-w-md space-y-6 rounded-2xl bg-white p-8 shadow-2xl">
                {/* Header */}
                <div className="text-center">
                    <h2 className="text-3xl font-bold text-gray-900">
                        {showForgotPassword ? "Reset Password" : (isRegistering ? "Create Account" : "Welcome Back")}
                    </h2>
                    <p className="mt-2 text-sm text-gray-600">
                        {showForgotPassword 
                            ? "Enter your email to receive a reset link"
                            : "Automated Project Management Tool"
                        }
                    </p>
                </div>

                {/* Success Message */}
                {success && (
                    <div className="rounded-lg bg-green-50 p-4 text-center text-sm text-green-700 border border-green-200">
                        {success}
                    </div>
                )}

                {/* Error Message */}
                {error && (
                    <div className="rounded-lg bg-red-50 p-4 text-center text-sm text-red-700 border border-red-200">
                        {error}
                    </div>
                )}

                {/* Forgot Password Form */}
                {showForgotPassword ? (
                    <form onSubmit={handleForgotPassword} className="space-y-4">
                        <div>
                            <label htmlFor="forgot-email" className="block text-sm font-medium text-gray-700">
                                Email address
                            </label>
                            <div className="relative mt-1">
                                <Mail className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
                                <input
                                    id="forgot-email"
                                    type="email"
                                    value={forgotEmail}
                                    onChange={(e) => setForgotEmail(e.target.value)}
                                    required
                                    placeholder="you@example.com"
                                    className="block w-full rounded-lg border border-gray-300 py-3 pl-10 pr-3 text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                                />
                            </div>
                        </div>
                        
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex w-full items-center justify-center rounded-lg bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            {loading ? (
                                <Loader2 className="h-5 w-5 animate-spin" />
                            ) : (
                                "Send Reset Link"
                            )}
                        </button>
                        
                        <button
                            type="button"
                            onClick={() => {
                                setShowForgotPassword(false);
                                setError(null);
                            }}
                            className="w-full text-sm text-gray-600 hover:text-gray-900"
                        >
                            ← Back to sign in
                        </button>
                    </form>
                ) : (
                    <>
                        {/* Google Sign-In Button */}
                        <button
                            onClick={handleGoogleSignIn}
                            disabled={loading}
                            className="flex w-full items-center justify-center gap-3 rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm font-medium text-gray-700 shadow-sm transition-all hover:bg-gray-50 hover:shadow focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            {loading ? (
                                <Loader2 className="h-5 w-5 animate-spin" />
                            ) : (
                                <svg className="h-5 w-5" viewBox="0 0 24 24">
                                    <path
                                        fill="#4285F4"
                                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                                    />
                                    <path
                                        fill="#34A853"
                                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                                    />
                                    <path
                                        fill="#FBBC05"
                                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                                    />
                                    <path
                                        fill="#EA4335"
                                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                                    />
                                </svg>
                            )}
                            Continue with Google
                        </button>

                        {/* Divider */}
                        <div className="relative">
                            <div className="absolute inset-0 flex items-center">
                                <div className="w-full border-t border-gray-200" />
                            </div>
                            <div className="relative flex justify-center text-sm">
                                <span className="bg-white px-4 text-gray-500">or continue with email</span>
                            </div>
                        </div>

                        {/* Email/Password Form */}
                        <form onSubmit={handleEmailSignIn} className="space-y-4">
                            <div>
                                <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                                    Email address
                                </label>
                                <div className="relative mt-1">
                                    <Mail className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
                                    <input
                                        id="email"
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                        placeholder="you@example.com"
                                        className="block w-full rounded-lg border border-gray-300 py-3 pl-10 pr-3 text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                                    />
                                </div>
                            </div>
                            
                            <div>
                                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                                    Password
                                </label>
                                <div className="relative mt-1">
                                    <Lock className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
                                    <input
                                        id="password"
                                        type={showPassword ? "text" : "password"}
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                        minLength={6}
                                        placeholder="••••••••"
                                        className="block w-full rounded-lg border border-gray-300 py-3 pl-10 pr-10 text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                                    >
                                        {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                                    </button>
                                </div>
                            </div>

                            {/* Forgot Password Link */}
                            {!isRegistering && (
                                <div className="text-right">
                                    <button
                                        type="button"
                                        onClick={() => {
                                            setShowForgotPassword(true);
                                            setError(null);
                                            setSuccess(null);
                                        }}
                                        className="text-sm text-blue-600 hover:text-blue-800"
                                    >
                                        Forgot password?
                                    </button>
                                </div>
                            )}

                            <button
                                type="submit"
                                disabled={loading}
                                className="flex w-full items-center justify-center rounded-lg bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                            >
                                {loading ? (
                                    <Loader2 className="h-5 w-5 animate-spin" />
                                ) : (
                                    isRegistering ? "Create Account" : "Sign In"
                                )}
                            </button>
                        </form>

                        {/* Toggle Sign In / Register */}
                        <div className="text-center">
                            <button
                                type="button"
                                onClick={() => {
                                    setIsRegistering(!isRegistering);
                                    setError(null);
                                    setSuccess(null);
                                }}
                                className="text-sm text-gray-600 hover:text-gray-900"
                            >
                                {isRegistering ? (
                                    <>Already have an account? <span className="font-semibold text-blue-600">Sign in</span></>
                                ) : (
                                    <>Need an account? <span className="font-semibold text-blue-600">Create one</span></>
                                )}
                            </button>
                        </div>
                    </>
                )}

                {/* Footer */}
                <p className="text-center text-xs text-gray-500">
                    By signing in, you agree to our Terms of Service and Privacy Policy
                </p>
            </div>
        </div>
    );
}
