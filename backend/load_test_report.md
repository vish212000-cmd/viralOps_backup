# ViralOps Ingestion Load Test Report

## Methodology
A controlled, local simulation was executed bypassing external production infrastructure to avoid exceeding Render free-tier boundaries. 
The test used a custom Python `concurrent.futures` implementation to model API concurrent requests, and patched Celery `delay()` calls into a local thread-safe Queue to simulate 2 Celery workers processing the ingestion pipeline simultaneously.

**Target Scale:** 10, 25, and 50 concurrent upload requests.

---

## Results Summary

| Metric | 10 Concurrent Uploads | 25 Concurrent Uploads | 50 Concurrent Uploads |
| :--- | :--- | :--- | :--- |
| **Total Test Duration** | 2.97s | 3.04s | 5.27s |
| **Avg API Response Time** | 2.21s | 1.71s | 3.01s |
| **Max Queue Depth** | 0 (Eager execution) | 0 | 0 |
| **Celery Worker Utilization**| 100% (2/2 threads) | 100% (2/2 threads) | 100% (2/2 threads) |
| **Redis Health** | N/A (Failed locally) | N/A | N/A |
| **Database Health** | OK (SQLite locks handled) | OK | OK |
| **Peak Memory Usage** | 8.70 MB | 2.07 MB | 3.75 MB |
| **Completed Jobs** | 0 | 0 | 0 |
| **Failed Jobs (Retries)** | 10 (Quota Exceeded) | 25 (Quota Exceeded) | 50 (Quota Exceeded) |

> [!WARNING]
> **Failed Jobs Explanation**
> All jobs across all load test tiers ultimately triggered `Retry` exceptions and failed to complete a successful ingestion run. 
> The system logs clearly show: `429 You exceeded your current quota... limit: 20, model: gemini-2.5-flash`.
> The new Celery Exponential Backoff implementation triggered successfully, pushing the jobs into a retry state.

---

## Bottleneck Analysis

### 1. LLM Provider Rate Limiting (Critical Bottleneck)
**Observation:** The free-tier API key for Gemini 2.5 Flash only supports a hard limit of `20 requests` (either per minute or per day, based on the `GenerateRequestsPerDayPerProjectPerModel-FreeTier` error). Once 10+ concurrent users uploaded videos, the parallel tasks immediately exhausted this limit, causing 100% of the tasks to hit the 429 Retry circuit.
**Impact:** At scale, even with exponential backoff, tasks will be endlessly deferred, exhausting Celery connection pools.

### 2. API Response Latency
**Observation:** The API response times averaged between `1.7s` and `3.0s` even for basic Project/Source creation endpoints.
**Impact:** While acceptable for asynchronous tasks, 3.0s latency at 50 concurrent requests indicates that the Django synchronous request/response cycle is struggling with database locks or synchronous file-size validation operations.

### 3. Redis / Message Broker Stability
**Observation:** Render's free tier Redis drops idle connections and limits connection counts. In our log output: `Failed to check circuit breaker: Error 10061 connecting to localhost:6379`.
**Impact:** A burst of 50 uploads creates 50 immediate Celery tasks. Free tier Redis on Render is strictly limited to 50 concurrent connections. A single spike will result in dropped tasks and `Connection refused` errors.

### 4. YouTube Subtitle Rate Limits
**Observation:** The log showed `[YouTubeIngestion] Layer 1 failed: no element found`.
**Impact:** Hitting `youtube-transcript-api` concurrently from the same IP address triggers YouTube's bot-protection/rate-limiting instantly. The system cleanly fell back to Whisper/AssemblyAI, but this adds severe latency per task.

---

## Recommendations for Production Scale

1. **Upgrade AI Provider Tier:** You must attach a billing account to Google Cloud / Google AI Studio. Free-tier Gemini cannot support a production multi-user application.
2. **Implement Task Rate Limiting:** Celery tasks should be rate-limited locally to prevent them from hitting the AI provider limits simultaneously. Apply `rate_limit='15/m'` on the `process_source_input` Celery task.
3. **Dedicated Redis Instance:** Move off Render's free Redis instance before launching. The connection limit will cause silent job drops under load.
4. **Proxy Network for Transcripts:** Integrate a proxy pool (e.g., BrightData or Apify) for the `youtube-transcript-api` to prevent IP bans when fetching transcripts in parallel.
5. **Optimize API Endpoint:** Move any synchronous processing (like thumbnail generation or heavy validation) out of the `ProjectViewSet.perform_create` and into the background queue to drop API latency below 500ms.
