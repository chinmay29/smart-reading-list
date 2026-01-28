#!/bin/bash
# Smart Reading List - Easy Start/Stop Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
LOG_DIR="$SCRIPT_DIR/logs"
DATA_DIR="$HOME/.smart-reading-list"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Ensure log directory exists
mkdir -p "$LOG_DIR"

start_backend() {
    echo -e "${GREEN}Starting backend...${NC}"
    cd "$BACKEND_DIR"
    
    # Activate venv if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Start uvicorn in background
    nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$LOG_DIR/backend.log" 2>&1 &
    echo $! > "$LOG_DIR/backend.pid"
    echo -e "  Backend PID: $(cat "$LOG_DIR/backend.pid")"
    echo -e "  Logs: $LOG_DIR/backend.log"
}

start_frontend() {
    echo -e "${GREEN}Starting frontend...${NC}"
    cd "$FRONTEND_DIR"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}  Installing dependencies...${NC}"
        npm install
    fi
    
    # Start dev server in background
    nohup npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
    echo $! > "$LOG_DIR/frontend.pid"
    echo -e "  Frontend PID: $(cat "$LOG_DIR/frontend.pid")"
    echo -e "  Logs: $LOG_DIR/frontend.log"
}

stop_service() {
    local name=$1
    local pid_file="$LOG_DIR/$name.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}Stopping $name (PID: $pid)...${NC}"
            kill "$pid"
            rm "$pid_file"
        else
            echo -e "${YELLOW}$name not running (stale PID file)${NC}"
            rm "$pid_file"
        fi
    else
        echo -e "${YELLOW}$name not running (no PID file)${NC}"
    fi
}

status() {
    echo -e "${GREEN}=== Smart Reading List Status ===${NC}"
    echo ""
    
    # Check backend
    if [ -f "$LOG_DIR/backend.pid" ] && kill -0 "$(cat "$LOG_DIR/backend.pid")" 2>/dev/null; then
        echo -e "Backend:  ${GREEN}Running${NC} (PID: $(cat "$LOG_DIR/backend.pid"))"
    else
        echo -e "Backend:  ${RED}Stopped${NC}"
    fi
    
    # Check frontend
    if [ -f "$LOG_DIR/frontend.pid" ] && kill -0 "$(cat "$LOG_DIR/frontend.pid")" 2>/dev/null; then
        echo -e "Frontend: ${GREEN}Running${NC} (PID: $(cat "$LOG_DIR/frontend.pid"))"
    else
        echo -e "Frontend: ${RED}Stopped${NC}"
    fi
    
    echo ""
    echo -e "Data directory: $DATA_DIR"
    if [ -d "$DATA_DIR" ]; then
        echo -e "  SQLite:   $(ls -lh "$DATA_DIR/reading_list.db" 2>/dev/null | awk '{print $5}' || echo 'not found')"
        echo -e "  ChromaDB: $(du -sh "$DATA_DIR/chroma" 2>/dev/null | awk '{print $1}' || echo 'not found')"
    fi
    
    echo ""
    echo "URLs:"
    echo "  App:     http://localhost:5173"
    echo "  API:     http://localhost:8000"
    echo "  Health:  http://localhost:8000/api/health"
}

logs() {
    local service=$1
    if [ -z "$service" ]; then
        echo "Usage: $0 logs [backend|frontend]"
        exit 1
    fi
    
    local log_file="$LOG_DIR/$service.log"
    if [ -f "$log_file" ]; then
        tail -f "$log_file"
    else
        echo "No log file found for $service"
    fi
}

case "$1" in
    start)
        start_backend
        sleep 2
        start_frontend
        sleep 2
        echo ""
        status
        ;;
    stop)
        stop_service "backend"
        stop_service "frontend"
        ;;
    restart)
        stop_service "backend"
        stop_service "frontend"
        sleep 2
        start_backend
        sleep 2
        start_frontend
        sleep 2
        status
        ;;
    status)
        status
        ;;
    logs)
        logs "$2"
        ;;
    sync)
        echo -e "${GREEN}Syncing data...${NC}"
        curl -s -X POST http://localhost:8000/api/sync | python3 -m json.tool
        ;;
    *)
        echo "Smart Reading List Manager"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|sync}"
        echo ""
        echo "Commands:"
        echo "  start   - Start backend and frontend in background"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        echo "  status  - Show service status"
        echo "  logs    - Tail logs (e.g., $0 logs backend)"
        echo "  sync    - Manually sync ChromaDB with SQLite"
        exit 1
        ;;
esac
