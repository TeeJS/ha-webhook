# Outbound Webhook for Home Assistant

<img src="custom_components/outbound_webhook/brand/icon.png" alt="Outbound Webhook" width="110" align="left">

A Home Assistant custom integration that sends outbound HTTP webhooks when entity states or attributes change. Configured entirely through the UI — no `configuration.yaml` required.

Built to bridge Home Assistant with automation platforms like [n8n](https://n8n.io) without needing Node-RED or YAML-based `rest_command` entries.

<br clear="left">


## Features

- **UI-only setup** — configure everything through Settings > Devices & Services
- **Entity triggers** — watch for state changes or specific attribute changes (brightness, volume, temperature, etc.)
- **Rate limiting** — throttle or debounce rapidly changing entities to avoid flooding your webhook endpoint
- **Multiple rules** — one integration hub holds any number of independent rules, each with its own entity, URL, and rate-limit settings
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

1. Go to **Settings > Devices & Services > Add Integration** and add **Outbound Webhook**. This creates a single hub — there's nothing to fill in.
2. Open the hub and click **Add webhook rule**. Repeat for as many rules as you need; each one is independent and can be edited or removed on its own.

Each rule has these fields:

| Field | Description |
|---|---|
| **Name** | Friendly name for this rule |
| **Entity** | The Home Assistant entity to watch |
| **Watch** | `State Change` or `Attribute Change` |
| **Attribute** | Attribute name (required if watching attributes, e.g. `brightness`) |
| **Webhook URL** | The HTTPS endpoint to send requests to |
| **HTTP Method** | `POST`, `GET`, `PUT`, or `DELETE` |
| **Rate Limit Mode** | `None`, `Throttle`, or `Debounce` (see below) |
| **Rate Limit Interval** | The time window in milliseconds used by Throttle and Debounce |

## Rate Limiting

Some entities change rapidly — a dimmer sliding, a power meter updating every second. Rate limiting stops a burst of changes from flooding your endpoint. Every rule has a **Mode** and an **Interval** (in milliseconds). The interval is only used by Throttle and Debounce.

### None

Send a webhook for **every** qualifying change. No limiting. Best for entities that change infrequently, like a door sensor or an on/off switch.

### Throttle

Send the **first** change immediately, then **ignore** further changes until the interval elapses — at most one webhook per interval. Best when you want an instant response but need to cap how often it fires.

```
Interval = 500 ms
  0 ms    change  ->  SEND
  100 ms  change  ->  drop
  250 ms  change  ->  drop
  500 ms  change  ->  SEND   (interval elapsed, allowed again)
```

### Debounce

Wait until changes **stop** for the full interval, then send **only the most recent** value. Nothing is sent while changes keep arriving. Best for values that slide and then settle — brightness, volume, a temperature setpoint.

```
Interval = 500 ms
  0 ms    change
  100 ms  change
  250 ms  change
  750 ms          ->  SEND latest value   (500 ms of quiet)
```

**Rule of thumb:** on/off entities → **None**. Sliders that settle on a final value → **Debounce**. High-frequency sensors where you want steady, capped updates → **Throttle**.

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
