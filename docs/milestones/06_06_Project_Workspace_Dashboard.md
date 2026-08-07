# MILESTONE 06.06 — Project Workspace Dashboard

## Summary
Build the frontend workspace dashboard UI for managing projects and accessing features.

## Detailed Description
This milestone creates the user-facing interface that enables users to:
- View and manage projects
- Browse and search lyrics content
- Navigate between features
- Access personalized settings
- Monitor activity and analytics

## Business Objective
Provide an intuitive, responsive workspace where users can efficiently discover, create, and manage content while enjoying a seamless navigation experience.

## Scope

**In Scope:**
- Dashboard home page with project overview
- Project listing and details view
- Lyrics browsing and search interface
- User profile management
- Settings and preferences panel
- Navigation sidebar/header
- Responsive design for various screen sizes

**Out of Scope:**
- Real-time collaboration features (can be added later)
- Advanced analytics dashboard
- Third-party integrations

## Prerequisites
- [ ] Milestone 06.05 — User Authentication completed
- [ ] API endpoints from previous milestones available
- [ ] Frontend build environment configured

## Dependencies
- Upstream: MILESTONE 06.05 — User Authentication
- Downstream: MILESTONE 07.01 (future milestone)
- External: Vue Router, Pinia (if not already installed)

---

## Functional Requirements

1. **Dashboard Layout**
   - Responsive navigation sidebar
   - Top header with user menu
   - Content area for main views
   - Breadcrumb navigation

2. **Project Overview**
   - Project cards/list view
   - Quick actions (create, edit, delete)
   - Status indicators
   - Sort and filter options

3. **Lyrics Library**
   - Search bar with filters
   - Grid/list toggle view
   - Pagination controls
   - Bulk selection for operations

4. **User Profile**
   - Display user information
   - Edit profile form
   - Change password option
   - Account settings

5. **Settings Panel**
   - Theme preferences (light/dark)
   - Language selection
   - Notification preferences
   - Data export options

## Technical Requirements

1. **Framework**
   - Vue 3 with Composition API
   - Pinia for state management
   - Vue Router for navigation
   - Tailwind CSS for styling

2. **Routing Structure**
   ```javascript
   // router/index.ts
   const routes = [
     { path: '/', component: DashboardView },        // Home/dashboard
     { path: '/projects', component: ProjectsView },
     { path: '/projects/:id', component: ProjectDetailView },
     { path: '/lyrics', component: LyricsLibraryView },
     { path: '/lyrics/search', component: LyricsSearchView },
     { path: '/profile', component: ProfileView },
     { path: '/settings', component: SettingsView },
   ]
   ```

3. **API Integration**
   - Axios or Fetch API for HTTP calls
   - JWT token storage in HttpOnly cookies
   - Request/response interceptors for auth headers
   - Error handling with user-friendly messages

4. **State Management**
   - User auth state in Pinia store
   - Cached API responses (where appropriate)
   - Theme preference persistence

## Acceptance Criteria

1. Dashboard renders with all navigation links working
2. Project listing displays data from API correctly
3. Lyrics search returns filtered results
4. Login redirects to dashboard after successful auth
5. All routes properly protected (redirect to login if not authenticated)
6. Responsive design works on mobile/tablet/desktop

## Validation Steps

1. Navigate to `/projects` - verify projects load
2. Navigate to `/lyrics` - verify lyrics display
3. Test search in `/lyrics/search` with various queries
4. Access `/profile` - verify user info displays
5. Check responsive behavior on different screen sizes
6. Verify protected routes redirect when not logged in

## Documentation Requirements
- [ ] Route mapping documented
- [ ] Component documentation complete
- [ ] API integration guide updated
- [ ] User manual section drafted

## Estimated Tasks

1. Set up Vue router with all routes
2. Create dashboard layout components
3. Implement project listing view
4. Build lyrics library component
5. Create search interface
6. Develop profile page
7. Build settings panel
8. Add responsive styling
9. Write integration tests
10. Update documentation

## Related APIs
- `/api/v1/projects` - Project data
- `/api/v1/lyrics` - Lyrics library
- `/api/v1/auth/profile` - User profile
- `/api/v1/search/lyrics` - Search functionality

## Database Changes
- None (frontend milestone)

## Frontend Changes
- [ ] `frontend/src/views/DashboardView.vue` - Dashboard home
- [ ] `frontend/src/views/ProjectsView.vue` - Project listing
- [ ] `frontend/src/views/ProjectDetailView.vue` - Project details
- [ ] `frontend/src/views/LyricsLibraryView.vue` - Lyrics browser
- [ ] `frontend/src/views/LyricsSearchView.vue` - Search interface
- [ ] `frontend/src/views/ProfileView.vue` - User profile
- [ ] `frontend/src/views/SettingsView.vue` - Settings panel
- [ ] `frontend/src/router/index.ts` - Route configuration
- [ ] `frontend/src/stores/auth.ts` - Auth state store
- [ ] `frontend/src/api/client.ts` - API client with auth

## Backend Changes
- None (pure frontend milestone)

## Testing Requirements
1. Unit tests for route guards
2. Component tests for all views
3. Integration tests for navigation flows
4. API call mocking with MSW/Test Server
5. Responsive design test cases
6. Authentication state persistence tests

## Completion Definition
Milestone 06.06 is complete when:
- All dashboard routes render correctly
- Navigation sidebar functional with all links
- Projects view displays data from API
- Lyrics library browse/search operational
- User profile page shows correct information
- Settings panel saves preferences
- Responsive design works on all breakpoints
- No console errors in production build

---

## Implementation Notes

### Component Structure
```
src/
  views/
    DashboardView.vue          # Main dashboard home
    ProjectsView.vue           # Project listing
    ProjectDetailView.vue      # Single project view
    LyricsLibraryView.vue      # Browse lyrics
    LyricsSearchView.vue       # Search interface
    ProfileView.vue            # User profile
    SettingsView.vue           # User settings
  components/
    layouts/
      DashboardLayout.vue      # Main layout wrapper
      Sidebar.vue              # Navigation sidebar
      Header.vue               # Top header bar
    projects/
      ProjectCard.vue          # Individual project card
    lyrics/
      LyricsList.vue           # List view component
      LyricsGrid.vue           # Grid view component
```

### API Client Configuration
```typescript
// src/api/client.ts
import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auth interceptor
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default api;
```

---

*Generated by Milestone Knowledge Base - STEP 22.1*
