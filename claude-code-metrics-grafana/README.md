# Claude Code Metrics — Prometheus & Grafana

Alternative to the AWS CloudWatch solution.

## Architecture

```
Claude Code (OTLP/HTTP JSON) → OTel Collector → Prometheus (scrape) → Grafana Dashboard
```

## Quick Start

```bash
# 1. Start the stack
docker compose up -d

# 2. Configure Claude Code (run once)
cd client
python3 install.py user@example.com

# 3. Open Grafana
open http://localhost:3000
# Navigate to Dashboards → Agentic Tool Metrics
```

## Services

| Service        | Port | Purpose                             |
|----------------|------|-------------------------------------|
| OTel Collector | 4318 | Receives OTLP/HTTP from Claude Code |
| Prometheus     | 9090 | Scrapes and stores metrics          |
| Grafana        | 3000 | Dashboard (no login required)       |

## Tear Down

```bash
docker compose down -v   # -v removes persistent volumes
```

## Client Setup

```bash
# Install
python3 client/install.py your-email@example.com

# Uninstall
python3 client/uninstall.py
```
