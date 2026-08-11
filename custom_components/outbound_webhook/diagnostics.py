from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, CONF_ENTITY_ID, CONF_ATTRIBUTE, CONF_WEBHOOK_URL, CONF_HTTP_METHOD

SENSITIVE_HEADERS = {"authorization", "x-api-key", "proxy-authorization"}


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry):
    data = entry.data

    diagnostics = {
        "version": "0.1.0",
        CONF_ENTITY_ID: data.get(CONF_ENTITY_ID),
        "trigger_type": data.get("trigger_type"),
        CONF_ATTRIBUTE: data.get(CONF_ATTRIBUTE),
        CONF_HTTP_METHOD: data.get(CONF_HTTP_METHOD),
        "rate_limit_mode": data.get("rate_limit_mode"),
        "rate_limit_interval": data.get("rate_limit_interval"),
    }

    if "headers" in data:
        diagnostics["headers"] = [
            {k: "REDACTED" if k.lower() in SENSITIVE_HEADERS else v for k, v in header.items()}
            for header in data["headers"]
        ]

    url = data.get(CONF_WEBHOOK_URL, "")
    if "?" in url:
        diagnostics[CONF_WEBHOOK_URL] = url.split("?")[0] + "?[REDACTED]"
    else:
        diagnostics[CONF_WEBHOOK_URL] = url

    return diagnostics
