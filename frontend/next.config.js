/** @type {import('next').NextConfig} */
const nextConfig = {
    // Don't redirect based on trailing slashes - let requests pass through as-is
    // This prevents redirect loops when using API rewrites
    skipTrailingSlashRedirect: true,

    // Proxy API requests to the backend
    // All API calls use /api prefix to distinguish from page routes
    // This allows the app to work through the Cloudflare tunnel
    async rewrites() {
        // In Docker, use the service name; locally use localhost
        const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";

        return [
            // API endpoints - all use /api prefix to avoid conflicts with page routes
            // Auth endpoints
            {
                source: "/api/auth/:path*",
                destination: `${backendUrl}/auth/:path*`,
            },
            // Projects endpoints
            {
                source: "/api/projects",
                destination: `${backendUrl}/projects/`,
            },
            {
                source: "/api/projects/",
                destination: `${backendUrl}/projects/`,
            },
            {
                source: "/api/projects/:path*",
                destination: `${backendUrl}/projects/:path*`,
            },
            // Users endpoints
            {
                source: "/api/users",
                destination: `${backendUrl}/users/`,
            },
            {
                source: "/api/users/",
                destination: `${backendUrl}/users/`,
            },
            {
                source: "/api/users/:path*",
                destination: `${backendUrl}/users/:path*`,
            },
            // Actions endpoints
            {
                source: "/api/actions",
                destination: `${backendUrl}/actions/`,
            },
            {
                source: "/api/actions/",
                destination: `${backendUrl}/actions/`,
            },
            {
                source: "/api/actions/:path*",
                destination: `${backendUrl}/actions/:path*`,
            },
            // Risks endpoints
            {
                source: "/api/risks",
                destination: `${backendUrl}/risks/`,
            },
            {
                source: "/api/risks/",
                destination: `${backendUrl}/risks/`,
            },
            {
                source: "/api/risks/:path*",
                destination: `${backendUrl}/risks/:path*`,
            },
            // Sync endpoints
            {
                source: "/api/sync",
                destination: `${backendUrl}/sync/`,
            },
            {
                source: "/api/sync/",
                destination: `${backendUrl}/sync/`,
            },
            {
                source: "/api/sync/:path*",
                destination: `${backendUrl}/sync/:path*`,
            },
            // Uploads endpoints (for serving uploaded files - no /api prefix needed)
            {
                source: "/uploads/:path*",
                destination: `${backendUrl}/uploads/:path*`,
            },
        ];
    },
};

module.exports = nextConfig;
