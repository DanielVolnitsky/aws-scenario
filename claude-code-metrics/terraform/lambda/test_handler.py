import json
import base64
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import handler


def _make_event(payload, base64_encode=False):
    body = json.dumps(payload)
    if base64_encode:
        body = base64.b64encode(body.encode("utf-8")).decode("utf-8")
    return {"body": body, "isBase64Encoded": base64_encode}


def _make_otlp_payload(user_attr_key="user.email",
                       user_attr_value="alice@example.com",
                       token_type="input",
                       value_key="asInt",
                       value=150,
                       time_unix_nano="1700000000000000000"):
    dp_attrs = [{"key": "type", "value": {"stringValue": token_type}}]
    if user_attr_key:
        dp_attrs.append({"key": user_attr_key, "value": {"stringValue": user_attr_value}})

    dp = {
        "attributes": dp_attrs,
        value_key: value,
    }
    if time_unix_nano is not None:
        dp["timeUnixNano"] = time_unix_nano

    return {
        "resourceMetrics": [
            {
                "resource": {"attributes": []},
                "scopeMetrics": [
                    {
                        "metrics": [
                            {
                                "name": "claude_code.token.usage",
                                "sum": {"dataPoints": [dp]},
                            }
                        ]
                    }
                ],
            }
        ]
    }


# @patch.object(handler, "cloudwatch") replaces the cloudwatch boto3 client (defined at module level in handler.py) with a MagicMock for the duration of  █
#   each test. This prevents real AWS API calls and lets you assert on mock_cw.put_metric_data.assert_called_once() etc. The mock is passed as the mock_cw  █
#   parameter to each test method
@patch.object(handler, "cloudwatch")
class TestHandler:
    def test_valid_metric(self, mock_cw):
        common_dp_attrs = [
            {"key": "user.id", "value": {"stringValue": "eda185f0a30fdf73d4b9e74165fe5a6a73020763bb624e0f47cb4832d5e670d3"}},
            {"key": "session.id", "value": {"stringValue": "e0c439d5-7164-41b6-8ec2-6136b74164b1"}},
            {"key": "organization.id", "value": {"stringValue": "6ce36d68-e988-41a8-9f73-9c843796fa0d"}},
            {"key": "user.email", "value": {"stringValue": "user@gmail.com"}},
            {"key": "user.account_uuid", "value": {"stringValue": "adbb6321-5476-430e-a0e2-e52a8fc4180f"}},
            {"key": "terminal.type", "value": {"stringValue": "pycharm"}},
            {"key": "model", "value": {"stringValue": "claude-haiku-4-5-20251001"}},
        ]
        payload = {
            "resourceMetrics": [{
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "claude-code"}},
                        {"key": "service.version", "value": {"stringValue": "2.1.34"}},
                    ],
                },
                "scopeMetrics": [{
                    "metrics": [
                        {
                            "name": "claude_code.cost.usage",
                            "sum": {"dataPoints": [{
                                "attributes": common_dp_attrs,
                                "asDouble": 0.000407,
                                "timeUnixNano": "1772186899885000000",
                            }]},
                        },
                        {
                            "name": "claude_code.token.usage",
                            "sum": {"dataPoints": [
                                {"attributes": common_dp_attrs + [{"key": "type", "value": {"stringValue": "input"}}],
                                 "asDouble": 287, "timeUnixNano": "1772186899885000000"},
                                {"attributes": common_dp_attrs + [{"key": "type", "value": {"stringValue": "output"}}],
                                 "asDouble": 24, "timeUnixNano": "1772186899885000000"},
                                {"attributes": common_dp_attrs + [{"key": "type", "value": {"stringValue": "cacheRead"}}],
                                 "asDouble": 0, "timeUnixNano": "1772186899885000000"},
                                {"attributes": common_dp_attrs + [{"key": "type", "value": {"stringValue": "cacheCreation"}}],
                                 "asDouble": 0, "timeUnixNano": "1772186899885000000"},
                            ]},
                        },
                    ],
                }],
            }]
        }
        event = _make_event(payload)
        resp = handler.handler(event, None)

        assert resp["statusCode"] == 200
        assert json.loads(resp["body"])["accepted"] == 3

        expected_ts = datetime.fromtimestamp(1772186899885000000 / 1e9, tz=timezone.utc)
        mock_cw.put_metric_data.assert_called_once_with(
            Namespace="AgenticToolMetrics",
            MetricData=[
                {
                    "MetricName": "CostUsage",
                    "Dimensions": [
                        {"Name": "ServiceName", "Value": "claude-code"},
                        {"Name": "User", "Value": "user@gmail.com"},
                    ],
                    "Value": 0.000407,
                    "Unit": "None",
                    "Timestamp": expected_ts,
                },
                {
                    "MetricName": "TokenUsage",
                    "Dimensions": [
                        {"Name": "ServiceName", "Value": "claude-code"},
                        {"Name": "User", "Value": "user@gmail.com"},
                        {"Name": "TokenType", "Value": "input"},
                    ],
                    "Value": 287,
                    "Unit": "Count",
                    "Timestamp": expected_ts,
                },
                {
                    "MetricName": "TokenUsage",
                    "Dimensions": [
                        {"Name": "ServiceName", "Value": "claude-code"},
                        {"Name": "User", "Value": "user@gmail.com"},
                        {"Name": "TokenType", "Value": "output"},
                    ],
                    "Value": 24,
                    "Unit": "Count",
                    "Timestamp": expected_ts,
                },
            ],
        )

    def test_base64_encoded_body(self, mock_cw):
        event = _make_event(_make_otlp_payload(), base64_encode=True)
        resp = handler.handler(event, None)

        assert resp["statusCode"] == 200
        assert json.loads(resp["body"])["accepted"] == 1
        mock_cw.put_metric_data.assert_called_once()

    def test_invalid_json_returns_400(self, mock_cw):
        event = {"body": "not json", "isBase64Encoded": False}
        resp = handler.handler(event, None)

        assert resp["statusCode"] == 400
        mock_cw.put_metric_data.assert_not_called()

    def test_ignores_non_token_metric(self, mock_cw):
        payload = _make_otlp_payload()
        payload["resourceMetrics"][0]["scopeMetrics"][0]["metrics"][0]["name"] = "other.metric"
        event = _make_event(payload)
        resp = handler.handler(event, None)

        assert json.loads(resp["body"])["accepted"] == 0
        mock_cw.put_metric_data.assert_not_called()

    def test_skips_zero_value(self, mock_cw):
        event = _make_event(_make_otlp_payload(value=0))
        resp = handler.handler(event, None)

        assert json.loads(resp["body"])["accepted"] == 0
        mock_cw.put_metric_data.assert_not_called()

    def test_skips_negative_value(self, mock_cw):
        event = _make_event(_make_otlp_payload(value=-5))
        resp = handler.handler(event, None)

        assert json.loads(resp["body"])["accepted"] == 0
        mock_cw.put_metric_data.assert_not_called()

    def test_as_double_value(self, mock_cw):
        event = _make_event(_make_otlp_payload(value_key="asDouble", value=42.5))
        resp = handler.handler(event, None)

        assert json.loads(resp["body"])["accepted"] == 1
        md = mock_cw.put_metric_data.call_args[1]["MetricData"][0]
        assert md["Value"] == 42.5

    def test_missing_type_attribute_skips_datapoint(self, mock_cw):
        payload = _make_otlp_payload()
        payload["resourceMetrics"][0]["scopeMetrics"][0]["metrics"][0]["sum"]["dataPoints"][0]["attributes"] = []
        event = _make_event(payload)
        resp = handler.handler(event, None)

        assert json.loads(resp["body"])["accepted"] == 0
        mock_cw.put_metric_data.assert_not_called()

    def test_user_fallback_to_account_uuid(self, mock_cw):
        event = _make_event(_make_otlp_payload(user_attr_key="user.account_uuid", user_attr_value="uuid-123"))
        resp = handler.handler(event, None)

        dims = {d["Name"]: d["Value"] for d in mock_cw.put_metric_data.call_args[1]["MetricData"][0]["Dimensions"]}
        assert dims["User"] == "uuid-123"

    def test_user_fallback_to_unknown(self, mock_cw):
        event = _make_event(_make_otlp_payload(user_attr_key=None))
        resp = handler.handler(event, None)

        dims = {d["Name"]: d["Value"] for d in mock_cw.put_metric_data.call_args[1]["MetricData"][0]["Dimensions"]}
        assert dims["User"] == "unknown"

    def test_timestamp_from_datapoint(self, mock_cw):
        event = _make_event(_make_otlp_payload(time_unix_nano="1700000000000000000"))
        handler.handler(event, None)

        md = mock_cw.put_metric_data.call_args[1]["MetricData"][0]
        assert md["Timestamp"] == datetime(2023, 11, 14, 22, 13, 20, tzinfo=timezone.utc)

    def test_timestamp_fallback_to_now(self, mock_cw):
        event = _make_event(_make_otlp_payload(time_unix_nano=None))
        handler.handler(event, None)

        md = mock_cw.put_metric_data.call_args[1]["MetricData"][0]
        assert md["Timestamp"].tzinfo == timezone.utc

    def test_batches_over_1000(self, mock_cw):
        payload = _make_otlp_payload()
        dp = payload["resourceMetrics"][0]["scopeMetrics"][0]["metrics"][0]["sum"]["dataPoints"][0]
        payload["resourceMetrics"][0]["scopeMetrics"][0]["metrics"][0]["sum"]["dataPoints"] = [dp] * 2500
        event = _make_event(payload)
        resp = handler.handler(event, None)

        assert json.loads(resp["body"])["accepted"] == 2500
        assert mock_cw.put_metric_data.call_count == 3

    def test_cache_read_tokens(self, mock_cw):
        event = _make_event(_make_otlp_payload(token_type="cacheRead", value=500))
        resp = handler.handler(event, None)

        assert json.loads(resp["body"])["accepted"] == 1
        md = mock_cw.put_metric_data.call_args[1]["MetricData"][0]
        assert md["Dimensions"] == [
            {"Name": "ServiceName", "Value": "unknown"},
            {"Name": "User", "Value": "alice@example.com"},
            {"Name": "TokenType", "Value": "cacheRead"},
        ]
        assert md["Value"] == 500

    def test_cache_creation_tokens(self, mock_cw):
        event = _make_event(_make_otlp_payload(token_type="cacheCreation", value=1024))
        resp = handler.handler(event, None)

        assert json.loads(resp["body"])["accepted"] == 1
        md = mock_cw.put_metric_data.call_args[1]["MetricData"][0]
        assert md["Dimensions"] == [
            {"Name": "ServiceName", "Value": "unknown"},
            {"Name": "User", "Value": "alice@example.com"},
            {"Name": "TokenType", "Value": "cacheCreation"},
        ]
        assert md["Value"] == 1024

    def test_empty_resource_metrics(self, mock_cw):
        event = _make_event({"resourceMetrics": []})
        resp = handler.handler(event, None)

        assert json.loads(resp["body"])["accepted"] == 0
        mock_cw.put_metric_data.assert_not_called()
