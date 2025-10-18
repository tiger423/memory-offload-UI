# Debug Quick Start Guide

Quick reference for debugging frontend-backend communication.

## 🚀 Quick Setup

1. **Enable Debug Logging**
   ```bash
   # Edit webapp/.env
   LOG_LEVEL=DEBUG
   ```

2. **Start Server**
   ```bash
   cd webapp
   npm start
   ```

3. **Open Logs in Two Terminals**
   ```bash
   # Terminal 1: Server logs
   tail -f logs/server_*.log

   # Terminal 2: Python logs (after starting inference)
   tail -f logs/inference_*.log
   ```

## 📍 Find Your Session ID

### In Browser Console
```javascript
// After starting inference, look for:
Session ID: abc-123-def-456
```

### In Server Log
```bash
grep "Created new session" logs/server_*.log | tail -1
```

## 🔍 Debug Specific Session

```bash
# Get session ID (example: abc123)
SESSION_ID="abc123"

# View all frontend events for this session
grep "\[$SESSION_ID\]" logs/server_*.log

# View backend log for this session
cat logs/inference_${SESSION_ID}_*.log

# Watch both in real-time
# Terminal 1:
tail -f logs/server_*.log | grep "\[$SESSION_ID\]"

# Terminal 2:
tail -f logs/inference_${SESSION_ID}_*.log
```

## 🐛 Common Issues

### Issue: No Response from Python

**Check:**
```bash
# 1. Was Python process started?
grep "Python process spawned" logs/server_*.log | tail -5

# 2. Any Python errors?
grep "STDERR" logs/server_*.log | tail -10

# 3. Check Python log directly
ls -lt logs/inference_*.log | head -1  # Find latest
tail -50 logs/inference_XXXXX.log      # Read it
```

**Common causes:**
- Missing HF_TOKEN
- Python dependencies not installed
- CUDA/GPU issues

### Issue: Stuck at "Loading..."

**Check:**
```bash
# What was last progress message?
grep "Progress:" logs/server_*.log | grep $SESSION_ID | tail -1

# What was last Python message?
tail -20 logs/inference_${SESSION_ID}_*.log

# Any errors in Python?
grep "ERROR" logs/inference_${SESSION_ID}_*.log
```

**Common causes:**
- Out of memory
- Model download stuck
- Network issues downloading from HuggingFace

### Issue: WebSocket Not Updating

**Check:**
```bash
# Is client connected?
grep "Client connected" logs/server_*.log | tail -5

# Did client subscribe?
grep "subscribed to session $SESSION_ID" logs/server_*.log

# Is Python sending messages?
grep "EMIT" logs/inference_${SESSION_ID}_*.log | tail -10
```

## 📊 Trace Complete Request

```bash
#!/bin/bash
# Save as trace_session.sh

SESSION_ID=$1

echo "=== FRONTEND (Node.js) ==="
grep "\[$SESSION_ID\]" logs/server_*.log | head -50

echo ""
echo "=== BACKEND (Python) ==="
cat logs/inference_${SESSION_ID}_*.log | head -100
```

Usage:
```bash
chmod +x trace_session.sh
./trace_session.sh abc123
```

## 🎯 What to Look For

### Healthy Request Flow

1. **Frontend receives request**
   ```
   [INFO] NEW INFERENCE REQUEST
   [INFO] Created new session: abc123
   ```

2. **Python starts**
   ```
   [INFO] Python process spawned with PID 12345
   ```

3. **Python loads model**
   ```
   [INFO] Progress: 30% - Loading model weights...
   [INFO] Progress: 70% - Model loaded in 85.1s
   ```

4. **Python generates**
   ```
   [INFO] Generation started - input: 10 tokens
   [INFO] Generation completed: 50 tokens in 15.23s
   ```

5. **Session completes**
   ```
   [INFO] Python process exited with code 0
   [INFO] Session COMPLETED - Duration: 161000ms
   ```

### Unhealthy Indicators

❌ **No Python output**
```
[INFO] Python process spawned with PID 12345
# Nothing after this = Python crashed immediately
```

❌ **Python errors on stderr**
```
[ERROR] STDERR: RuntimeError: CUDA out of memory
[ERROR] STDERR: ModuleNotFoundError: No module named 'transformers'
```

❌ **Process exits with error code**
```
[INFO] Python process exited with code 1
[INFO] Session FAILED
```

❌ **JSON parse errors**
```
[WARN] Non-JSON output: Traceback (most recent call last):
```

## 📋 Debug Checklist

Before asking for help, check:

- [ ] Server logs exist in `logs/` directory
- [ ] Python logs exist for your session
- [ ] No ERROR lines in server log
- [ ] No ERROR lines in Python log
- [ ] Python process was spawned (has PID)
- [ ] Python process exited with code 0
- [ ] WebSocket client connected
- [ ] Client subscribed to session
- [ ] HF_TOKEN is set in .env
- [ ] All dependencies installed (npm, pip)

## 🔧 Enable Maximum Verbosity

```bash
# In .env
LOG_LEVEL=DEBUG

# Restart server
cd webapp
npm start

# Now every single message is logged:
# - Every HTTP request
# - Every WebSocket event
# - Every JSON message from Python
# - Every progress update
# - Every memory update
```

## 📞 Get Help

When reporting issues, include:

1. **Session ID**
2. **Relevant log snippets** (use `grep` examples above)
3. **Error messages** from both logs
4. **System info**:
   ```bash
   echo "Node: $(node --version)"
   echo "Python: $(python --version)"
   echo "OS: $(uname -a)"
   ```

## 🎓 Learn More

Full documentation: [LOGGING_GUIDE.md](LOGGING_GUIDE.md)

## 💡 Pro Tips

1. **Use two terminals side-by-side** - One for server log, one for Python log
2. **Grep is your friend** - Filter logs by session ID
3. **Search for ERROR first** - Usually tells you exactly what's wrong
4. **Check timestamps** - Make sure logs are recent
5. **DEBUG mode in development** - INFO mode in production

## 🎬 Example Debug Session

```bash
# User reports: "Stuck at loading forever"

# Step 1: Find the session
$ grep "Created new session" logs/server_*.log | tail -1
Created new session: abc123

# Step 2: Check Python started
$ grep "\[abc123\]" logs/server_*.log | grep "spawned"
Python process spawned with PID 12345

# Step 3: Check Python progress
$ grep "Progress:" logs/server_*.log | grep abc123
Progress: 10% - Starting...
Progress: 30% - Loading model weights...
# <-- Stuck here!

# Step 4: Check Python log
$ tail -50 logs/inference_abc123_*.log
...
[INFO] Starting model loading...
[ERROR] CUDA out of memory
# <-- Found the issue!

# Solution: Reduce GPU memory or enable CPU offload
```

Happy debugging! 🔍✨
