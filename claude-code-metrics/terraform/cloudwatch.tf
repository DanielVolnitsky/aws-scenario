# CloudWatch Dashboard showing daily token usage metrics from Claude Code.
# Uses SEARCH expressions to dynamically discover all users without hardcoding.

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "ClaudeCodeMetrics"

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
          title   = "Daily Token Usage by User"
          view    = "bar"
          region  = var.aws_region
          period  = 86400
          metrics = [
            [{ expression = "SEARCH('{ClaudeCode/Metrics,User,TokenType} MetricName=\"TokenUsage\"', 'Sum', 86400)", id = "e1" }]
          ]
        }
      }
    ]
  })
}
