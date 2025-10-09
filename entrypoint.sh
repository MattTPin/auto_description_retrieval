#!/usr/bin/env bash
set -euo pipefail

# entrypoint.sh
# MODE can be 'api' or 'cli'
# API_AUTO_START=true -> auto-launch uvicorn (otherwise, container will wait for a manual start)

MODE="${MODE:-api}" # defaults to api
API_AUTO_START="${API_AUTO_START:-true}"

# CLI mode: simply run the command passed to docker run (if any)
if [ "$MODE" = "cli" ]; then
    if [ $# -eq 0 ]; then
        python main.py --help
        exit 0
    else
        exec python main.py "$@"
    fi
# API mode: Create API endpoint and launch Swagger UI to run it with
elif [ "$MODE" = "api" ]; then
    if [ "${API_AUTO_START}" = "true" ]; then
        # Automatically launch the server by default
        echo "[entrypoint] MODE=api; starting FastAPI server on 0.0.0.0:8000"

        # Notice of where the site was launched
        echo "================================================================="
        echo "🚀 API is now running and accessible at: http://localhost:8000"
        echo "   Swagger docs available at: http://localhost:8000/docs"
        echo "================================================================="

        exec uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload
    else
        # Wait indefinitely so user can exec into container and start service manually.
        echo "[entrypoint] MODE=api; API_AUTO_START=false; container is idle for manual start."
        echo "[entrypoint] To start server manually, run:"
        echo "docker exec -it <container_name> uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload"
        tail -f /dev/null
    fi
else
    echo "[entrypoint] Unknown MODE: ${MODE}. Exiting."
    exit 2
fi
