# PostgreSQL Production Setup Guide

## Overview
The Film Production app uses:
- **Development**: SQLite (file-based, local)
- **Production**: PostgreSQL (optional, set via `DATABASE_URL`)

## Quick Start

### Development (SQLite)
Simply run the app normally - it will use SQLite automatically:
```bash
python -m flask run
```

### Production (PostgreSQL)

#### Option 1: Heroku (Recommended for Easy Setup)
```bash
# Create Heroku app
heroku create your-app-name

# Add PostgreSQL add-on (free tier available)
heroku addons:create heroku-postgresql:hobby-dev

# Deploy
git push heroku main

# Initialize database
heroku run python -c "from app import init_db; init_db()"
```

#### Option 2: Railway.app
```bash
# Deploy to Railway
railway up

# Railway auto-sets DATABASE_URL - just set SECRET_KEY
railway variables set SECRET_KEY=your-secret-key
```

#### Option 3: Render.com
1. Create PostgreSQL database on Render
2. Copy connection string as `DATABASE_URL`
3. Deploy app with environment variable

#### Option 4: AWS RDS
```bash
# Create RDS PostgreSQL instance
# Copy connection string to environment variable
export DATABASE_URL=postgresql://user:pass@host:5432/dbname
python app.py
```

#### Option 5: Local PostgreSQL
```bash
# Install PostgreSQL locally
# Create database
createdb film_production

# Set connection string
export DATABASE_URL=postgresql://localhost/film_production

# Run app
python -m flask run
```

## Environment Variables

### Required
- `DATABASE_URL`: PostgreSQL connection string (production only)
  - Format: `postgresql://user:password@host:port/database`
  - Leave unset for SQLite development

### Optional
- `SECRET_KEY`: Session secret (change for production!)
- `FLASK_ENV`: Set to `production` for production
- `SMTP_USERNAME`: Gmail address for email notifications
- `SMTP_PASSWORD`: Gmail app password

## Database Migration

If you have existing SQLite data:
```bash
# Export from SQLite
sqlite3 data/film_production.db ".dump" > backup.sql

# This manual export is needed; import to PostgreSQL as needed
# Or simply start fresh with PostgreSQL for production
```

## Troubleshooting

**Error: "psycopg2 not installed"**
```bash
pip install psycopg2-binary
```

**Error: "could not connect to database"**
- Check `DATABASE_URL` format
- Verify PostgreSQL server is running
- Check credentials and network access

**Error: "relation does not exist"**
- Run: `heroku run python -c "from app import init_db; init_db()"`
- Or locally: `python -c "from app import init_db; init_db()"`

## Features by Database

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| Development | ✓ | ✓ |
| Local testing | ✓ | ✓ |
| Production | ✗ | ✓ |
| Concurrent users | Limited | ✓ |
| Advanced security | Limited | ✓ |
| Backups | Manual | Automated |
