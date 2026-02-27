import json
import logging
import base64
import boto3
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cloudwatch = boto3.client("cloudwatch")

NAMESPACE = "ClaudeCode/Metrics"
TOKEN_METRIC_NAME = "claude_code.token.usage"
COST_METRIC_NAME = "claude_code.cost.usage"


def handler(event, context):
    body = event.get("body", "")
    if event.get("isBase64Encoded", False):
        body = base64.b64decode(body).decode("utf-8")

    logger.info("Received event body: %s", body)

    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, TypeError):
        logger.error("Invalid JSON payload")
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON"})}

    metric_data = []

    for rm in payload.get("resourceMetrics", []):
        for sm in rm.get("scopeMetrics", []):
            for metric in sm.get("metrics", []):
                metric_name = metric.get("name")

                if metric_name == TOKEN_METRIC_NAME:
                    for dp in metric.get("sum", {}).get("dataPoints", []):
                        dp_attrs = dp.get("attributes", [])
                        token_type = _extract_attribute(dp_attrs, "type")
                        if not token_type:
                            continue

                        value = _extract_value(dp)
                        if value is None or value <= 0:
                            continue

                        metric_data.append(
                            {
                                "MetricName": "TokenUsage",
                                "Dimensions": [
                                    {"Name": "User", "Value": _extract_user(dp_attrs)},
                                    {"Name": "TokenType", "Value": token_type},
                                ],
                                "Value": value,
                                "Unit": "Count",
                                "Timestamp": _extract_timestamp(dp),
                            }
                        )

                elif metric_name == COST_METRIC_NAME:
                    for dp in metric.get("sum", {}).get("dataPoints", []):
                        dp_attrs = dp.get("attributes", [])

                        value = _extract_value(dp)
                        if value is None or value <= 0:
                            continue

                        metric_data.append(
                            {
                                "MetricName": "CostUsage",
                                "Dimensions": [
                                    {"Name": "User", "Value": _extract_user(dp_attrs)},
                                ],
                                "Value": value,
                                "Unit": "None",
                                "Timestamp": _extract_timestamp(dp),
                            }
                        )

    if metric_data:
        for md in metric_data:
            logger.info("Publishing metric: %s", json.dumps(md, default=str))
        for i in range(0, len(metric_data), 1000):
            cloudwatch.put_metric_data(
                Namespace=NAMESPACE, MetricData=metric_data[i: i + 1000]
            )
        logger.info("Published %d metric data points", len(metric_data))

    return {
        "statusCode": 200,
        "body": json.dumps({"accepted": len(metric_data)}),
    }


def _extract_value(data_point):
    if "asInt" in data_point:
        return int(data_point["asInt"])
    if "asDouble" in data_point:
        return data_point["asDouble"]
    return None


def _extract_user(attributes):
    for key in ("user.email", "user.account_uuid", "user.id"):
        value = _extract_attribute(attributes, key)
        if value:
            return value
    return "unknown"


def _extract_attribute(attributes, key):
    for attr in attributes:
        if attr.get("key") == key:
            v = attr.get("value", {})
            if "stringValue" in v:
                return v["stringValue"]
            if "intValue" in v:
                return str(v["intValue"])
            if "doubleValue" in v:
                return str(v["doubleValue"])
    return None


def _extract_timestamp(data_point):
    time_nano = data_point.get("timeUnixNano")
    if time_nano:
        return datetime.fromtimestamp(int(time_nano) / 1e9, tz=timezone.utc)
    return datetime.now(tz=timezone.utc)
