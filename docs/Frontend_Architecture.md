# Frontend Architecture & Design Patterns

## 1. Overview

The frontend is a modern web application built with **Next.js 14 (App Router)**. It prioritizes type safety, developer experience, and architectural consistency. The application consumes the Python FastAPI backend via contract-driven OpenAPI types.

**Key Technologies:**
- **Framework**: Next.js 14 (React, App Router)
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS + Shadcn UI (built on Radix UI primitives)
- **State Management**:
  - **Server state**: TanStack Query (React Query) via Orval-generated hooks
  - **Global client state**: Zustand (`store/authStore.ts`) for authenticated user/session
- **API Client**: Orval-generated React Query hooks + Axios (custom instance in `lib/api/orvalMutator.ts`)
- **Type Generation**: Orval (OpenAPI to TypeScript)

## 2. Architecture

### 2.1. Contract-Driven Development

The frontend uses **OpenAPI-generated types and hooks** as the single source of truth for API contracts:

```
Backend Pydantic schemas → OpenAPI JSON → Orval → TypeScript types + React Query hooks
```

**Workflow:**
1. Backend defines response schemas in `backend/schemas/`
2. Run `make api-generate` to:
   - Export OpenAPI spec from FastAPI to `frontend/openapi.json`
   - Generate TypeScript models in `frontend/lib/api/generated/models/`
   - Generate React Query hooks in `frontend/lib/api/generated/*/`
   - Format generated files with Prettier

**Benefits:**
- Types are never manually defined—they come from the backend contract
- Breaking API changes are caught at compile time
- Generated hooks include proper error types and loading states

### 2.2. Type Import Surface

All API types are imported from a stable barrel file:

```typescript
// Import types from the stable barrel (not directly from generated/)
import type { Project, User, ActionItem, Risk } from "@/lib/api/types";
import { HealthStatus, UserRole, ActionStatus } from "@/lib/api/types";

// For ergonomic enum constants (uppercase keys)
import { HEALTH_STATUS, USER_ROLE, ACTION_STATUS } from "@/lib/domain/enums";
```

**Key files:**
- `lib/api/types.ts` - Re-exports generated models with convenience aliases
- `lib/domain/enums.ts` - Ergonomic wrappers for generated enums with uppercase keys

### 2.3. Layered Design

The frontend follows a strict layered architecture enforced by dependency-cruiser:

```
┌─────────────────────────────────────────┐
│          Page Layer (app/)              │  ← Route definitions, Layouts
├─────────────────────────────────────────┤
│      Feature Layer (components/)        │  ← Feature-specific components (containers)
├─────────────────────────────────────────┤
│        UI Layer (components/ui/)        │  ← Pure presentational components
├─────────────────────────────────────────┤
│        Logic Layer (hooks/)             │  ← React Query hooks, state management
├─────────────────────────────────────────┤
│      Data Layer (lib/, store/)          │  ← API types, utilities, Zustand stores
└─────────────────────────────────────────┘
```

**Layer Rules (enforced by `make arch-check`):**
- `lib/` must not import from `components/`, `hooks/`, `store/`, or `app/`
- `hooks/` must not import from `components/` or `app/`
- `store/` must not import from `components/` or `app/`
- `components/ui/` must not import from `hooks/` or `store/` (pure presentational)
- Nothing outside `app/` should import from `app/`
- No imports from the legacy `types/` path (directory has been removed)

## 3. Directory Structure

```text
frontend/
├── app/                        # Next.js App Router (Routes)
│   ├── layout.tsx              # Root layout (Providers, Fonts)
│   ├── page.tsx                # Dashboard (Home)
│   ├── login/                  # Login Route
│   └── projects/
│       └── [id]/               # Project Details Route
│
├── components/
│   ├── dashboard/              # Dashboard-specific components
│   ├── project/                # Project-specific components
│   ├── comments/               # Comment thread components
│   ├── ui/                     # Pure presentational components (Shadcn)
│   ├── providers/              # React Context Providers
│   ├── CommandMenu.tsx         # Container for command palette
│   └── ImpersonationBar.tsx    # Dev impersonation UI
│
├── hooks/                      # Custom React Hooks (Logic Layer)
│   ├── useActions.ts           # Action CRUD hooks (wraps generated)
│   ├── useProjects.ts          # Project CRUD hooks (wraps generated)
│   ├── useRisks.ts             # Risk CRUD hooks (wraps generated)
│   ├── useSync.ts              # Sync operation hooks
│   ├── useUsers.ts             # User management hooks
│   └── useEffectiveUser.ts     # Returns impersonated or real user
│
├── lib/                        # Utilities and Configuration
│   ├── api/
│   │   ├── types.ts            # Stable type import surface
│   │   ├── generated/          # Orval-generated code (DO NOT EDIT)
│   │   │   ├── models/         # TypeScript types
│   │   │   ├── actions/        # Action API hooks
│   │   │   ├── projects/       # Project API hooks
│   │   │   ├── risks/          # Risk API hooks
│   │   │   └── ...
│   │   └── orvalMutator.ts     # Custom Axios instance for Orval
│   ├── domain/
│   │   └── enums.ts            # Ergonomic enum wrappers
│   ├── api.ts                  # Legacy Axios instance (for upload)
│   ├── permissions.ts          # Role-based permission helpers
│   ├── error.ts                # Error handling utilities
│   └── utils.ts                # Helper functions
│
├── store/                      # Global Client State (Zustand)
│   └── authStore.ts            # Authenticated user/session
│
├── openapi.json                # Generated OpenAPI spec
├── orval.config.cjs            # Orval configuration
└── .dependency-cruiser.cjs     # Architecture rule definitions
```

## 4. Design Patterns

### 4.1. React Query Hooks

All data fetching uses Orval-generated React Query hooks wrapped in `hooks/*.ts`:

```typescript
// hooks/useProjects.ts
import { useListProjectsProjectsGet } from "@/lib/api/generated/projects/projects";

export const useProjects = () => {
    const { isAuthenticated } = useAuthStore();
    return useListProjectsProjectsGet({
        query: { enabled: isAuthenticated },
    });
};

// Usage in components
const { data: projects, isLoading, isError, error } = useProjects();
```

**Benefits:**
- Automatic caching and request deduplication
- Background refetching on focus/reconnect
- Mutation invalidation for optimistic updates
- Type-safe responses from OpenAPI contract

### 4.2. Container/Presentational Pattern

Feature components follow a container/presentational split where needed:

```typescript
// components/CommandMenu.tsx (container - handles logic)
export function CommandMenu() {
    const router = useRouter();
    const { logout } = useAuthStore();
    const user = useEffectiveUser();

    return (
        <CommandMenuUI
            userName={user?.name ?? null}
            onLogout={() => { logout(); router.push("/login"); }}
            onNavigate={(path) => router.push(path)}
        />
    );
}

// components/ui/command-menu.tsx (presentational - pure)
export function CommandMenuUI({ userName, onLogout, onNavigate }: Props) {
    // Pure rendering, no hooks/store imports allowed
}
```

### 4.3. Permission Helpers

Role-based access is handled via pure permission functions:

```typescript
// lib/permissions.ts
import type { UserRole } from "@/lib/api/types";
import { USER_ROLE } from "@/lib/domain/enums";

export const isCogniter = (role: UserRole): boolean =>
    role === USER_ROLE.COGNITER;

export const canViewFinancials = (role: UserRole): boolean =>
    role === USER_ROLE.COGNITER || role === USER_ROLE.CLIENT_FINANCIALS;

// Usage
const user = useEffectiveUser();
if (canViewFinancials(user.role)) {
    // show financials
}
```

## 5. Development Workflow

### 5.1. Regenerating API Types

When backend schemas change:

```bash
make api-generate
```

This exports the OpenAPI spec and regenerates all TypeScript types and hooks.

### 5.2. Architecture Checks

To verify layer boundaries and dependency rules:

```bash
make arch-check-frontend
# or from frontend/
npm run arch:check
```

**Rules enforced:**
- No circular dependencies
- Layer boundary violations (see Section 2.3)
- UI component purity (no hooks/store imports in `components/ui/`)
- No imports from removed `types/` directory

### 5.3. Building and Linting

```bash
cd frontend
npm run build     # Production build with type checking
npm run lint      # ESLint
npm run format    # Prettier formatting
```

## 6. Authentication

### 6.1. Auth Flow

1. User authenticates via Google OAuth or Firebase
2. Backend returns JWT access token
3. Token stored in Zustand auth store + localStorage
4. Orval custom instance attaches token to all API requests

### 6.2. Auth Store

```typescript
// store/authStore.ts
interface AuthState {
    user: User | null;
    accessToken: string | null;
    isAuthenticated: boolean;
    impersonatedUser: User | null;
    setAuth: (user: User, token: string) => void;
    logout: () => void;
}
```

### 6.3. Effective User Hook

Components use `useEffectiveUser()` which returns the impersonated user (dev mode) or the real user:

```typescript
const user = useEffectiveUser();
// Returns impersonatedUser if set, otherwise the authenticated user
```

## 7. API Integration

### 7.1. Generated Hooks (Primary)

Most API calls use Orval-generated hooks:

```typescript
// Queries
const { data, isLoading } = useListProjectsProjectsGet();
const { data: project } = useGetProjectProjectsProjectIdGet(projectId);

// Mutations
const createProject = useCreateProjectProjectsPost();
createProject.mutate({ data: projectData }, {
    onSuccess: () => queryClient.invalidateQueries(["projects"]),
});
```

### 7.2. Direct Axios (Fallback)

For operations not covered by generated hooks (e.g., file uploads):

```typescript
import { api, uploadLogo } from "@/lib/api";

const logoUrl = await uploadLogo(file);
await api.patch(`/projects/${id}`, { logo_url: logoUrl });
```

## 8. Testing

### 8.1. Architecture Tests

The architecture is validated by:
- `npm run arch:check` - Dependency-cruiser rules
- `npm run build` - TypeScript compilation

### 8.2. Manual Testing

For comprehensive testing, run:

```bash
make test-backend    # Backend unit + integration tests
npm run build        # Frontend type checking
npm run lint         # ESLint
```

## 9. Known Patterns

### 9.1. Enum Usage

Generated enums use capitalized keys (`HealthStatus.Green`). For cleaner code, use the domain wrapper:

```typescript
// Instead of: HealthStatus.Green (generated)
// Use: HEALTH_STATUS.GREEN (wrapper)

import { HEALTH_STATUS } from "@/lib/domain/enums";

if (project.health_status === HEALTH_STATUS.GREEN) { ... }
```

### 9.2. Nullable Fields

Generated types accurately reflect API optionality. Fields that can be null are typed as `Type | null` (not optional `?`):

```typescript
interface ProjectRead {
    id: string;                    // Required, never null
    name: string;                  // Required, never null
    client_logo_url: string | null; // Required, can be null
}
```

### 9.3. Mutation Signatures

Orval generates mutations that expect data wrapped in a `data` property:

```typescript
// Correct
createProject.mutate({ data: { name: "Project", ... } });

// Wrong - will cause TypeScript error
createProject.mutate({ name: "Project", ... });
```
