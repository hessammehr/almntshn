.PHONY: serve serve-ts dev clean reset-db help ip

# Tailscale CLI path (macOS app location)
TAILSCALE := /Applications/Tailscale.app/Contents/MacOS/Tailscale

# Get Tailscale hostname
TS_HOST := $(shell $(TAILSCALE) status --json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['Self']['DNSName'].rstrip('.'))" 2>/dev/null || echo "your-hostname.ts.net")

# Default target
help:
	@echo "almntshn - Home food inventory tracker"
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  serve     Start server (HTTP on localhost:8000)"
	@echo "  serve-ts  Start server + Tailscale HTTPS (for phone camera access)"
	@echo "  dev       Alias for serve"
	@echo "  clean     Remove Python cache files"
	@echo "  reset-db  Delete database and start fresh"
	@echo "  ip        Show access URLs"

# Start development server with auto-reload (HTTP only)
serve:
	cd backend && uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Start server with Tailscale HTTPS proxy (required for camera on phones)
serve-ts:
	@echo "Starting server with Tailscale HTTPS..."
	@echo ""
	@# First, clear any existing tailscale serve config
	@$(TAILSCALE) serve reset 2>/dev/null || true
	@# Configure tailscale to proxy port 8000 with HTTPS
	@$(TAILSCALE) serve --bg --https=443 http://127.0.0.1:8000
	@echo ""
	@echo "✓ Tailscale HTTPS proxy configured"
	@echo ""
	@echo "Access from your iPhone at:"
	@echo "  https://$(TS_HOST)"
	@echo ""
	@echo "Starting uvicorn (press Ctrl+C to stop)..."
	@echo ""
	@cd backend && uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload; \
		$(TAILSCALE) serve reset 2>/dev/null || true

# Alias for serve
dev: serve

# Show access URLs
ip:
	@echo "Local access:"
	@echo "  http://localhost:8000"
	@echo ""
	@echo "Tailscale access (run 'make serve-ts' for HTTPS):"
	@echo "  https://$(TS_HOST)"

# Clean Python cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Reset database (delete and recreate on next run)
reset-db:
	rm -f data/inventory.db
	@echo "Database deleted. Will be recreated on next server start."
