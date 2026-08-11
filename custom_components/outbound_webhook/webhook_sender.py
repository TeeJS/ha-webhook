import logging
from aiohttp import ClientError, ClientResponseError, ClientConnectorError, ClientTimeout
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

SENSITIVE_HEADERS = {"authorization", "x-api-key", "proxy-authorization"}
DEFAULT_TIMEOUT = 10


async def async_send_webhook(hass, config, payload):
    url = config["webhook_url"]
    method = config.get("http_method", "POST").upper()
    headers = config.get("headers", {})

    if not any(k.lower() == "content-type" for k in headers):
        headers["Content-Type"] = "application/json"

    safe_headers = {
        k: "REDACTED" if k.lower() in SENSITIVE_HEADERS else v
        for k, v in headers.items()
    }
    _LOGGER.debug("Sending %s to %s with headers %s", method, url, safe_headers)

    try:
        session = hass.async_clientsession()
        timeout = ClientTimeout(total=DEFAULT_TIMEOUT)

        async with session.request(
            method, url, json=payload, headers=headers, timeout=timeout
        ) as resp:
            if resp.status >= 400:
                _LOGGER.warning("Webhook request to %s failed with status %s", url, resp.status)
                return {"status": resp.status, "success": False}
            _LOGGER.debug("Webhook sent successfully to %s", url)
            return {"status": resp.status, "success": True}

    except ClientResponseError as err:
        _LOGGER.error("HTTP error sending webhook to %s: %s", url, err)
        return {"status": err.status, "success": False, "error": str(err)}
    except ClientConnectorError:
        _LOGGER.error("Connection error sending webhook to %s", url)
        return {"success": False, "error": "Connection failed"}
    except ClientError as err:
        _LOGGER.error("Client error sending webhook to %s: %s", url, err)
        return {"success": False, "error": str(err)}
    except Exception as err:
        _LOGGER.error("Unexpected error sending webhook to %s: %s", url, err)
        return {"success": False, "error": str(err)}
