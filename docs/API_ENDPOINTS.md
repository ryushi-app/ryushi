# Ryushi REST API Endpoints

This guide shows how to access the Ryushi REST API endpoints.

## Available Endpoints

### Health Check

**Get combined health status:**
```bash
GET /health
```

Response:
```json
{
  "status": "ok",
  "scheduler": {
    "running": true,
    "jobs_count": 3
  }
}
```

### Jobs API

**List all configured jobs:**
```bash
GET /jobs
```

Response:
```json
{
  "jobs": [
    {
      "category_slug": "technology",
      "status": "scheduled",
      "last_run": "2024-01-15T10:30:00Z",
      "next_run": "2024-01-16T06:00:00Z"
    }
  ]
}
```

**Get status for a specific job:**
```bash
GET /jobs/{category_slug}/status
```

Example:
```bash
GET /jobs/technology/status
```

Response:
```json
{
  "category_slug": "technology",
  "status": "scheduled",
  "last_run": "2024-01-15T10:30:00Z",
  "next_run": "2024-01-16T06:00:00Z"
}
```

**Manually trigger a job:**
```bash
POST /jobs/{category_slug}/run
```

Example:
```bash
POST /jobs/technology/run
```

Response:
```json
{
  "status": "started",
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Get job history:**
```bash
GET /jobs/{category_slug}/history?limit=20
```

Example:
```bash
GET /jobs/technology/history?limit=10
```

Response:
```json
{
  "runs": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "category_slug": "technology",
      "status": "success",
      "started_at": "2024-01-15T10:00:00Z",
      "finished_at": "2024-01-15T10:05:00Z",
      "article_count": 25,
      "error": null
    }
  ]
}
```

### Feeds API

**List all available feeds:**
```bash
GET /feeds
```

Response:
```json
{
  "feeds": [
    {
      "category": "Technology",
      "slug": "technology",
      "url": "https://ryushi.example.com/feeds/technology/atom.xml",
      "last_updated": "2024-01-15T10:30:00Z",
      "item_count": 5
    },
    {
      "category": "Software Engineering",
      "slug": "software-engineering",
      "url": "https://ryushi.example.com/feeds/software-engineering/atom.xml",
      "last_updated": "2024-01-15T11:00:00Z",
      "item_count": 3
    }
  ]
}
```

**Get Atom feed for a category:**
```bash
GET /feeds/{category_slug}/atom.xml
```

Example:
```bash
GET /feeds/technology/atom.xml
```

Returns Atom XML format feed that can be consumed by any RSS reader.

## Usage Examples

### Using curl

```bash
# Check if API is running
curl http://localhost:8000/health

# List all jobs
curl http://localhost:8000/jobs

# Get specific job status
curl http://localhost:8000/jobs/technology/status

# Trigger a job manually
curl -X POST http://localhost:8000/jobs/technology/run

# Get job history (last 10 runs)
curl "http://localhost:8000/jobs/technology/history?limit=10"

# List all feeds
curl http://localhost:8000/feeds

# Get Atom feed
curl http://localhost:8000/feeds/technology/atom.xml
```

### Using Python

```python
import httpx

# Get all jobs
async with httpx.AsyncClient() as client:
    response = await client.get("http://localhost:8000/jobs")
    jobs = response.json()
    print(jobs)

# Trigger a job
async with httpx.AsyncClient() as client:
    response = await client.post("http://localhost:8000/jobs/technology/run")
    result = response.json()
    print(f"Job {result['job_id']} started")

# Get Atom feed
async with httpx.AsyncClient() as client:
    response = await client.get("http://localhost:8000/feeds/technology/atom.xml")
    print(response.text)
```

### Using JavaScript/Node.js

```javascript
// List all jobs
const response = await fetch("http://localhost:8000/jobs");
const jobs = await response.json();
console.log(jobs);

// Trigger a job
const result = await fetch("http://localhost:8000/jobs/technology/run", {
  method: "POST"
});
const job = await result.json();
console.log(`Job ${job.job_id} started`);

// Get Atom feed
const feed = await fetch("http://localhost:8000/feeds/technology/atom.xml");
const xml = await feed.text();
console.log(xml);
```

## Error Responses

### 404 - Category Not Found

```bash
curl http://localhost:8000/jobs/nonexistent/status
```

Response:
```json
{
  "detail": "Job not found: 'nonexistent'. Use GET /jobs to see available jobs."
}
```

HTTP Status: 404

### 409 - Job Already Running

```bash
curl -X POST http://localhost:8000/jobs/technology/run
```

If the job is already running:

```json
{
  "detail": "Job already running for 'technology'. Wait for it to complete."
}
```

HTTP Status: 409

### 503 - Scheduler Not Initialized

If Ryushi is still starting up:

```json
{
  "detail": "Scheduler not initialized"
}
```

HTTP Status: 503

## Query Parameters

### Job History Limit

The `/jobs/{category_slug}/history` endpoint accepts a `limit` parameter (1-100, default 20):

```bash
# Get last 5 runs
curl "http://localhost:8000/jobs/technology/history?limit=5"

# Get last 100 runs
curl "http://localhost:8000/jobs/technology/history?limit=100"
```

## Tips

1. **Get category slugs**: Use `GET /jobs` to see all configured categories and their slugs
2. **Monitor jobs**: Check status with `GET /jobs/{slug}/status` or view history with `GET /jobs/{slug}/history`
3. **Feed URLs**: Use `GET /feeds` to get the correct Atom feed URLs for each category
4. **RSS readers**: Subscribe to `/feeds/{slug}/atom.xml` in your favorite RSS reader
5. **Debugging**: Use `/health` endpoint for quick diagnostics
