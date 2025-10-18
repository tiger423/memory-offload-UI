#!/bin/bash
# Comprehensive diagnostic script

echo "========================================="
echo "LLM Inference UI Diagnostics"
echo "========================================="

# Check Node.js
echo -e "\n1. Node.js:"
if command -v node &> /dev/null; then
    node --version
    echo "✅ Node.js installed"
else
    echo "❌ Node.js not found"
fi

# Check Python
echo -e "\n2. Python:"
if command -v python &> /dev/null; then
    python --version
    echo "✅ Python installed"
elif command -v python3 &> /dev/null; then
    python3 --version
    echo "✅ Python3 installed"
else
    echo "❌ Python not found"
fi

# Check CUDA
echo -e "\n3. CUDA:"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    echo "✅ CUDA available"
else
    echo "⚠️  CUDA not detected"
fi

# Check Python packages
echo -e "\n4. Python Packages:"
python -c "import torch; print(f'torch: {torch.__version__}')" 2>/dev/null && echo "✅ torch" || echo "❌ torch"
python -c "import transformers; print(f'transformers: {transformers.__version__}')" 2>/dev/null && echo "✅ transformers" || echo "❌ transformers"
python -c "import accelerate; print(f'accelerate: {accelerate.__version__}')" 2>/dev/null && echo "✅ accelerate" || echo "❌ accelerate"
python -c "import bitsandbytes; print(f'bitsandbytes: {bitsandbytes.__version__}')" 2>/dev/null && echo "✅ bitsandbytes" || echo "❌ bitsandbytes"

# Check Node packages
echo -e "\n5. Node.js Packages:"
cd webapp 2>/dev/null
if [ -d "node_modules" ]; then
    echo "✅ node_modules exists"
    [ -d "node_modules/express" ] && echo "✅ express" || echo "❌ express"
    [ -d "node_modules/socket.io" ] && echo "✅ socket.io" || echo "❌ socket.io"
else
    echo "❌ node_modules not found. Run: npm install"
fi
cd ..

# Check .env file
echo -e "\n6. Configuration:"
if [ -f "webapp/.env" ]; then
    echo "✅ .env file exists"
    if grep -q "HF_TOKEN=hf_" webapp/.env; then
        echo "✅ HF_TOKEN configured"
    else
        echo "⚠️  HF_TOKEN not set or invalid"
    fi
else
    echo "❌ .env file not found"
fi

# Check backend imports
echo -e "\n7. Backend Imports:"
python -c "from backend.inference_engine import InferenceEngine; print('✅ backend imports work')" 2>/dev/null || echo "❌ backend import failed"

# Check server
echo -e "\n8. Server Status:"
if curl -s http://localhost:3000/api/status > /dev/null 2>&1; then
    echo "✅ Server is running"
else
    echo "⚠️  Server not running. Start with: cd webapp && npm start"
fi

echo -e "\n========================================="
echo "Diagnostics Complete"
echo "========================================="
