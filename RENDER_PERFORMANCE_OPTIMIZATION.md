# Render Performance Optimization Guide

## Changes Made to Improve Load Times

### 1. **Switch from Flask Dev Server to Gunicorn** ✅
- **Before**: Using `python run.py` (Flask's development server)
- **After**: Using Gunicorn with optimized configuration
- **Impact**: 2-3x faster request handling, better concurrency

### 2. **Optimized Gunicorn Configuration** ✅
- **Workers**: 2 workers with 2 threads each (balanced for free tier)
- **Preload App**: Enabled to reduce memory usage
- **Worker Temp Dir**: Using `/dev/shm` (shared memory) for faster worker heartbeats
- **Timeout**: 60 seconds
- **Auto-restart**: Workers restart after 1000-1100 requests to prevent memory leaks

### 3. **Health Check Endpoint** ✅
- Added `/health` endpoint for monitoring
- Can be used with external services to keep the app warm (see below)

## Understanding Render Free Tier Limitations

### The Cold Start Problem
Render's free tier **spins down your app after 15 minutes of inactivity**. When a user visits:
1. Render must spin up a new container (15-30 seconds)
2. Install dependencies (cached, but still takes time)
3. Start your app (10-20 seconds)
4. **Total: 30-60+ seconds for first load**

This is **unavoidable** on the free tier, but we can minimize it.

## Additional Strategies to Reduce Cold Starts

### Option 1: Use an External Pinger Service (Recommended)
Use a free monitoring service to ping your app every 10-14 minutes:

**Free Services:**
- **[UptimeRobot](https://uptimerobot.com/)** (50 monitors free)
  - Set up HTTP monitor
  - URL: `https://your-app.onrender.com/health`
  - Interval: 5 minutes (or 10 to stay under limits)
  
- **[Cron-Job.org](https://cron-job.org/)** (3 jobs free)
  - Create a cron job
  - URL: `https://your-app.onrender.com/health`
  - Schedule: Every 10 minutes (`*/10 * * * *`)

- **[Koyeb](https://www.koyeb.com/)** (has a free tier with always-on apps)

**⚠️ Important**: 
- Don't ping too frequently (< 5 minutes) - it may violate Render's terms
- This strategy works but isn't officially supported by Render

### Option 2: Upgrade to Render Paid Tier
- **Starter Plan**: $7/month for always-on service
- **No cold starts** ever
- More resources (512 MB RAM vs 512 MB on free tier)

### Option 3: Self-Ping from the App (Not Recommended)
You could add a scheduled task within your app to ping itself, but:
- ❌ Violates Render's fair use policy
- ❌ May get your account suspended
- ❌ Not a good practice

## Performance Monitoring

### Check Your App's Speed
1. **Cold start time**: Visit after 20+ minutes of inactivity
2. **Warm response time**: Visit immediately after another visit

### Expected Times with Optimizations:
- **Cold start**: 30-50 seconds (unavoidable on free tier)
- **Warm response**: 200-800ms (much faster with Gunicorn)

## Deployment Checklist

When you deploy these changes to Render:

1. **Push changes to GitHub**
   ```bash
   git add render.yaml gunicorn.conf.py dictation/routes.py RENDER_PERFORMANCE_OPTIMIZATION.md
   git commit -m "Optimize for Render with Gunicorn and health check"
   git push origin main
   ```

2. **Render will auto-deploy** (if connected to GitHub)
   - Watch the deploy logs
   - Look for: "Starting gunicorn" message

3. **Test the health endpoint**
   ```bash
   curl https://your-app.onrender.com/health
   ```
   Should return: `{"status": "ok", "service": "chinese-dictation"}`

4. **Set up UptimeRobot** (optional but recommended)
   - Create account
   - Add monitor for `/health` endpoint
   - Set 10-minute interval

## Additional Optimizations (Future)

### If App Still Feels Slow:
1. **Enable caching**: Add Flask-Caching for frequently accessed data
2. **Lazy load JSON files**: Don't load all conversations/stories at startup
3. **Use CDN for static assets**: Serve audio files from a CDN
4. **Optimize database queries**: Add indexes, use connection pooling
5. **Compress responses**: Enable gzip compression in Gunicorn

### If You Want Even Better Performance:
1. **Use Vercel/Netlify for frontend** + Keep backend on Render
2. **Switch to Railway.app** (similar free tier but different constraints)
3. **Use Fly.io** (generous free tier, faster cold starts)
4. **Deploy to Heroku** (no free tier anymore, but Eco dyno is $5/month)

## Current Configuration Summary

| Setting | Value | Reason |
|---------|-------|--------|
| Server | Gunicorn | Production-ready WSGI server |
| Workers | 2 | Balance performance/memory on free tier |
| Threads | 2 per worker | Handle concurrent requests |
| Timeout | 60s | Allow for slow database queries |
| Preload | Enabled | Reduce memory usage |
| Health endpoint | `/health` | For monitoring/pinging |

## Questions?

If load times are still unacceptable after these optimizations:
- The bottleneck is likely **cold starts** (Render's free tier limitation)
- Consider using a pinger service or upgrading to paid tier
- For critical apps, the $7/month is worth it for always-on performance

