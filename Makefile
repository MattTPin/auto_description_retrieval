cli:
	docker compose -f docker-compose.cli.yml run --rm auto_description_cli $(ARGS)

# Run scrape_description command with provided URL
scrape_description:
ifndef URL
	$(error URL is undefined. Usage: make scrape_description URL=<VDP_URL>)
endif
	docker compose -f docker-compose.cli.yml run --rm auto_description_cli scrape_description $(URL)

test_all:
	docker compose -f docker-compose.cli.yml run --rm auto_description_cli pytest --rootdir=. --import-mode=importlib tests/test_fetch_vdp_html.py
