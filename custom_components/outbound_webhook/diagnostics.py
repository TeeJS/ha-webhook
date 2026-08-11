from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import (
    CONF_ENTITY_ID, CONF_ATTRIBUTE, CONF_WEBHOOK_URL, CONF_HTTP_METHOD,
    SUBENTRY_TYPE_RULE,
)

SENSITIVE_HEADERS = {"authorization", "x-api-key", "proxy-authorization"}


def _redact_rule(data: dict) -> dict:
    rule = {
        CONF_ENTITY_ID: data.get(CONF_ENTITY_ID),
        "trigger_type": data.get("trigger_type"),
        CONF_ATTRIBUTE: data.get(CONF_ATTRIBUTE),
        CONF_HTTP_METHOD: data.get(CONF_HTTP_METHOD),
        "rate_limit_mode": data.get("rate_limit_mode"),
        "rate_limit_interval": data.get("rate_limit_interval"),
    }

    if "headers" in data:
        headers = data["headers"]
        if isinstance(headers, dict):
            rule["headers"] = {
                k: "REDACTED" if k.lower() in SENSITIVE_HEADERS else v
                for k, v in headers.items()
            }

    url = data.get(CONF_WEBHOOK_URL, "")
    if "?" in url:
        rule[CONF_WEBHOOK_URL] = url.split("?")[0] + "?[REDACTED]"
    else:
        rule[CONF_WEBHOOK_URL] = url

    return rule


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry):
    return {
        "rule_count": len(entry.subentries),
        "rules": [
            _redact_rule(dict(subentry.data))
            for subentry in entry.subentries.values()
            if subentry.subentry_type == SUBENTRY_TYPE_RULE
        ],
    }
