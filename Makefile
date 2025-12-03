.PHONY: help install init preview up refresh destroy clean

help:
	@echo "Clustera Infrastructure - Pulumi Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install     Install dependencies with uv"
	@echo "  make init        Initialize Pulumi stack"
	@echo ""
	@echo "Deployment:"
	@echo "  make preview     Preview infrastructure changes"
	@echo "  make up          Deploy infrastructure"
	@echo "  make refresh     Refresh Pulumi state"
	@echo "  make destroy     Destroy infrastructure"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean       Remove virtual environment"

install:
	@echo "Installing dependencies with uv..."
	uv sync

init:
	@echo "Initializing Pulumi stack..."
	@echo "Please ensure you have:"
	@echo "  1. Created .env from .env.example"
	@echo "  2. Set up S3 bucket for state storage"
	@echo "  3. Configured stack YAML (Pulumi.<stack>.yaml)"
	@read -p "Enter stack name (e.g., dev, prod): " stack; \
	pulumi login s3://clustera-pulumi-state && \
	pulumi stack init $$stack

preview:
	@echo "Previewing infrastructure changes..."
	uv run pulumi preview

up:
	@echo "Deploying infrastructure..."
	uv run pulumi up

refresh:
	@echo "Refreshing Pulumi state..."
	uv run pulumi refresh

destroy:
	@echo "Destroying infrastructure..."
	uv run pulumi destroy

outputs:
	@echo "Stack outputs:"
	uv run pulumi stack output

clean:
	@echo "Cleaning up virtual environment..."
	rm -rf .venv
	rm -f uv.lock
