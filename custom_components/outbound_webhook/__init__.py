import logging
from homeassistant.core import HomeAssistant
from . import config_flow  # noqa: F401
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util
from .const import (
    DOMAIN, CONF_ENTITY_ID, CONF_TRIGGER_TYPE, CONF_ATTRIBUTE,
    TRIGGER_TYPE_ATTRIBUTE
)
from .rate_limiter import RateLimiter
from .webhook_sender import async_send_webhook

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    data = entry.data

    rate_limiter = RateLimiter(
        hass,
        data.get(CONF_RATE_LIMIT_MODE, "none"),
        data.get(CONF_RATE_LIMIT_INTERVAL, 0)
    )

    async def handle_state_change(event):
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        if not new_state:
            return

        if data[CONF_TRIGGER_TYPE] == TRIGGER_TYPE_ATTRIBUTE:
            attr = data[CONF_ATTRIBUTE]
            old_val = old_state.attributes.get(attr) if old_state else None
            new_val = new_state.attributes.get(attr)
            if old_val == new_val:
                return

            payload = {
                "entity_id": new_state.entity_id,
                "state": new_state.state,
                "old_state": old_state.state if old_state else None,
                "new_state": new_state.state,
                "attribute": attr,
                "old_value": old_val,
                "new_value": new_val,
                "timestamp": dt_util.utcnow().isoformat()
            }
        else:
            if old_state and old_state.state == new_state.state:
                return

            payload = {
                "entity_id": new_state.entity_id,
                "old_state": old_state.state if old_state else None,
                "new_state": new_state.state,
                "timestamp": dt_util.utcnow().isoformat()
            }

        async def send():
            await async_send_webhook(hass, data, payload)

        await rate_limiter.trigger(payload, send)

    remove_listener = async_track_state_change_event(
        hass, data[CONF_ENTITY_ID], handle_state_change
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "remove_listener": remove_listener,
        "rate_limiter": rate_limiter,
    }

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    runtime = hass.data[DOMAIN].pop(entry.entry_id)
    runtime["remove_listener"]()
    runtime["rate_limiter"].cancel()
    return True
