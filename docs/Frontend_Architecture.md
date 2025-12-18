# Frontend Architecture & Design Patterns

> **Status Legend:**
> - 🟢 **IMPLEMENTED** - Currently working in production
> - 🟡 **PARTIAL** - Some work done, needs completion
> - 🔴 **PLANNED** - Not started, future work

## 1. Overview

The frontend of the Automated Project Management Tool is a modern web application built with **Next.js 14 (App Router)**. It prioritizes performance, type safety, and developer experience. The application consumes the Python FastAPI backend and provides a responsive interface for Cogniters and Clients.

**Key Technologies:**
- 🟢 **Framework**: Next.js 14 (React, App Router)
- 🟢 **Language**: TypeScript (strict mode)
- 🟢 **Styling**: Tailwind CSS
- 🟢 **UI Library**: Shadcn UI (built on Radix UI primitives)
- **State Management**:
  - 🟡 **Server state**: TanStack Query (React Query) - *installed but not yet integrated*
  - 🟢 **Global client state**: Zustand (`store/authStore.ts`) for authenticated user/session
- 🟢 **HTTP Client**: Axios (singleton instance in `lib/api.ts` with an auth interceptor)

## 2. Architecture

The application uses the **Next.js App Router** with a client-side rendering approach. All data fetching currently happens on the client using Axios with manual state management.

### 2.1. Rendering Strategy (Current - 🟢 IMPLEMENTED)

- **Root layout**:
  - `app/layout.tsx` is a **server component** that sets up global styles, fonts, and wraps the app in the `GoogleAuthProvider`.
- **Pages**:
  - `app/page.tsx` (dashboard), `app/login/page.tsx` (login), and `app/projects/[id]/page.tsx` (project detail) are **client components** (`"use client"`).
  - They run on the client and fetch data via Axios with `useState`/`useEffect`.

### 2.1.1. Data Fetching (Current Implementation - 🟢 IMPLEMENTED, 🔴 NEEDS REFACTOR)

**Current Pattern:**
All components fetch data directly using Axios with manual state management:

```typescript
// Current pattern in ProjectList, ActionTable, RiskList, etc.
const [data, setData] = useState([]);
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);

useEffect(() => {
  api.get("/endpoint")
    .then(res => setData(res.data))
    .catch(err => setError(err.message))
    .finally(() => setLoading(false));
}, []);
```

**Issues with Current Approach:**
- ❌ Repetitive boilerplate in every component
- ❌ No caching or request deduplication
- ❌ Manual error handling everywhere
- ❌ "Refresh hack" using key changes to force component remounts
- ❌ No optimistic updates
- ❌ Race conditions possible with concurrent requests

**Components Using This Pattern:**
- `ProjectList` - fetches all projects
- `ActionTable` - fetches actions for a project
- `RiskList` - fetches risks for a project
- `SyncButton` - triggers sync operations

### 2.2. Layered Design (🟡 PARTIAL)

The frontend follows a separation of concerns similar to the backend:

```
┌─────────────────────────────────────────┐
│          Page Layer (Pages)            │  ← Route definitions, Layouts
├─────────────────────────────────────────┤
│      Feature Layer (Components)        │  ← Feature-specific components
├─────────────────────────────────────────┤
│        UI Layer (components/ui)        │  ← Dumb/Presentational Components
├─────────────────────────────────────────┤
│        Logic Layer (hooks)             │  ← State, Effects, API calls
├─────────────────────────────────────────┤
│      Data Layer (lib/store)            │  ← Axios client, React Query, Zustand
└─────────────────────────────────────────┘
```

**Current mapping:**
- 🟢 **Page Layer**: `app/` (routes and layouts) - well organized
- 🟢 **Feature Layer**: `components/dashboard`, `components/project`, and `components/providers` - implemented
- 🟢 **UI Layer**: `components/ui` (Shadcn primitives like `Button`, `Card`) - working well
- 🟡 **Logic Layer**: `hooks/useProjects.ts` exists but is NOT USED. Most components still contain inline data fetching.
- 🟢 **Data Layer**: `lib/api.ts` (Axios instance + interceptor) and `store/authStore.ts` (Zustand for auth) - implemented

## 3. Directory Structure (🟢 IMPLEMENTED)

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
│   ├── ui/                     # Reusable UI components (Shadcn)
│   └── providers/              # React Context Providers (e.g. GoogleAuthProvider)
│
├── hooks/                      # Custom React Hooks (Logic Layer)
│   └── useProjects.ts          # React Query hooks: useProjects, useProject, useCreateProject
│
├── lib/                        # Utilities and Configuration
│   ├── api.ts                  # Axios instance & interceptors
│   ├── permissions.ts          # Role-based permission helpers
│   └── utils.ts                # Helper functions (Tailwind merge, etc.)
│
├── store/                      # Global Client State (Zustand)
│   └── authStore.ts            # Authenticated user/session
│
├── types/                      # TypeScript Definitions
│   ├── index.ts                # Project domain types (includes UserRole enum)
│   ├── actions-risks.ts        # Action & risk types
│   └── all.ts                  # Barrel exports
│
└── public/                     # Static Assets (standard Next.js folder)
```

## 4. Design Patterns

### 4.1. Custom Hooks (Logic Layer) - 🟡 PARTIAL

**Status: Hooks exist but are NOT integrated yet.**

React Query hooks for project data have been created in `hooks/useProjects.ts` but are **not currently used** by any components. The hooks are well-designed and ready to be integrated once QueryClientProvider is set up.

```typescript
// hooks/useProjects.ts (EXISTS, NOT USED)
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Project } from "@/types";

export const useProjects = () => {
  return useQuery({
    queryKey: ["projects"],
    queryFn: async () => {
      const { data } = await api.get<Project[]>("/projects/");
      return data;
    },
  });
};

export const useProject = (id: string) => {
  return useQuery({
    queryKey: ["projects", id],
    queryFn: async () => {
      const { data } = await api.get<Project>(`/projects/${id}`);
      return data;
    },
    enabled: !!id,
  });
};

export const useCreateProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (newProject: Partial<Project>) => {
      const { data } = await api.post<Project>("/projects/", newProject);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
};
```

**Why this is good architecture:**
- ✅ Encapsulates data fetching logic
- ✅ Provides automatic caching via React Query
- ✅ Automatic refetching on mutation success
- ✅ Type-safe API responses

**What's missing:**
- ❌ QueryClientProvider not set up in `app/layout.tsx`
- ❌ Components still use old `useState`/`useEffect` pattern
- ❌ No hooks for Actions, Risks, or other resources yet

### 4.2. Container vs. Presentational Components - 🔴 PLANNED

**Status: Not implemented. Most components are monolithic.**

**Current Reality:**
- All feature components (`ProjectList`, `ActionTable`, `RiskList`) mix data fetching with presentation
- No separation between "smart" (data-fetching) and "dumb" (presentational) components

**Target Pattern (not yet implemented):**
```typescript
// Container (data logic) - NOT YET IMPLEMENTED
export function ProjectListContainer() {
  const { data, isLoading, error } = useProjects();
  
  if (isLoading) return <Loader />;
  if (error) return <ErrorDisplay error={error} />;
  
  return <ProjectListPresenter projects={data} />;
}

// Presenter (pure UI) - NOT YET IMPLEMENTED
export function ProjectListPresenter({ projects }: { projects: Project[] }) {
  return (
    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {projects.map((project) => (
        <ProjectCard key={project.id} project={project} />
      ))}
    </div>
  );
}
```

**Presentational Components (already exist):**
- 🟢 `ProjectCard` - renders a single project (good)
- 🟢 `HealthIndicator` - displays health status (good)
- 🟢 `Button`, `Card`, etc. - Shadcn UI primitives (good)

**Monolithic Components (need refactoring):**
- ❌ `ProjectList` - fetches + renders
- ❌ `ActionTable` - fetches + renders
- ❌ `RiskList` - fetches + renders

### 4.3. Global State vs. Server State - 🟡 PARTIAL

#### Server State (🟡 React Query - Installed but not integrated)

**Current Status:**
- React Query is installed (`@tanstack/react-query`)
- Hooks are written but unused
- Components fetch data directly with Axios
- No caching, no automatic refetching, no optimistic updates

**Target State (once integrated):**
- Project data managed by `useProjects`, `useProject`, `useCreateProject` hooks
- Action data managed by `useActions` hook (to be created)
- Risk data managed by `useRisks` hook (to be created)
- Automatic caching, background refetching, and stale-while-revalidate strategy

#### Client State (🟢 Zustand - Implemented)

**What works:**
- Global auth state in `store/authStore.ts`
- Persists user object and `isAuthenticated` flag to localStorage
- Provides `setAuth` and `logout` methods

**Known Issue (Bug):**
- ⚠️ `accessToken` is stored in BOTH localStorage directly AND Zustand state
- ⚠️ Zustand persist does NOT include the token (only `user` and `isAuthenticated`)
- ⚠️ This creates sync issues on page refresh
- ⚠️ API interceptor reads from localStorage instead of Zustand store

**Fix Required:**
```typescript
// store/authStore.ts - NEEDS FIX
partialize: (state) => ({ 
  user: state.user, 
  accessToken: state.accessToken,  // ADD THIS LINE
  isAuthenticated: state.isAuthenticated 
}),
```

### 4.4. Component Composition - 🟢 IMPLEMENTED

The UI is composed from small, reusable primitives and feature components:
- ✅ Shadcn primitives (`components/ui/button.tsx`, `components/ui/card.tsx`) provide accessible building blocks
- ✅ Feature components compose these primitives (e.g. `ProjectCard` uses `Card`; `CreateProjectModal` uses `Button`)
- ✅ React's `children` prop and slots (via Radix `Slot`) are used where flexibility is needed

## 5. Authentication & Security (🟢 IMPLEMENTED, ⚠️ HAS BUGS)

### 5.1. Auth Strategy - 🟢 IMPLEMENTED

- **JWT (JSON Web Token)** based authentication with FastAPI backend issuing access tokens
- **Google SSO** via `@react-oauth/google` is the primary login method
- Email/password login is documented in requirements but not yet implemented

### 5.2. Current Login Flow - 🟢 IMPLEMENTED

1. `GoogleAuthProvider` (in `components/providers/GoogleAuthProvider.tsx`) wraps the app in `app/layout.tsx`
2. `app/login/page.tsx` renders a `GoogleLogin` button
3. On successful Google authentication:
   - Google credential is posted to `/auth/login` on the backend
   - Backend returns an `access_token` (JWT)
   - Token is stored in `localStorage` directly (line 24 of `login/page.tsx`)
   - Client calls `/auth/me` to fetch the current user
   - User and token stored in Zustand via `setAuth`
   - User redirected to dashboard

### 5.3. Token Storage - ⚠️ BUG PRESENT

**Current Implementation (has issues):**

```typescript
// app/login/page.tsx
localStorage.setItem('accessToken', access_token);  // Direct write

// store/authStore.ts
setAuth: (user, token) => {
  localStorage.setItem('accessToken', token);  // Duplicate write!
  set({ user, accessToken: token, isAuthenticated: true });
},

// Zustand persist config
partialize: (state) => ({ 
  user: state.user, 
  isAuthenticated: state.isAuthenticated 
  // accessToken is NOT persisted! ⚠️
}),

// lib/api.ts interceptor
const token = localStorage.getItem('accessToken');  // Reads from localStorage, not Zustand
```

**Problems:**
1. ❌ Token is written to localStorage in TWO places (duplication)
2. ❌ Token is stored in Zustand state but NOT persisted
3. ❌ API interceptor reads from localStorage instead of Zustand
4. ❌ On page refresh, Zustand rehydrates user/isAuthenticated but token is only in localStorage
5. ❌ Creates sync issues and confusing state management

**Security Concerns:**
- ⚠️ Storing JWT in localStorage is vulnerable to XSS attacks
- 🔴 **PLANNED**: Migrate to httpOnly cookies for production (more secure, prevents JavaScript access)

### 5.4. API Interceptors - 🟢 IMPLEMENTED (but reads from wrong source)

`lib/api.ts` defines a singleton Axios instance with a request interceptor:
- Reads `accessToken` from `localStorage` (should read from Zustand)
- Attaches `Authorization: Bearer <token>` to outgoing requests

```typescript
// lib/api.ts (current implementation)
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');  // Should use Zustand
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);
```

### 5.5. Route Protection - 🟢 IMPLEMENTED (but repetitive)

**Current Implementation:**
Every protected page has this boilerplate:

```typescript
// app/page.tsx, app/projects/[id]/page.tsx
const { user, isAuthenticated } = useAuthStore();
const router = useRouter();

useEffect(() => {
  if (!isAuthenticated) {
    router.push("/login");
  }
}, [isAuthenticated, router]);

if (!isAuthenticated) {
  return null;  // Prevents flash of content
}
```

**Issues:**
- ❌ Boilerplate repeated in every protected page
- ❌ Client-side only (no SSR/middleware protection)
- ⚠️ Still shows brief flash before redirect sometimes

**Future Improvement (🔴 PLANNED):**
- Add Next.js middleware for auth checks at the edge
- Create a `ProtectedLayout` wrapper component
- Or use a higher-order component pattern

## 6. Authorization & Permissions (🟢 IMPLEMENTED)

The frontend implements role-based UI gating to match the backend's three-tier persona system.

### 6.1. User Roles

```typescript
// types/index.ts
export enum UserRole {
  COGNITER = "Cogniter",           // Full access
  CLIENT_FINANCIALS = "Client + Financials",  // Projects + Financials
  CLIENT = "Client"                // Projects only
}
```

### 6.2. Permission Helpers (`lib/permissions.ts`)

Pure functions for checking user capabilities:

```typescript
// lib/permissions.ts
import { UserRole } from '@/types';

export const isCogniter = (role: UserRole): boolean => 
    role === UserRole.COGNITER;

export const canViewFinancials = (role: UserRole): boolean =>
    role === UserRole.COGNITER || role === UserRole.CLIENT_FINANCIALS;

export const isClientRole = (role: UserRole): boolean =>
    role === UserRole.CLIENT || role === UserRole.CLIENT_FINANCIALS;
```

### 6.3. Usage in Components

Components use these helpers to conditionally render UI based on user role:

```typescript
// components/project/FinancialsCard.tsx
import { useAuthStore } from "@/store/authStore";
import { canViewFinancials } from "@/lib/permissions";

export const FinancialsCard = ({ project }: FinancialsCardProps) => {
    const { user } = useAuthStore();

    // Gate visibility by role
    if (!user || !canViewFinancials(user.role as UserRole)) {
        return null;
    }

    // ... render financial data
};
```

### 6.4. Auth Store Role Type

The Zustand auth store supports all three roles:

```typescript
// store/authStore.ts
interface User {
  id: string;
  email: string;
  name: string;
  role: 'Cogniter' | 'Client + Financials' | 'Client';
}
```

---

## 7. UI/UX System (🟢 IMPLEMENTED)

- **Shadcn UI**:
  - ✅ The project uses Shadcn-style components copied into `components/ui`
  - ✅ Full control over implementation while starting from accessible, well-structured primitives
  - ✅ Components like `Button`, `Card`, etc. follow Radix UI patterns
- **Tailwind CSS**:
  - ✅ Utility-first CSS enables rapid iteration with consistent spacing, color, and layout tokens
  - ✅ `globals.css` imports Tailwind base, components, and utilities
  - ✅ Custom configuration in `tailwind.config.js`
- **Responsive Design**:
  - ✅ Components use Tailwind's responsive breakpoints (`sm`, `md`, `lg`)
  - ✅ Desktop-first layout that degrades gracefully on smaller screens
  
**What's Missing (🔴 PLANNED):**
- ❌ No loading skeletons (only spinners)
- ❌ No toast notifications (using `alert()` instead)
- ❌ No error boundaries
- ❌ Limited accessibility (no ARIA labels, keyboard navigation)

## 8. API Integration (🟢 IMPLEMENTED)

- **Centralized Client**:
  - ✅ A singleton Axios instance in `lib/api.ts` manages the base URL and default headers
  - ✅ Base URL is derived from `NEXT_PUBLIC_API_URL` with a local default (`http://localhost:8000`)
- **Auth Interceptor**:
  - ✅ Request interceptor attaches the `Authorization` header from localStorage
  - ⚠️ Should read from Zustand store instead (see Section 5.3)
- **Type Safety**:
  - ✅ API responses are typed using TypeScript interfaces and enums defined in `types/`
  - ✅ Types: `Project`, `ActionItem`, `Risk`, `HealthStatus`, `ProjectType`, etc.
  - ⚠️ No runtime validation (Zod recommended for production)

```typescript
// lib/api.ts (simplified - current implementation)
import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("accessToken");  // ⚠️ Should use Zustand
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);
```

**Missing Features (🔴 PLANNED):**
- ❌ No response interceptor for error handling
- ❌ No retry logic for failed requests
- ❌ No request/response logging in development
- ❌ No request cancellation on component unmount

## 9. Testing Strategy (🔴 NOT IMPLEMENTED)

**Current Status:** There are **zero tests** in the frontend codebase.

**Planned Stack:**
- 🔴 **Unit Testing**: Jest + React Testing Library for components and hooks
  - Test individual components (`ProjectCard`, `HealthIndicator`, etc.)
  - Test custom hooks (`useProjects`, `useActions`, `useRisks`)
  - Test utility functions
- 🔴 **Integration Testing**: Testing Library for component interactions
  - Test key flows across parent/child components
  - Example: Dashboard loading project list → opening create-project modal → refreshing list
- 🔴 **E2E Testing**: Playwright for full user journeys
  - Test complete workflows: Login → Create Project → View Dashboard → View Project Details
  - Test error scenarios and edge cases
  - Test across different browsers

**Priority Testing Candidates:**
1. Authentication flow (login, logout, token refresh)
2. Project CRUD operations
3. Form validation in CreateProjectModal
4. Auth state persistence across page refreshes
5. Error handling and retry logic

---

## 10. Known Issues & Technical Debt

### 10.1. Critical Issues (Must Fix)

1. **🔴 Token Storage Bug** (Section 5.3)
   - Token stored in both localStorage and Zustand but not persisted correctly
   - Creates sync issues on page refresh
   - Fix: Include `accessToken` in Zustand persist config

2. **🔴 React Query Not Integrated**
   - Installed but QueryClientProvider not set up
   - Hooks exist but unused
   - Components use manual `useState`/`useEffect` everywhere
   - Fix: Add QueryClientProvider to layout, migrate components

3. **🔴 "Refresh Hack" Pattern**
   - Uses `key` changes to force component remounts
   - Destroys entire component tree unnecessarily
   - Fix: Use React Query automatic invalidation

### 10.2. High Priority Issues

4. **🟡 No Error Boundaries**
   - Any component error crashes the entire app
   - No graceful error recovery
   - Fix: Add error boundaries at key levels

5. **🟡 Repetitive Auth Checks**
   - Every protected page duplicates auth redirect logic
   - Fix: Create ProtectedLayout or middleware

6. **🟡 Using `alert()` Instead of Toast**
   - Poor UX with browser native alerts
   - Fix: Install sonner or react-hot-toast

### 10.3. Medium Priority Issues

7. **🟡 No Form Validation**
   - Only HTML5 `required` attribute
   - No schema validation
   - Fix: Add react-hook-form + zod

8. **🟡 Mock Data in Components**
   - `FinancialsCard` has hardcoded mock data
   - `Timeline` has placeholder data
   - Fix: Wire up to real API endpoints

9. **🟡 No Loading Skeletons**
   - Only spinners for loading states
   - Fix: Add skeleton screens for better perceived performance

10. **🟡 API Interceptor Reads From localStorage**
    - Should read from Zustand store
    - Inconsistent with state management pattern

### 10.4. Low Priority / Nice to Have

11. **🟢 No Accessibility Features**
    - Missing ARIA labels
    - No keyboard navigation
    - Color-only status indicators

12. **🟢 No Request Cancellation**
    - API requests not cancelled on component unmount
    - Potential memory leaks

13. **🟢 No Runtime Type Validation**
    - Only compile-time TypeScript
    - Consider Zod for API response validation

---

## 11. Migration Plan: React Query Integration

### Phase 1: Setup (30 minutes)

1. **Add QueryClientProvider** to `app/layout.tsx`
   ```typescript
   'use client';
   import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
   import { useState } from 'react';
   
   export default function RootLayout({ children }) {
     const [queryClient] = useState(() => new QueryClient({
       defaultOptions: {
         queries: {
           staleTime: 60 * 1000,
           retry: 1,
         },
       },
     }));
   
     return (
       <html lang="en">
         <body>
           <QueryClientProvider client={queryClient}>
             <GoogleAuthProvider>
               {children}
             </GoogleAuthProvider>
           </QueryClientProvider>
         </body>
       </html>
     );
   }
   ```

2. **Convert layout to client component** (add `'use client'` directive)

### Phase 2: Projects Migration (1 hour)

3. **Update ProjectList** to use `useProjects` hook
4. **Update CreateProjectModal** to use `useCreateProject` mutation
5. **Remove refresh hack** from `app/page.tsx`
6. **Update project detail page** to use `useProject(id)` hook

### Phase 3: Actions & Risks (2 hours)

7. **Create `hooks/useActions.ts`** with React Query hooks
8. **Create `hooks/useRisks.ts`** with React Query hooks
9. **Update ActionTable** to use `useActions` hook
10. **Update RiskList** to use `useRisks` hook

### Phase 4: Cleanup (1 hour)

11. **Remove manual useState/useEffect** from all components
12. **Test all CRUD operations** work with React Query
13. **Verify caching** is working correctly
14. **Add React Query Devtools** for development

**Total Estimated Time: 4.5 hours**

---

## 12. Next Steps & Roadmap

### Immediate (Next Sprint)
- [ ] Fix token storage bug (15 min)
- [ ] Integrate React Query (4.5 hours)
- [ ] Add toast notifications (1 hour)
- [ ] Create ProtectedLayout wrapper (1 hour)

### Short Term (1-2 Sprints)
- [ ] Add error boundaries
- [ ] Add form validation (react-hook-form + zod)
- [ ] Add loading skeletons
- [ ] Wire up real financial data
- [ ] Wire up real timeline data from Jira

### Medium Term (2-4 Sprints)
- [ ] Write unit tests for critical flows
- [ ] Add E2E tests with Playwright
- [ ] Improve accessibility (ARIA labels, keyboard nav)
- [ ] Add request cancellation
- [ ] Add runtime validation with Zod

### Long Term (Production Readiness)
- [ ] Migrate to httpOnly cookies for auth tokens
- [ ] Add Next.js middleware for auth
- [ ] Add error tracking (Sentry)
- [ ] Add analytics
- [ ] Performance optimization (React.memo, useMemo)
- [ ] SEO optimization
- [ ] Add monitoring and logging