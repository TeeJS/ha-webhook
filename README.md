# Outbound Webhook for Home Assistant

A Home Assistant custom integration that sends outbound HTTP webhooks when entity states or attributes change. Configured entirely through the UI — no `configuration.yaml` required.

Built to bridge Home Assistant with automation platforms like [n8n](https://n8n.io) without needing Node-RED or YAML-based `rest_command` entries.

## Features

- **UI-only setup** — configure everything through Settings > Devices & Services
- **Entity triggers** — watch for state changes or specific attribute changes (brightness, volume, temperature, etc.)
- **Rate limiting** — throttle or debounce rapidly changing entities to avoid flooding your webhook endpoint
- **Multiple rules** — each webhook rule is independent with its own entity, URL, and rate-limit settings
- **Async HTTP** — non-blocking requests that won't stall Home Assistant
- **Secure by default** — sensitive headers and URL parameters are redacted from logs and diagnostics

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** > **Download custom repository**
3. Enter this repository URL and select it
4. Restart Home Assistant
5. Go to **Settings** > **Devices & Services** > **Add Integration** and search for **Outbound Webhook**

### Manual

1. Copy the `custom_components/outbound_webhook/` directory into your Home Assistant `config/` folder
2. Restart Home Assistant
3. Go to **Settings** > **Devices & Services** > **Add Integration** and search for **Outbound Webhook**

## Configuration

When adding the integration, you'll be prompted to create a webhook rule:

| Field | Description |
|---|---|
| **Name** | Friendly name for this rule |
| **Entity** | The Home Assistant entity to watch |
| **Watch** | `State Change` or `Attribute Change` |
| **Attribute** | Attribute name (required if watching attributes, e.g. `brightness`) |
| **Webhook URL** | The HTTPS endpoint to send POST requests to |
| **HTTP Method** | `POST`, `GET`, `PUT`, or `DELETE` |
| **Rate Limit Mode** | `None`, `Throttle`, or `Debounce` |
| **Rate Limit Interval** | Interval in milliseconds |

You can create multiple rules by adding the integration multiple times.

## Rate Limiting

### Throttle
Sends the first qualifying event, then suppresses further events until the interval expires. Good for periodic sensor updates.

```
0 ms     -> SEND
100 ms   -> DROP
250 ms   -> DROP
1000 ms  -> SEND
```

### Debounce
Waits until changes stop for the configured interval, then sends only the most recent value. Ideal for sliders (brightness, volume).

```
0 ms     -> event
100 ms   -> event
250 ms   -> event
900 ms   -> SEND latest value
```

## Payload Format

### State Change
```json
{
  "entity_id": "binary_sensor.front_door",
  "old_state": "off",
  "new_state": "on",
  "timestamp": "2026-08-11T18:55:47Z"
}
```

### Attribute Change
```json
{
  "entity_id": "light.living_room",
  "state": "on",
  "old_state": "on",
  "new_state": "on",
  "attribute": "brightness",
  "old_value": 130,
  "new_value": 180,
  "timestamp": "2026-08-11T18:55:47Z"
}
```

## Troubleshooting

- **Webhook not firing:** Verify the entity ID is correct and the trigger type matches your use case
- **Too many requests:** Enable throttle or debounce rate limiting
- **Connection errors:** Check that the webhook URL is reachable from your Home Assistant instance (use HTTPS)
- Check logs at **Settings** > **System** > **Logs** for `custom_components.outbound_webhook` entries

## License

MIT
