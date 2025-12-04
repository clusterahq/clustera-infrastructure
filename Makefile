.PHONY: help install init preview up refresh destroy clean select-dev select-testing select-staging select-prod

help:
	@echo "Clustera Infrastructure - Pulumi Commands"
	@echo ""
	@echo "Environments: development, testing, staging, prod"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install dependencies with uv"
	@echo "  make init             Initialize Pulumi stack (handles R2 login + stack creation)"
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
	@if [ ! -f .env ]; then \
		echo "❌ Error: .env file not found!"; \
		echo "Please create .env from .env.example first:"; \
		echo "  cp .env.example .env"; \
		echo "  # Edit .env with your credentials"; \
		exit 1; \
	fi
	@echo ""
	@echo "Please ensure you have:"
	@echo "  1. ✅ .env file configured with R2 credentials"
	@echo "  2. 📦 R2 bucket created (will check automatically)"
	@echo "  3. 📝 Stack config YAML ready (Pulumi.<stack>.yaml)"
	@echo ""
	@echo "Available environments: development, testing, staging, prod"
	@read -p "Enter stack name: " stack; \
	echo ""; \
	echo "🔐 Logging in to R2 backend..."; \
	set -a; source .env; set +a; \
	if ! pulumi login "s3://clustera-infrastructure-pulumi?endpoint=2d45fcd3b3e68735a6ab3542fb494c19.r2.cloudflarestorage.com" 2>/dev/null; then \
		echo ""; \
		echo "⚠️  Login failed. Creating R2 bucket..."; \
		npx wrangler r2 bucket create clustera-infrastructure-pulumi || true; \
		echo ""; \
		echo "🔄 Retrying login..."; \
		pulumi login "s3://clustera-infrastructure-pulumi?endpoint=2d45fcd3b3e68735a6ab3542fb494c19.r2.cloudflarestorage.com"; \
	fi && \
	echo "✅ Logged in to R2 backend" && \
	echo "" && \
	echo "📚 Creating stack: $$stack" && \
	pulumi stack init $$stack && \
	echo "" && \
	echo "🎉 Stack '$$stack' initialized successfully!" && \
	echo "" && \
	echo "Next steps:" && \
	echo "  1. Copy stack config: cp Pulumi.$$stack.yaml.example Pulumi.$$stack.yaml" && \
	echo "  2. Edit config: vim Pulumi.$$stack.yaml" && \
	echo "  3. Configure stack: pulumi config set <key> <value>" && \
	echo "  4. Preview changes: make preview" && \
	echo "  5. Deploy: make up"

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
