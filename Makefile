# --------------------------------------------------------------------
# This Makefile orchestrates building and running the CLI Docker container.
# --------------------------------------------------------------------

# Helper target: ensure the CLI image exists
# If the image 'auto_description_cli_image' does not exist, build it.
ensure_image:
	@if [ -z "$$(docker images -q auto_description_cli_image)" ]; then \
	    docker compose -f docker-compose.cli.yml build; \
	fi

# --------------------------------------------------------------------
# Generic CLI run target
# Runs a command inside the CLI container.
# $(ARGS) can be passed for additional commands.
# --------------------------------------------------------------------
cli: ensure_image
	@docker compose -f docker-compose.cli.yml run --rm auto_description_cli $(ARGS)

# --------------------------------------------------------------------
# Run the 'scrape_description' command with a provided URL
# Usage:
#   make scrape_description URL=<VDP_URL>
# --------------------------------------------------------------------
scrape_description: ensure_image
ifndef URL
	$(error URL is undefined. Usage: make scrape_description URL=<VDP_URL>)
endif
	@docker compose -f docker-compose.cli.yml run --rm auto_description_cli scrape_description $(URL)

# --------------------------------------------------------------------
# Run the 'demo_scrape_description' command with no arugments
# Usage:
#   make demo_scrape_description
# --------------------------------------------------------------------
demo_scrape_description: ensure_image
	@docker compose -f docker-compose.cli.yml run --rm auto_description_cli demo_scrape_description

# --------------------------------------------------------------------
# Run the 'determine_vpd_search_paths' command with a provided URL
# Usage:
#   make determine_vpd_search_paths URL=<VDP_URL>
# --------------------------------------------------------------------
determine_vpd_search_paths: ensure_image
ifndef URL
	$(error URL is undefined. Usage: make determine_vpd_search_paths URL=<VDP_URL>)
endif
	@docker compose -f docker-compose.cli.yml run --rm auto_description_cli determine_vpd_search_paths $(URL)

# --------------------------------------------------------------------
# Run all tests inside the CLI container
# This runs pytest for the tests/test_fetch_vdp_html.py file
# --------------------------------------------------------------------
test_all: ensure_image
	@docker compose -f docker-compose.cli.yml run --rm auto_description_cli pytest --rootdir=. --import-mode=importlib tests/test_fetch_vdp_html.py
