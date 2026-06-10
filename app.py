import os
import sqlite3
import sys
import smtplib
from email.message import EmailMessage
from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, g, send_from_directory, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
# Use environment-provided secret in production; fall back to a generated key for local/dev
secret = os.environ.get('SECRET_KEY')
if not secret:
    # generate a random key for development if none provided
    secret = os.urandom(24)
app.secret_key = secret

# Cookie/session protection settings
is_production = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('PRODUCTION') == '1'
app.config.update({
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    # Only send secure cookies when running in production (HTTPS)
    'SESSION_COOKIE_SECURE': bool(is_production),
    'PERMANENT_SESSION_LIFETIME': timedelta(days=7),
    'SESSION_REFRESH_EACH_REQUEST': True,
})

BASE_DIR = os.path.dirname(__file__)
DATABASE_URL = os.environ.get('DATABASE_URL')
# For PostgreSQL, replace postgres:// with postgresql:// (Render standard)
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

USE_POSTGRES = bool(DATABASE_URL)
DATABASE = os.path.join(BASE_DIR, 'data', 'film_production.db') if not USE_POSTGRES else DATABASE_URL
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema_postgres.sql' if USE_POSTGRES else 'schema.sql')
SCHEMA_PATH_SQLITE = os.path.join(BASE_DIR, 'schema.sql')
SCHEMA_PATH_POSTGRES = os.path.join(BASE_DIR, 'schema_postgres.sql')

os.makedirs(os.path.join(BASE_DIR, 'data'), exist_ok=True)

# Database wrapper to provide consistent interface for both SQLite and PostgreSQL
class DatabaseCursor:
    """Wrapper around SQLite or PostgreSQL cursor to provide unified interface"""
    def __init__(self, cursor, is_postgres=False):
        self.cursor = cursor
        self.is_postgres = is_postgres
        self.rowcount = 0
        
    def execute(self, query, params=None):
        if self.is_postgres and params:
            # Convert SQLite ? placeholders to PostgreSQL %s placeholders
            query = query.replace('?', '%s')
        result = self.cursor.execute(query, params or [])
        self.rowcount = self.cursor.rowcount
        return self
        
    def fetchone(self):
        row = self.cursor.fetchone()
        if self.is_postgres and row:
            return dict(row) if hasattr(row, 'keys') else row
        return row
        
    def fetchall(self):
        rows = self.cursor.fetchall()
        if self.is_postgres and rows:
            return [dict(row) if hasattr(row, 'keys') else row for row in rows]
        return rows
        
    def close(self):
        self.cursor.close()

class DatabaseConnection:
    """Wrapper around SQLite or PostgreSQL connection"""
    def __init__(self, conn, is_postgres=False):
        self.conn = conn
        self.is_postgres = is_postgres
        
    def execute(self, query, params=None):
        if self.is_postgres:
            query = query.replace('?', '%s')
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            cursor = self.conn.cursor()
        cursor.execute(query, params or [])
        return cursor
        
    def cursor(self):
        if self.is_postgres:
            return self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            return self.conn.cursor()
        
    def commit(self):
        self.conn.commit()
        
    def close(self):
        self.conn.close()

# Initialize PostgreSQL driver if needed
if USE_POSTGRES:
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except ImportError:
        print("WARNING: psycopg2 not installed, falling back to SQLite")
        USE_POSTGRES = False

def get_db():
    if USE_POSTGRES:
        # PostgreSQL connection
        if 'db' not in g:
            try:
                conn = psycopg2.connect(DATABASE_URL)
                g.db = DatabaseConnection(conn, is_postgres=True)
            except psycopg2.Error as e:
                print(f"PostgreSQL connection error: {e}")
                raise
        return g.db
    else:
        # SQLite connection (local development)
        if not os.path.exists(DATABASE):
            init_db()

        if 'db' not in g:
            conn = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
            conn.row_factory = sqlite3.Row
            g.db = DatabaseConnection(conn, is_postgres=False)
            # ensure DB schema migrations (add attachment column if missing)
            try:
                cur = conn.execute("PRAGMA table_info(inquiries)")
                cols = [r[1] for r in cur.fetchall()]
                if 'attachment' not in cols:
                    conn.execute("ALTER TABLE inquiries ADD COLUMN attachment TEXT")
                    conn.commit()
            except Exception:
                # if migration fails, continue; init_db or manual migration may be required
                pass
        return g.db

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        if hasattr(db, 'conn'):
            db.conn.close()
        elif hasattr(db, 'close'):
            db.close()

# Initialize database on app startup
@app.before_request
def before_request():
    # Ensure database is initialized
    if USE_POSTGRES:
        try:
            # Test connection and ensure tables exist
            db = get_db()
            cursor = db.execute('SELECT 1 FROM admin_users LIMIT 1')
            cursor.close()
        except Exception as e:
            print(f"Database check failed, attempting initialization: {e}")
            try:
                init_db()
            except Exception as init_err:
                print(f"Database initialization failed: {init_err}")

def init_db():
    if USE_POSTGRES:
        # Initialize PostgreSQL database
        db = psycopg2.connect(DATABASE_URL)
        cursor = db.cursor()
        try:
            with open(SCHEMA_PATH_POSTGRES, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
                # Execute schema statements
                cursor.execute(schema_sql)
            # Create admin user if not exists
            cursor.execute(
                'INSERT INTO admin_users (username, password) VALUES (%s, %s) ON CONFLICT (username) DO NOTHING',
                ('admin', generate_password_hash('film2026'))
            )
            db.commit()
        except psycopg2.Error as e:
            print(f"Error initializing PostgreSQL: {e}")
            db.rollback()
            raise
        finally:
            cursor.close()
            db.close()
    else:
        # Initialize SQLite database
        os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
        db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        db.row_factory = sqlite3.Row
        with open(SCHEMA_PATH_SQLITE, 'r', encoding='utf-8') as f:
            db.executescript(f.read())
        db.execute(
            'INSERT OR IGNORE INTO admin_users (username, password) VALUES (?, ?)',
            ('admin', generate_password_hash('film2026'))
        )
        db.commit()
        db.close()

def get_user(username):
    db = get_db()
    return db.execute(
        'SELECT * FROM admin_users WHERE username = ?', (username,)
    ).fetchone()


def verify_password(stored_password, provided_password):
    if not stored_password or not provided_password:
        return False
    return check_password_hash(stored_password, provided_password)


def create_admin(username, password):
    db = get_db()
    db.execute(
        'INSERT INTO admin_users (username, password) VALUES (?, ?)',
        (username, generate_password_hash(password))
    )
    db.commit()

def update_admin_password(username, new_password):
    db = get_db()
    db.execute(
        'UPDATE admin_users SET password = ? WHERE username = ?',
        (generate_password_hash(new_password), username)
    )
    db.commit()

def send_notification_inquiry(name, email, message):
    """Send email notification to admins about a new inquiry (optional feature)."""
    # This is a placeholder that can be configured with actual email settings
    # For now, it does nothing but prevent errors if the function is called
    pass


def create_inquiry(name, email, message, attachment=None):
    db = get_db()
    db.execute(
        'INSERT INTO inquiries (name, email, message, attachment) VALUES (?, ?, ?, ?)',
        (name, email, message, attachment)
    )
    db.commit()
    # best-effort: notify admins via email if configured
    try:
        send_notification_inquiry(name, email, message)
    except Exception:
        pass

def get_inquiries(search=None, limit=10, offset=0):
    db = get_db()
    if search:
        q = f'%{search}%'
        rows = db.execute(
            'SELECT id, name, email, message, attachment, created_at FROM inquiries WHERE name LIKE ? OR email LIKE ? OR message LIKE ? ORDER BY created_at DESC LIMIT ? OFFSET ?',
            (q, q, q, limit, offset)
        ).fetchall()
    else:
        rows = db.execute(
            'SELECT id, name, email, message, attachment, created_at FROM inquiries ORDER BY created_at DESC LIMIT ? OFFSET ?',
            (limit, offset)
        ).fetchall()
    return rows


def get_inquiries_count(search=None):
    db = get_db()
    if search:
        q = f'%{search}%'
        row = db.execute('SELECT COUNT(*) AS c FROM inquiries WHERE name LIKE ? OR email LIKE ? OR message LIKE ?', (q, q, q)).fetchone()
    else:
        row = db.execute('SELECT COUNT(*) AS c FROM inquiries').fetchone()
    return row['c'] if row else 0


def get_team_members():
    db = get_db()
    return db.execute(
        'SELECT * FROM team_members ORDER BY display_order ASC, created_at DESC'
    ).fetchall()


def get_team_member(team_id):
    db = get_db()
    return db.execute(
        'SELECT * FROM team_members WHERE id = ?', (team_id,)
    ).fetchone()


def save_team_image(file):
    if not file or not file.filename:
        return None

    uploads_dir = os.path.join(BASE_DIR, 'data', 'uploads', 'team')
    os.makedirs(uploads_dir, exist_ok=True)

    filename = secure_filename(file.filename)
    save_path = os.path.join(uploads_dir, filename)
    if os.path.exists(save_path):
        base, ext = os.path.splitext(filename)
        i = 1
        while os.path.exists(save_path):
            filename = f"{base}-{i}{ext}"
            save_path = os.path.join(uploads_dir, filename)
            i += 1

    file.save(save_path)
    return filename


@app.route('/team-images/<path:filename>')
def team_image(filename):
    images_dir = os.path.join(BASE_DIR, 'data', 'uploads', 'team')
    return send_from_directory(images_dir, filename)


@app.route('/gallery')
def gallery():
    team_members = get_team_members()
    return render_template('gallery.html', team_members=team_members)


@app.route('/admin/team')
def admin_team():
    if not session.get('logged_in'):
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))
    team_members = get_team_members()
    return render_template('admin_team.html', team_members=team_members)


@app.route('/admin/team/add', methods=['GET', 'POST'])
def admin_team_add():
    if not session.get('logged_in'):
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    error = None
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        role = request.form.get('role', '').strip()
        bio = request.form.get('bio', '').strip()
        display_order = request.form.get('display_order', '0').strip()
        try:
            display_order = int(display_order)
        except ValueError:
            display_order = 0

        if not name or not role:
            error = 'Name and role are required.'
        else:
            image_file = request.files.get('image')
            image_filename = save_team_image(image_file)
            db = get_db()
            db.execute(
                'INSERT INTO team_members (name, role, bio, image_filename, display_order) VALUES (?, ?, ?, ?, ?)',
                (name, role, bio, image_filename, display_order)
            )
            db.commit()
            flash('Team member added successfully.', 'success')
            return redirect(url_for('admin_team'))

    return render_template('admin_team_add.html', error=error)


@app.route('/admin/team/edit/<int:team_id>', methods=['GET', 'POST'])
def admin_team_edit(team_id):
    if not session.get('logged_in'):
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    team_member = get_team_member(team_id)
    if not team_member:
        abort(404)

    error = None
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        role = request.form.get('role', '').strip()
        bio = request.form.get('bio', '').strip()
        display_order = request.form.get('display_order', '0').strip()
        try:
            display_order = int(display_order)
        except ValueError:
            display_order = 0

        if not name or not role:
            error = 'Name and role are required.'
        else:
            image_file = request.files.get('image')
            image_filename = team_member['image_filename']
            if image_file and image_file.filename:
                saved_filename = save_team_image(image_file)
                if saved_filename:
                    image_filename = saved_filename

            db = get_db()
            db.execute(
                'UPDATE team_members SET name = ?, role = ?, bio = ?, image_filename = ?, display_order = ? WHERE id = ?',
                (name, role, bio, image_filename, display_order, team_id)
            )
            db.commit()
            flash('Team member updated successfully.', 'success')
            return redirect(url_for('admin_team'))

    return render_template('admin_team_edit.html', team_member=team_member, error=error)


@app.route('/admin/team/delete/<int:team_id>', methods=['POST'])
def admin_team_delete(team_id):
    if not session.get('logged_in'):
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    db = get_db()
    db.execute('DELETE FROM team_members WHERE id = ?', (team_id,))
    db.commit()
    flash('Team member deleted.', 'info')
    return redirect(url_for('admin_team'))


@app.context_processor
def inject_user():
    return {
        'logged_in': session.get('logged_in', False),
        'admin_username': session.get('username')
    }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    error = None
    form_data = {
        'name': '',
        'email': '',
        'message': ''
    }

    if request.method == 'POST':
        form_data['name'] = request.form.get('name', '').strip()
        form_data['email'] = request.form.get('email', '').strip()
        form_data['message'] = request.form.get('message', '').strip()

        if not form_data['name'] or not form_data['email'] or not form_data['message']:
            error = 'All fields are required to submit your request.'
        else:
            # handle optional file attachment
            attachment_filename = None
            file = request.files.get('attachment')
            if file and file.filename:
                uploads_dir = os.path.join(BASE_DIR, 'data', 'uploads')
                os.makedirs(uploads_dir, exist_ok=True)
                filename = secure_filename(file.filename)
                save_path = os.path.join(uploads_dir, filename)
                # avoid overwrite by adding suffix if file exists
                if os.path.exists(save_path):
                    base, ext = os.path.splitext(filename)
                    i = 1
                    while os.path.exists(save_path):
                        filename = f"{base}-{i}{ext}"
                        save_path = os.path.join(uploads_dir, filename)
                        i += 1
                file.save(save_path)
                attachment_filename = filename

            create_inquiry(form_data['name'], form_data['email'], form_data['message'], attachment_filename)
            flash('Thank you! Your inquiry has been saved and we will follow up shortly.', 'success')
            return redirect(url_for('contact'))

    return render_template('contact.html', error=error, form_data=form_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('admin'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user = get_user(username)
        if user and verify_password(user['password'], password):
            session['logged_in'] = True
            session['username'] = username
            # make session persistent according to `PERMANENT_SESSION_LIFETIME`
            session.permanent = True
            flash('Successfully signed in.', 'success')
            return redirect(url_for('admin'))
        error = 'Invalid username or password.'

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        flash('Please log in to access the admin dashboard.', 'warning')
        return redirect(url_for('login'))

    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    q = request.args.get('q', '').strip() or None
    per_page = 8
    offset = (page - 1) * per_page
    total = get_inquiries_count(q)
    inquiries = get_inquiries(search=q, limit=per_page, offset=offset)
    pages = (total + per_page - 1) // per_page if total else 1

    return render_template('admin.html', inquiries=inquiries, page=page, pages=pages, q=q)

@app.route('/admin/inquiries')
def admin_inquiries():
    if not session.get('logged_in'):
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))
    # Redirect to unified admin dashboard which now displays inquiries
    return redirect(url_for('admin'))


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    # Only allow admin users to download uploaded attachments
    if not session.get('logged_in'):
        abort(403)
    uploads_dir = os.path.join(BASE_DIR, 'data', 'uploads')
    return send_from_directory(uploads_dir, filename, as_attachment=True)

@app.route('/admin/add', methods=['GET', 'POST'])
def add_admin():
    if not session.get('logged_in'):
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    error = None
    if request.method == 'POST':
        new_username = request.form.get('username', '').strip()
        new_password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not new_username or not new_password or not confirm_password:
            error = 'All fields are required.'
        elif get_user(new_username):
            error = 'That administrator already exists.'
        elif new_password != confirm_password:
            error = 'Passwords do not match.'
        else:
            create_admin(new_username, new_password)
            flash(f'Admin "{new_username}" created successfully.', 'success')
            return redirect(url_for('admin'))

    return render_template('admin_add.html', error=error)


@app.route('/admin/inquiries/delete/<int:inquiry_id>', methods=['POST'])
def admin_delete_inquiry(inquiry_id):
    if not session.get('logged_in'):
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))
    db = get_db()
    db.execute('DELETE FROM inquiries WHERE id = ?', (inquiry_id,))
    db.commit()
    flash('Inquiry deleted.', 'info')
    return redirect(url_for('admin'))

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if session.get('logged_in'):
        return redirect(url_for('admin'))

    error = None
    username = ''

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not username or not current_password or not new_password or not confirm_password:
            error = 'All fields are required.'
        else:
            user = get_user(username)
            if not user or not verify_password(user['password'], current_password):
                error = 'Current password is incorrect.'
            elif new_password != confirm_password:
                error = 'Passwords do not match.'
            else:
                update_admin_password(username, new_password)
                flash('Password changed successfully. Please log in with your new password.', 'success')
                return redirect(url_for('login'))

    return render_template('admin_change_password.html', error=error, reset=True, username=username)


@app.route('/admin/change-password', methods=['GET', 'POST'])
def change_password():
    if not session.get('logged_in'):
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    username = session.get('username')
    error = None

    if request.method == 'POST':
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        user = get_user(username)
        if not current_password or not new_password or not confirm_password:
            error = 'All fields are required.'
        elif not user or not verify_password(user['password'], current_password):
            error = 'Current password is incorrect.'
        elif new_password != confirm_password:
            error = 'Passwords do not match.'
        else:
            update_admin_password(username, new_password)
            flash('Password changed successfully.', 'success')
            return redirect(url_for('admin'))

    return render_template('admin_change_password.html', error=error, reset=False, username=username)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'init-db':
        with app.app_context():
            init_db()
        print('Initialized the database.')
        sys.exit(0)
    app.run(debug=True)
