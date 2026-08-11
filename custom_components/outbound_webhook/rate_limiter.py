import asyncio
import logging
import time
from homeassistant.helpers import event as async_event

_LOGGER = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, hass, mode, interval_ms):
        self.hass = hass
        self.mode = mode
        self.interval = interval_ms / 1000.0
        self.last_send = 0
        self._debounce_timer = None
        self._latest_payload = None

    async def trigger(self, payload, callback):
        if self.mode == "none":
            await callback(payload)
            return

        if self.mode == "throttle":
            now = time.monotonic()
            if now - self.last_send >= self.interval:
                self.last_send = now
                await callback(payload)

        elif self.mode == "debounce":
            self._latest_payload = payload
            if self._debounce_timer:
                self._debounce_timer()

            def _fire(_):
                self._debounce_timer = None
                p = self._latest_payload
                asyncio.create_task(callback(p))

            self._debounce_timer = async_event.async_call_later(
                self.hass, self.interval, _fire
            )

    def cancel(self):
        if self._debounce_timer:
            self._debounce_timer()
            self._debounce_timer = None
