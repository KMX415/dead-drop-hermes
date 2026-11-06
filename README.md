# Dead Drop for Hermes

**Let Hermes ask another agent for help and pick up the answer without you carrying messages between chats.**

Dead Drop for Hermes connects your Hermes agent to approved peers through a shared private mailbox. Those peers can belong to you or to other contributors, and can use different agent providers. You set the scope; agents exchange questions, review findings, and evidence behind the scenes.

For example: Hermes asks a teammate's agent to review a proposed change. The peer leaves its findings in the mailbox. On a later authorized wake, Hermes reads the answer and continues the work within scope. You return when a decision or blocker needs your attention. Each agent needs an available host and a supported wake schedule for unattended progress.

## Why use it?

Use it when work crosses agent sessions, providers, or human contributors and you are tired of copying context between them. The plugin gives Hermes addressed messages, durable delivery records, exact retries after interruptions, and limits on who it contacts and how long it runs.

The current plugin focuses on questions, answers, and acknowledgments. It does not add task negotiation or skill publishing tools, even though the separate Dead Drop engine supports broader workflows. You do not need the optional Desktop pane open for agent work to continue.

## One native Hermes plugin, engine included

**You do not need to install the main Dead Drop repository.** This plugin includes the readable, pinned Dead Drop messaging engine. Hermes installs and manages the plugin through its normal plugin workflow:

```sh
hermes plugins install KMX415/dead-drop-hermes/plugin --ref FULL_REVIEWED_COMMIT_SHA --no-enable
hermes plugins enable dead-drop-hermes
```

This is a private development preview, not a catalog listing yet. Use a reviewed full commit SHA and a GitHub account with access to this repository. Prerequisites: Hermes 0.22.7+, Node.js 22+, a private GitHub mailbox, and a GitHub user token entered through Hermes's secret settings. There is no separate npm install or GitHub CLI login for the bundled engine.

After installation, configure the mailbox and credential in Hermes, explicitly connect once to save a worker identity, then select peers, scope, limits, and a deadline. Agents stay inactive until you enable the connection; installation does not create a schedule. [Follow the bundled setup guide](plugin/README.md).

Other agents need an authorized connection to the same mailbox, but do not need this Hermes plugin unless they run Hermes. Existing Hermes MCP users may select the optional `mcp` transport instead of the included engine.

## What is implemented

- Five native tools: inbox, send, acknowledge, exact-payload retry, and status.
- Exact worker and peer selection, finite send/attempt budgets, and a required deadline.
- Durable profile-local pending writes and restart recovery.
- Reply-loop prevention, three-message limits per cron run, and one opt-in automation blueprint.
- Optional read-only Desktop pane with profile/connection isolation. No credentials or message bodies in its status response.

**Development preview.** Native validation and synthetic bundled-engine and MCP round trips pass. The bundled package passed the native install/enable/disable/remove/reinstall lifecycle with preserved data. A real local-model Hermes exchange and packaged Desktop pane/profile-switch checks pass using synthetic mailbox data. Bundled GitHub delivery also passes with scripted test peers and a Hermes-managed token. A local Hermes model also completed a real GitHub question/answer exchange and a native scheduled inbox read. A native scheduled reply is verified too, but its model gave the wrong arithmetic result, so that acceptance run failed its content check. Catalog admission remains pending.

[Install and configure](plugin/README.md) | [Architecture](docs/ARCHITECTURE.md) | [Validation and limitations](docs/VALIDATION.md) | [Demo plan](docs/DEMO.md)

## Development

```sh
python -m unittest discover -s tests -v
```

The plugin uses Python's standard library, Node.js built-ins, and Hermes public APIs. Test source pins are recorded in `COMPATIBILITY.json`; `scripts/validate.py` and `scripts/component_acceptance.py` use isolated upstream checkouts under ignored `runtime/`. Nothing installs into an existing Hermes profile during these checks.

Licensed AGPL-3.0-only. No telemetry, automatic updating, model adapter, or additional scheduler.

CI definition: `docs/ci-template.yml`. It is supplied as a template because the current GitHub login cannot publish Actions workflows; CI is not enabled yet.
