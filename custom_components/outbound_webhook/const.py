"""Constants for the Outbound Webhook integration."""

DOMAIN = "outbound_webhook"

# Trigger types
TRIGGER_TYPE_STATE = "state"
TRIGGER_TYPE_ATTRIBUTE = "attribute"

# Rate limiting modes
RATE_LIMIT_MODE_NONE = "none"
RATE_LIMIT_MODE_THROTTLE = "throttle"
RATE_LIMIT_MODE_DEBOUNCE = "debounce"

# HTTP methods
HTTP_METHOD_POST = "POST"
HTTP_METHOD_GET = "GET"
HTTP_METHOD_PUT = "PUT"
HTTP_METHOD_DELETE = "DELETE"

# Config entry options keys
CONF_NAME = "name"
CONF_ENTITY_ID = "entity_id"
CONF_TRIGGER_TYPE = "trigger_type"
CONF_ATTRIBUTE = "attribute"
CONF_WEBHOOK_URL = "webhook_url"
CONF_HTTP_METHOD = "http_method"
CONF_HEADERS = "headers"
CONF_RATE_LIMIT_MODE = "rate_limit_mode"
CONF_RATE_LIMIT_INTERVAL = "rate_limit_interval"
CONF_ENABLED = "enabled"
