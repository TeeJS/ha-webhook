# Project Handoff: Home Assistant Outbound Webhook Integration

**Project type:** Home Assistant custom integration distributed through HACS  
**Primary goal:** Send outbound HTTP webhooks from Home Assistant based on entity/state triggers without requiring `configuration.yaml`, with built-in rate limiting.

## 1. Project Objective

Build a Home Assistant custom integration that can be installed through HACS and configured entirely through the Home Assistant UI.

The integration should allow a user to define outbound webhook rules that:

- Watch a Home Assistant entity for state or attribute changes.
- Optionally filter the change being watched.
- Send an HTTP request to a configured webhook endpoint.
- Support rate limiting so rapidly changing entities do not flood the destination.
- Require no `rest_command` entries or other webhook-related edits in `configuration.yaml`.

The immediate use case is sending Home Assistant events to n8n.

Current n8n public endpoint base:

```text
https://n8n.schmitzplex.com
```

Example webhook endpoint used during testing:

```text
https://n8n.schmitzplex.com/webhook/lightbrightness
```

For n8n test mode:

```text
https://n8n.schmitzplex.com/webhook-test/lightbrightness
```

## 2. Why This Project Exists

Home Assistant can send outbound HTTP requests through `rest_command`, but that integration still requires YAML configuration.

The project requirement is specifically to avoid adding webhook definitions to `configuration.yaml`.

Node-RED was considered as an intermediary:

```text
Home Assistant -> Node-RED -> n8n
```

That would work, but installing and maintaining Node-RED solely to relay HTTP requests to n8n is unnecessary overhead.

The preferred architecture is:

```text
Home Assistant
    |
    | entity/state/attribute change
    v
Custom HACS Integration
    |
    | rate limit / debounce
    v
HTTP Request
    |
    v
n8n Webhook
```

## 3. Scope for Version 1

Version 1 should be intentionally focused.

### Required

- HACS-compatible custom integration.
- UI-only setup using a Home Assistant config flow.
- Multiple independently configurable webhook rules.
- Entity selection.
- Trigger on entity state changes.
- Trigger on a specific attribute changing.
- Optional filtering by old/new state or attribute value where practical.
- HTTP POST support.
- Configurable webhook URL.
- JSON request body.
- Rate limiting.
- Throttle mode.
- Debounce mode.
- Enable/disable each webhook rule.
- Basic error logging.
- No dependency on `configuration.yaml`.
- Asynchronous/non-blocking HTTP requests.

### Strongly Preferred

- Configurable HTTP method.
- Custom request headers.
- Optional authentication header support.
- Last successful send timestamp.
- Last error status/message.
- Config-entry options flow so rules can be edited after creation.
- Sensible timeout handling.
- Retries disabled by default unless explicitly configured.

### Out of Scope for Initial Release

Do not add these unless explicitly approved:

- MQTT.
- Incoming webhook handling.
- Node-RED integration.
- Full scripting engine.
- Arbitrary Python expressions.
- Complex retry queues.
- Persistent event queues.
- Delivery guarantees.
- Database-backed history.
- Advanced Jinja templating unless needed after the core feature is stable.

## 4. Recommended Integration Design

Use a normal Home Assistant custom integration under:

```text
custom_components/outbound_webhook/
```

Suggested initial structure:

```text
custom_components/outbound_webhook/
├── __init__.py
├── manifest.json
├── config_flow.py
├── const.py
├── coordinator.py
├── webhook_sender.py
├── rate_limiter.py
├── diagnostics.py
└── translations/
    └── en.json
```

The exact module split may change during implementation, but the integration should remain small and understandable.

## 5. Trigger Model

Do not build a replacement automation engine.

Use Home Assistant's established state-change event helpers to subscribe to entity changes.

The initial trigger types should be:

### Entity State Change

Example:

```text
light.living_room
```

Send when the entity state changes.

### Entity Attribute Change

Example:

```text
Entity:    light.living_room
Attribute: brightness
```

Send only when the specified attribute changes.

This is important for values such as:

- Light brightness.
- Color temperature.
- Temperature.
- Humidity.
- Media volume.
- Sensor values.
- Position/percentage values.

## 6. Rate Limiting

Rate limiting is a core requirement, not an optional enhancement.

The integration should support at least two distinct modes.

### Throttle

Send the first qualifying event, then suppress events until the configured interval expires.

Example:

```text
0 ms     -> SEND
100 ms   -> DROP
250 ms   -> DROP
500 ms   -> DROP
1000 ms  -> SEND
```

Typical use:

- Periodic sensor updates.
- Preventing excessive webhook volume.
- Situations where intermediate values are acceptable to discard.

### Debounce

Wait until changes stop for the configured interval, then send the most recent value.

Example:

```text
0 ms     -> event
100 ms   -> event
250 ms   -> event
400 ms   -> event
900 ms   -> SEND latest value
```

Typical use:

- Light brightness sliders.
- Volume sliders.
- Rapid UI adjustments.
- Where only the final settled value matters.

## 7. Suggested Rate-Limit Configuration

Initial UI options:

```text
Mode:
- None
- Throttle
- Debounce

Interval:
- milliseconds or seconds
```

The implementation should internally use monotonic time for interval calculations.

Each configured webhook rule must maintain its own independent rate-limit state.

One rule must never suppress another rule.

## 8. HTTP Behavior

The integration must perform HTTP requests asynchronously.

Do not block the Home Assistant event loop with synchronous networking.

### Initial Method

POST

### Suggested Headers

```http
Content-Type: application/json
```

Allow optional user-defined headers later or in the initial release if implementation remains simple.

### Suggested Default Timeout

Use a finite timeout appropriate for webhook delivery. Do not allow an unreachable endpoint to stall Home Assistant indefinitely.

### Failure Behavior

A webhook failure must:

- Be logged clearly.
- Not crash the integration.
- Not block future events permanently.
- Expose useful diagnostics where practical.

## 9. Default Payload

A useful default payload should include enough Home Assistant context that n8n can make routing decisions without requiring custom templates.

Suggested structure:

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

For a normal state change with no specific attribute:

```json
{
  "entity_id": "binary_sensor.example",
  "state": "off",
  "new_state": "on",
  "timestamp": "2026-08-11T18:55:47Z"
}
```

Do not send every entity attribute by default unless there is a clear reason. Keep payloads predictable and compact.

## 10. Home Assistant UI

The integration should be configured through:

```text
Settings -> Devices & services -> Add integration
```

Suggested setup flow:

```text
Name:
Living Room Brightness

Entity:
light.living_room

Watch:
Attribute

Attribute:
brightness

Webhook URL:
https://n8n.schmitzplex.com/webhook/lightbrightness

HTTP method:
POST

Rate-limit mode:
Debounce

Rate-limit interval:
500 ms
```

After creation, the rule should be editable through an options flow.

No YAML should be required.

## 11. Config Entry Model

Each outbound webhook rule should preferably be its own Home Assistant config entry.

Advantages:
- Independent enable/disable behavior.
- Independent URL.
- Independent trigger.
- Independent rate limiting.
- Easier editing.
- Easier diagnostics.
- Easier unload/reload handling.

Suggested stored values:

```text
name
entity_id
trigger_type
attribute
webhook_url
http_method
headers
rate_limit_mode
rate_limit_interval
enabled
```

Avoid storing runtime state such as active debounce timers in the config entry.

## 12. Runtime State

Runtime-only state may include:

```text
last_send_monotonic
pending_debounce_task
latest_event
last_success_timestamp
last_error
```

Cancel pending tasks cleanly when:
- A config entry is unloaded.
- Home Assistant shuts down.
- A rule is disabled.
- An options change requires reload.

## 13. HACS Packaging

The integration should be structured as a standard Home Assistant custom integration repository suitable for HACS.

The integration directory must be:

```text
custom_components/outbound_webhook/
```

The project will also need repository-level HACS metadata/documentation as required for distribution.

At minimum, include:

```text
README.md
LICENSE
custom_components/outbound_webhook/manifest.json
custom_components/outbound_webhook/translations/en.json
```

The exact domain name `outbound_webhook` is a recommendation and should be confirmed before coding if a different public name is desired.

## 14. Home Assistant Compatibility

The target environment is Home Assistant running as a Docker container.

Do not assume:
- Home Assistant OS.
- Supervisor.
- Add-ons.
- Access to the Home Assistant Add-on Store.

The integration must work as a normal custom component.

The implementation should follow current Home Assistant APIs and avoid deprecated interfaces.

## 15. Security Considerations

We must not log authorization tokens or full sensitive headers.

Webhook URLs and headers may contain secrets.

Requirements:
- Do not log authorization tokens.
- Do not log full sensitive headers.
- Avoid exposing secrets in diagnostics.
- Redact common sensitive headers such as:
  - Authorization
  - X-API-Key
  - Proxy-Authorization

HTTPS should be used for remote endpoints.

Current n8n endpoint already uses HTTPS:

```text
https://n8n.schmitzplex.com
```

## 16. n8n Notes

Direct communication to n8n has already been verified through the reverse proxy.

A test POST to:

```text
https://n8n.schmitzplex.com/webhook-test/lightbrightness
```

returned:

```json
{"message":"Workflow was started"}
```

Direct LAN access to:

```text
http://192.168.1.125:5678
```

timed out from the Windows workstation.

Therefore, the integration should use the reverse-proxy URL rather than depending on direct access to n8n's container port.

For active n8n workflows, use the production webhook path:

```text
/webhook/...
```

The `/webhook-test/...` path is intended for n8n test/listening mode.

## 17. Error Handling Expectations

Errors should be classified where practical.

Examples:
- DNS failure
- Connection timeout
- TLS failure
- HTTP 4xx
- HTTP 5xx
- Invalid URL
- Invalid JSON/body construction
- Canceled debounce task

A failed webhook request must not disable the rule automatically.

Repeated failures should be logged without creating an uncontrolled log flood.

## 18. Diagnostics

A diagnostics export should avoid secrets and may include:

```text
integration version
configured entity_id
trigger type
attribute name
HTTP method
rate-limit mode
rate-limit interval
last success timestamp
last HTTP status
last error type
```

Do not include:
- Authorization headers
- API keys
- secret tokens
- full sensitive URLs if query parameters contain secrets

## 19. Testing Requirements

At least:
- State-change trigger sends exactly once.
- Attribute trigger ignores unrelated attribute changes.
- Attribute trigger sends when target attribute changes.
- Throttle suppresses events inside the interval.
- Throttle sends again after the interval.
- Debounce sends only the latest event.
- New debounce events reset the timer.
- Multiple rules do not interfere with each other.
- Failed HTTP requests do not crash Home Assistant.
- Config entry unload cancels listeners/tasks.
- Config entry reload restores listeners.
- Sensitive headers are redacted from diagnostics/logging.
- Production n8n endpoint works through HTTPS reverse proxy.

## 20. Suggested First Milestone

The first working milestone should do only this:

1. Install through custom_components/HACS.
2. Add integration through the Home Assistant UI.
3. Select one entity.
4. Select one attribute.
5. Enter one webhook URL.
6. Choose throttle or debounce.
7. Enter an interval.
8. Save.
9. Change the entity/attribute.
10. Confirm one JSON POST reaches n8n.

## 21. Acceptance Criteria for Version 1

Version 1 is complete when:
- It installs cleanly through HACS.
- It can be configured entirely from the Home Assistant UI.
- No `configuration.yaml` changes are required.
- A rule can watch a Home Assistant entity state.
- A rule can watch a specific entity attribute.
- Matching changes generate an HTTP POST.
- The POST reaches n8n through `https://n8n.schmitzplex.com`.
- Throttle works.
- Debounce works.
- Multiple webhook rules work independently.
- Rules can be edited and removed through the UI.
- Integration reload/unload works without restarting Home Assistant.
- Errors are logged without crashing Home Assistant.
- Sensitive values are not exposed in logs or diagnostics.

## 22. Design Principle

Keep the integration narrowly focused:

```text
Home Assistant event -> controlled outbound HTTP webhook
```

It should not become another general automation engine.

Home Assistant should remain responsible for entity state and event generation.

The custom integration should be responsible for:
- observing
- filtering
- rate limiting
- payload construction
- HTTP delivery
```