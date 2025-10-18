/**
 * Frontend JavaScript for LLM Inference UI
 * Handles WebSocket communication and UI updates
 */

// Global state
let socket = null;
let currentSessionId = null;
let models = [];
let isRunning = false;

// DOM elements
const elements = {
    modelSelect: document.getElementById('modelSelect'),
    modelInfo: document.getElementById('modelInfo'),
    modelSize: document.getElementById('modelSize'),
    modelGpu: document.getElementById('modelGpu'),
    modelRam: document.getElementById('modelRam'),
    quantization: document.getElementById('quantization'),
    fp32CpuOffload: document.getElementById('fp32CpuOffload'),
    gpuMemory: document.getElementById('gpuMemory'),
    cpuMemory: document.getElementById('cpuMemory'),
    maxLength: document.getElementById('maxLength'),
    temperature: document.getElementById('temperature'),
    tempValue: document.getElementById('tempValue'),
    topP: document.getElementById('topP'),
    topPValue: document.getElementById('topPValue'),
    promptInput: document.getElementById('promptInput'),
    startBtn: document.getElementById('startBtn'),
    stopBtn: document.getElementById('stopBtn'),
    statusCard: document.getElementById('statusCard'),
    statusSpinner: document.getElementById('statusSpinner'),
    statusText: document.getElementById('statusText'),
    statusDetail: document.getElementById('statusDetail'),
    progressBar: document.getElementById('progressBar'),
    output: document.getElementById('output'),
    metricsCard: document.getElementById('metricsCard'),
    deviceMapCard: document.getElementById('deviceMapCard'),
    deviceMapContent: document.getElementById('deviceMapContent'),
    serverStatus: document.getElementById('serverStatus'),
    gpuProgress: document.getElementById('gpuProgress'),
    gpuText: document.getElementById('gpuText'),
    cpuProgress: document.getElementById('cpuProgress'),
    cpuText: document.getElementById('cpuText')
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeWebSocket();
    loadModels();
    setupEventListeners();
});

// ============================================================
// WebSocket Setup
// ============================================================

function initializeWebSocket() {
    socket = io();

    socket.on('connect', () => {
        console.log('Connected to server');
        updateServerStatus(true);
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        updateServerStatus(false);
    });

    socket.on('status', (data) => {
        console.log('Status update:', data);
        updateStatus(data.status, data.message);
    });

    socket.on('progress', (data) => {
        console.log('Progress update:', data);
        updateProgress(data.percent, data.message);
    });

    socket.on('memory', (data) => {
        console.log('Memory update:', data);
        updateMemoryDisplay(data);
    });

    socket.on('device_map', (data) => {
        console.log('Device map:', data);
        displayDeviceMap(data);
    });

    socket.on('token', (data) => {
        console.log('Token:', data.token);
        appendToken(data.token);
    });

    socket.on('result', (data) => {
        console.log('Result:', data);
        displayResult(data);
    });

    socket.on('error', (data) => {
        console.error('Error:', data);
        displayError(data.error);
    });

    socket.on('complete', (data) => {
        console.log('Complete:', data);
        handleCompletion(data);
    });
}

// ============================================================
// API Functions
// ============================================================

async function loadModels() {
    try {
        const response = await fetch('/api/models');
        const data = await response.json();

        if (data.success) {
            models = data.models;
            populateModelSelect(models);
        } else {
            showError('Failed to load models');
        }
    } catch (error) {
        console.error('Error loading models:', error);
        showError('Failed to connect to server');
    }
}

async function startInference() {
    const modelId = elements.modelSelect.value;
    const prompt = elements.promptInput.value.trim();
    
    // just for tracking the flow
    alert('Inside app.js - startInference() ');
    
    if (!modelId) {
        alert('Please select a model');
        return;
    }

    if (!prompt) {
        alert('Please enter a prompt');
        return;
    }


    const config = {
        modelId,
        prompt,
        quantization: elements.quantization.value,
        enableFp32CpuOffload: elements.fp32CpuOffload.checked,
        maxLength: parseInt(elements.maxLength.value),
        temperature: parseFloat(elements.temperature.value),
        topP: parseFloat(elements.topP.value),
        gpuMemory: elements.gpuMemory.value,
        cpuMemory: elements.cpuMemory.value
    };
 
    try {
        const response = await fetch('/api/inference/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)        
        })

        const data = await response.json();

        if (data.success) {
            currentSessionId = data.sessionId;
            socket.emit('subscribe', currentSessionId);

            isRunning = true;
            updateUIForRunning(true);
            clearOutput();
            showStatusCard();
            updateStatus('starting', 'Initializing inference session...');
        } else {
            alert('Failed to start inference: ' + data.error);
        }
    } catch (error) {
        console.error('Error starting inference:', error);
        alert('Failed to start inference');
    }
}

async function stopInference() {
    if (!currentSessionId) return;

    try {
        const response = await fetch(`/api/session/${currentSessionId}/stop`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            updateStatus('stopped', 'Inference stopped by user');
            isRunning = false;
            updateUIForRunning(false);
        }
    } catch (error) {
        console.error('Error stopping inference:', error);
    }
}

// ============================================================
// UI Update Functions
// ============================================================

function populateModelSelect(models) {
    elements.modelSelect.innerHTML = '<option value="">-- Select a model --</option>';

    models.forEach(model => {
        const option = document.createElement('option');
        option.value = model.id;
        option.textContent = model.name;
        option.dataset.model = JSON.stringify(model);
        elements.modelSelect.appendChild(option);
    });
}

function updateModelInfo() {
    const selectedOption = elements.modelSelect.selectedOptions[0];

    if (!selectedOption || !selectedOption.value) {
        elements.modelInfo.style.display = 'none';
        return;
    }

    const model = JSON.parse(selectedOption.dataset.model);
    elements.modelSize.textContent = model.size;
    elements.modelGpu.textContent = model.minGpuMemory;
    elements.modelRam.textContent = model.minRamMemory;
    elements.modelInfo.style.display = 'block';
}

function updateServerStatus(connected) {
    if (connected) {
        elements.serverStatus.className = 'badge bg-success';
        elements.serverStatus.innerHTML = '<i class="bi bi-circle-fill"></i> Connected';
    } else {
        elements.serverStatus.className = 'badge bg-danger';
        elements.serverStatus.innerHTML = '<i class="bi bi-circle-fill"></i> Disconnected';
    }
}

function updateUIForRunning(running) {
    elements.startBtn.style.display = running ? 'none' : 'block';
    elements.stopBtn.style.display = running ? 'block' : 'none';
    elements.modelSelect.disabled = running;
    elements.quantization.disabled = running;
    elements.fp32CpuOffload.disabled = running;
    elements.promptInput.disabled = running;
}

function showStatusCard() {
    elements.statusCard.style.display = 'block';
    elements.statusCard.classList.add('card-animate');
}

function hideStatusCard() {
    elements.statusCard.style.display = 'none';
}

function updateStatus(status, message) {
    elements.statusText.textContent = getStatusText(status);
    elements.statusDetail.textContent = message || '';

    // Update spinner
    if (status === 'completed' || status === 'failed' || status === 'stopped') {
        elements.statusSpinner.style.display = 'none';
    } else {
        elements.statusSpinner.style.display = 'block';
    }

    // Update status color
    elements.statusCard.className = 'card shadow-sm mb-3 card-animate';
    if (status === 'completed') {
        elements.statusCard.classList.add('border-success');
    } else if (status === 'failed') {
        elements.statusCard.classList.add('border-danger');
    }
}

function getStatusText(status) {
    const statusMap = {
        'starting': '🚀 Starting...',
        'loading': '📥 Loading model...',
        'generating': '✍️ Generating text...',
        'completed': '✅ Complete!',
        'failed': '❌ Failed',
        'stopped': '⏹️ Stopped'
    };
    return statusMap[status] || status;
}

function updateProgress(percent, message) {
    elements.progressBar.style.width = `${percent}%`;
    if (message) {
        elements.statusDetail.textContent = message;
    }
}

function updateMemoryDisplay(memoryData) {
    if (memoryData.gpu) {
        const gpuPercent = (memoryData.gpu.allocated / memoryData.gpu.total) * 100;
        elements.gpuProgress.style.width = `${gpuPercent}%`;
        elements.gpuText.textContent = `${memoryData.gpu.allocated.toFixed(1)} / ${memoryData.gpu.total.toFixed(1)} GB`;
    }

    if (memoryData.cpu) {
        const cpuPercent = memoryData.cpu.percent;
        elements.cpuProgress.style.width = `${cpuPercent}%`;
        elements.cpuText.textContent = `${memoryData.cpu.used.toFixed(1)} / ${memoryData.cpu.total.toFixed(1)} GB`;
    }
}

function clearOutput() {
    elements.output.innerHTML = '';
    elements.metricsCard.style.display = 'none';
    elements.deviceMapCard.style.display = 'none';
}

function appendToken(token) {
    const span = document.createElement('span');
    span.textContent = token;
    span.className = 'new-token';
    elements.output.appendChild(span);

    // Auto-scroll to bottom
    elements.output.scrollTop = elements.output.scrollHeight;
}

function displayResult(data) {
    elements.output.innerHTML = '';

    // Display prompt
    const promptDiv = document.createElement('div');
    promptDiv.className = 'output-prompt';
    promptDiv.textContent = '📝 Prompt: ' + data.prompt;
    elements.output.appendChild(promptDiv);

    // Display separator
    const separator = document.createElement('div');
    separator.className = 'output-separator';
    elements.output.appendChild(separator);

    // Display generated text
    const outputDiv = document.createElement('div');
    outputDiv.className = 'output-generated';
    outputDiv.textContent = data.text;
    elements.output.appendChild(outputDiv);

    // Display metrics
    if (data.metrics) {
        displayMetrics(data.metrics);
    }
}

function displayMetrics(metrics) {
    elements.metricsCard.style.display = 'block';
    elements.metricsCard.classList.add('card-animate');

    document.getElementById('metricLoadTime').textContent =
        metrics.loadTime ? `${metrics.loadTime.toFixed(1)}s` : '-';

    document.getElementById('metricGenTime').textContent =
        metrics.genTime ? `${metrics.genTime.toFixed(1)}s` : '-';

    document.getElementById('metricTPS').textContent =
        metrics.tokensPerSecond ? metrics.tokensPerSecond.toFixed(2) : '-';

    document.getElementById('metricGpuLayers').textContent =
        metrics.gpuLayers || '-';

    document.getElementById('metricCpuLayers').textContent =
        metrics.cpuLayers || '-';
}

function displayDeviceMap(deviceMap) {
    elements.deviceMapCard.style.display = 'block';
    elements.deviceMapCard.classList.add('card-animate');

    let html = '<div class="row">';

    // Group by device
    const grouped = {};
    for (const [module, device] of Object.entries(deviceMap)) {
        const deviceName = device === 0 ? 'GPU' : device.toString().toUpperCase();
        if (!grouped[deviceName]) {
            grouped[deviceName] = [];
        }
        grouped[deviceName].push(module);
    }

    // Display grouped
    for (const [device, modules] of Object.entries(grouped)) {
        const color = device === 'GPU' ? 'success' : device === 'CPU' ? 'info' : 'warning';
        html += `
            <div class="col-md-6 mb-3">
                <div class="badge bg-${color} w-100 mb-2">${device} (${modules.length} modules)</div>
                <small class="text-muted">
                    ${modules.slice(0, 5).join('<br>')}
                    ${modules.length > 5 ? `<br>... and ${modules.length - 5} more` : ''}
                </small>
            </div>
        `;
    }

    html += '</div>';
    elements.deviceMapContent.innerHTML = html;
}

function displayError(error) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'output-error';
    errorDiv.innerHTML = `<strong>❌ Error:</strong><br>${error}`;
    elements.output.appendChild(errorDiv);

    updateStatus('failed', 'Inference failed');
    isRunning = false;
    updateUIForRunning(false);
}

function showError(message) {
    alert(message);
}

function handleCompletion(data) {
    updateStatus(data.status, `Completed in ${(data.duration / 1000).toFixed(1)}s`);
    isRunning = false;
    updateUIForRunning(false);
}

// ============================================================
// Event Listeners
// ============================================================

function setupEventListeners() {
    // Model selection
    elements.modelSelect.addEventListener('change', updateModelInfo);

    // Temperature slider
    elements.temperature.addEventListener('input', (e) => {
        elements.tempValue.textContent = e.target.value;
    });

    // Top P slider
    elements.topP.addEventListener('input', (e) => {
        elements.topPValue.textContent = e.target.value;
    });

    // Start button
    elements.startBtn.addEventListener('click', startInference);

    // Stop button
    elements.stopBtn.addEventListener('click', stopInference);

    // Enter key in prompt
    elements.promptInput.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            startInference();
        }
    });
}

// ============================================================
// Utility Functions
// ============================================================

function formatTime(seconds) {
    if (seconds < 60) {
        return `${seconds.toFixed(1)}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs.toFixed(0)}s`;
}

function formatBytes(bytes) {
    const gb = bytes / (1024 ** 3);
    return `${gb.toFixed(2)} GB`;
}

console.log('LLM Inference UI initialized');
