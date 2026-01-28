---
name: add-language
description: Add a new language to the Starview app. Handles frontend UI translations (i18next JSON), backend Django settings, and transactional email translations (.po files). Use when adding support for a new language.
user-invocable: true
allowed-tools: Read, Grep, Glob, Edit, Write, Bash, TodoWrite
model: sonnet
---

# Add Language Skill

Adds complete internationalization support for a new language across the entire Starview application.

## When to Use

Invoke this skill when the user wants to:
- Add a new language to the app
- Add internationalization for a new locale
- Translate the app to a new language

Trigger phrases: "add language", "add French", "add German support", "translate to Italian"

## Arguments

Parse from user input:
- `--code XX` or language code: ISO 639-1 code (e.g., `fr`, `de`, `it`, `pt`)
- `--name "Name"`: Native name (e.g., `Français`, `Deutsch`, `Italiano`)
- `--flag XX`: Flag code for flag-icons (usually same as country code, e.g., `fr`, `de`, `it`)
- `--region "Name"`: Region/country name (e.g., `France`, `Deutschland`, `Italia`)

If arguments are missing, ask the user for them.

## What Gets Created/Modified

| Component | Files | Purpose |
|-----------|-------|---------|
| Frontend Config | `starview_frontend/src/i18n/config.js` | Add to SUPPORTED_LANGUAGES and LANGUAGE_CONFIG |
| Frontend Translations | `starview_frontend/public/locales/{code}/*.json` | UI strings (common, navbar, footer) |
| Backend Config | `django_project/settings.py` | Add to LANGUAGES tuple |
| Email Translations | `locale/{code}/LC_MESSAGES/django.po` | Transactional email strings |
| Compiled Translations | `locale/{code}/LC_MESSAGES/django.mo` | Binary compiled translations |

## Execution Steps

**IMPORTANT: Execute these steps automatically. Do not just display instructions.**

---

### Step 1: Validate Input

Ensure you have all required information:
- Language code (2-letter ISO 639-1)
- Native name (how the language is written in that language)
- Flag code (for flag-icons library)
- Region name (country/region where language is spoken)

If any are missing, use AskUserQuestion to gather them.

---

### Step 2: Update Frontend Config

Edit `starview_frontend/src/i18n/config.js`:

1. Add the language code to `SUPPORTED_LANGUAGES` array
2. Add the language metadata to `LANGUAGE_CONFIG` object

**Example addition:**
```javascript
// In SUPPORTED_LANGUAGES array
export const SUPPORTED_LANGUAGES = ['en', 'es', 'fr', 'NEW_CODE'];

// In LANGUAGE_CONFIG object
NEW_CODE: {
  name: 'English Name',
  nativeName: 'Native Name',
  flag: 'flag_code',
  region: 'Region Name',
},
```

---

### Step 3: Create Frontend Translation Files

Create directory and 3 JSON files:
- `starview_frontend/public/locales/{code}/common.json`
- `starview_frontend/public/locales/{code}/navbar.json`
- `starview_frontend/public/locales/{code}/footer.json`

**Source files to translate from:**
- `starview_frontend/public/locales/en/common.json`
- `starview_frontend/public/locales/en/navbar.json`
- `starview_frontend/public/locales/en/footer.json`

Read each English file, translate all string values to the target language, and write the translated version.

**Translation guidelines:**
- Keep JSON structure identical
- Only translate string values, not keys
- Preserve interpolation placeholders like `{{year}}`
- Use natural, native phrasing (not word-for-word translation)

---

### Step 4: Update Django Settings

Edit `django_project/settings.py`:

Find the `LANGUAGES` list and add the new language tuple:

```python
LANGUAGES = [
    ('en', 'English'),
    ('es', 'Español'),
    ('NEW_CODE', 'Native Name'),  # Add new language
]
```

---

### Step 5: Create Django Translation File

Create directory structure:
```bash
mkdir -p locale/{code}/LC_MESSAGES
```

Create `locale/{code}/LC_MESSAGES/django.po` with translations for all email strings.

**Source file to translate from:**
- `locale/es/LC_MESSAGES/django.po` (use as structural template)

**The .po file must include:**
1. Header with language metadata
2. All msgid/msgstr pairs from the Spanish file, translated to the new language

**Header template:**
```
# Starview {Language} Translations
# Copyright (C) 2025 Starview
#
msgid ""
msgstr ""
"Project-Id-Version: Starview 1.0\n"
"Language-Team: {Language}\n"
"Language: {code}\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\n"
```

**Strings to translate (from existing .po file):**
- Email subjects (Verify Your Account, Password Reset, etc.)
- Email body text (Welcome messages, security alerts, etc.)
- Password validation messages
- Common phrases (Hello, Best regards, The Starview Team, etc.)

---

### Step 6: Compile Translations

Run Django's compilemessages command:

```bash
djvenv/bin/python manage.py compilemessages
```

This creates the binary `.mo` file needed for Django to use the translations.

---

### Step 7: Verify Installation

Confirm all files were created:

```bash
# Check frontend files
ls -la starview_frontend/public/locales/{code}/

# Check backend files
ls -la locale/{code}/LC_MESSAGES/
```

Expected output:
- 3 JSON files in frontend locales
- django.po and django.mo in locale directory

---

## Summary Template

After completion, display:

```
## Language Added: {Native Name} ({code})

### Frontend (UI)
- ✓ Config updated: starview_frontend/src/i18n/config.js
- ✓ Translations created:
  - starview_frontend/public/locales/{code}/common.json
  - starview_frontend/public/locales/{code}/navbar.json
  - starview_frontend/public/locales/{code}/footer.json

### Backend (Django)
- ✓ Settings updated: django_project/settings.py
- ✓ Email translations: locale/{code}/LC_MESSAGES/django.po
- ✓ Compiled: locale/{code}/LC_MESSAGES/django.mo

### What's Translated
- Navigation bar
- Footer
- Common UI elements (buttons, labels, status messages)
- Transactional emails:
  - Account verification
  - Welcome email
  - Password reset
  - Password changed confirmation
  - Email change notification
  - Password validation errors

### Testing
Users can select {Native Name} from the language selector in the footer.
Authenticated users will receive emails in {Native Name} when their
language preference is set to '{code}'.
```

---

## Reference: Currently Supported Languages

Check current languages by reading:
- `starview_frontend/src/i18n/config.js` → SUPPORTED_LANGUAGES array
- `django_project/settings.py` → LANGUAGES tuple

---

## Reference: Translation String Count

Approximate strings to translate:
- common.json: ~25 strings
- navbar.json: ~15 strings
- footer.json: ~25 strings
- django.po: ~90 strings (emails + validation)

Total: ~155 strings per language
