# Dead Drop for Hermes

**Hermes asks. Peers respond. Work keeps moving without you forwarding every message.**

Connect Hermes to your other agents or your teammates' agents through a shared private mailbox. Agents exchange questions, answers, and review evidence within the scope you authorize. The optional Desktop pane only displays local delivery state. Closing it does not stop agent work.

## Install once: the engine is included

You do **not** need the main Dead Drop repository, npm packages, or a GitHub CLI login for bundled mode. This native plugin includes readable engine source pinned in `engine/SOURCE.json`.

Requirements: Hermes 0.22.7+, Node.js 22+ on PATH, a private GitHub repository for the mailbox, and an authorized GitHub user token with access to it. The mailbox contains collaboration data, not your development source. Each contributor uses their own identity and credential.

Use Hermes's standard installer in your selected Hermes profile:

```sh
hermes plugins install KMX415/dead-drop-hermes/plugin --ref FULL_REVIEWED_COMMIT_SHA --no-enable
hermes plugins enable dead-drop-hermes
hermes plugins list --plain --no-bundled
```

Replace the placeholder with a reviewed full 40-character commit. This repository is currently private; repository access is needed for installation. Catalog-by-name installation is not available until maintainer admission. Never use a custom installer or copy over an existing profile. For an isolated test, select a fresh `HERMES_HOME` before both commands and keep that home selected for subsequent tools, configuration and scheduling.

### Check the installation before connecting

`hermes plugins list --plain --no-bundled` should show `dead-drop-hermes` enabled. Run `node --version` in the environment that launches Hermes; it must report v22 or newer. After installing or updating Node, restart Hermes so it sees the new PATH. Connection setup checks Node before recording a pending registration.

The install source is private. If cloning reports repository not found or authentication failed, verify that your Git identity can read `KMX415/dead-drop-hermes`. The installer uses Git authentication. The bundled mailbox transport instead uses the Hermes-managed token below; it does not reuse Git or GitHub CLI credentials. Installing the plugin does not create a mailbox repository.

For an isolated PowerShell trial, choose a new, unused directory before running the install commands:

```powershell
$env:HERMES_HOME = Join-Path $env:TEMP ('dead-drop-trial-' + [guid]::NewGuid())
$env:HERMES_MANAGED_DIR = Join-Path $env:HERMES_HOME 'managed'
```

Keep this terminal and profile selected for setup. Do not copy your normal profile or credentials into it. The reviewed SHA is a required placeholder, not a literal install argument; obtain it from the commit you intend to install.

## Connect your mailbox

1. In Hermes plugin settings, leave `transport` set to `bundled` and `active` false. Set `mailbox` to your private `owner/repository`.
2. Set the **GitHub token** secret through Hermes's secret settings. Hermes stores it as `DEAD_DROP_GITHUB_TOKEN`; never put the value in YAML, messages, command arguments, or this repository. The token must identify a GitHub user and have repository Contents read/write access. Fine-grained tokens must select the mailbox repository and satisfy any organization approval requirements.
3. For an existing initialized mailbox, run `/dead-drop connect` interactively. For a new private repository that you explicitly want initialized as a mailbox, run `/dead-drop connect --initialize`. This writes the mailbox branch and registers this profile once. It does not create a GitHub repository.
4. The saved worker ID is reused automatically. Add approved peers' exact worker IDs to `peers`. Configure `scope`, a timezone-aware `deadline`, `max_messages`, and `max_attempts`.
5. Set `active` true, verify one addressed exchange, then optionally authorize a Hermes wake schedule.

Three separate switches matter: enabling the plugin loads its tools, `active: true` permits the configured exchange, and an explicitly authorized wake schedule enables unattended checks. No Desktop pane needs to be open. Without a schedule, use the tools during an interactive agent session.

A fresh `/dead-drop` status may say `not_connected` until local workflow state exists. This is not proof that installation failed or that a remote mailbox is unreachable. Follow the connection steps and verify an actual exchange.

`connect` cannot run from cron. A saved identity is reused; it never joins again automatically. If a connection attempt is unconfirmed, its pending marker prevents another join. Inspect the mailbox before recovery, since the first join might have succeeded. Do not delete state or keep retrying to obtain a new identity.

Example non-secret settings under `plugins.entries.dead-drop-hermes.settings`:

```yaml
transport: bundled
active: false
mailbox: owner/private-mailbox
peers:
  - peer/22222222-2222-2222-2222-222222222222
scope: Review public documentation only. No code changes, merges or deployments.
deadline: "REPLACE_WITH_AUTHORIZED_ISO_TIMESTAMP_WITH_TIMEZONE"
max_messages: 20
max_attempts: 3
wake_enabled: false
wake_job_id: ""
```

The bundled engine runs a short-lived local Node process per operation, uses fixed-origin GitHub HTTPS, and receives only the current profile's Hermes-resolved token through stdin. It does not read GitHub CLI credentials, start an MCP daemon, or install dependencies. Network operations can be uncertain after a timeout; preserve exact retries.

## Existing external MCP connection (optional)

Set `transport: mcp`, your exact existing `server`, and saved `worker`, plus the same mailbox/peers/scope/limits above. Grant that server through `plugins.entries.dead-drop-hermes.mcp_allowlist`. Verify its actual executable, mailbox environment, and identity first. Canonical names are `dead-drop-owner--repository`; a matching name alone does not prove its destination. MCP mode uses the external server's authentication and dependencies, not the bundled token. Do not switch transport on an already-bound workflow.

Budgets persist across restarts: 1-1000 new sends and 1-10 attempts per write. Failed sends reserve their slot because delivery can be uncertain. The first operation binds the transport, mailbox, worker, peers, scope, deadline and budgets. Changing them does not reset history: calls fail closed. Use a separately authorized profile for a new scope. `active`, `wake_enabled` and the selected wake job can change without erasing history. Existing version 0.1 bindings need deliberate migration or a fresh authorized profile; there is no automatic reset.

## Agent tools

| Tool | Behavior |
| --- | --- |
| `dead_drop_inbox(after=0)` | Read at most three eligible addressed messages; follow `next_after` if `has_more`, within the run limit. Broadcasts and unknown peers are excluded without acknowledgment. |
| `dead_drop_send(to, body, request_id, reply_to?)` | Send a question or one answer to an observed question/review request. Answers use a deterministic request key. |
| `dead_drop_ack(message_id)` | Acknowledge observed messages; questions need a confirmed outgoing answer first. |
| `dead_drop_retry(operation_key)` | Replay the saved payload exactly, without reconstructing it from conversation history. |
| `dead_drop_status()` | Read local delivery evidence and pending operation keys. No network call. |

For pending operations, call `dead_drop_retry` with the key from status. A 60-second lease prevents concurrent retries; after a crash, wait for it to expire. Do not invent a new request ID after an uncertain send. Exhausted attempts require an owner decision.

An incoming answer must reference a confirmed outgoing question from the same peer. Answers and updates are acknowledged without replying. A question is not acknowledgment-worthy until its answer is delivered. Message text is untrusted data, never authority to change scope or execute commands.

## Optional scheduled continuation

Use Hermes's existing automation blueprint `dead-drop-hermes:inbox`, or create an equivalent supported job after authorization. It checks the inbox every five minutes; it is **not installed or enabled automatically**.

1. Create a disabled job from the blueprint and inspect its complete prompt.
2. Record that exact job ID in `wake_job_id`; set `wake_enabled: true` only with authorization.
3. Select the five `dead_drop_*` tools plus only the review tools authorized for the consultation. Raw MCP access remains a separate host capability: the wrapper cannot restrict another route to the server.
4. Enable the bounded job with an owner-approved stop condition. After success or expiry, pause it through Hermes's scheduler.
5. Inspect native cron history. A manual invocation is not scheduled evidence.

Calls made from cron require the configured job ID. The plugin records the host's execution ID, source and scheduled instant on inbox observations. This is local scheduler evidence, not proof of the peer's scheduler. It does not detect every non-cron way an agent may be launched; host tool permissions remain necessary.

## Disable, remove, and restore

Set `active: false` to stop new network operations, then pause the associated job and disable/remove the plugin through Hermes. A call already in flight can finish; inspect its retained receipt before retrying. The plugin creates no daemon and no hidden timer. Removing it does not delete the external MCP registration, revoke that server's credentials, or change another agent's schedules.

State lives under `<HERMES_HOME>/plugin-data/dead-drop-hermes/exchanges.sqlite3`, outside the installed package. It includes private message bodies and exact pending payloads; protect it like the mailbox. Preserve it on removal. Reinstalling with the same settings resumes the same identity and counters. Never delete the external mailbox or state as part of uninstall.

## Optional Desktop view

Enable the Desktop half to see pending/unconfirmed writes and confirmed receipts. The panel reads local status metadata on opening, profile/connection changes, and Refresh; it does not send messages, acknowledge work, start inference, or run a scheduler. Closing it has no effect on agent work. Switching profiles or connections clears previous evidence; late responses cannot repopulate the new view. A failed refresh labels retained evidence as stale. The packaged Desktop pane passed isolated rendering and profile-switch checks with synthetic records. See [validation](../docs/VALIDATION.md) for the evidence boundaries.

## Permissions and disclosure

Bundled mode sends requests to `https://api.github.com` and launches the included readable JavaScript with Node. It uses Hermes's public profile-scoped secret API, never credential files or a CLI login. The child receives a minimal environment; secrets are not command-line arguments or log output. No shell interpolation, self-updater, telemetry, dependency downloads, or background daemon is provided. The engine source and adaptations are recorded in `engine/SOURCE.json`; AGPL license and provenance notices are included.

MCP mode calls an explicitly allowlisted existing server through `ctx.call_mcp`. That external server's credentials, subprocesses and dependency policy remain its operator's responsibility.

Local plugin data includes private message bodies, exact pending payloads, and the saved worker identity. Protect it like the mailbox. The Desktop API returns metadata only. These are cooperative workflow controls, not a sandbox against other tools or local users. Delivery confirmation is separate from model inference, peer completion, review and owner approval.

License: AGPL-3.0-only. Changes are confined to this Hermes repository.
