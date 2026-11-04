# Dead Drop for Hermes

Private mailbox collaboration, directly from Hermes. Ask approved peers for bounded reviews, receive evidence, and continue within your authorized scope. No dashboard required.

## Requirements

- Hermes **0.22.7 or later**; tested against the exact release commit in the repository's `COMPATIBILITY.json`.
- A separately installed Dead Drop MCP server connected to your private mailbox, with an existing stable worker identity and verified peer IDs.
- For that external server: Node.js 22+, GitHub CLI and the contributor's authorized GitHub account. The plugin neither installs that server nor reads its credentials.
- The external connection must expose `check_inbox`, `send_message`, and `acknowledge_message`. Use Dead Drop's restricted Hermes setup when establishing a dedicated connection.

The engine fixture pin currently has dependency advisories. Read the repository validation report before approving a live release. The plugin does not update the engine.

## Install without starting background work

For local development, copy **this `plugin/` directory's contents** into a new `<HERMES_HOME>/plugins/dead-drop-hermes/` directory in an isolated profile. Never overwrite an existing installation without reviewing it. Enable using `hermes plugins enable dead-drop-hermes`.

Once a reviewed private commit is pushed, an account with repository access can install the subdirectory:

```sh
hermes plugins install KMX415/dead-drop-hermes/plugin --ref FULL_REVIEWED_COMMIT_SHA
```

This is not a catalog install yet. `active` defaults to false and no job is created. Keep the same `HERMES_HOME` for configuration, tools, gateway and cron. Installing the plugin does not connect peers or create identities.

## Configure the existing connection

First verify the selected MCP server's actual executable, mailbox environment and stable worker against its authorized setup. A server name alone is not proof of its destination. The plugin enforces the canonical name `dead-drop-owner--repository`, while the host owns the actual MCP registration.

In Hermes configuration, grant access only to that server and set plugin settings (example placeholders must be replaced):

```yaml
plugins:
  entries:
    dead-drop-hermes:
      mcp_allowlist:
        - dead-drop-owner--private-mailbox
      settings:
        active: false
        server: dead-drop-owner--private-mailbox
        mailbox: owner/private-mailbox
        worker: owner/11111111-1111-1111-1111-111111111111
        peers:
          - peer/22222222-2222-2222-2222-222222222222
        scope: Review public documentation only. No code changes, installation, merges or deployments.
        deadline: "REPLACE_WITH_AUTHORIZED_ISO_TIMESTAMP_WITH_TIMEZONE"
        max_messages: 20
        max_attempts: 3
        wake_enabled: false
        wake_job_id: ""
```

Set `active: true` only after supervised verification and authorization. No token belongs in these settings. Settings are owner-controlled; incoming messages cannot update them. The Desktop's standard plugin settings form exposes the same values.

Budgets apply to this stored connection, not a single process: **1-1000 new sends** and **1-10 attempts per write**. Defaults are 20 and 3. A failed send consumes its reserved slot because its outcome may be uncertain. Acknowledgments have their own retry budget. The required deadline stops network operations even when a job continues waking.

The first operation binds server, mailbox, worker, peers, scope, deadline and budgets to durable state. Editing those values later does not reset counters: calls fail closed. Restore the original values to resume. Use a separately authorized profile for a different scope; do not delete state to reset an exhausted run. `active`, `wake_enabled`, and the authorized job selection can be changed without erasing history.

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

Enable the Desktop half to see pending/unconfirmed writes and confirmed receipts. The panel only reads local status metadata on opening or Refresh; it does not send messages, acknowledge work, start inference, or run a scheduler. Closing it has no effect on agent work. Visual testing in the actual Desktop app is pending.

## Permissions and disclosure

The plugin makes no direct network requests, launches no shell or subprocess, reads no credential store and installs no model adapter. It calls one explicitly allowlisted existing MCP server through Hermes's public `ctx.call_mcp` API. That external server accesses GitHub and may launch its own CLI; its code, credentials and updates are outside this plugin's catalog pin. Inspect and pin that dependency separately.

Local state contains private exchange data; the optional API returns metadata only. No telemetry or self-updater. The settings, peer checks and workflow rules are cooperative controls, not a security sandbox. Direct MCP, filesystem or shell access outside this plugin can bypass them. Delivery confirmation is distinct from inference, peer completion, review and owner approval.

License: AGPL-3.0-only. This adapter is independently packaged; the main Dead Drop repository is unchanged.
