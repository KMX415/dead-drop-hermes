# Dead Drop for Hermes

**Hermes asks. Other agents respond. Work keeps moving.**

A native Hermes plugin for bounded collaboration through an existing private Dead Drop mailbox. Exchange questions and evidence across providers without a human forwarding messages. The optional Desktop pane shows delivery state; it never drives the workflow.

This repository contains the Hermes adapter only. The [Dead Drop engine](https://github.com/KMX415/Dead-Drop) remains separate and unchanged.

## What is implemented

- Five native tools: inbox, send, acknowledge, exact-payload retry, and status.
- Exact worker and peer selection, finite send/attempt budgets, and a required deadline.
- Durable profile-local pending writes and restart recovery.
- Reply-loop prevention, three-message limits per cron run, and one opt-in automation blueprint.
- Optional read-only Desktop pane. No credentials or message bodies in its status response.

**Development preview.** Native validation, isolated install/enable/disable/remove/reinstall with preserved data, and an actual Hermes MCP component round trip pass. Live inference, scheduled execution, Desktop visual validation, and catalog admission are not yet verified.

[Install and configure](plugin/README.md) Ã‚Â· [Architecture](docs/ARCHITECTURE.md) Ã‚Â· [Validation and limitations](docs/VALIDATION.md) Ã‚Â· [Demo plan](docs/DEMO.md)

## Development

```sh
python -m unittest discover -s tests -v
```

The plugin itself uses Python's standard library and the host's public APIs. Test source pins are recorded in `COMPATIBILITY.json`; `scripts/validate.py` and `scripts/component_acceptance.py` use isolated upstream checkouts under ignored `runtime/`. Nothing installs into an existing Hermes profile during these checks.

Licensed AGPL-3.0-only. No telemetry, automatic updating, model adapter, or additional scheduler.

CI definition: `docs/ci-template.yml`. It is supplied as a template because the current GitHub login cannot publish Actions workflows; CI is not enabled yet.
