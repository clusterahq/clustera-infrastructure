.PHONY: help install init preview up refresh destroy clean select-dev select-testing select-staging select-prod

help:
	@echo "Clustera Infrastructure - Pulumi Commands"
	@echo ""
	@echo "Environments: development, testing, staging, prod"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install dependencies with uv"
	@echo "  make init             Initialize Pulumi stack"
	@echo ""
	@echo "Stack Selection:"
	@echo "  make select-dev       Select development stack"
	@echo "  make select-testing   Select testing stack"
	@echo "  make select-staging   Select staging stack"
	@echo "  make select-prod      Select production stack"
	@echo ""
	@echo "Deployment:"
	@echo "  make preview          Preview infrastructure changes"
	@echo "  make up               Deploy infrastructure"
	@echo "  make refresh          Refresh Pulumi state"
	@echo "  make destroy          Destroy infrastructure"
	@echo "  make outputs          Show stack outputs"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean            Remove virtual environment"

install:
	@echo "Installing dependencies with uv..."
	uv sync

init:
	@echo "Initializing Pulumi stack..."
	@echo "Please ensure you have:"
	@echo "  1. Created .env from .env.example"
	@echo "  2. Set up S3 bucket for state storage"
	@echo "  3. Configured stack YAML (Pulumi.<stack>.yaml)"
	@echo ""
	@echo "Available environments: development, testing, staging, prod"
	@read -p "Enter stack name: " stack; \
	pulumi login s3://clustera-pulumi-state && \
	pulumi stack init $$stack

select-dev:
	@echo "Selecting development stack..."
	uv run pulumi stack select development

select-testing:
	@echo "Selecting testing stack..."
	uv run pulumi stack select testing

select-staging:
	@echo "Selecting staging stack..."
	uv run pulumi stack select staging

select-prod:
	@echo "Selecting production stack..."
	uv run pulumi stack select prod

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
