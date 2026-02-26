# Plan: Claude Code Metrics

## Reference Implementation Analysis

The [reference implementation](https://github.com/aws-solutions-library-samples/guidance-for-claude-code-with-amazon-bedrock/blob/main/assets/docs/MONITORING.md) uses:
- ECS Fargate + ADOT Collector + ALB + VPC (heavy infrastructure)
- Lambda + DynamoDB for dashboard widgets
- CloudFormation (not Terraform)
- OIDC/JWT authentication
- Quota monitoring, analytics pipeline (Kinesis, S3, Athena)

**Verdict**: Way too complex for our scope. We only need daily token usage per person for ~100 users with no auth. A serverless approach is simpler, cheaper, and easier to maintain. The reference also won't fit within AWS Free Tier (ECS Fargate + ALB have no free tier).

## Proposed Architecture

```
Claude Code (OTLP/HTTP JSON) → API Gateway HTTP API → Lambda → CloudWatch Metrics
                                                                      ↓
                                                            CloudWatch Dashboard
```

**Why this is better for our case:**
- No VPC, no ECS, no ALB — dramatically less infrastructure
- Serverless = zero cost when idle, scales automatically
- ~5 Terraform resources vs ~20+ in the reference
- Easy to deploy and tear down
- Fits within AWS Free Tier for testing (see cost estimate below)

**CloudWatch custom metrics approach:**
- Lambda publishes metrics via `PutMetricData` — simple, native dashboard support, auto-aggregation
- Free Tier includes 10 custom metrics. For a single test user (2 metrics) this is free
- At 100 users (200 metrics) cost would be ~$60/month — at that point, switching to CloudWatch Logs + Insights queries is a straightforward optimization

**Expected load:**
- Each user pushes metrics every ~60 seconds (OTEL default export interval)
- ~100 users × 1 req/min × 8 hours/day × 22 workdays = ~1M requests/month

## Step-by-Step Plan

### Step 0: Local AWS Setup ✅
Ensure Terraform can access your AWS account:
1. Install AWS CLI (`brew install awscli` on macOS)
2. Run `aws configure` — enter your Access Key ID, Secret Access Key, and region (e.g. `us-east-1`)
3. Verify with `aws sts get-caller-identity` — should show your account ID
4. Install Terraform (`brew install terraform` on macOS)

This creates `~/.aws/credentials` which Terraform uses automatically (no extra config needed).

### Step 1: Terraform Project Structure ✅
Create the directory layout:
```
claude-code-metrics/
├── terraform/
│   ├── main.tf              # Provider config, backend
│   ├── variables.tf         # Input variables
│   ├── outputs.tf           # Endpoint URL output
│   ├── lambda.tf            # Lambda function + IAM
│   ├── api_gateway.tf       # API Gateway HTTP API
│   ├── cloudwatch.tf        # CloudWatch Dashboard
│   └── lambda/
│       └── handler.py       # Lambda function code
├── bootstrap/
│   └── bootstrap.sh         # S3 backend bootstrap script
├── client/
│   └── settings.json        # Claude Code client config template
├── PLAN.md
├── TASK.md
└── README.md
```

### Step 2: Bootstrap Script ✅
Create `bootstrap/bootstrap.sh` to:
- Create S3 bucket for Terraform state (with versioning)
- Create DynamoDB table for state locking
- Output backend config for `main.tf`

### Step 3: Terraform — Lambda Function ✅
**`lambda/handler.py`**:
- Receives OTLP JSON metrics via API Gateway
- Parses `resourceMetrics` → extracts `claude_code.token.usage` (or `claude_code.tokens.*`) metrics
- Extracts user identity from resource attributes (`user.email` or OTEL resource attributes)
- Publishes to CloudWatch via `PutMetricData`:
  - Namespace: `ClaudeCode/Metrics`
  - MetricName: `TokenUsage`
  - Dimensions: `User` (email), `TokenType` (input/output)
  - Value: token count

**IAM Role**:
- `cloudwatch:PutMetricData`
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`

### Step 4: Terraform — API Gateway REST API ✅
- Create HTTP API (v2) — simpler and cheaper than REST API
- Single `POST /v1/metrics` route → Lambda integration
- API key authentication — auto-generate a key in Terraform, attach usage plan
- Output the endpoint URL and API key

### Step 5: Terraform — CloudWatch Dashboard ✅
Dashboard named `ClaudeCodeMetrics` with metric widgets:
1. **DAU** — unique users per day (number widget, based on `TokenUsage` metric unique `User` dimension count)
2. **Daily Token Usage by User** — bar/table showing per-user daily token consumption
3. **Total Daily Tokens** — line graph of aggregate input + output tokens over time

### Step 6: Claude Code Client Configuration
Create `client/settings.json` template:
```json
{
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "http/json",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "<API_GATEWAY_ENDPOINT>",
    "OTEL_EXPORTER_OTLP_HEADERS": "x-api-key=<API_KEY>"
  }
}
```
Users copy this to `~/.claude/settings.json` (or admins distribute via managed settings).

### Step 7: README Documentation
- Prerequisites (AWS CLI, Terraform)
- Bootstrap steps
- Deploy / destroy commands
- Client setup instructions
- Dashboard access

## Implementation Order
1. Step 1 (project structure)
2. Step 2 (bootstrap)
3. Step 3 + Step 4 (Lambda + API Gateway — tightly coupled)
4. Step 5 (dashboard)
5. Step 6 + Step 7 (client config + docs)

## Cost Estimate (~100 users)

**Single test user — within AWS Free Tier (first 12 months):**
- API Gateway HTTP API: 1M requests/month free → 1 user ≈ 14K requests/month ✓
- Lambda: 1M requests + 400K GB-sec free → well within ✓
- CloudWatch: 10 custom metrics free → 1 user = 2 metrics ✓
- CloudWatch Dashboard: 3 dashboards free → we need 1 ✓
- S3 (Terraform state): 5GB free → our state file ~few KB ✓
- DynamoDB (state lock): 25GB free → 1 row ✓
- **Total: ~$0/month**

**At 100 users:** ~$65/month (mainly CloudWatch custom metrics at $0.30 × 200)
- To optimize: switch to CloudWatch Logs + Insights queries (~$3-5/month)

vs. Reference implementation: ~$30-50/month (ECS Fargate + ALB — no free tier for those)
