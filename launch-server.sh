#!/bin/bash
# HiveRecon Server Launcher - Starts server and opens browser

PROJECT_DIR="/home/vibhxr/hiverecon"
PORT=8000

cd "$PROJECT_DIR"
source venv/bin/activate

# Check if server is already running
if ss -tlnp 2>/dev/null | grep -q ":${PORT} "; then
    # Server already running, just open browser
    firefox "http://localhost:${PORT}/app" &
    exit 0
fi

# Start server in background
nohup uvicorn hiverecon.api.server:app --host 0.0.0.0 --port $PORT --log-level warning > /dev/null 2>&1 &
SERVER_PID=$!

# Wait for server to be ready (max 15 seconds)
for i in $(seq 1 30); do
    if curl -s "http://localhost:${PORT}/" > /dev/null 2>&1; then
        firefox "http://localhost:${PORT}/app" &
        exit 0
    fi
    sleep 0.5
done

# If we get here, server failed to start
echo "ERROR: HiveRecon server failed to start" >&2
kill $SERVER_PID 2>/dev/null
exit 1
