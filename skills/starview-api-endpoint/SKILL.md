---
name: starview-api-endpoint
description: Create or integrate API endpoints end-to-end. Use when adding new endpoints, connecting frontend to existing APIs, or resuming interrupted endpoint work. Handles backend (DRF) and frontend (services, React Query) integration with crash recovery support.
user-invocable: true
allowed-tools: Read, Grep, Glob, Edit, Write, Bash, EnterPlanMode, ExitPlanMode, AskUserQuestion, TodoWrite
model: opus
---

# API Endpoint Skill for Starview

Create or integrate API endpoints with full backend-to-frontend workflow.

## IMPORTANT: Plan Mode Required

**You MUST enter plan mode before proceeding.** Use the `EnterPlanMode` tool now.

This ensures:
- Proper codebase exploration before implementation
- User approval of the implementation plan
- No wasted work on wrong approaches

---

## Prerequisites

Once in plan mode, gather from user:
- **Feature name** (e.g., "celestial events", "user notifications")
- **Endpoint path** (e.g., `/api/events/`, `/api/notifications/`)
- **HTTP methods needed** (GET, POST, PUT, PATCH, DELETE)
- **Authentication required?** (public vs authenticated)

---

## Step 0: Determine Starting Point

Ask the user using AskUserQuestion:

**Question:** "Does the backend endpoint already exist?"

| Option | Description |
|--------|-------------|
| **Yes, backend exists** | Endpoint is live, skip to frontend integration (Step 8) |
| **No, start fresh** | Need full backend implementation (Step 1) |
| **I don't know** | Investigate codebase first (Step 0.5) |

---

## Step 0.5: Codebase Investigation (If "I don't know")

Run these checks to determine current state:

### Backend Checks

```bash
# 1. Check URL routing
grep -r "endpoint-path" starview_app/urls.py starview_app/*/urls.py

# 2. Search for related serializers
grep -ri "featurename" starview_app/serializers*.py

# 3. Search for related views
grep -ri "featurename" starview_app/views*.py

# 4. Check for related models
grep -ri "class.*FeatureName" starview_app/models.py
```

### Frontend Checks

```bash
# 5. Check if frontend service exists
grep -ri "endpoint-path" starview_frontend/src/services/

# 6. Check for React Query hooks
grep -ri "featurename" starview_frontend/src/hooks/
```

### Report Findings

After investigation, report to user:

```
## Investigation Results

**Backend:**
- [ ] URL route exists: Yes/No (found in urls.py:XX)
- [ ] Serializer exists: Yes/No (found in serializers.py:XX)
- [ ] View/ViewSet exists: Yes/No (found in views.py:XX)
- [ ] Model exists: Yes/No (found in models.py:XX)

**Frontend:**
- [ ] Service function exists: Yes/No (found in services/X.js:XX)
- [ ] React Query hook exists: Yes/No (found in hooks/X.js:XX)

**Recommendation:** [Start from Step X]
```

Then proceed to the appropriate step.

---

## BACKEND IMPLEMENTATION (Steps 1-7)

Skip this section if backend already exists.

### Step 1: Model (If Needed)

If endpoint requires a new model, create a file in `starview_app/models/` (e.g., `feature.py`) and export it in `__init__.py`:

```python
class FeatureName(models.Model):
    """
    Brief description of what this model represents.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feature_items')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
```

Then create migration:
```bash
djvenv/bin/python manage.py makemigrations
djvenv/bin/python manage.py migrate
```

### Step 2: Serializer

Create a file in `starview_app/serializers/` (e.g., `feature_serializers.py`) and export in `__init__.py`:

```python
class FeatureNameSerializer(serializers.ModelSerializer):
    """List serializer - minimal fields for performance."""

    class Meta:
        model = FeatureName
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['id', 'created_at']


class FeatureNameDetailSerializer(FeatureNameSerializer):
    """Detail serializer - includes nested/expensive fields."""
    user = UserMinimalSerializer(read_only=True)

    class Meta(FeatureNameSerializer.Meta):
        fields = FeatureNameSerializer.Meta.fields + ['user', 'description', 'updated_at']
```

**Pattern:** Use minimal serializer for lists, detailed serializer for single-item views.

### Step 3: View/ViewSet

Create a view file in `starview_app/views/` (e.g., `views_feature.py`) and export in `__init__.py`:

```python
class FeatureNameViewSet(viewsets.ModelViewSet):
    """
    API endpoint for feature name.

    list: GET /api/feature/ - List all items
    create: POST /api/feature/ - Create new item
    retrieve: GET /api/feature/{id}/ - Get single item
    update: PUT /api/feature/{id}/ - Update item
    destroy: DELETE /api/feature/{id}/ - Delete item
    """
    permission_classes = [IsAuthenticated]  # or [AllowAny] for public
    throttle_classes = [UserRateThrottle]   # See Step 4

    def get_queryset(self):
        return FeatureName.objects.filter(user=self.request.user)\
            .select_related('user')\
            .order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'list':
            return FeatureNameSerializer
        return FeatureNameDetailSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
```

### Step 4: Rate Limiting

Choose appropriate throttle class from `starview_app/utils/throttles.py`:

| Throttle Class | Rate | Use For |
|----------------|------|---------|
| `LoginRateThrottle` | 5/min | Login attempts |
| `PasswordResetRateThrottle` | 3/hour | Password reset requests |
| `ContentCreationThrottle` | 20/hour | Creating locations, reviews |
| `VotingRateThrottle` | 60/hour | Upvotes, downvotes |
| `ReportingRateThrottle` | 10/hour | Content reports |
| `UserRateThrottle` | 100/hour | General authenticated actions |

```python
throttle_classes = [ContentCreationThrottle]  # For create-heavy endpoints
```

### Step 5: URL Routing

Add to `starview_app/urls.py`:

```python
from rest_framework.routers import DefaultRouter
from .views import FeatureNameViewSet

router = DefaultRouter()
router.register(r'feature', FeatureNameViewSet, basename='feature')

urlpatterns = [
    # ... existing patterns
    path('', include(router.urls)),
]
```

Or for non-ViewSet endpoints:
```python
urlpatterns = [
    path('feature/', FeatureListView.as_view(), name='feature-list'),
    path('feature/<int:pk>/', FeatureDetailView.as_view(), name='feature-detail'),
]
```

### Step 6: Permissions (If Custom Needed)

Add to `starview_app/permissions.py`:

```python
class IsOwnerOrReadOnly(permissions.BasePermission):
    """Allow owners to edit, others can only read."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user
```

### Step 7: Test the Backend

```bash
# Start server if not running
djvenv/bin/python manage.py runserver

# Test with curl
curl -X GET http://127.0.0.1:8000/api/feature/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID"

# Or use Django shell
djvenv/bin/python manage.py shell
>>> from starview_app.models import FeatureName
>>> FeatureName.objects.all()
```

**Backend complete!** Proceed to frontend integration.

---

## FRONTEND INTEGRATION (Steps 8-11)

### Step 8: Add to Service Layer

Determine which service file to use:

| Endpoint Type | Service File |
|---------------|--------------|
| Auth-related | `services/auth.js` |
| User profile | `services/profile.js` |
| Locations | `services/locations.js` |
| Platform stats | `services/stats.js` |
| **New domain** | Create `services/feature.js` |

**Add to existing service:**

```javascript
// In services/profile.js (example)
export const profileApi = {
  // ... existing methods

  // New endpoint
  getFeatureItems: async () => {
    const response = await api.get('/feature/');
    return response.data;
  },

  createFeatureItem: async (data) => {
    const response = await api.post('/feature/', data);
    return response.data;
  },

  updateFeatureItem: async (id, data) => {
    const response = await api.patch(`/feature/${id}/`, data);
    return response.data;
  },

  deleteFeatureItem: async (id) => {
    await api.delete(`/feature/${id}/`);
  },
};
```

**Or create new service file:**

```javascript
// services/feature.js
import api from './api';

const featureApi = {
  getAll: async () => {
    const response = await api.get('/feature/');
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/feature/${id}/`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/feature/', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.patch(`/feature/${id}/`, data);
    return response.data;
  },

  delete: async (id) => {
    await api.delete(`/feature/${id}/`);
  },
};

export default featureApi;
```

### Step 9: Create React Query Hook (If Data-Fetching)

Create `hooks/useFeatureData.js`:

```javascript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import featureApi from '../services/feature';

export function useFeatureList() {
  return useQuery({
    queryKey: ['feature', 'list'],
    queryFn: featureApi.getAll,
  });
}

export function useFeatureItem(id) {
  return useQuery({
    queryKey: ['feature', id],
    queryFn: () => featureApi.getById(id),
    enabled: !!id,
  });
}

export function useCreateFeature() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: featureApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feature'] });
    },
  });
}

export function useDeleteFeature() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: featureApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feature'] });
    },
  });
}
```

### Step 10: Component Usage Example

```javascript
import { useFeatureList, useCreateFeature } from '../hooks/useFeatureData';
import LoadingSpinner from '../components/shared/LoadingSpinner';
import Alert from '../components/shared/Alert';

function FeatureComponent() {
  const { data: items, isLoading, error } = useFeatureList();
  const createMutation = useCreateFeature();

  if (isLoading) return <LoadingSpinner />;
  if (error) return <Alert type="error" message="Failed to load items" />;

  const handleCreate = async (newItem) => {
    try {
      await createMutation.mutateAsync(newItem);
    } catch (err) {
      console.error('Failed to create:', err);
    }
  };

  return (
    <div>
      {items.map(item => (
        <div key={item.id}>{item.name}</div>
      ))}
    </div>
  );
}
```

### Step 11: Update Documentation

Update `.claude/frontend/docs/API_GUIDE.md`:

```markdown
## Feature Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/feature/` | List all items |
| POST | `/api/feature/` | Create new item |
| GET | `/api/feature/{id}/` | Get single item |
| PATCH | `/api/feature/{id}/` | Update item |
| DELETE | `/api/feature/{id}/` | Delete item |
```

---

## Quick Reference: Existing Patterns

### Backend Files (Directory Structure)
- Models: `starview_app/models/` (e.g., `user.py`, `location.py`, `review.py`, `badge.py`)
- Serializers: `starview_app/serializers/` (e.g., `location_serializers.py`, `user_serializers.py`)
- Views: `starview_app/views/` (e.g., `views_location.py`, `views_auth.py`, `views_user.py`)
- URLs: `starview_app/urls.py`
- Throttling: `starview_app/utils/throttles.py`
- Services: `starview_app/services/` (e.g., `badge_service.py`, `mapbox_service.py`)

### Frontend Files
- API client: `services/api.js`
- Auth service: `services/auth.js`
- Profile service: `services/profile.js`
- Locations service: `services/locations.js`
- Hooks: `hooks/useProfileData.js`, `hooks/useStats.js`, `hooks/useLocations.js`

### Documentation
- Backend: `.claude/backend/ARCHITECTURE.md`
- Frontend API: `.claude/frontend/docs/API_GUIDE.md`
- Frontend arch: `.claude/frontend/ARCHITECTURE.md`
