# Auto Description Retrieval

This project takes a URL containing a listing a vehicle (Vehicle Detail Page (VDPs)) and retrieves and isolates vehicle descriptions using HTML scraping and LLM-based text extraction.

---

## Supported Websites

Currently, the project is configured to extract vehicle descriptions from the following websites:

    - greghublerford.com
    - sftoyota.com
    - bergeronchryslerjeep.com

Each site has predefined search paths in the code to locate vehicle descriptions.

---

## Run Modes

This project can be run in several Dockerized contexts depending on your use case.

---


### **1. API Mode**

Launches a FastAPI server inside Docker.  
The API will be available at:

- **Base URL:** [http://localhost:8000/](http://localhost:8000/)
- **Interactive Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)

**Command:**
```bash
docker compose -f docker-compose.api.yml up --build
```

This will build the image (if needed), launch the API container, and start the web server automatically.

---

### **2. CLI Mode**

Run commands inside an ephemeral (temporary) container that will delete itself after the job is complete — perfect for quick testing or batch jobs.

#### Using Makefile (recommended)

```bash
# Run a scrape_description command with a URL
make scrape_description URL=<VDP_URL>
```

#### Full equivalent Docker command

```bash
docker compose -f docker-compose.cli.yml run --rm auto_description_cli scrape_description <VDP_URL>
```

#### Rebuild CLI image manually (only needed if dependencies change)
```bash
docker compose -f docker-compose.cli.yml build --no-cache
```

---

### **3. Dev Container (VS Code) Mode**

Used for developing and debugging directly inside Docker through VS Code.  
Relies on `devcontainer.json` and `docker-compose.api-dev.yml`.

- **Launch API:**  
  ```bash
  docker compose -f docker-compose.api-dev.yml up
  ```

- **Base URL:** [http://localhost:8001/](http://localhost:8001/)
- **Swagger UI:** [http://localhost:8001/docs](http://localhost:8001/docs)

Alternatively, you can open the repo in VS Code → “Reopen in Container” and run `main.py` or `uvicorn` directly inside the dev environment.
---

## Actions

| Action | Description |
|--------|--------------|
| `scrape_description` | _(Retrieve the HTML at the provided page and extract the Vehicle Description Paragrah)_ |
| `determine_vpd_search_paths` | _(Retrieve the HTML at the provided page and attempt to determine the tags, class names, etc. that contain the dealer description)_ |
| `demo_scrape_description` | _(Run multiple `scrape_description` queries in a row from urls in `tests/demo_urls.json` with full debug output)_ |

Example usage:

### <u>CLI</u>
- With Makefile
    ```bash
    make scrape_description URL=https://www.greghublerford.com/inventory/used-2010-subaru-outback-3-6r-awd-4d-sport-utility-4s4brejc2a2319275/
    ```
OR
- With docker compose
    ```bash
    docker compose -f docker-compose.cli.yml run --rm auto_description_cli scrape_description https://www.greghublerford.com/inventory/used-2010-subaru-outback-3-6r-awd-4d-sport-utility-4s4brejc2a2319275/
    ```

### <u>API</u>
- **Endpoint:**  
`POST /scrape_description`

- **Example cURL request:**
    ```bash
    curl -X POST http://localhost:8000/scrape_description \
        -H "Content-Type: application/json" \
        -d '{
            "vdp_url": "https://www.greghublerford.com/inventory/used-2010-subaru-outback-3-6r-awd-4d-sport-utility-4s4brejc2a2319275/"
            }'
    ```

- **Expected JSON response:**
    ```json
    {
        "description": "Take on any road with confidence in this 2010 Subaru Outback 3.6R AWD, a versatile crossover SUV known for its legendary all-wheel-drive capability and dependability.",
        "token_count": 108
    }
    ```


### <u>Python Direct</u>
```bash
python main.py scrape_description https://www.greghublerford.com/inventory/used-2010-subaru-outback-3-6r-awd-4d-sport-utility-4s4brejc2a2319275/
```

---

## LLM Configuration

This project uses **LangChain** as a universal interface for interacting with multiple Large Language Model (LLM) APIs.  
You can dynamically switch between **Anthropic (Claude)**, **OpenAI (GPT)**, and **Mistral** models simply by updating the `.env` configuration.

---

### **Supported Providers**

| Provider | Example Model |
|-----------|----------------|-------------|
| `anthropic` | `claude-sonnet-4-5-20250929` |
| `openai` | `gpt-4o-mini` |
| `mistral` | `mistral-large-latest` |

---

### **Selecting a Provider**

Set your preferred provider and model in the `.env` file:

```bash
# Choose which company's API to utilize
# One of: "anthropic", "openai", "mistral"
LLM_PROVIDER=anthropic
```

The system will automatically route requests through the corresponding LangChain wrapper.

---

### **Provider API Credentials**

Each provider requires its own API key and model ID.  
Add these values to your `.env` file (examples below):

```bash
# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_MODEL_ID=claude-sonnet-4-5-20250929

# OpenAI (GPT)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL_ID=gpt-4o-mini

# Mistral
MISTRAL_API_KEY=<REPLACE_ME>
MISTRAL_MODEL_ID=mistral-large-latest
```

> Use a local `.env` file (ignored by `.gitignore`) or a secure secret manager.

---

### **Additional Configuration**

```bash
PRINT_DEBUG_COMMENTS=true 
```
> Displays various debug comments when functions are run.

---

## Running All Tests

This project uses **pytest** as the testing framework. The testing pathing is configured in `pytest.ini`

To run all tests, simply navigate to the project root and execute:

```bash
pytest tests/
```

Some tests involve LLM clients (Anthropic, OpenAI, Mistral).

- If an API key for a specific LLM provider is not set in your environment variables, tests for that provider will be skipped automatically.

- This allows tests to run for other components without requiring access to all LLM services.

---