import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export { API_URL };

export const api = axios.create({
    baseURL: API_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

// Add a request interceptor to attach the token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem("accessToken");
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
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
