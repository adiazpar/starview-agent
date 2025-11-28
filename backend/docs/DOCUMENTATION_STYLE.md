# Documentation Style Guide

## Header Comment Format for Python Files

All Python files in the `stars_app` directory should include a header comment block that follows this format:

### Structure

```python
# ----------------------------------------------------------------------------------------------------- #
# This [filename] file [primary purpose in one sentence]:                                               #
#                                                                                                       #
# [High-level sections explaining WHY and WHAT, not HOW]                                                #
# ----------------------------------------------------------------------------------------------------- #
```

### Key Principles

1. **Focus on the "WHY" and "WHAT"** - Not the "HOW"
   - Explain the purpose and role of the file in the overall project
   - Don't duplicate what's already visible in the code below
   - Avoid listing every function, class, or model

2. **Keep it High-Level**
   - Explain the file's role in the Django project architecture
   - Describe what value it provides to the project
   - Mention key concepts or frameworks used (e.g., ContentTypes, signals)

3. **Be Concise**
   - Aim for 10-20 lines maximum
   - Use bullet points for clarity
   - Group related concepts together

### Examples

#### Good Example (admin.py):
```python
# ----------------------------------------------------------------------------------------------------- #
# This admin.py file configures the Django admin interface for the stars_app application:               #
#                                                                                                       #
# Purpose:                                                                                              #
# The Django admin interface provides a web-based interface for managing database content. This file    #
# registers models with the admin site and customizes how they appear and behave in the admin panel.    #
#                                                                                                       #
# What This Provides:                                                                                   #
# - Staff users can view, create, edit, and delete records through a web interface at /admin/           #
# - Custom admin classes enhance the default interface with better displays, filters, and search        #
# - Generic models use custom admins to handle ContentTypes framework complexity                        #
#                                                                                                       #
# Access:                                                                                               #
# Only users with is_staff=True can access the admin interface. Superusers have full permissions.       #
# ----------------------------------------------------------------------------------------------------- #
```

#### Bad Example (too detailed):
```python
# This admin.py file registers the following models:
# - Location: shows id, name, latitude, longitude
# - UserProfile: shows id, user, bio, profile_picture
# - Review: shows id, user, location, rating
# [continues listing every model and field...]
```

### File-Specific Guidelines

- **apps.py**: Explain AppConfig purpose, startup hooks, and signal registration
- **admin.py**: Explain Django admin interface role and access permissions
- **signals.py**: Explain signal handlers and when they trigger
- **__init__.py**: Explain why it exists even when empty (package vs namespace packages)
- **utils.py** or **services/**: Explain the separation of concerns and architectural pattern

### Function/Method Comments

**Use boxed format for substantive functions/methods:**

```python
# ----------------------------------------------------------------------------- #
# Brief description of what the function does.                                  #
#                                                                               #
# Args:   param1 (type): Description                                            #
#         param2 (type): Description                                            #
# Returns: Description of return value                                          #
# ----------------------------------------------------------------------------- #
def function_name(param1, param2):
    pass
```

**Use simple comments for short classes/methods:**

For simple classes or methods that only set attributes (like Django class-based views with just template configuration), use a simple one-line comment:

```python
# Display password reset request form (users enter their email):
class CustomPasswordResetView(PasswordResetView):
    template_name = 'stars_app/password_reset.html'
    success_url = reverse_lazy('password_reset_done')
```

**Guidelines:**
- Use **boxed format** for functions with logic, complex operations, or multiple responsibilities
- Use **simple comments** for configuration-only classes or trivial wrappers
- When in doubt, use the boxed format for clarity

### Section Dividers

For major sections within a file:

```python
# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                       SECTION NAME                                                    #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #
```

---

## Summary

The goal is to write documentation that helps future developers (including yourself) quickly understand:
1. What the file does in the context of the project
2. Why it exists and what problem it solves
3. Key architectural patterns or frameworks used

Avoid documenting implementation details that are already clear from reading the code itself.
