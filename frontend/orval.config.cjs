/**
 * Orval configuration for generating React Query hooks from OpenAPI.
 *
 * This generates:
 * - TypeScript types for all API request/response models
 * - React Query hooks (useQuery/useMutation) for all endpoints
 * - Uses our existing Axios instance for authentication/impersonation headers
 *
 * Run with: npm run api:generate
 */

/** @type {import('orval').Config} */
module.exports = {
    pmApp: {
        input: {
            target: "./openapi.json",
        },
        output: {
            target: "./lib/api/generated/index.ts",
            schemas: "./lib/api/generated/models",
            mode: "tags-split",
            client: "react-query",
            httpClient: "axios",
            override: {
                mutator: {
                    path: "./lib/api/orvalMutator.ts",
                    name: "customInstance",
                },
                query: {
                    useQuery: true,
                    useMutation: true,
                    useInfinite: false,
                    signal: true,
                },
            },
        },
        hooks: {
            afterAllFilesWrite: "prettier --write",
        },
    },
};
