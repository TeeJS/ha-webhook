import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigSubentryFlow
from homeassistant.core import callback
from homeassistant.helpers import selector
from .const import (
    DOMAIN,
    SUBENTRY_TYPE_RULE,
    CONF_NAME, CONF_ENTITY_ID, CONF_TRIGGER_TYPE, CONF_ATTRIBUTE,
    CONF_WEBHOOK_URL, CONF_HTTP_METHOD,
    CONF_RATE_LIMIT_MODE, CONF_RATE_LIMIT_INTERVAL,
    TRIGGER_TYPE_STATE, TRIGGER_TYPE_ATTRIBUTE,
    RATE_LIMIT_MODE_NONE, RATE_LIMIT_MODE_THROTTLE, RATE_LIMIT_MODE_DEBOUNCE,
    HTTP_METHOD_POST,
)


def _rule_schema() -> vol.Schema:
    """Schema for a single webhook rule."""
    return vol.Schema({
        vol.Required(CONF_NAME): str,
        vol.Required(CONF_ENTITY_ID): selector.EntitySelector(),
        vol.Required(CONF_TRIGGER_TYPE, default=TRIGGER_TYPE_STATE): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[TRIGGER_TYPE_STATE, TRIGGER_TYPE_ATTRIBUTE]
            )
        ),
        vol.Optional(CONF_ATTRIBUTE): str,
        vol.Required(CONF_WEBHOOK_URL): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.URL)
        ),
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
    """Hub config flow. A single hub entry holds all rules as subentries."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        # Single hub entry; individual rules are added as subentries.
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        return self.async_create_entry(title="Outbound Webhook", data={})

    @classmethod
    @callback
    def async_get_supported_subentry_types(cls, config_entry: ConfigEntry):
        return {SUBENTRY_TYPE_RULE: RuleSubentryFlowHandler}


class RuleSubentryFlowHandler(ConfigSubentryFlow):
    """Add and reconfigure individual webhook rules."""

    def _validate(self, user_input):
        if user_input[CONF_TRIGGER_TYPE] == TRIGGER_TYPE_ATTRIBUTE and not user_input.get(CONF_ATTRIBUTE):
            return {CONF_ATTRIBUTE: "attribute_required"}
        return {}

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            errors = self._validate(user_input)
            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_rule_schema(),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input=None):
        errors = {}
        subentry = self._get_reconfigure_subentry()
        if user_input is not None:
            errors = self._validate(user_input)
            if not errors:
                return self.async_update_and_abort(
                    self._get_entry(),
                    subentry,
                    title=user_input[CONF_NAME],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                _rule_schema(), dict(subentry.data)
            ),
            errors=errors,
        )
