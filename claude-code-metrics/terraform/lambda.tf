# --- IAM Role for Lambda ---

# Trust policy that allows the AWS Lambda service to assume the execution role.
# Without this, Lambda cannot use the role and has no permissions to run.
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# IAM execution role for the Lambda function.
# Every Lambda needs a role to define what AWS services it can access.
resource "aws_iam_role" "lambda" {
  name               = "${var.project_name}-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

# Permissions policy granting the Lambda access to CloudWatch Metrics (to publish
# token usage data) and CloudWatch Logs (to write its own execution logs).
data "aws_iam_policy_document" "lambda_permissions" {
  statement {
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]
  }

  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }
}

# Attaches the permissions policy to the Lambda role so the permissions take effect.
resource "aws_iam_role_policy" "lambda" {
  name   = "${var.project_name}-lambda-policy"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.lambda_permissions.json
}

# --- Lambda Function ---

# Packages the Python handler into a .zip file required by the Lambda deployment.
# Terraform re-zips automatically when the source file changes.
data "archive_file" "lambda" {
  type        = "zip"
  source_file = "${path.module}/lambda/handler.py"
  output_path = "${path.module}/lambda/handler.zip"
}

# The Lambda function itself. Receives metrics via API Gateway, parses them,
# and publishes per-user token usage to CloudWatch using PutMetricData.
resource "aws_lambda_function" "metrics_handler" {
  function_name    = "${var.project_name}-handler"
  role             = aws_iam_role.lambda.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  timeout          = 10
  memory_size      = 128
}
