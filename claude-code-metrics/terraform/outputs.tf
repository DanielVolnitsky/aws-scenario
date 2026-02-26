output "api_endpoint" {
  description = "OTLP endpoint URL (set as OTEL_EXPORTER_OTLP_ENDPOINT)"
  value       = aws_api_gateway_stage.prod.invoke_url
}

output "dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards/dashboard/${aws_cloudwatch_dashboard.main.dashboard_name}"
}
