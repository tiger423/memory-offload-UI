# Logging and Debugging Guide

This guide explains the comprehensive logging system added to debug frontend-backend communication.

## 📁 Log File Locations

All logs are stored in the `logs/` directory at the project root:

```
vLLM/
├── logs/
│   ├── server_2025-01-15T10-30-45.log      # Node.js server logs
│   ├── inference_abc123_20250115_103100.log # Python inference logs (per session)
│   └── inference_def456_20250115_104500.log # Another session
```

## 🔍 Logging Levels

Both backend and frontend support multiple log levels:

| Level | Backend (Python) | Frontend (Node.js) | Description |
|-------|-----------------|-------------------|-------------|
| **DEBUG** | All messages | All messages | Verbose debugging info |
| **INFO** | Important events | Important events | Normal operation |
| **WARN** | Warnings | Warnings | Potential issues |
| **ERROR** | Errors only | Errors only | Failures |

### Setting Log Level

**Environment Variable (applies to both):**
```bash
# In .env file
LOG_LEVEL=DEBUG

# Or set temporarily
export LOG_LEVEL=DEBUG  # Linux/Mac
set LOG_LEVEL=DEBUG     # Windows
```

**Backend Python (per-session override):**
```bash
python backend/inference_api.py --log-level DEBUG ...
```

## 📝 Backend Python Logging

### What Gets Logged

**Location:** `logs/inference_{session_id}_{timestamp}.log`

**Logged Events:**

1. **Session Initialization**
   ```
   2025-01-15 10:31:00 [INFO] [inference_api] ================================================================================
   2025-01-15 10:31:00 [INFO] [inference_api] INFERENCE API STARTED - Session: abc123
   2025-01-15 10:31:00 [INFO] [inference_api] ================================================================================
   2025-01-15 10:31:00 [INFO] [inference_api] Log file: /path/to/logs/inference_abc123_20250115_103100.log
   2025-01-15 10:31:00 [INFO] [inference_api] Model: opt-30b
   2025-01-15 10:31:00 [INFO] [inference_api] Prompt: Once upon a time...
   2025-01-15 10:31:00 [INFO] [inference_api] Quantization: 8-bit
   2025-01-15 10:31:00 [INFO] [inference_api] GPU Memory: 14GiB
   ```

2. **Model Validation**
   ```
   2025-01-15 10:31:01 [INFO] [inference_api] Validating model: opt-30b
   2025-01-15 10:31:01 [INFO] [inference_api] Initializing InferenceEngine for opt-30b
   ```

3. **Model Loading**
   ```
   2025-01-15 10:31:05 [INFO] [inference_api] Starting model loading...
   2025-01-15 10:32:30 [INFO] [inference_api] Model loaded successfully, starting text generation
   ```

4. **JSON Messages Sent to Frontend**
   ```
   2025-01-15 10:31:05 [DEBUG] [inference_api] EMIT -> status: {
     "status": "loading",
     "message": "Loading model..."
   }
   2025-01-15 10:31:10 [DEBUG] [inference_api] EMIT -> progress: {
     "percent": 30,
     "message": "Loading model weights..."
   }
   ```

5. **Generation Completion**
   ```
   2025-01-15 10:33:45 [INFO] [inference_api] Generation completed: 50 tokens in 15.23s
   2025-01-15 10:33:46 [INFO] [inference_api] ================================================================================
   2025-01-15 10:33:46 [INFO] [inference_api] INFERENCE COMPLETED SUCCESSFULLY
   ```

6. **Errors**
   ```
   2025-01-15 10:31:05 [ERROR] [inference_api] EXCEPTION: Model opt-30b not found in registry
   2025-01-15 10:31:05 [ERROR] [inference_api] Stack trace:
   Traceback (most recent call last):
     ...
   ```

### Reading Backend Logs

```bash
# Find your session log
ls -lt logs/ | grep inference_

# Tail a specific session
tail -f logs/inference_abc123_20250115_103100.log

# Search for errors
grep ERROR logs/inference_*.log

# Search for specific session
grep "abc123" logs/inference_*.log
```

## 🌐 Frontend Node.js Logging

### What Gets Logged

**Location:** `logs/server_{timestamp}.log`

**Logged Events:**

1. **Server Startup**
   ```
   2025-01-15T10:30:45.123Z [INFO] [server] ============================================================
   2025-01-15T10:30:45.124Z [INFO] [server] Server Logger Initialized
   2025-01-15T10:30:45.125Z [INFO] [server] Log file: /path/to/logs/server_2025-01-15T10-30-45.log
   ```

2. **HTTP Requests**
   ```
   2025-01-15T10:31:00.234Z [INFO] [server] GET /api/models {
     "query": {},
     "body": undefined,
     "ip": "::1"
   }
   2025-01-15T10:31:00.235Z [INFO] [server] Fetching available models list
   2025-01-15T10:31:00.236Z [DEBUG] [server] Returned models: [ "opt-30b", "llama2-7b", "llama2-13b", "falcon-7b" ]
   ```

3. **Inference Requests**
   ```
   2025-01-15T10:31:05.456Z [INFO] [server] ============================================================
   2025-01-15T10:31:05.457Z [INFO] [server] NEW INFERENCE REQUEST
   2025-01-15T10:31:05.458Z [INFO] [server] ============================================================
   2025-01-15T10:31:05.459Z [INFO] [server] Request parameters: {
     "modelId": "opt-30b",
     "promptLength": 50,
     "quantization": "8-bit",
     "enableFp32CpuOffload": true,
     "maxLength": 50,
     "temperature": 0.7,
     "topP": 0.9,
     "gpuMemory": "14GiB",
     "cpuMemory": "56GiB"
   }
   2025-01-15T10:31:05.500Z [INFO] [server] Created new session: abc123
   2025-01-15T10:31:05.501Z [INFO] [server] Active sessions count: 1
   ```

4. **Python Process Management**
   ```
   2025-01-15T10:31:05.502Z [INFO] [server] [abc123] Starting Python inference process
   2025-01-15T10:31:05.503Z [INFO] [server] [abc123] Python command: python backend/inference_api.py --model opt-30b --prompt "Once upon a time..." ...
   2025-01-15T10:31:05.750Z [INFO] [server] [abc123] Python process spawned with PID 12345
   ```

5. **Python Communication (stdout/stderr)**
   ```
   2025-01-15T10:31:10.100Z [DEBUG] [server] [abc123] STDOUT: {"type":"status","data":{"status":"loading","message":"Loading model..."}}
   2025-01-15T10:31:10.101Z [DEBUG] [server] [abc123] Parsed message: {
     "type": "status",
     "data": {
       "status": "loading",
       "message": "Loading model..."
     }
   }
   2025-01-15T10:31:10.102Z [INFO] [server] [abc123] Status update: loading - Loading model...
   ```

6. **WebSocket Events**
   ```
   2025-01-15T10:31:00.100Z [INFO] [server] WebSocket: Client connected - AbC123XyZ
   2025-01-15T10:31:05.200Z [INFO] [server] WebSocket: Client AbC123XyZ subscribed to session abc123
   2025-01-15T10:35:00.300Z [INFO] [server] WebSocket: Client disconnected - AbC123XyZ
   ```

7. **Message Handling**
   ```
   2025-01-15T10:31:15.400Z [INFO] [server] [abc123] Progress: 30% - Loading model weights...
   2025-01-15T10:32:30.500Z [INFO] [server] [abc123] Status update: ready - Model ready! Loaded in 85.3s
   2025-01-15T10:32:35.600Z [INFO] [server] [abc123] Generation started - input: 10 tokens, max: 50
   2025-01-15T10:33:45.700Z [INFO] [server] [abc123] Result received - 250 characters
   2025-01-15T10:33:46.800Z [INFO] [server] [abc123] Inference complete - completed
   ```

8. **Process Exit**
   ```
   2025-01-15T10:33:46.900Z [INFO] [server] [abc123] Python process exited with code 0
   2025-01-15T10:33:46.901Z [INFO] [server] [abc123] Session COMPLETED - Duration: 161000ms
   ```

9. **Session Cleanup**
   ```
   2025-01-15T11:33:46.900Z [INFO] [server] [abc123] Cleaning up session from memory
   ```

10. **Errors**
    ```
    2025-01-15T10:31:05.123Z [ERROR] [server] [abc123] STDERR: RuntimeError: CUDA out of memory
    2025-01-15T10:31:05.124Z [ERROR] [server] [abc123] Error received: CUDA out of memory
    ```

### Reading Frontend Logs

```bash
# Find current server log
ls -lt logs/ | grep server_ | head -1

# Tail the server log
tail -f logs/server_2025-01-15T10-30-45.log

# Search for specific session
grep "abc123" logs/server_*.log

# Search for errors
grep ERROR logs/server_*.log

# Filter by log level
grep "\[INFO\]" logs/server_*.log
grep "\[ERROR\]" logs/server_*.log
```

## 🔄 Complete Request Flow Example

Here's what a complete inference request looks like in the logs:

### 1. Frontend Receives Request
```
[INFO] [server] POST /api/inference/start
[INFO] [server] NEW INFERENCE REQUEST
[INFO] [server] Created new session: abc123
```

### 2. Frontend Spawns Python
```
[INFO] [server] [abc123] Starting Python inference process
[INFO] [server] [abc123] Python command: python backend/inference_api.py ...
[INFO] [server] [abc123] Python process spawned with PID 12345
```

### 3. Backend Starts
```python
# In logs/inference_abc123_20250115_103100.log
[INFO] [inference_api] INFERENCE API STARTED - Session: abc123
[INFO] [inference_api] Model: opt-30b
[INFO] [inference_api] Quantization: 8-bit
```

### 4. Backend Sends Progress
```python
# Backend emits JSON
[DEBUG] [inference_api] EMIT -> progress: {"percent": 30, "message": "Loading..."}
```

### 5. Frontend Receives and Forwards
```javascript
// Frontend receives on stdout
[DEBUG] [server] [abc123] STDOUT: {"type":"progress","data":{"percent":30,"message":"Loading..."}}
[DEBUG] [server] [abc123] Parsed message: {"type":"progress","data":{...}}
[INFO] [server] [abc123] Progress: 30% - Loading...
// Frontend forwards to WebSocket
```

### 6. Generation Completes
```python
# Backend
[INFO] [inference_api] Generation completed: 50 tokens in 15.23s
[DEBUG] [inference_api] EMIT -> result: {"text": "...", "metrics": {...}}
```

```javascript
// Frontend
[DEBUG] [server] [abc123] STDOUT: {"type":"result",...}
[INFO] [server] [abc123] Result received - 250 characters
[INFO] [server] [abc123] Python process exited with code 0
[INFO] [server] [abc123] Session COMPLETED - Duration: 161000ms
```

## 🐛 Debugging Common Issues

### Issue 1: Frontend Not Receiving Python Messages

**Symptoms:**
- Frontend shows "Loading..." forever
- No progress updates in browser

**Debug Steps:**

1. Check if Python process started:
   ```bash
   grep "Python process spawned" logs/server_*.log
   ```

2. Check Python stdout in frontend log:
   ```bash
   grep "STDOUT" logs/server_*.log | grep abc123
   ```

3. Check Python's own log:
   ```bash
   tail -f logs/inference_abc123_*.log
   ```

4. Look for Python errors:
   ```bash
   grep "ERROR" logs/inference_abc123_*.log
   ```

**Common Causes:**
- Python not installed or wrong path
- Missing dependencies (transformers, torch, etc.)
- HF_TOKEN not set
- CUDA/GPU issues

### Issue 2: JSON Parse Errors

**Symptoms:**
```
[WARN] [server] [abc123] Non-JSON output: Loading...
```

**Debug Steps:**

1. Check what Python is printing to stdout:
   ```bash
   grep "STDOUT" logs/server_*.log | grep abc123
   ```

2. Verify Python is emitting valid JSON:
   ```bash
   grep "EMIT" logs/inference_abc123_*.log
   ```

**Common Causes:**
- Python print statements outside emit_json()
- Library warnings going to stdout (should go to stderr)
- Incomplete JSON (buffer split mid-message)

### Issue 3: WebSocket Not Connecting

**Symptoms:**
- Browser console shows "WebSocket connection failed"
- No real-time updates

**Debug Steps:**

1. Check WebSocket connections:
   ```bash
   grep "WebSocket" logs/server_*.log
   ```

2. Verify client subscribed to session:
   ```bash
   grep "subscribed to session abc123" logs/server_*.log
   ```

**Common Causes:**
- CORS issues
- Firewall blocking WebSocket port
- Client not calling socket.emit('subscribe', sessionId)

### Issue 4: Session Not Found

**Symptoms:**
- GET /api/session/abc123 returns 404

**Debug Steps:**

1. Check if session was created:
   ```bash
   grep "Created new session: abc123" logs/server_*.log
   ```

2. Check active sessions:
   ```bash
   grep "Active sessions count" logs/server_*.log | tail -1
   ```

**Common Causes:**
- Session expired (1 hour cleanup)
- Server restarted (sessions in memory only)
- Wrong session ID

## 📊 Log Analysis Tools

### Quick Stats Script

Create `logs/analyze.sh`:

```bash
#!/bin/bash

LOG_FILE=$1

if [ -z "$LOG_FILE" ]; then
    echo "Usage: $0 <log_file>"
    exit 1
fi

echo "=== Log Analysis for $LOG_FILE ==="
echo
echo "Total lines: $(wc -l < "$LOG_FILE")"
echo "Errors: $(grep -c ERROR "$LOG_FILE")"
echo "Warnings: $(grep -c WARN "$LOG_FILE")"
echo "Info: $(grep -c INFO "$LOG_FILE")"
echo "Debug: $(grep -c DEBUG "$LOG_FILE")"
echo
echo "=== Sessions ==="
grep "Created new session" "$LOG_FILE" | sed 's/.*session: //' | sort | uniq
echo
echo "=== Recent Errors ==="
grep ERROR "$LOG_FILE" | tail -5
```

Usage:
```bash
chmod +x logs/analyze.sh
./logs/analyze.sh logs/server_2025-01-15T10-30-45.log
```

### Watch Live Logs (Both)

```bash
# Terminal 1: Server logs
tail -f logs/server_*.log | grep --line-buffered -E "INFO|ERROR|WARN"

# Terminal 2: Latest Python inference
tail -f logs/inference_*.log | grep --line-buffered -E "INFO|ERROR|WARN"
```

### Extract Session Timeline

```bash
#!/bin/bash
SESSION_ID=$1

echo "=== Timeline for Session $SESSION_ID ==="
echo
echo "--- Frontend Events ---"
grep "\\[$SESSION_ID\\]" logs/server_*.log
echo
echo "--- Backend Events ---"
cat logs/inference_${SESSION_ID}_*.log
```

## 🎯 Best Practices

1. **Always check logs when debugging**
   - Frontend log: Communication layer
   - Backend log: Model loading and inference

2. **Use appropriate log levels**
   - Development: `LOG_LEVEL=DEBUG`
   - Production: `LOG_LEVEL=INFO`
   - Troubleshooting: `LOG_LEVEL=DEBUG`

3. **Search by session ID**
   - All logs include `[session_id]` prefix
   - Easy to trace entire request flow

4. **Monitor both logs simultaneously**
   - Open two terminal windows
   - Watch communication flow in real-time

5. **Archive old logs**
   - Logs can grow large over time
   - Rotate/compress logs periodically

## 📦 Log Rotation

Add to `.env`:
```bash
# Maximum log file age (days)
LOG_MAX_AGE=7

# Maximum log file size (MB)
LOG_MAX_SIZE=100
```

Create `logs/rotate.sh`:
```bash
#!/bin/bash
find logs/ -name "*.log" -mtime +7 -exec gzip {} \;
find logs/ -name "*.log.gz" -mtime +30 -delete
```

Run daily via cron:
```bash
0 0 * * * /path/to/vLLM/logs/rotate.sh
```

## 🔍 Advanced: Real-time Log Viewer

Create `logs/viewer.html` for browser-based log viewing:

```html
<!DOCTYPE html>
<html>
<head>
    <title>vLLM Log Viewer</title>
    <style>
        body { font-family: monospace; background: #1e1e1e; color: #dcdcdc; }
        .error { color: #f44336; }
        .warn { color: #ff9800; }
        .info { color: #4caf50; }
        .debug { color: #2196f3; }
    </style>
</head>
<body>
    <h1>vLLM Log Viewer</h1>
    <select id="logFile"></select>
    <button onclick="refreshLogs()">Refresh</button>
    <pre id="logs"></pre>
    <script>
        // Fetch and display logs via API
        // (requires API endpoint to serve logs)
    </script>
</body>
</html>
```

## 📞 Support

If you encounter issues:

1. Check this guide
2. Review both frontend and backend logs
3. Search for your error message
4. Check session timeline
5. Verify environment variables

Happy debugging! 🐛✨
