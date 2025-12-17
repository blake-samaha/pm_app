import axios, { AxiosError } from "axios";

export function getErrorMessage(error: unknown): string {
    if (axios.isAxiosError(error)) {
        const axiosError = error as AxiosError<any>;
        if (axiosError.response?.data) {
            // Handle specific backend error formats
            if (typeof axiosError.response.data === "string") {
                return axiosError.response.data;
            }
            if (axiosError.response.data.detail) {
                return axiosError.response.data.detail;
            }
            if (axiosError.response.data.message) {
                return axiosError.response.data.message;
            }
        }
        return axiosError.message;
    }

    if (error instanceof Error) {
        return error.message;
    }

    if (typeof error === "string") {
        return error;
    }

    return "An unknown error occurred";
}


