/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
    forbidden: [
        // No circular dependencies
        {
            name: "no-circular",
            severity: "error",
            comment: "Circular dependencies make the codebase harder to understand and maintain.",
            from: {},
            to: {
                circular: true,
            },
        },

        // lib/ must not import from components/, hooks/, store/, or app/
        {
            name: "lib-no-upward-imports",
            severity: "error",
            comment: "lib/ should be low-level utilities that don't depend on React-specific code.",
            from: {
                path: "^lib/",
            },
            to: {
                path: "^(components|hooks|store|app)/",
            },
        },

        // hooks/ must not import from components/ or app/
        {
            name: "hooks-no-component-imports",
            severity: "error",
            comment:
                "hooks/ should provide data/state logic without depending on specific components.",
            from: {
                path: "^hooks/",
            },
            to: {
                path: "^(components|app)/",
            },
        },

        // store/ must not import from components/ or app/
        {
            name: "store-no-upward-imports",
            severity: "error",
            comment: "store/ should be pure state management without depending on UI components.",
            from: {
                path: "^store/",
            },
            to: {
                path: "^(components|app)/",
            },
        },

        // Nothing outside app/ should import from app/
        {
            name: "no-imports-from-app",
            severity: "error",
            comment: "app/ (routes/pages) is the top layer - other layers should not depend on it.",
            from: {
                path: "^(components|hooks|lib|store)/",
            },
            to: {
                path: "^app/",
            },
        },

        // components/ui/ should not import hooks/ or store/ (pure presentational)
        {
            name: "ui-components-are-pure",
            severity: "error",
            comment:
                "components/ui/ should be pure presentational components that receive all data via props.",
            from: {
                path: "^components/ui/",
            },
            to: {
                path: "^(hooks|store)/",
            },
        },

        // Forbid legacy types/ imports - use lib/api/types.ts instead
        {
            name: "no-legacy-types-imports",
            severity: "error",
            comment:
                "The types/ directory has been removed. Import types from lib/api/types.ts or lib/domain/enums.ts instead.",
            from: {},
            to: {
                path: "^types/",
            },
        },
    ],
    options: {
        doNotFollow: {
            path: "node_modules",
        },
        tsPreCompilationDeps: true,
        tsConfig: {
            fileName: "tsconfig.json",
        },
        enhancedResolveOptions: {
            exportsFields: ["exports"],
            conditionNames: ["import", "require", "node", "default"],
        },
        reporterOptions: {
            text: {
                highlightFocused: true,
            },
        },
    },
};
