output "api_endpoint" {
  description = "OTLP endpoint URL (set as OTEL_EXPORTER_OTLP_ENDPOINT)"
  value       = aws_api_gateway_stage.prod.invoke_url
}
