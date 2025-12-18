import axios from "axios";

// Use /api prefix for all API calls - Next.js rewrites proxy them to the backend
// This distinguishes API calls from page routes (e.g., /projects/123 page vs /api/projects/123 API)
// Set NEXT_PUBLIC_API_URL to override (e.g., for direct backend access in development)
const API_URL = process.env.NEXT_PUBLIC_API_URL || "/api";

export { API_URL };

export const api = axios.create({
    baseURL: API_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

// Add a request interceptor to attach the token and impersonation header
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem("accessToken");
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        // Add impersonation header if set (for superuser viewing as another user)
        const authStorage = localStorage.getItem("auth-storage");
        if (authStorage) {
            try {
                const { state } = JSON.parse(authStorage);
                const url = config.url || "";
                // Do not impersonate calls that must remain "actor" scoped (admin tooling),
                // otherwise impersonating a Client would break superuser-only endpoints.
                // Note: URLs may or may not have /api prefix depending on baseURL config
                const isActorScopedEndpoint =
                    url.startsWith("/users") ||
                    url.startsWith("/auth") ||
                    url.startsWith("/api/users") ||
                    url.startsWith("/api/auth");

                if (!isActorScopedEndpoint && state.impersonatingUserId) {
                    config.headers["X-Impersonate-User-Id"] = state.impersonatingUserId;
                }
            } catch {
                // Ignore parse errors
            }
        }

        return config;
    },
    (error) => Promise.reject(error)
);

/**
 * Upload a logo file to the server.
 * @param file The image file to upload
 * @returns The URL path to the uploaded file
 */
export async function uploadLogo(file: File): Promise<string> {
    const formData = new FormData();
    formData.append("file", file);

    const { data } = await api.post<{ url: string }>("/uploads/logo", formData, {
        headers: {
            "Content-Type": "multipart/form-data",
        },
    });

    return data.url;
}
