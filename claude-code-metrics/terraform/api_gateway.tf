# This Terraform provisions an AWS API Gateway REST API endpoint that accepts
# POST requests at /v1/metrics and forwards them to a Lambda function.

# --- REST API ---

# Top-level API Gateway REST API container.
# All resources, methods, and integrations are defined under this API.
resource "aws_api_gateway_rest_api" "metrics" {
  name = "${var.project_name}-api"
}

# --- Path: /v1/metrics ---

# Creates the "/v1" path segment under the API root.
# Provides URL versioning so future breaking changes can use /v2, /v3, etc.
resource "aws_api_gateway_resource" "v1" {
  rest_api_id = aws_api_gateway_rest_api.metrics.id
  parent_id   = aws_api_gateway_rest_api.metrics.root_resource_id
  path_part   = "v1"
}

# Creates the "/v1/metrics" path segment.
# This is the endpoint that receives OTLP metric payloads from clients.
resource "aws_api_gateway_resource" "metrics" {
  rest_api_id = aws_api_gateway_rest_api.metrics.id
  parent_id   = aws_api_gateway_resource.v1.id
  path_part   = "metrics"
}

# --- POST /v1/metrics → Lambda ---

# Defines the POST method on /v1/metrics.
# Open access with no authorization — suitable for an initial simplified version.
resource "aws_api_gateway_method" "post_metrics" {
  rest_api_id   = aws_api_gateway_rest_api.metrics.id
  resource_id   = aws_api_gateway_resource.metrics.id
  http_method   = "POST"
  authorization = "NONE"
}

# Connects the POST method to the Lambda function using AWS_PROXY integration.
# AWS_PROXY passes the full HTTP request (headers, body, query params) to the
# Lambda and returns its response directly to the caller.
resource "aws_api_gateway_integration" "lambda" {
  rest_api_id             = aws_api_gateway_rest_api.metrics.id
  resource_id             = aws_api_gateway_resource.metrics.id
  http_method             = aws_api_gateway_method.post_metrics.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.metrics_handler.invoke_arn
}

# --- Deployment & Stage ---

# Packages the current API configuration into an immutable deployment snapshot.
resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.metrics.id

  depends_on = [aws_api_gateway_integration.lambda]

  # Forces a new deployment whenever any of the referenced
  # resources change, ensuring the live API stays in sync with Terraform state.
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.v1.id,
      aws_api_gateway_resource.metrics.id,
      aws_api_gateway_method.post_metrics.id,
      aws_api_gateway_integration.lambda.id,
    ]))
  }

  lifecycle {
    # avoids downtime during redeployments.
    create_before_destroy = true
  }
}

# Points the "prod" stage at the current deployment.
# The stage provides the public invoke URL (used in the api_endpoint output)
# and is the target for the usage plan below.
resource "aws_api_gateway_stage" "prod" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.metrics.id
  stage_name    = "prod"
}

# --- Lambda Permission ---

# Grants API Gateway permission to invoke the Lambda function.
# Without this resource-based policy, API Gateway calls would be denied by IAM
# even though the integration is configured. The wildcard source_arn covers
# all methods and resources under this API.
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.metrics_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.metrics.execution_arn}/*/*"
}
