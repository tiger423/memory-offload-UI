/**
 * LLM Inference & Fine-tuning Web UI
 * Express server with Socket.IO for real-time updates
 */

const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const bodyParser = require('body-parser');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const { v4: uuidv4 } = require('uuid');
require('dotenv').config();

// ============================================================
// Logging Setup
// ============================================================

const LOG_DIR = path.join(__dirname, '..', 'logs');
if (!fs.existsSync(LOG_DIR)) {
    fs.mkdirSync(LOG_DIR, { recursive: true });
}

const LOG_LEVELS = {
    DEBUG: 0,
    INFO: 1,
    WARN: 2,
    ERROR: 3
};

const CURRENT_LOG_LEVEL = LOG_LEVELS[process.env.LOG_LEVEL || 'INFO'];

class Logger {
    constructor(name) {
        this.name = name;
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
        this.logFile = path.join(LOG_DIR, `server_${timestamp}.log`);
        this.logStream = fs.createWriteStream(this.logFile, { flags: 'a' });
    }

    _log(level, ...args) {
        const timestamp = new Date().toISOString();
        const message = args.map(arg =>
            typeof arg === 'object' ? JSON.stringify(arg, null, 2) : arg
        ).join(' ');

        const logEntry = `${timestamp} [${level}] [${this.name}] ${message}\n`;

        // Write to file
        this.logStream.write(logEntry);

        // Write to console if level is high enough
        if (LOG_LEVELS[level] >= CURRENT_LOG_LEVEL) {
            const colorCode = {
                'DEBUG': '\x1b[36m',
                'INFO': '\x1b[32m',
                'WARN': '\x1b[33m',
                'ERROR': '\x1b[31m'
            }[level] || '\x1b[0m';

            console.log(`${colorCode}${timestamp} [${level}] [${this.name}] ${message}\x1b[0m`);
        }
    }

    debug(...args) { this._log('DEBUG', ...args); }
    info(...args) { this._log('INFO', ...args); }
    warn(...args) { this._log('WARN', ...args); }
    error(...args) { this._log('ERROR', ...args); }

    close() {
        this.logStream.end();
    }
}

const logger = new Logger('server');
logger.info('='  .repeat(60));
logger.info('Server Logger Initialized');
logger.info(`Log file: ${logger.logFile}`);
logger.info('='  .repeat(60));

// Initialize Express app
const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"]
    }
});

// Request logging middleware
app.use((req, res, next) => {
    logger.info(`${req.method} ${req.path}`, {
        query: req.query,
        body: req.method === 'POST' ? req.body : undefined,
        ip: req.ip
    });
    next();
});

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

// Configuration
const PORT = process.env.PORT || 3000;
const PYTHON_PATH = process.env.PYTHON_PATH || 'python';

// Active sessions storage
const activeSessions = new Map();

// Available models configuration
const AVAILABLE_MODELS = [
    {
        id: 'opt-30b',
        name: 'OPT-30B (Meta)',
        fullName: 'facebook/opt-30b',
        size: '30B parameters (~60GB FP16, ~30GB INT8)',
        minGpuMemory: '16GB',
        minRamMemory: '32GB',
        supportedTasks: ['inference'],
        quantizationSupport: ['8-bit', '4-bit']
    },
    {
        id: 'llama2-7b',
        name: 'LLaMA 2 7B',
        fullName: 'meta-llama/Llama-2-7b-hf',
        size: '7B parameters (~14GB FP16, ~7GB INT8)',
        minGpuMemory: '8GB',
        minRamMemory: '16GB',
        supportedTasks: ['inference', 'fine-tuning'],
        quantizationSupport: ['8-bit', '4-bit']
    },
    {
        id: 'llama2-13b',
        name: 'LLaMA 2 13B',
        fullName: 'meta-llama/Llama-2-13b-hf',
        size: '13B parameters (~26GB FP16, ~13GB INT8)',
        minGpuMemory: '16GB',
        minRamMemory: '32GB',
        supportedTasks: ['inference', 'fine-tuning'],
        quantizationSupport: ['8-bit', '4-bit']
    },
    {
        id: 'falcon-7b',
        name: 'Falcon 7B',
        fullName: 'tiiuae/falcon-7b',
        size: '7B parameters (~14GB FP16, ~7GB INT8)',
        minGpuMemory: '8GB',
        minRamMemory: '16GB',
        supportedTasks: ['inference'],
        quantizationSupport: ['8-bit', '4-bit']
    }
];

// ============================================================
// API Routes
// ============================================================

// Get available models
app.get('/api/models', (req, res) => {
    logger.info('Fetching available models list');
    res.json({
        success: true,
        models: AVAILABLE_MODELS
    });
    logger.debug('Returned models:', AVAILABLE_MODELS.map(m => m.id));
});

// Get model details
app.get('/api/models/:modelId', (req, res) => {
    const model = AVAILABLE_MODELS.find(m => m.id === req.params.modelId);
    if (model) {
        res.json({ success: true, model });
    } else {
        res.status(404).json({ success: false, error: 'Model not found' });
    }
});

// Get system status
app.get('/api/status', (req, res) => {
    res.json({
        success: true,
        status: {
            activeSessions: activeSessions.size,
            server: 'running',
            pythonPath: PYTHON_PATH,
            hfToken: process.env.HF_TOKEN ? 'configured' : 'not configured'
        }
    });
});

// Start inference session
app.post('/api/inference/start', (req, res) => {
    logger.info('='  .repeat(60));
    logger.info('NEW INFERENCE REQUEST');
    logger.info('='  .repeat(60));

    const {
        modelId,
        prompt,
        quantization = '8-bit',
        enableFp32CpuOffload = true,
        maxLength = 50,
        temperature = 0.7,
        topP = 0.9,
        gpuMemory = '14GiB',
        cpuMemory = '56GiB'
    } = req.body;

    logger.info('Request parameters:', {
        modelId,
        promptLength: prompt?.length,
        quantization,
        enableFp32CpuOffload,
        maxLength,
        temperature,
        topP,
        gpuMemory,
        cpuMemory
    });

    // Validate input
    if (!modelId || !prompt) {
        logger.warn('Validation failed: missing modelId or prompt');
        return res.status(400).json({
            success: false,
            error: 'modelId and prompt are required'
        });
    }

    const model = AVAILABLE_MODELS.find(m => m.id === modelId);
    if (!model) {
        logger.error(`Model not found: ${modelId}`);
        return res.status(404).json({
            success: false,
            error: 'Model not found'
        });
    }

    // Create session
    const sessionId = uuidv4();
    logger.info(`Created new session: ${sessionId}`);

    const session = {
        id: sessionId,
        modelId,
        modelName: model.fullName,
        prompt,
        config: {
            quantization,
            enableFp32CpuOffload,
            maxLength,
            temperature,
            topP,
            gpuMemory,
            cpuMemory
        },
        status: 'starting',
        startTime: Date.now(),
        output: '',
        metrics: {}
    };

    activeSessions.set(sessionId, session);
    logger.info(`Active sessions count: ${activeSessions.size}`);

    // Start Python inference process
    logger.info(`Starting Python inference process for session ${sessionId}`);
    startInferenceProcess(session);

    res.json({
        success: true,
        sessionId,
        message: 'Inference session started'
    });

    logger.info('Response sent to client');
    logger.info('='  .repeat(60));
});

// Get session status
app.get('/api/session/:sessionId', (req, res) => {
    const session = activeSessions.get(req.params.sessionId);
    if (session) {
        res.json({ success: true, session });
    } else {
        res.status(404).json({ success: false, error: 'Session not found' });
    }
});

// Stop session
app.post('/api/session/:sessionId/stop', (req, res) => {
    const session = activeSessions.get(req.params.sessionId);
    if (session && session.process) {
        session.process.kill();
        session.status = 'stopped';
        res.json({ success: true, message: 'Session stopped' });
    } else {
        res.status(404).json({ success: false, error: 'Session not found' });
    }
});

// ============================================================
// WebSocket Connection
// ============================================================

io.on('connection', (socket) => {
    logger.info(`WebSocket: Client connected - ${socket.id}`);

    socket.on('subscribe', (sessionId) => {
        socket.join(`session-${sessionId}`);
        logger.info(`WebSocket: Client ${socket.id} subscribed to session ${sessionId}`);
    });

    socket.on('disconnect', () => {
        logger.info(`WebSocket: Client disconnected - ${socket.id}`);
    });
});

// ============================================================
// Python Process Management
// ============================================================

function startInferenceProcess(session) {
    logger.info(`[${session.id}] Starting Python inference process`);

    // Use new backend structure
    const scriptPath = path.join(__dirname, '..', 'backend', 'inference_api.py');

    const args = [
        scriptPath,
        '--model', session.modelId,  // Use modelId instead of modelName
        '--prompt', session.prompt,
        '--quantization', session.config.quantization,
        '--max-length', session.config.maxLength.toString(),
        '--temperature', session.config.temperature.toString(),
        '--top-p', session.config.topP.toString(),
        '--gpu-memory', session.config.gpuMemory,
        '--cpu-memory', session.config.cpuMemory,
        '--session-id', session.id,
        '--offload-folder', './offload',
        '--log-level', process.env.LOG_LEVEL || 'INFO'
    ];

    if (session.config.enableFp32CpuOffload) {
        args.push('--enable-fp32-cpu-offload');
    }

    // Set environment variables
    const env = { ...process.env };
    if (process.env.HF_TOKEN) {
        env.HF_TOKEN = process.env.HF_TOKEN;
    }

    logger.info(`[${session.id}] Python command: ${PYTHON_PATH} ${args.join(' ')}`);
    logger.debug(`[${session.id}] Environment:`, {
        HF_TOKEN: env.HF_TOKEN ? 'SET' : 'NOT SET',
        LOG_LEVEL: env.LOG_LEVEL
    });

    const pythonProcess = spawn(PYTHON_PATH, args, {
        env,
        cwd: path.join(__dirname, '..')
    });

    session.process = pythonProcess;
    session.status = 'loading';
    logger.info(`[${session.id}] Python process spawned with PID ${pythonProcess.pid}`);

    // Emit initial status
    io.to(`session-${session.id}`).emit('status', {
        status: 'loading',
        message: 'Loading model...'
    });

    // Handle stdout (progress updates)
    pythonProcess.stdout.on('data', (data) => {
        const output = data.toString();
        logger.debug(`[${session.id}] STDOUT: ${output.trim()}`);

        // Parse JSON messages from Python
        const lines = output.split('\n').filter(line => line.trim());
        lines.forEach(line => {
            try {
                const message = JSON.parse(line);
                logger.debug(`[${session.id}] Parsed message:`, message);
                handlePythonMessage(session, message);
            } catch (e) {
                // Not JSON, treat as regular output
                logger.warn(`[${session.id}] Non-JSON output: ${line}`);
                session.output += output;
                io.to(`session-${session.id}`).emit('output', { text: output });
            }
        });
    });

    // Handle stderr (errors)
    pythonProcess.stderr.on('data', (data) => {
        const error = data.toString();
        logger.error(`[${session.id}] STDERR: ${error.trim()}`);

        io.to(`session-${session.id}`).emit('error', {
            error: error
        });
    });

    // Handle process exit
    pythonProcess.on('close', (code) => {
        logger.info(`[${session.id}] Python process exited with code ${code}`);

        session.status = code === 0 ? 'completed' : 'failed';
        session.endTime = Date.now();
        session.duration = session.endTime - session.startTime;

        logger.info(`[${session.id}] Session ${session.status.toUpperCase()} - Duration: ${session.duration}ms`);

        io.to(`session-${session.id}`).emit('complete', {
            status: session.status,
            duration: session.duration,
            metrics: session.metrics
        });

        // Clean up after 1 hour
        setTimeout(() => {
            logger.info(`[${session.id}] Cleaning up session from memory`);
            activeSessions.delete(session.id);
        }, 3600000);
    });
}

function handlePythonMessage(session, message) {
    const { type, data, timestamp } = message;
    logger.debug(`[${session.id}] Handling message type: ${type}`, data);

    switch (type) {
        case 'status':
            session.status = data.status;
            logger.info(`[${session.id}] Status update: ${data.status} - ${data.message}`);
            io.to(`session-${session.id}`).emit('status', data);
            break;

        case 'progress':
            logger.info(`[${session.id}] Progress: ${data.percent}% - ${data.message}`);
            io.to(`session-${session.id}`).emit('progress', data);
            break;

        case 'memory':
            session.metrics.memory = data;
            logger.debug(`[${session.id}] Memory update:`, {
                gpu: data.gpu?.allocated,
                cpu: data.cpu?.used
            });
            io.to(`session-${session.id}`).emit('memory', data);
            break;

        case 'device_map':
            session.metrics.deviceMap = data;
            logger.info(`[${session.id}] Device map received - ${Object.keys(data).length} entries`);
            io.to(`session-${session.id}`).emit('device_map', data);
            break;

        case 'generation_start':
            session.status = 'generating';
            logger.info(`[${session.id}] Generation started - input: ${data.input_length} tokens, max: ${data.max_length}`);
            io.to(`session-${session.id}`).emit('status', {
                status: 'generating',
                message: 'Generating text...'
            });
            break;

        case 'token':
            session.output += data.token;
            logger.debug(`[${session.id}] Token generated: ${data.token}`);
            io.to(`session-${session.id}`).emit('token', data);
            break;

        case 'result':
            session.output = data.text;
            session.metrics = { ...session.metrics, ...data.metrics };
            logger.info(`[${session.id}] Result received - ${data.text?.length} characters`);
            io.to(`session-${session.id}`).emit('result', data);
            break;

        case 'error':
            session.status = 'failed';
            session.error = data.error;
            logger.error(`[${session.id}] Error received: ${data.error}`);
            io.to(`session-${session.id}`).emit('error', data);
            break;

        case 'complete':
            logger.info(`[${session.id}] Inference complete - ${data.status}`);
            io.to(`session-${session.id}`).emit('complete', data);
            break;

        default:
            logger.warn(`[${session.id}] Unknown message type: ${type}`, data);
    }
}

// ============================================================
// Start Server
// ============================================================

server.listen(PORT, () => {
    console.log('='.repeat(60));
    console.log(`🚀 LLM Inference UI Server Running`);
    console.log('='.repeat(60));
    console.log(`📍 Server: http://localhost:${PORT}`);
    console.log(`🔌 WebSocket: ws://localhost:${PORT}`);
    console.log(`🐍 Python: ${PYTHON_PATH}`);
    console.log(`🔑 HF Token: ${process.env.HF_TOKEN ? '✅ Configured' : '❌ Not configured'}`);
    console.log('='.repeat(60));
    console.log('Available endpoints:');
    console.log('  GET  /api/models          - List available models');
    console.log('  GET  /api/status          - Get server status');
    console.log('  POST /api/inference/start - Start inference session');
    console.log('  GET  /api/session/:id     - Get session status');
    console.log('='.repeat(60));
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\n\nShutting down gracefully...');

    // Kill all active Python processes
    activeSessions.forEach((session) => {
        if (session.process) {
            session.process.kill();
        }
    });

    server.close(() => {
        console.log('Server closed');
        process.exit(0);
    });
});
