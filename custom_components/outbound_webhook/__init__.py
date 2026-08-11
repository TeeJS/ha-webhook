import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util
from . import config_flow  # noqa: F401
from .const import (
    DOMAIN, CONF_ENTITY_ID, CONF_TRIGGER_TYPE, CONF_ATTRIBUTE,
    CONF_RATE_LIMIT_MODE, CONF_RATE_LIMIT_INTERVAL,
    TRIGGER_TYPE_ATTRIBUTE, SUBENTRY_TYPE_RULE,
)
from .rate_limiter import RateLimiter
from .webhook_sender import async_send_webhook

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the hub entry and one rule per subentry."""
    hass.data.setdefault(DOMAIN, {})

    rules = {}
    for subentry_id, subentry in entry.subentries.items():
        if subentry.subentry_type != SUBENTRY_TYPE_RULE:
            continue
        rules[subentry_id] = _setup_rule(hass, dict(subentry.data))

    hass.data[DOMAIN][entry.entry_id] = rules

    # Reload when subentries (rules) are added / removed / reconfigured.
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


def _setup_rule(hass: HomeAssistant, data: dict) -> dict:
    """Wire up a single rule's state listener and rate limiter."""
    rate_limiter = RateLimiter(
        hass,
        data.get(CONF_RATE_LIMIT_MODE, "none"),
        data.get(CONF_RATE_LIMIT_INTERVAL, 0),
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
                "timestamp": dt_util.utcnow().isoformat(),
            }
        else:
            if old_state and old_state.state == new_state.state:
                return

            payload = {
                "entity_id": new_state.entity_id,
                "old_state": old_state.state if old_state else None,
                "new_state": new_state.state,
                "timestamp": dt_util.utcnow().isoformat(),
            }

        async def send(rule_payload):
            await async_send_webhook(hass, data, rule_payload)

        await rate_limiter.trigger(payload, send)

    remove_listener = async_track_state_change_event(
        hass, data[CONF_ENTITY_ID], handle_state_change
    )

    return {"remove_listener": remove_listener, "rate_limiter": rate_limiter}


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    rules = hass.data.get(DOMAIN, {}).pop(entry.entry_id, {})
    for rule in rules.values():
        rule["remove_listener"]()
        rule["rate_limiter"].cancel()
    return True
