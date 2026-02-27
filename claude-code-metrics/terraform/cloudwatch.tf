# CloudWatch Dashboard showing daily usage metrics from agentic coding tools.
# Uses SEARCH expressions to dynamically discover all users without hardcoding.

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "AgenticToolMetrics"

  dashboard_body = jsonencode({
    widgets = [
      # Per-user token breakdown — bar chart with one bar per user × token type.
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 24
        height = 6
        properties = {
          title  = "Token Usage"
          view   = "bar"
          region = var.aws_region
          period = 86400
          metrics = [
            [{ expression = "SEARCH('{AgenticToolMetrics,ServiceName,User,TokenType} MetricName=\"TokenUsage\"', 'Sum', 86400)", id = "e1" }]
          ]
        }
      },
      # Per-user cost breakdown — bar chart with one bar per user.
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 24
        height = 6
        properties = {
          title  = "Cost Usage"
          view   = "bar"
          region = var.aws_region
          period = 86400
          metrics = [
            [{ expression = "SEARCH('{AgenticToolMetrics,ServiceName,User} MetricName=\"CostUsage\"', 'Sum', 86400)", id = "e2" }]
          ]
        }
      }
    ]
  })
}
