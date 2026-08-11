import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import (
    DOMAIN,
    CONF_NAME, CONF_ENTITY_ID, CONF_TRIGGER_TYPE, CONF_ATTRIBUTE,
    CONF_WEBHOOK_URL, CONF_HTTP_METHOD,
    CONF_RATE_LIMIT_MODE, CONF_RATE_LIMIT_INTERVAL,
    TRIGGER_TYPE_STATE, TRIGGER_TYPE_ATTRIBUTE,
    RATE_LIMIT_MODE_NONE, RATE_LIMIT_MODE_THROTTLE, RATE_LIMIT_MODE_DEBOUNCE,
    HTTP_METHOD_POST
)

BASE_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): str,
    vol.Required(CONF_ENTITY_ID): selector.EntitySelector(),
    vol.Required(CONF_TRIGGER_TYPE, default=TRIGGER_TYPE_STATE): selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[TRIGGER_TYPE_STATE, TRIGGER_TYPE_ATTRIBUTE]
        )
    ),
    vol.Optional(CONF_ATTRIBUTE): str,
    vol.Required(CONF_WEBHOOK_URL): selector.UrlSelector(),
    vol.Required(CONF_HTTP_METHOD, default=HTTP_METHOD_POST): selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=["POST", "GET", "PUT", "DELETE"]
        )
    ),
    vol.Required(CONF_RATE_LIMIT_MODE, default=RATE_LIMIT_MODE_NONE): selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[RATE_LIMIT_MODE_NONE, RATE_LIMIT_MODE_THROTTLE, RATE_LIMIT_MODE_DEBOUNCE]
        )
    ),
    vol.Required(CONF_RATE_LIMIT_INTERVAL, default=500): selector.NumberSelector(
        selector.NumberSelectorConfig(min=0, max=30000, unit_of_measurement="ms", mode=selector.NumberSelectorMode.BOX)
    ),
})


class OutboundWebhookConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            if user_input[CONF_TRIGGER_TYPE] == TRIGGER_TYPE_ATTRIBUTE and not user_input.get(CONF_ATTRIBUTE):
                errors[CONF_ATTRIBUTE] = "required"
            else:
                return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=BASE_SCHEMA,
            errors=errors,
        )
