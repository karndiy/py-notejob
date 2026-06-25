import uuid
import os
import json
from datetime import datetime
import urllib.parse
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
app.secret_key = 'jd-8f2a4e6b9c1d3e5f'

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CONFIG_FILE = 'config.json'
DEFAULT_CONFIG = {'vault_name': 'WorkVault', 'sheet_name': 'JobDiary'}

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = "credentials.json"


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=2)


def get_sheets_client():
    cfg = load_config()
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
    client = gspread.authorize(creds)
    return client.open(cfg['sheet_name']).sheet1


def get_all_jobs():
    sheet = get_sheets_client()
    all_values = sheet.get_all_values()
    if len(all_values) < 2:
        return []
    headers = all_values[0]
    valid_cols = [(i, h) for i, h in enumerate(headers) if h.strip()]
    return [
        {h: (row[i] if i < len(row) else '') for i, h in valid_cols}
        for row in all_values[1:]
        if any(cell.strip() for cell in row)
    ]


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_obsidian_uri(job_id, date_str, category, title, description, status, link=''):
    cfg = load_config()
    vault_name = cfg['vault_name']

    safe_id = job_id or "Unknown"
    safe_date = date_str or "No-Date"
    safe_category = category or "Uncategorized"
    safe_title = title or "Untitled"
    safe_desc = description or "No description provided."
    safe_status = status or "Pending"
    safe_link = link or ""

    tag_name = str(safe_category).lower().replace(' ', '-')
    filename = f"Job-{safe_id}"
    link_section = f"\n## Reference Link\n{safe_link}\n" if safe_link else ""

    markdown_content = f"""---
id: {safe_id}
date: {safe_date}
category: {safe_category}
status: {safe_status}
tags: [job-diary, {tag_name}]
---

# {safe_title}

## Description
{safe_desc}
{link_section}
## Status Log
- [ ] Initial Logging: {safe_date} ({safe_status})
"""
    encoded_vault = urllib.parse.quote(vault_name, safe='')
    encoded_title = urllib.parse.quote(filename, safe='')
    encoded_content = urllib.parse.quote(markdown_content, safe='')
    return f"obsidian://new?vault={encoded_vault}&name={encoded_title}&content={encoded_content}&overwrite=true"


def enrich(jobs):
    for row in jobs:
        row['obsidian_uri'] = generate_obsidian_uri(
            job_id=row.get('ID'),
            date_str=row.get('Timestamp'),
            category=row.get('Category'),
            title=row.get('Title'),
            description=row.get('Description'),
            status=row.get('Status'),
            link=row.get('Link', '')
        )
    return jobs


@app.route('/')
def home():
    try:
        jobs = get_all_jobs()
    except Exception as e:
        return render_template('home.html', error=str(e), stats={}, recent=[])
    stats = {
        'total': len(jobs),
        'pending': sum(1 for j in jobs if j.get('Status') == 'Pending'),
        'in_progress': sum(1 for j in jobs if j.get('Status') == 'In Progress'),
        'software': sum(1 for j in jobs if j.get('Category') == 'Software Request'),
        'problems': sum(1 for j in jobs if j.get('Category') == 'Problem Log'),
    }
    recent = list(reversed(jobs))[:5]
    return render_template('home.html', stats=stats, recent=recent, error=None)


@app.route('/dashboard')
def dashboard():
    try:
        jobs = enrich(list(reversed(get_all_jobs())))
    except Exception as e:
        return render_template('dashboard.html', error=str(e), jobs=[])
    return render_template('dashboard.html', jobs=jobs, error=None)


@app.route('/job/<job_id>')
def detail(job_id):
    try:
        jobs = get_all_jobs()
        job = next((j for j in jobs if j.get('ID') == job_id), None)
        if not job:
            return render_template('detail.html', job=None, error="Job record not found.")
        job = enrich([job])[0]
    except Exception as e:
        return render_template('detail.html', job=None, error=str(e))
    return render_template('detail.html', job=job, error=None)


@app.route('/add', methods=['GET', 'POST'])
def add_job():
    if request.method == 'POST':
        category = request.form.get('category')
        title = request.form.get('title')
        description = request.form.get('description')
        link = request.form.get('link', '').strip()
        status = "Pending"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        job_id = str(uuid.uuid4())[:8]

        attachment = ''
        file = request.files.get('attachment')
        if file and file.filename and allowed_file(file.filename):
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            fname = secure_filename(f"{job_id}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            attachment = fname

        try:
            sheet = get_sheets_client()
            sheet.append_row([job_id, timestamp, category, title, description, 'Pending', attachment, link, ''])
            flash('Entry logged successfully.', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            return render_template('add.html', error=str(e))
    return render_template('add.html', error=None)


@app.route('/job/<job_id>/edit', methods=['GET', 'POST'])
def edit_job(job_id):
    try:
        jobs = get_all_jobs()
        job = next((j for j in jobs if j.get('ID') == job_id), None)
        if not job:
            return render_template('edit.html', job=None, error="Job not found.")
    except Exception as e:
        return render_template('edit.html', job=None, error=str(e))

    if request.method == 'POST':
        category    = request.form.get('category')
        title       = request.form.get('title')
        description = request.form.get('description')
        status      = request.form.get('status')
        link        = request.form.get('link', '').strip()

        attachment = job.get('Attachment', '')
        file = request.files.get('attachment')
        if file and file.filename and allowed_file(file.filename):
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            fname = secure_filename(f"{job_id}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            attachment = fname

        try:
            sheet = get_sheets_client()
            all_values = sheet.get_all_values()
            row_num = next(
                (i + 1 for i, row in enumerate(all_values) if row and row[0] == job_id),
                None
            )
            if row_num is None:
                return render_template('edit.html', job=job, error="Row not found in sheet.")
            updated_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for col, value in {3: category, 4: title, 5: description,
                               6: status, 7: attachment, 8: link, 9: updated_ts}.items():
                sheet.update_cell(row_num, col, value)
            flash('Entry updated successfully.', 'success')
            return redirect(url_for('detail', job_id=job_id))
        except Exception as e:
            return render_template('edit.html', job=job, error=str(e))

    return render_template('edit.html', job=job, error=None)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    cfg = load_config()
    message = None
    if request.method == 'POST':
        cfg['vault_name'] = request.form.get('vault_name', '').strip() or DEFAULT_CONFIG['vault_name']
        cfg['sheet_name'] = request.form.get('sheet_name', '').strip() or DEFAULT_CONFIG['sheet_name']
        save_config(cfg)
        message = 'Settings saved successfully.'
    return render_template('settings.html', config=cfg, message=message)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
