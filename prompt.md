# Job Diary — File Reference

Complete technical description of every file in the project. Use this as a reference when regenerating, extending, or debugging any part of the codebase.

---

## `app.py`

**Role:** Single-file Flask application. Contains all route handlers, helper functions, and configuration management.

**Key constants:**
- `UPLOAD_FOLDER` — `static/uploads/` — where uploaded images are saved
- `ALLOWED_EXTENSIONS` — `{png, jpg, jpeg, gif, webp}`
- `CONFIG_FILE` — `config.json`
- `DEFAULT_CONFIG` — `{'vault_name': 'WorkVault', 'sheet_name': 'JobDiary'}`
- `SCOPE` — Google Sheets + Drive OAuth2 scopes
- `CREDS_FILE` — `credentials.json`

**Helper functions:**

| Function | Purpose |
|---|---|
| `load_config()` | Reads `config.json`; falls back to `DEFAULT_CONFIG` if file missing |
| `save_config(cfg)` | Writes dict to `config.json` |
| `get_sheets_client()` | Authenticates with OAuth2 and returns `sheet1` of the configured spreadsheet |
| `get_all_jobs()` | Fetches all rows via `get_all_values()`, skips blank header columns and empty rows, returns list of dicts |
| `allowed_file(filename)` | Returns True if file extension is in `ALLOWED_EXTENSIONS` |
| `generate_obsidian_uri(...)` | Builds an `obsidian://new?...&overwrite=true` URI with URL-encoded vault name, note name (`Job-<id>`), and YAML-frontmatter markdown content |
| `enrich(jobs)` | Adds `obsidian_uri` key to each job dict in a list |

**Routes:**

| Method | URL | Handler | Description |
|---|---|---|---|
| GET | `/` | `home` | Loads all jobs, computes stats (total/pending/software/problems), passes last 5 as `recent` |
| GET | `/dashboard` | `dashboard` | Loads and enriches all jobs reversed (newest first) |
| GET | `/job/<job_id>` | `detail` | Finds single job by ID, enriches it |
| GET/POST | `/add` | `add_job` | GET: render form. POST: save image if present, append 9-column row to sheet (`Updated` = `''`), flash success, redirect to dashboard |
| GET/POST | `/job/<job_id>/edit` | `edit_job` | GET: load job for form. POST: scan `get_all_values()` for matching ID row number, call `update_cell` for columns 3–9 (Category through Updated timestamp) |
| GET/POST | `/settings` | `settings` | GET: render with current config. POST: save new vault/sheet names to `config.json` |

**Column mapping used in `edit_job`:**
```
Col 3 = Category
Col 4 = Title
Col 5 = Description
Col 6 = Status
Col 7 = Attachment (filename)
Col 8 = Link
Col 9 = Updated (datetime.now() on every edit)
```

**Status workflow enforced by the app:**
- `add_job` always writes `'Pending'` to Status regardless of form input
- `edit_job` only offers `'In Progress'` and `'Done'` in the status dropdown

---

## `config.json`

**Role:** Runtime configuration. Created by the Settings page; read on every request.

```json
{
  "vault_name": "WorkVault",
  "sheet_name": "JobDiary"
}
```

- `vault_name` — must exactly match the Obsidian vault name (case-sensitive)
- `sheet_name` — must exactly match the Google Spreadsheet name

If absent, `load_config()` returns the defaults without error.

---

## `credentials.json`

**Role:** Google Cloud service account key. Required for `oauth2client` to authenticate with Google Sheets API.

**Structure:** Standard Google service account JSON — contains `client_email`, `private_key`, `project_id`, etc.

**Important:** This file must be kept secret. Add to `.gitignore`. Never commit to version control.

The service account email (`client_email`) must be added as an **Editor** on the Google Spreadsheet.

---

## `requestments.txt`

**Role:** Pip install reference listing the project's Python dependencies.

```
pip install Flask gspread oauth2client Werkzeug
```

**Dependencies:**
| Package | Purpose |
|---|---|
| `Flask` | Web framework, routing, templating, flash messages |
| `gspread` | Google Sheets read/write client |
| `oauth2client` | Service account authentication for Google APIs |
| `Werkzeug` | `secure_filename()` for safe image upload filenames |

`urllib.parse` is part of Python's standard library — no install needed.

---

## `templates/base.html`

**Role:** Shared layout inherited by all page templates via `{% extends 'base.html' %}`.

**Contains:**
- Complete CSS design system (iOS Human Interface Guidelines-inspired)
- CSS custom properties (design tokens) in `:root`
- Fixed translucent navbar with backdrop blur
- Flash message rendering (`get_flashed_messages`)
- `{% block content %}` injection point
- Footer

**Design tokens (CSS variables):**
```
--blue   #007AFF     iOS system blue
--green  #34C759     iOS system green
--red    #FF3B30     iOS system red
--orange #FF9500     iOS system orange
--bg     #F2F2F7     iOS grouped background
--card   #FFFFFF     Card surface
--label  #000000     Primary text
--label2 rgba(60,60,67,0.60)   Secondary text
--label3 rgba(60,60,67,0.30)   Tertiary / placeholder
--sep    rgba(60,60,67,0.12)   Separator / border
```

**Key CSS components:**
- `.navbar` — fixed, `backdrop-filter: blur(20px)`, iOS glass effect
- `.card` / `.card-padded` — white rounded cards with subtle shadow
- `.job-card` — dashboard job entry with `.job-card-body` and `.job-card-actions` strip
- `.form-card` + `.form-row` + `.form-full` — iOS Settings-style grouped form
- `.hero` — gradient banner (blue → indigo)
- `.stats-grid` — 2-col (mobile) / 4-col (desktop) stat tiles
- `.badge` / `.badge-status` — colored pill labels
- `.btn` variants: `btn-primary`, `btn-tinted`, `btn-gray`, `btn-sm`, `btn-full`
- `.list-row` — iOS table cell row with icon, content, chevron
- `.section-header` — uppercase gray label above a card group
- `.back-btn` — iOS-style `‹ Back` link in blue

**Navbar active state logic:**
- Dashboard link is active for `endpoint in ['dashboard', 'detail', 'edit_job']`
- Other links check `request.endpoint == 'home'` / `'add_job'` / `'settings'`

---

## `templates/home.html`

**Role:** Landing page (`/`). Shows a hero banner, stat tiles, and recent entries.

**Template variables:**
- `stats` — dict with keys: `total`, `pending`, `in_progress`, `software`, `problems`
- `recent` — list of up to 5 job dicts (most recent first, not enriched — no obsidian_uri)
- `error` — string or `None`

**Layout:**
1. Error alert (if `error`)
2. `.hero` — gradient card with "Job Diary" title and two CTA buttons
3. `.stats-grid` — 4 stat tiles (Total, Pending, Requests, Problems)
4. Recent entries as iOS `.list-row` items inside a `.card`, each linking to `/job/<id>`

---

## `templates/dashboard.html`

**Role:** Full job list page (`/dashboard`). Shows all jobs newest first.

**Template variables:**
- `jobs` — list of enriched job dicts (includes `obsidian_uri`)
- `error` — string or `None`

**Layout:**
- Page title + entry count subtitle
- Empty state card if no jobs
- For each job: `.job-card` with
  - Meta row: category badge, status badge, timestamp (Updated if set, else Created)
  - Title (ID prefix + title text)
  - Description (2-line clamp)
  - Actions strip: View Detail, ✏️ Edit, 💜 Obsidian

---

## `templates/detail.html`

**Role:** Single entry full view (`/job/<job_id>`).

**Template variables:**
- `job` — enriched job dict or `None`
- `error` — string or `None`

**Layout:**
- `‹ Dashboard` back link
- Summary card: category badge, status badge, ID, title, Created timestamp, Updated timestamp (if set)
- Description section (`.detail-section`)
- Attachment section (image, shown only if `job.Attachment` is non-empty)
- Reference link section (shown only if `job.Link` is non-empty)
- Action buttons: ✏️ Edit Entry, 💜 Obsidian, ‹ Dashboard

---

## `templates/add.html`

**Role:** New entry form (`/add`).

**Form fields:**

| Field | Input type | Name | Notes |
|---|---|---|---|
| Category | `<select>` | `category` | Software Request / Problem Log |
| Title | `<input text>` | `title` | Required |
| Description | `<textarea>` | `description` | Required |
| Image | `<input file>` | `attachment` | Optional; accepts `image/*` |
| Link | `<input text>` | `link` | Optional |

Status is **not** shown — hardcoded to `'Pending'` in `add_job()`.

Form uses `enctype="multipart/form-data"`. Posts to `url_for('add_job')`.

**Layout:** Three grouped iOS form cards — Details, Description, Extras — followed by a full-width submit button.

---

## `templates/edit.html`

**Role:** Edit entry form (`/job/<job_id>/edit`).

**Form fields:**

| Field | Input type | Name | Notes |
|---|---|---|---|
| Category | `<select>` | `category` | Pre-selected from existing value |
| Status | `<select>` | `status` | Only `In Progress` / `Done`; defaults to In Progress unless already Done |
| Title | `<input text>` | `title` | Pre-filled |
| Description | `<textarea>` | `description` | Pre-filled |
| Image | `<input file>` | `attachment` | Optional; shows existing image thumbnail if present |
| Link | `<input text>` | `link` | Pre-filled |

Posts to `url_for('edit_job', job_id=job.ID)` with `enctype="multipart/form-data"`.

**Behavior on POST:** Keeps existing attachment filename if no new file is uploaded. Writes `Updated` timestamp automatically — not user-editable.

**Layout:** Same three-section iOS form as add.html, with current values pre-filled.

---

## `templates/settings.html`

**Role:** Configuration page (`/settings`). Reads/writes `config.json`.

**Form fields:**

| Field | Name | Default |
|---|---|---|
| Vault Name | `vault_name` | `WorkVault` |
| Spreadsheet Name | `sheet_name` | `JobDiary` |

Shows success alert if `message` is set after a POST save.

Also includes an **About** section listing the expected Google Sheet column order:
`ID · Timestamp · Category · Title · Description · Status · Attachment · Link · Updated`

---

## `static/uploads/` (directory)

**Role:** Stores uploaded image attachments.

- Created automatically by `os.makedirs(..., exist_ok=True)` on first upload
- Filenames are `secure_filename(f"{job_id}_{original_filename}")` — prefixed with the job ID to avoid collisions
- Served by Flask via `url_for('static', filename='uploads/' + job.Attachment)`
- Stored filename (without path) is written to the `Attachment` column in Google Sheets

---

## Google Sheets Column Contract

The app assumes this exact column order (1-indexed, as used by `update_cell`):

```
1  ID           — 8-char UUID prefix, set on create, never changed
2  Timestamp    — Created datetime (YYYY-MM-DD HH:MM:SS), set on create
3  Category     — "Software Request" or "Problem Log"
4  Title        — Short summary
5  Description  — Full notes / details
6  Status       — "Pending" | "In Progress" | "Done"
7  Attachment   — Image filename (blank if none)
8  Link         — Reference URL (blank if none)
9  Updated      — Edit datetime (blank until first edit)
```

`get_all_jobs()` reads by header name (not position), so extra blank columns at the end do not cause errors. Blank-header columns are ignored.
