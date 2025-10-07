#!/usr/bin/env bash
set -euo pipefail

# entrypoint.sh
# MODE can be 'api' or 'cli'
# API_FORCE_INSTALL=true -> force a pip install at container start (fresh install requirement)
# API_AUTO_START=true -> auto-launch uvicorn (otherwise, container will wait for a manual start)

MODE="${MODE:-api}" # defaults to api
API_FORCE_INSTALL="${API_FORCE_INSTALL:-false}"
API_AUTO_START="${API_AUTO_START:-true}"
PIP_CACHE_DIR="${PIP_CACHE_DIR:-/root/.cache/pip}"

# Helper: do fresh install of pip packages if called (uses pip cache if mounted to speed up)
full_package_install() {
    echo "[entrypoint] Performing API fresh install (pip)."
    # --upgrade --force-reinstall ensures fresh copies (can be slower)
    pip install --upgrade pip
    pip install --upgrade --force-reinstall -r requirements.txt
}

# CLI mode: simply run the command passed to docker run (if any)
# If docker run has no command, we default to invoking python main.py --help
if [ "$MODE" = "cli" ]; then
    if [ $# -eq 0 ]; then
        echo "[entrypoint] MODE=cli; running default CLI: python main.py --help"
        python main.py --help
        exit 0
    else
        echo "[entrypoint] MODE=cli; executing: python main.py $*"
        exec python main.py "$@"
    fi
# API mode: Create API endpoint and launch Swagger UI to run it with
elif [ "$MODE" = "api" ]; then
    # Run fresh install on launch if API_FORCE_INSTALL is set to True
    if [ "${API_FORCE_INSTALL}" = "true" ]; then
        full_package_install
    else
        echo "[entrypoint] MODE=api; API_FORCE_INSTALL=false; using image-baked dependencies."
    fi

    if [ "${API_AUTO_START}" = "true" ]; then
        # Automatically launch the server by default
        echo "[entrypoint] MODE=api; starting FastAPI server on 0.0.0.0:8000"

        # Informative message for local users
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
