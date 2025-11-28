# Media Storage Configuration

## Overview

Starview supports two storage backends for user-uploaded media files (profile pictures, review photos):

1. **Local Filesystem** - Files saved to `media/` directory (development)
2. **Cloudflare R2** - Files saved to cloud object storage (production/testing)

---

## Quick Start

### Use Local Storage (Development - Default)

```bash
# In .env file:
USE_R2_STORAGE=False
```

**Benefits:**
- ✅ Fast uploads (no network latency)
- ✅ Works offline
- ✅ No API costs
- ✅ Easy to inspect files locally

**Files saved to:** `/Users/adiaz/event-horizon/media/`

---

### Use R2 Storage (Production/Testing)

```bash
# In .env file:
USE_R2_STORAGE=True
```

**Benefits:**
- ✅ Same storage as production (test integration)
- ✅ Global CDN (fast worldwide access)
- ✅ Persistent storage (survives server restarts)
- ✅ Scalable (no local disk usage)

**Files saved to:** Cloudflare R2 bucket `starview-media`

---

## Configuration Details

### Settings (django_project/settings.py)

```python
USE_R2_STORAGE = os.getenv('USE_R2_STORAGE', 'False' if DEBUG else 'True') == 'True'
```

**Default Behavior:**
- Development (`DEBUG=True`): Local filesystem
- Production (`DEBUG=False`): R2 storage

**Override:** Set `USE_R2_STORAGE` in `.env` to force a specific mode

**Required Dependencies:**
```
django-storages==1.14.6  # S3-compatible storage backend
boto3==1.40.59           # AWS SDK (required by django-storages)
```

### Storage Backends

**Local Filesystem:**
```python
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    }
}
MEDIA_ROOT = /Users/adiaz/event-horizon/media
MEDIA_URL = /media/
```

**Cloudflare R2:**
```python
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
}

# R2 Configuration
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', 'starview-media')
AWS_S3_REGION_NAME = 'auto'  # Required by Cloudflare R2
AWS_S3_ENDPOINT_URL = f"https://{CLOUDFLARE_ACCOUNT_ID}.r2.cloudflarestorage.com"
AWS_S3_SIGNATURE_VERSION = 's3v4'  # R2 doesn't support SigV2
AWS_S3_FILE_OVERWRITE = False  # Don't overwrite files with same name
AWS_DEFAULT_ACL = None  # R2 doesn't use ACLs
AWS_QUERYSTRING_AUTH = False  # Don't add auth query params to URLs
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',  # Cache for 24 hours
}

# Public URL for media files (set via R2_PUBLIC_URL env var)
# This is separate from the API endpoint
AWS_S3_CUSTOM_DOMAIN = os.getenv('R2_PUBLIC_URL', '').replace('https://', '').replace('http://', '')
# Example: pub-39455e1b48194c52b2f1262ab8c5e075.r2.dev
# Or custom domain: media.starview.app
```

---

## File Paths & URLs

### Upload Path Functions

**Profile Pictures:**
- Uses static path: `profile_pics/`
- Defined in: `starview_app/models/model_user_profile.py`
- Field: `ImageField(upload_to='profile_pics/')`

**Review Photos:**
- Dynamic path based on location and review IDs
- Defined in: `starview_app/models/model_review_photo.py`
- Functions:
  - `review_photo_path()`: `review_photos/{location_id}/{review_id}/{uuid}.ext`
  - `review_thumbnail_path()`: `review_photos/{location_id}/{review_id}/thumbnails/{uuid}_thumb.ext`
- UUID filenames prevent collisions
- Organized by location and review for easy cleanup

### Local Storage

| File Type | Path | URL |
|-----------|------|-----|
| Profile Pictures | `media/profile_pics/{uuid}.ext` | `/media/profile_pics/{uuid}.ext` |
| Review Photos | `media/review_photos/{location_id}/{review_id}/{uuid}.ext` | `/media/review_photos/{location_id}/{review_id}/{uuid}.ext` |
| Thumbnails | `media/review_photos/{location_id}/{review_id}/thumbnails/{uuid}_thumb.ext` | `/media/review_photos/{location_id}/{review_id}/thumbnails/{uuid}_thumb.ext` |

**How Local Files Are Served:**
- Django development server: Automatic via `MEDIA_URL`
- Production: Via `django_project/urls.py` pattern: `re_path(r'^media/(?P<path>.*)$', ...)`
- URL: `http://127.0.0.1:8000/media/...`

**Example URLs:**
- Profile: `http://127.0.0.1:8000/media/profile_pics/abc123.jpg`
- Review: `http://127.0.0.1:8000/media/review_photos/5/12/xyz789.jpg`
- Thumbnail: `http://127.0.0.1:8000/media/review_photos/5/12/thumbnails/xyz789_thumb.jpg`

### R2 Storage

| File Type | Path in Bucket | Public URL |
|-----------|----------------|------------|
| Profile Pictures | `profile_pics/{uuid}.ext` | `https://pub-{id}.r2.dev/profile_pics/{uuid}.ext` |
| Review Photos | `review_photos/{location_id}/{review_id}/{uuid}.ext` | `https://pub-{id}.r2.dev/review_photos/{location_id}/{review_id}/{uuid}.ext` |
| Thumbnails | `review_photos/{location_id}/{review_id}/thumbnails/{uuid}_thumb.ext` | `https://pub-{id}.r2.dev/review_photos/{location_id}/{review_id}/thumbnails/{uuid}_thumb.ext` |

**How R2 Files Are Served:**
- Files are uploaded to Cloudflare R2 using S3-compatible API
- Public access via R2.dev domain (or custom domain)
- No Django URL pattern needed - files served directly from R2
- Cache-Control header: `max-age=86400` (24 hours)

**Example URLs:**
- Profile: `https://pub-39455e1b48194c52b2f1262ab8c5e075.r2.dev/profile_pics/abc123.jpg`
- Review: `https://pub-39455e1b48194c52b2f1262ab8c5e075.r2.dev/review_photos/5/12/xyz789.jpg`
- Thumbnail: `https://pub-39455e1b48194c52b2f1262ab8c5e075.r2.dev/review_photos/5/12/thumbnails/xyz789_thumb.jpg`

**Custom Domain (Production):**
- Set `R2_PUBLIC_URL=https://media.starview.app` in `.env`
- Configure DNS CNAME in Cloudflare dashboard
- Benefits: Better branding, no rate limits, improved performance

---

## Testing Storage Modes

### Test Local Storage

```bash
# 1. Set local storage in .env
USE_R2_STORAGE=False

# 2. Run test script
djvenv/bin/python .claude/backend/tests/verification/test_local_storage.py
```

**What it does:**
1. Uploads test profile picture
2. Creates test review with photo
3. Verifies files exist in `media/` directory
4. Deletes files and verifies cleanup

**Expected output:**
```
[Storage] Using local filesystem for media files (Directory: /Users/adiaz/event-horizon/media)
✓ Using LOCAL filesystem storage
✓ File exists on filesystem: /Users/adiaz/event-horizon/media/profile_pics/test_image.jpg
✅ ALL TESTS COMPLETED SUCCESSFULLY
```

---

### Test R2 Storage

```bash
# 1. Set R2 storage in .env
USE_R2_STORAGE=True

# 2. Run test script
djvenv/bin/python .claude/backend/tests/verification/test_r2_upload.py
```

**What it does:**
1. Uploads test profile picture to R2
2. Creates test review with photo in R2
3. Verifies files are accessible via public URLs
4. Deletes files from R2 and verifies cleanup

**Expected output:**
```
[Storage] Using Cloudflare R2 for media files (Bucket: starview-media)
✓ URL is R2-hosted
✓ Image is accessible (HTTP 200)
✓ Profile picture deleted from R2
✅ ALL TESTS COMPLETED SUCCESSFULLY
```

---

## Signal Handlers (File Cleanup)

Both storage modes use the same signal handlers for automatic file cleanup.

**Location:** `starview_app/utils/signals.py`

**UserProfile Deletion:**
```python
@receiver(pre_delete, sender=UserProfile)
def delete_user_profile_picture(instance, **kwargs):
    if instance.profile_picture:
        safe_delete_file(instance.profile_picture)  # Works for both local & R2
        # Try to clean up empty directory (local filesystem only)
        try:
            if hasattr(instance.profile_picture, 'path'):
                dir_path = os.path.dirname(instance.profile_picture.path)
                safe_delete_directory(dir_path)
        except (NotImplementedError, AttributeError):
            # Storage backend doesn't support .path (R2/S3)
            pass
```

**ReviewPhoto Deletion:**
```python
@receiver(pre_delete, sender=ReviewPhoto)
def delete_review_photo_files(instance, **kwargs):
    # Delete main image (pass field object for R2/S3 compatibility)
    if instance.image:
        safe_delete_file(instance.image)

    # Delete thumbnail (pass field object for R2/S3 compatibility)
    if instance.thumbnail:
        safe_delete_file(instance.thumbnail)

    # Clean up directories if they're empty (local filesystem only)
    # For R2/S3, directory cleanup is handled by storage backend
    if instance.image:
        try:
            if hasattr(instance.image, 'path'):
                review_dir = os.path.dirname(instance.image.path)
                safe_delete_directory(os.path.join(review_dir, 'thumbnails'))
                safe_delete_directory(review_dir)
                # Try to clean up location directory if empty
                location_dir = os.path.dirname(review_dir)
                safe_delete_directory(location_dir)
        except (NotImplementedError, AttributeError):
            # Storage backend doesn't support .path (R2/S3)
            pass
```

**The `safe_delete_file()` Function:**

Handles deletion for both storage backends:
```python
def safe_delete_file(file_path):
    """
    Safely delete a file from local filesystem or cloud storage (R2/S3).

    Handles both:
    - Local filesystem paths (legacy/development)
    - Django storage backend paths (R2/S3 production)
    """
    if not file_path:
        return False

    try:
        # For local filesystem paths (absolute paths starting with /)
        if isinstance(file_path, str) and file_path.startswith('/'):
            path = Path(file_path)
            if path.exists() and str(path).startswith(str(settings.MEDIA_ROOT)):
                path.unlink()
                return True

        # For Django FileField/ImageField objects (R2/S3 storage)
        # These have a 'storage' attribute and 'name' attribute
        elif hasattr(file_path, 'storage') and hasattr(file_path, 'name'):
            if file_path.name and file_path.storage.exists(file_path.name):
                file_path.storage.delete(file_path.name)
                return True

        # For storage path strings (R2/S3 relative paths)
        else:
            from django.core.files.storage import default_storage
            file_str = str(file_path)
            if default_storage.exists(file_str):
                default_storage.delete(file_str)
                return True

        return True
    except Exception as e:
        logger.warning("Error deleting file %s: %s", str(file_path), str(e))
        return False
```

**Key Fix (2025-11-11):**
- Updated signals to pass field objects (not `.path`) to `safe_delete_file()`
- This ensures compatibility with both local filesystem and R2 storage
- R2 storage doesn't support `.path` attribute (raises `NotImplementedError`)
- Added try/except blocks for directory cleanup (only works with local filesystem)

---

## Image Processing

Starview automatically processes uploaded images to optimize storage and performance.

**Location:** `starview_app/models/model_review_photo.py`

### Profile Pictures

- No automatic processing (uses Django's default ImageField behavior)
- Recommended size: 500x500 pixels or smaller
- Accepted formats: JPEG, PNG, GIF, WebP

### Review Photos

**Automatic Processing (`_process_image()` method):**

1. **Format Conversion:**
   - Converts RGBA/LA/P images to RGB
   - Adds white background for transparency
   - Saves as JPEG format

2. **Image Resizing:**
   - Maximum dimensions: 1920x1920 pixels
   - Maintains aspect ratio
   - Uses LANCZOS resampling for quality

3. **Optimization:**
   - JPEG quality: 90%
   - Optimize flag enabled
   - Typical file size: 300-800 KB

4. **Thumbnail Generation (`_create_thumbnail()` method):**
   - Size: 300x300 pixels (maintains aspect ratio)
   - JPEG quality: 85%
   - Typical file size: 20-50 KB
   - Stored in `thumbnails/` subdirectory
   - Filename: `{original_uuid}_thumb.jpg`

**Why Thumbnails?**

Thumbnails provide critical performance optimization with minimal storage cost:

- **Performance Impact:**
  - Full-size image: ~300-800 KB each
  - Thumbnail: ~20-50 KB each (6% of original size)
  - Page with 20 thumbnails: 400 KB vs 6-16 MB (10-40x faster load time)

- **Storage Impact:**
  - NOT a doubling: thumbnails add only ~5-10% to total storage
  - Storage cost: ~$0.02/GB/month on R2 (negligible)
  - User experience improvement: priceless

- **Use Cases:**
  - Review galleries showing multiple photos
  - Location detail pages with photo carousels
  - User profile pages displaying photo collections
  - Any list view where multiple photos appear simultaneously

**Processing Errors:**

If image processing fails:
- Error logged with review ID and error message
- Upload continues (original image saved)
- Thumbnail may be missing
- Application continues to function

---

## Production Deployment

When deploying to production:

1. **Do NOT set `USE_R2_STORAGE` in production `.env`**
   - It will default to `True` (based on `DEBUG=False`)

2. **Ensure R2 credentials are set:**
   ```bash
   AWS_ACCESS_KEY_ID=...
   AWS_SECRET_ACCESS_KEY=...
   AWS_STORAGE_BUCKET_NAME=starview-media
   CLOUDFLARE_ACCOUNT_ID=...
   R2_PUBLIC_URL=https://pub-{id}.r2.dev  # or custom domain
   ```

3. **Custom Domain (Optional):**
   ```bash
   # Instead of pub-{id}.r2.dev, use:
   R2_PUBLIC_URL=https://media.starview.app
   ```
   - Requires DNS configuration in Cloudflare
   - Better performance, no rate limits

---

## Security & Validation

**File Upload Validation:** `django_project/settings.py`

```python
MAX_UPLOAD_SIZE_MB = 5
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
ALLOWED_IMAGE_MIMETYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
```

**Review Photo Limits:**
- Maximum 5 photos per review
- Enforced via `ReviewPhoto.clean()` method
- ValidationError raised if limit exceeded

**File Naming:**
- UUID-based filenames prevent collisions
- UUIDs generated using `uuid4().hex`
- No user-provided filenames used (security)

**Content Security Policy (CSP):**

The app's CSP allows images from:
```python
'img-src': (
    "'self'",
    "data:",                                    # Data URIs for inline images
    "https://*.mapbox.com",                     # Mapbox tile images
    "https://api.mapbox.com",                   # Mapbox API images
    "https://*.r2.dev",                         # Cloudflare R2 dev URLs (development/testing)
    "https://media.starview.app",               # R2 custom domain (production)
),
```

**Storage Security:**

**Local Storage:**
- Files only deleted if within `MEDIA_ROOT` (security check in `safe_delete_file()`)
- Prevents accidental deletion of system files
- Files served via Django (access control possible)

**R2 Storage:**
- Files stored in private bucket with public read access
- No ACLs used (R2 doesn't support them)
- No authentication required for read (public URLs)
- Write access requires API credentials (stored in environment variables)
- Bucket name: `starview-media`

---

## Troubleshooting

### Files Not Appearing Locally

**Check:**
1. `USE_R2_STORAGE=False` in `.env`
2. Django server restarted after changing `.env`
3. `media/` directory exists and has write permissions

**Debug:**
```bash
djvenv/bin/python .claude/backend/tests/verification/test_local_storage.py
```

---

### Files Not Uploading to R2

**Check:**
1. `USE_R2_STORAGE=True` in `.env`
2. R2 credentials are correct in `.env`
3. Network connection (R2 requires internet)
4. Cloudflare account has R2 enabled

**Debug:**
```bash
djvenv/bin/python .claude/backend/tests/verification/test_r2_upload.py
```

---

### "NotImplementedError: This backend doesn't support absolute paths"

**Cause:** Code is trying to use `.path` on R2 storage

**Fix:** Use field object directly, not `.path`
```python
# ✗ WRONG (breaks R2)
file_path = instance.image.path
safe_delete_file(file_path)

# ✓ CORRECT (works for both)
safe_delete_file(instance.image)
```

---

## Summary

| Setting | Local Storage | R2 Storage |
|---------|---------------|------------|
| `.env` | `USE_R2_STORAGE=False` | `USE_R2_STORAGE=True` |
| Backend | `FileSystemStorage` | `S3Storage` |
| Location | `media/` directory | Cloudflare R2 bucket |
| URLs | `/media/...` | `https://pub-{id}.r2.dev/...` |
| Best For | Development | Production/Testing |
| Cost | Free | ~$0.015/GB/month |
| Internet | Not required | Required |

**Current Mode:** Local Storage (`USE_R2_STORAGE=False`)

**Switch Anytime:** Just change `.env` and restart Django server - no code changes needed!

---

## Storage Costs & Performance

### Cloudflare R2 Pricing (Production)

**Storage:**
- $0.015/GB/month
- First 10 GB free
- Example: 100 GB = $1.35/month

**Operations:**
- Class A (writes): $4.50 per million requests
- Class B (reads): Free (unlimited)
- Data egress: Free (unlimited)

**Estimated Monthly Cost:**
- 1,000 users, 10 photos each = ~30 GB storage = $0.30/month
- 100,000 monthly uploads = ~450 write operations = negligible
- Unlimited reads/downloads = Free
- **Total: ~$0.50-$2/month for typical usage**

### Local Storage Costs (Development)

- Free (uses local disk)
- Storage limited by available disk space
- No egress costs (local network)
- **Total: $0/month**

### Performance Comparison

| Metric | Local Storage | R2 Storage |
|--------|---------------|------------|
| Upload Speed | Fast (local I/O) | Slower (network latency) |
| Download Speed | Fast (local I/O) | Fast (global CDN) |
| Availability | Single server only | 99.9% SLA globally |
| Scalability | Limited by disk | Unlimited |
| Backup | Manual required | Automatic redundancy |
| Cost | Free | ~$0.50-$2/month |

**Recommendation:**
- Development: Use local storage (fast, free, easy debugging)
- Production: Use R2 storage (scalable, reliable, global CDN)
- Testing R2: Switch locally to test integration before deploying

---

## Additional Resources

**Related Documentation:**
- `.claude/backend/ARCHITECTURE.md` - Overall backend architecture
- `starview_app/models/model_review_photo.py` - ReviewPhoto model and image processing
- `starview_app/models/model_user_profile.py` - UserProfile model
- `starview_app/utils/signals.py` - Signal handlers for file cleanup

**Django Storages Documentation:**
- https://django-storages.readthedocs.io/
- S3/R2 backend configuration
- Custom storage backends

**Cloudflare R2 Documentation:**
- https://developers.cloudflare.com/r2/
- Bucket configuration
- Public access and custom domains
- API reference
