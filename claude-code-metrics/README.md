# Claude Code Metrics

Lightweight serverless solution to capture Claude Code token usage metrics and display daily per-user consumption in a
CloudWatch dashboard.

## Architecture

```
Claude Code (OTLP/HTTP JSON) → API Gateway HTTP API → Lambda → CloudWatch Metrics
                                                                      ↓
                                                            CloudWatch Dashboard
```

- **No VPC, no ECS, no ALB** — pure serverless, zero cost when idle
- Fits within **AWS Free Tier** for a single test user
- ~5 Terraform resources, easy to deploy and tear down

## Project Structure

```
claude-code-metrics/
├── terraform/                 # All Terraform-managed infrastructure
│   ├── main.tf                # Provider config, S3 backend
│   ├── variables.tf           # Input variables
│   ├── outputs.tf             # Endpoint URL, API key
│   ├── lambda.tf              # Lambda function + IAM role
│   ├── api_gateway.tf         # API Gateway HTTP API
│   ├── cloudwatch.tf          # CloudWatch Dashboard
│   └── lambda/
│       └── handler.py         # Lambda code (zipped and deployed by Terraform)
├── bootstrap/
│   └── bootstrap.sh           # One-time script to create S3 bucket for Terraform state
├── client/
│   └── settings.json          # Claude Code client config template
├── PLAN.md
├── TASK.md
└── README.md
```

**Why this layout:**

- **`terraform/`** — everything Terraform manages, split by AWS resource type (standard convention). `lambda/handler.py`
  lives here because Terraform needs to zip and deploy it.
- **`bootstrap/`** — runs **once before** `terraform init`. Terraform can't create the S3 bucket that stores its own
  state (chicken-and-egg problem), so this simple AWS CLI script does it first.
- **`client/`** — end-user config distributed to developers' machines. Not infrastructure, not Terraform-managed.

## Prerequisites

- AWS CLI (`brew install awscli` on macOS)
- Terraform (`brew install terraform` on macOS)
- AWS credentials configured (`aws configure`)

## Deployment

```bash
# 1. Bootstrap — creates S3 bucket for Terraform state (run once, ever)
cd bootstrap
./bootstrap.sh

# 2. Update the S3 backend bucket name in terraform/main.tf:
#    Replace ACCOUNT_ID in the backend "s3" block with your AWS account ID
#    (the bootstrap script prints the bucket name for you)

# 3. Deploy infrastructure
cd ../terraform
terraform init
terraform apply

# 4. Tear down everything
terraform destroy
```

## Verifying the Bootstrap

```bash
# Check if the state bucket exists
aws s3api head-bucket --bucket claude-code-metrics-tfstate

# List objects in the bucket (empty until first terraform apply)
aws s3 ls s3://claude-code-metrics-tfstate/

# Check versioning is enabled
aws s3api get-bucket-versioning --bucket claude-code-metrics-tfstate
```

## Client Setup

Copy `client/settings.json` to `~/.claude/settings.json`, replacing the placeholder values with the endpoint URL and API
key from `terraform output`.

## Cost

| Scale       | Monthly Cost                            |
|-------------|-----------------------------------------|
| 1 test user | ~$0 (Free Tier)                         |
| 100 users   | ~$65 (mainly CloudWatch custom metrics) |

## Design Decisions

- **No DynamoDB lock table** — this repo is used by a single person, so concurrent Terraform runs aren't a concern. For
  team use, add `dynamodb_table` to the S3 backend config.
- **CloudWatch custom metrics via PutMetricData** — simplest approach with native dashboard support. At 100+ users,
  switching to CloudWatch Logs + Insights queries reduces cost to ~$3-5/month.
- **Rejected
  the [reference implementation](https://github.com/aws-solutions-library-samples/guidance-for-claude-code-with-amazon-bedrock/blob/main/assets/docs/MONITORING.md)
  ** — it uses ECS Fargate + ADOT Collector + ALB + VPC, which is over-engineered for daily token tracking and doesn't
  fit within Free Tier.
