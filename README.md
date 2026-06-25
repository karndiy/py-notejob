# Job Diary

A lightweight internal work-log tool built with Flask and Google Sheets. Log software requests and problem entries, track their status through a workflow, and push each entry as a structured note directly into Obsidian.

---

## Features

- **Log entries** — two categories: Software Request and Problem Log
- **Status workflow** — Pending → In Progress → Done with automatic timestamps
- **Edit & update** — update any field; records a separate "Updated" timestamp
- **Obsidian integration** — one-click pushes a pre-formatted markdown note with YAML frontmatter into your vault (supports overwrite)
- **Image attachments** — upload screenshots or reference images per entry
- **Reference links** — attach a URL to any entry
- **Settings page** — configure vault name and sheet name without touching code
- **iOS-style UI** — clean, system-font interface with translucent navbar

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3 / Flask |
| Database | Google Sheets (via gspread) |
| Auth | OAuth2 service account (oauth2client) |
| Note export | Obsidian URI scheme |
| Frontend | Jinja2 templates, vanilla CSS (iOS HIG theme) |

---

## Prerequisites

- Python 3.9+
- A Google account with Google Sheets and Google Drive APIs enabled
- A Google Cloud service account with a `credentials.json` key file
- Obsidian desktop app installed (for the note push feature)

---

## Setup

### 1. Clone and install dependencies

```bash
pip install Flask gspread oauth2client Werkzeug
```

### 2. Google Sheets API — service account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → enable **Google Sheets API** and **Google Drive API**
3. Create a **Service Account** → download the JSON key as `credentials.json`
4. Place `credentials.json` in the project root

### 3. Create the Google Spreadsheet

1. Create a new Google Sheet named **`JobDiary`** (or your preferred name)
2. Share it with the service account email (found inside `credentials.json` as `client_email`) — give **Editor** access
3. Set up the header row in **row 1** exactly as follows:

| A | B | C | D | E | F | G | H | I |
|---|---|---|---|---|---|---|---|---|
| ID | Timestamp | Category | Title | Description | Status | Attachment | Link | Updated |

### 4. Configure settings

Edit `config.json` (created automatically on first settings save) or update via the **Settings** page in the app:

```json
{
  "vault_name": "WorkVault",
  "sheet_name": "JobDiary"
}
```

### 5. Run

```bash
python app.py
```

App runs at **http://localhost:5000**

---

## Usage Workflow

### Adding an entry
1. Click **+ Log** in the nav bar
2. Choose category, fill in title and description
3. Optionally attach an image or reference URL
4. Submit → entry is appended to Google Sheets with `Status = Pending`

### Updating an entry
1. Open the entry from Dashboard → click **Edit**
2. Change status to **In Progress** or **Done**
3. Update any other fields
4. Save → Google Sheets row is updated; `Updated` timestamp is recorded

### Pushing to Obsidian
1. Open **Dashboard** or **Detail** page
2. Click **💜 Obsidian** — this opens an `obsidian://new` URI
3. Obsidian creates (or overwrites) a note named `Job-<ID>` in your vault
4. The note contains YAML frontmatter and a structured description + status log

---

## Google Sheet Column Reference

| Col | Header | Set by | Notes |
|---|---|---|---|
| A | ID | `add` | 8-char UUID prefix |
| B | Timestamp | `add` | Created datetime, never changes |
| C | Category | `add` / `edit` | Software Request or Problem Log |
| D | Title | `add` / `edit` | |
| E | Description | `add` / `edit` | |
| F | Status | `add` / `edit` | Pending → In Progress → Done |
| G | Attachment | `add` / `edit` | Filename saved in `static/uploads/` |
| H | Link | `add` / `edit` | Optional reference URL |
| I | Updated | `edit` | Datetime of last edit, blank until first edit |

---

## Project Structure

```
py-jobs/
├── app.py                  # Flask application — all routes and logic
├── config.json             # Runtime config (vault name, sheet name)
├── credentials.json        # Google service account key — DO NOT COMMIT
├── requestments.txt        # pip install reference
├── static/
│   └── uploads/            # Uploaded images (auto-created)
└── templates/
    ├── base.html           # Shared layout, CSS, navbar
    ├── home.html           # Landing page with stats + recent entries
    ├── dashboard.html      # All jobs list
    ├── detail.html         # Single job full view
    ├── add.html            # New entry form
    ├── edit.html           # Edit entry form
    └── settings.html       # Vault and sheet name config
```

---

## Configuration File

`config.json` is written by the Settings page and read on every request:

```json
{
  "vault_name": "YourObsidianVaultName",
  "sheet_name": "YourGoogleSheetName"
}
```

If the file does not exist, defaults (`WorkVault` / `JobDiary`) are used.

---

## Security Notes

- **Never commit `credentials.json`** — it contains your Google service account private key
- Add `credentials.json` and `config.json` to `.gitignore`
- `debug=True` in `app.run()` — disable before any shared deployment
- `app.secret_key` is hardcoded — replace with an environment variable for production

---

## Suggested Next Features

| Priority | Feature |
|---|---|
| High | Delete entry with confirmation |
| High | Keyword search on Dashboard |
| Medium | Quick status toggle (tap badge to advance status) |
| Medium | Priority level (High / Medium / Low) |
| Low | Due date with overdue highlight |
| Low | CSV export |
| Low | Sort and filter by status / category / date |
