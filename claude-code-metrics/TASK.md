# Task

Implement AWS solution to capture Claude Code metrics that are pushed by the Claude Code client and display some single
DAU metric.
As a first step, interview me on any details of the task to understand what I really want.
As a second step, prepare a step-by-step plan and capture it in PLAN.md.
When the plan is created and explicitly approved, proceed to the step-by-step implementation.

# Requirements

- Scope - both AWS-side and Claude Code side changes
- Metrics scope - daily token usage per person
- Metrics should be displayed in the CloudWatch dashboard
- I want a possibility to deploy all the necessary AWS setup with a one button (e.g. via Terraform)
- I want a possibility to delete all the deployed resources
- Target solution should be production-ready in a company of ~100 people
- No security for metrics endpoint is needed for the first iteration
- Terraform state backend is not configured, the solution should include the bootstrap step
- AWS Free tier should be able to host all the needed infrastructure to test the solution with a single user

## Technology

- AWS
- Terraform (latest version as of 2026-02-01)

# Implementation

## Hints

- I have this implementation reference, analyze if it is adequate solution, and we should implement it, or some changes
  to be done to make it simpler | better - https://github.com/aws-solutions-library-samples/guidance-for-claude-code-with-amazon-bedrock/blob/main/assets/docs/MONITORING.md
- Claude Code client push mechanism is the built-in hooks/telemetry system
- Metrics will be pushed every 10 minutes by a single person