# Deployment Guide - Film Production Website

This guide covers multiple deployment options for the Film Production Website application.

## Prerequisites

- Python 3.12 or higher
- pip or conda package manager
- Docker (optional, for containerized deployment)

## Local Development Setup

1. **Create virtual environment:**
   ```bash
   python -m venv .venv
   ```

2. **Activate virtual environment:**
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   # Copy the example .env file
   cp .env .env.local
   # Edit .env.local with your development settings
   ```

5. **Initialize database:**
   ```bash
   python app.py init-db
   ```

6. **Run development server:**
   ```bash
   python app.py
   ```

   The app will be available at `http://localhost:5000`

## Production Deployment

### Option 1: Using Gunicorn (Recommended for Linux/macOS)

1. **Install Gunicorn:**
   ```bash
   pip install gunicorn
   ```

2. **Create production .env file:**
   ```bash
   cp .env.production.example .env.production
   # Edit .env.production with your production settings
   ```

3. **Generate a secure SECRET_KEY:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   Add the output to your `.env.production` as `SECRET_KEY`

4. **Initialize database:**
   ```bash
   python app.py init-db
   ```

5. **Run with Gunicorn:**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 --env FLASK_ENV=production wsgi:app
   ```

   For better performance, adjust worker count:
   - `-w 4`: For a 2-core server use 4 workers (cores × 2 + 1)
   - Increase for more cores

### Option 2: Using Docker (Recommended for All Platforms)

1. **Build Docker image:**
   ```bash
   docker build -t film-production-app:latest .
   ```

2. **Run container:**
   ```bash
   docker run -d \
     --name film-production \
     -p 8000:8000 \
     -e SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))') \
     -e FLASK_ENV=production \
     -v $(pwd)/data:/app/data \
     film-production-app:latest
   ```

3. **Or use docker-compose:**
   ```bash
   # Create .env file with production values
   docker-compose up -d
   ```

### Option 3: Deploy to Heroku

1. **Install Heroku CLI:**
   ```bash
   # macOS: brew tap heroku/brew && brew install heroku
   # Windows: Download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login to Heroku:**
   ```bash
   heroku login
   ```

3. **Create Heroku app:**
   ```bash
   heroku create your-app-name
   ```

4. **Set environment variables:**
   ```bash
   heroku config:set SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
   heroku config:set FLASK_ENV=production
   heroku config:set SMTP_SERVER=your_smtp_server
   heroku config:set SMTP_PORT=587
   heroku config:set SMTP_USERNAME=your_email
   heroku config:set SMTP_PASSWORD=your_password
   heroku config:set ADMIN_EMAIL=admin@yoursite.com
   ```

5. **Deploy:**
   ```bash
   git push heroku main
   ```

### Option 4: Deploy to PythonAnywhere

1. Go to https://www.pythonanywhere.com and create an account

2. Upload your code via GitHub or manual upload

3. Create a web app with Python 3.12

4. Configure the WSGI file to point to `wsgi.py`

5. Set environment variables in Web app settings

6. Reload the web app

### Option 5: Deploy to Railway

1. Connect your GitHub repository

2. Set environment variables in Railway dashboard

3. Railway will auto-detect Flask and deploy

## Environment Variables

### Required for Production
- `SECRET_KEY` - Strong random secret key for Flask sessions

### Optional
- `FLASK_ENV` - Set to `production`
- `FLASK_DEBUG` - Set to `False` for production
- `FLASK_HOST` - Bind address (default: 0.0.0.0)
- `FLASK_PORT` - Port number (default: 8000)
- `SMTP_SERVER` - Email server for contact form
- `SMTP_PORT` - Email server port
- `SMTP_USERNAME` - Email account
- `SMTP_PASSWORD` - Email password
- `ADMIN_EMAIL` - Admin email for notifications

## SSL/HTTPS Setup

For production with HTTPS:

### Using Nginx as Reverse Proxy

1. **Install Nginx:**
   ```bash
   sudo apt-get install nginx
   ```

2. **Configure Nginx:**
   Create `/etc/nginx/sites-available/film-production`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. **Enable the site:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/film-production /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

4. **Setup SSL with Let's Encrypt:**
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

## Systemd Service (for Linux)

Create `/etc/systemd/system/film-production.service`:

```ini
[Unit]
Description=Film Production Website
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/film-production
Environment="PATH=/var/www/film-production/venv/bin"
ExecStart=/var/www/film-production/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 wsgi:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable film-production
sudo systemctl start film-production
```

## Performance Optimization

1. **Enable Gzip compression in Nginx**
2. **Set up CDN for static assets**
3. **Use database connection pooling**
4. **Enable browser caching headers**
5. **Monitor performance with tools like New Relic or DataDog**

## Database

The app uses SQLite by default. For production with multiple workers:
- Consider PostgreSQL or MySQL for better concurrency
- Update connection settings in `app.py`

## Monitoring & Logging

### View Logs with Docker
```bash
docker logs -f film-production
```

### View Logs with Systemd
```bash
sudo journalctl -u film-production -f
```

## Backup Strategy

Regular backup of database and uploads:
```bash
# Backup database
cp data/film_production.db data/film_production.db.backup

# Or with Docker
docker exec film-production cp data/film_production.db data/film_production.db.backup
```

## Security Checklist

- [ ] Set `FLASK_DEBUG=False` in production
- [ ] Set a strong `SECRET_KEY`
- [ ] Use HTTPS/SSL
- [ ] Keep dependencies updated: `pip install --upgrade -r requirements.txt`
- [ ] Set up proper file permissions
- [ ] Use a production database (PostgreSQL/MySQL)
- [ ] Enable CORS only for trusted domains
- [ ] Regular security audits of dependencies
- [ ] Set up Web Application Firewall (WAF) if possible
- [ ] Monitor logs for suspicious activity

## Troubleshooting

### Port already in use
```bash
# Find process using port 8000
lsof -i :8000
# Kill the process
kill -9 <PID>
```

### Module not found errors
```bash
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

### Database locked errors
```bash
# Reset the database
python app.py init-db
```

## Support

For issues or questions about deployment, please refer to the README.md or contact your hosting provider.
