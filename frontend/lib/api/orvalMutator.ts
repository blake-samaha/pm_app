/**
 * Custom Axios instance for Orval-generated API client.
 *
 * This mutator wraps our existing Axios instance (from lib/api.ts) so that
 * the generated React Query hooks automatically include:
 * - Authorization header (JWT token)
 * - X-Impersonate-User-Id header (when impersonating)
 * - Proper base URL configuration
 */

import Axios, { AxiosError, AxiosRequestConfig } from "axios";
import { api } from "@/lib/api";

/**
 * Custom instance that Orval uses to make API requests.
 *
 * This wraps the existing `api` Axios instance which already has
 * interceptors for auth tokens and impersonation headers.
 */
export const customInstance = <T>(config: AxiosRequestConfig): Promise<T> => {
    const source = Axios.CancelToken.source();

    const promise = api({
        ...config,
        cancelToken: source.token,
    }).then(({ data }) => data);

    // @ts-expect-error - Adding cancel method for React Query
    promise.cancel = () => {
        source.cancel("Query was cancelled");
    };

    return promise;
};

export default customInstance;

/**
 * Error type for API errors.
 * This is used by generated hooks for error typing.
 */
export type ErrorType<Error> = AxiosError<Error>;

/**
 * Body type for request bodies.
 * This is used by generated hooks for request body typing.
 */
export type BodyType<BodyData> = BodyData;
