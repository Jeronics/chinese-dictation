"""
Gunicorn configuration file for production deployment on Render
Optimized for free tier constraints while maintaining good performance
"""
import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
backlog = 2048

# Worker processes
# Use 2 workers on free tier to balance performance and memory usage
workers = 2
worker_class = "sync"
worker_connections = 1000
threads = 2
timeout = 60
keepalive = 5

# Restart workers after this many requests to prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "chinese-dictation"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Preload app for faster worker spawn
preload_app = True

# Performance tuning
worker_tmp_dir = "/dev/shm"  # Use shared memory for worker heartbeat (faster than disk)

