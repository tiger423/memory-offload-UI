# Deployment Checklist

Complete checklist for deploying the LLM Inference Web UI in different environments.

## 📋 Pre-Deployment Checklist

### System Requirements Verified

```
□ Node.js v18+ installed and accessible
□ Python 3.9+ installed and accessible
□ CUDA 11.8+ installed (if using GPU)
□ GPU with 16GB+ VRAM available
□ System RAM: 32GB+ (64GB recommended)
□ Storage: 100GB+ free space
□ Network: Stable internet for model downloads
```

### Dependencies Installed

```
□ Node.js packages: npm install (in webapp/)
□ Python packages: pip install -r backend/requirements.txt
□ All imports work: python -c "from backend import InferenceEngine"
□ CUDA available: python -c "import torch; print(torch.cuda.is_available())"
```

### Configuration Complete

```
□ .env file created in webapp/
□ HF_TOKEN set with valid token
□ PYTHON_PATH configured correctly
□ PORT configured (default 3000)
□ Firewall rules allow port access
□ offload/ directory created
□ model_cache/ directory created
```

### Testing Complete

```
□ Backend config tests pass
□ Memory utils tests pass
□ Diagnostics script passes
□ Server starts without errors
□ WebSocket connects successfully
□ At least one inference test completed
□ No memory leaks detected
```

---

## 🏠 Local Development Deployment

### Step 1: Environment Setup

```bash
# Navigate to project
cd vLLM

# Install dependencies
cd webapp && npm install
cd .. && pip install -r backend/requirements.txt

# Configure
cd webapp
cp .env.example .env
# Edit .env with your settings
```

### Step 2: Configuration

**webapp/.env:**
```env
PORT=3000
PYTHON_PATH=python
HF_TOKEN=hf_your_token_here
NODE_ENV=development
```

### Step 3: Start Server

```bash
cd webapp
npm run dev  # Development mode with auto-reload
```

### Step 4: Verify

```
□ Open http://localhost:3000
□ WebSocket connects (green badge)
□ Models load in dropdown
□ Run test inference
□ Check browser console for errors
□ Check server terminal for errors
```

---

## 🌐 Production Deployment

### Step 1: Production Environment

```bash
# Set production environment
export NODE_ENV=production

# Use production-grade process manager
npm install -g pm2
```

### Step 2: Configuration

**webapp/.env:**
```env
PORT=3000
PYTHON_PATH=/usr/bin/python3
HF_TOKEN=hf_your_token_here
NODE_ENV=production
HF_CACHE_DIR=/var/cache/llm_models
OFFLOAD_DIR=/var/tmp/llm_offload
LOG_LEVEL=INFO
```

### Step 3: Security Hardening

```bash
□ Remove hardcoded tokens
□ Use environment variables only
□ Set proper file permissions
□ Configure firewall rules
□ Enable HTTPS (if external access)
□ Set up reverse proxy (nginx)
□ Configure rate limiting
□ Enable logging
```

### Step 4: Start with PM2

```bash
cd webapp

# Start application
pm2 start server.js --name llm-ui

# Configure auto-restart
pm2 startup
pm2 save

# Monitor
pm2 monit
pm2 logs llm-ui
```

### Step 5: Configure Nginx (Optional)

**/etc/nginx/sites-available/llm-ui:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL certificates
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Main application
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket endpoint
    location /socket.io/ {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Static files (if serving directly)
    location /static {
        alias /path/to/vLLM/webapp/public;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/llm-ui /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 6: Monitoring

```bash
# PM2 monitoring
pm2 monit

# Check logs
pm2 logs llm-ui --lines 100

# Check resource usage
pm2 show llm-ui

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

---

## 🐳 Docker Deployment

### Step 1: Create Dockerfile

**Dockerfile:**
```dockerfile
FROM node:18-slim

# Install Python
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package files
COPY webapp/package*.json ./webapp/
COPY backend/requirements.txt ./backend/

# Install Node.js dependencies
WORKDIR /app/webapp
RUN npm ci --only=production

# Install Python dependencies
WORKDIR /app
RUN pip3 install --no-cache-dir -r backend/requirements.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 3000

# Set environment
ENV NODE_ENV=production
ENV PYTHON_PATH=python3

# Start application
WORKDIR /app/webapp
CMD ["node", "server.js"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  llm-ui:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - PYTHON_PATH=python3
      - HF_TOKEN=${HF_TOKEN}
      - PORT=3000
    volumes:
      - model_cache:/app/model_cache
      - offload:/app/offload
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  model_cache:
  offload:
```

### Step 2: Build and Run

```bash
# Build image
docker build -t llm-ui:latest .

# Run with docker-compose
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## ☁️ Cloud Deployment

### AWS EC2

**Instance Requirements:**
```
Instance Type: g4dn.xlarge or larger
GPU: NVIDIA T4 (16GB) or better
vCPU: 4+
RAM: 16GB+
Storage: 100GB+ EBS
OS: Ubuntu 22.04 LTS
```

**Setup Steps:**

```bash
# 1. Launch EC2 instance with GPU
# 2. SSH into instance
ssh -i your-key.pem ubuntu@ec2-xx-xx-xx-xx.compute.amazonaws.com

# 3. Install CUDA
sudo apt update
sudo apt install nvidia-driver-525 nvidia-cuda-toolkit

# 4. Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 5. Install Python
sudo apt install python3 python3-pip

# 6. Clone/upload project
git clone <your-repo> or scp files

# 7. Follow production deployment steps above

# 8. Configure security group
# Allow inbound: Port 22 (SSH), Port 80 (HTTP), Port 443 (HTTPS)
# Restrict to your IP or use VPN

# 9. Set up CloudWatch for monitoring
# 10. Configure auto-scaling (optional)
```

### Google Cloud Platform (GCP)

**Instance Requirements:**
```
Machine Type: n1-standard-4 with 1x NVIDIA T4
GPU: NVIDIA T4 (16GB)
vCPU: 4
RAM: 15GB
Storage: 100GB SSD
OS: Ubuntu 22.04 LTS
```

**Setup Steps:**

```bash
# 1. Create Compute Engine instance with GPU
# 2. SSH into instance via Cloud Console
# 3. Install NVIDIA drivers
curl https://raw.githubusercontent.com/GoogleCloudPlatform/compute-gpu-installation/main/linux/install_gpu_driver.py --output install_gpu_driver.py
sudo python3 install_gpu_driver.py

# 4. Follow same steps as AWS above
# 5. Configure firewall rules
# 6. Set up Cloud Monitoring
```

---

## 🔧 Post-Deployment Configuration

### Health Checks

```bash
# Create health check script
cat > health_check.sh << 'EOF'
#!/bin/bash
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/status)
if [ $RESPONSE -eq 200 ]; then
    echo "✅ Server healthy"
    exit 0
else
    echo "❌ Server unhealthy (HTTP $RESPONSE)"
    exit 1
fi
EOF

chmod +x health_check.sh

# Add to cron for monitoring
crontab -e
# Add: */5 * * * * /path/to/health_check.sh >> /var/log/health_check.log 2>&1
```

### Backup Strategy

```bash
# Backup configuration
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
    webapp/.env \
    backend/config.py

# Backup model cache (if modified)
tar -czf models_backup_$(date +%Y%m%d).tar.gz model_cache/

# Upload to S3 or similar
# aws s3 cp config_backup_*.tar.gz s3://your-bucket/backups/
```

### Log Rotation

```bash
# Configure logrotate
sudo cat > /etc/logrotate.d/llm-ui << 'EOF'
/var/log/llm-ui/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        pm2 reloadLogs
    endscript
}
EOF
```

### Performance Tuning

```bash
# Increase Node.js memory limit (if needed)
pm2 start server.js --name llm-ui --node-args="--max-old-space-size=4096"

# Configure Python memory limits
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Enable GPU persistence mode
nvidia-smi -pm 1
```

---

## 📊 Monitoring & Alerts

### Metrics to Monitor

```
□ CPU usage (< 80%)
□ RAM usage (< 90%)
□ GPU usage
□ GPU memory usage
□ Disk usage (< 90%)
□ Network I/O
□ HTTP response times
□ WebSocket connections
□ Active inference sessions
□ Error rates
```

### Alert Thresholds

```
Critical:
  - CPU > 95% for 5 minutes
  - RAM > 95% for 5 minutes
  - Disk > 95%
  - Server down

Warning:
  - CPU > 80% for 10 minutes
  - RAM > 80% for 10 minutes
  - Disk > 80%
  - Error rate > 5%
```

### Monitoring Tools

**PM2 Monitoring:**
```bash
pm2 install pm2-server-monit
pm2 web  # Access http://localhost:9615
```

**Custom Monitoring Script:**
```bash
#!/bin/bash
# monitor.sh

while true; do
    # CPU
    CPU=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')

    # RAM
    RAM=$(free | grep Mem | awk '{print ($3/$2) * 100.0}')

    # GPU
    GPU=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits)

    echo "$(date): CPU=${CPU}% RAM=${RAM}% GPU=${GPU}%"

    # Alert if thresholds exceeded
    if (( $(echo "$CPU > 95" | bc -l) )); then
        echo "ALERT: High CPU usage!"
    fi

    sleep 60
done
```

---

## 🔐 Security Checklist

### Application Security

```
□ No hardcoded secrets
□ Environment variables only
□ Input validation enabled
□ Rate limiting configured
□ CORS properly configured
□ HTTPS enabled (production)
□ Security headers set
□ Dependencies updated
□ Vulnerabilities scanned (npm audit)
```

### System Security

```
□ Firewall configured
□ SSH key-based auth only
□ Fail2ban installed
□ Automatic security updates
□ Regular backups scheduled
□ Logs monitored
□ Intrusion detection configured
□ Least privilege principle applied
```

---

## ✅ Final Verification

### Smoke Tests

```bash
# 1. Server responds
curl http://localhost:3000/api/status

# 2. Models endpoint works
curl http://localhost:3000/api/models

# 3. WebSocket connects
# Check browser console at http://localhost:3000

# 4. Can start inference
# Use web UI or curl to POST /api/inference/start

# 5. Logs are clean
pm2 logs llm-ui --lines 50

# 6. No errors in browser console
# Open http://localhost:3000 and check F12 console

# 7. Performance acceptable
# Run benchmark: python benchmark.py
```

### Load Testing (Optional)

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test API endpoint
ab -n 100 -c 10 http://localhost:3000/api/models

# Expected: < 100ms average response time
```

---

## 📝 Deployment Sign-Off

```
Deployment Date: __________
Deployed By: __________
Environment: □ Development  □ Staging  □ Production
Version/Commit: __________

Pre-Deployment:
□ All tests passed
□ Configuration reviewed
□ Backup created
□ Team notified

Post-Deployment:
□ Health checks passing
□ Monitoring active
□ Logs reviewed
□ Performance verified
□ Documentation updated

Sign-Off: __________
```

---

## 🆘 Rollback Procedure

If deployment fails:

```bash
# 1. Stop current deployment
pm2 stop llm-ui

# 2. Restore previous version
git checkout <previous-commit>
# or restore from backup

# 3. Restart with previous version
pm2 restart llm-ui

# 4. Verify rollback successful
curl http://localhost:3000/api/status

# 5. Investigate issue
pm2 logs llm-ui
# Check error logs

# 6. Document incident
# Add to deployment log
```

---

## 📚 Additional Resources

- [Production Best Practices](https://expressjs.com/en/advanced/best-practice-performance.html)
- [PM2 Documentation](https://pm2.keymetrics.io/docs/usage/quick-start/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)

---

**Deployment Complete!** 🎉

Remember to:
- Monitor logs regularly
- Update dependencies
- Perform regular backups
- Test disaster recovery
- Document changes
