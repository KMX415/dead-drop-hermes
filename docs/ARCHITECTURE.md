# Architecture

Default: Hermes tools → bounded workflow → short-lived Node bridge → bundled engine → GitHub HTTPS → shared private mailbox → peer agent.

The native Hermes installer ships the Python plugin, optional Desktop pane, and readable engine modules as one package. `plugin/engine/SOURCE.json` records the upstream commit, source hashes and adapted GitHub transport. No standalone installer, npm install, or separately installed Dead Drop checkout is required. Node.js 22+ is a prerequisite.

The GitHub token comes from Hermes's public `agent.secret_scope.get_secret` API. Only the active profile's token crosses stdin to the engine; it is not written by the plugin or inherited from a CLI credential store. GitHub requests use a fixed HTTPS origin and refuse redirects. The bridge exposes messaging plus explicit interactive worker connection/initialization, not the engine's entire domain surface.

Optional MCP mode preserves the original `ctx.call_mcp` route to an existing operator-configured server. It has separate dependency and credential ownership. Neither transport installs schedules.

The workflow stores an immutable connection binding and a write journal in profile-local SQLite. It commits each exact payload and attempt before the remote operation. A crash can leave an uncertain result; a later retry reuses the same request key, allowing Dead Drop's existing deduplication to converge. A lease prevents ordinary overlapping attempts. This is not distributed exactly-once execution for arbitrary external work.

Incoming messages are retained only after exact recipient, peer and kind filtering. An answer needs an observed confirmed parent question from that peer. Outgoing replies to answers or updates are rejected. Scope text is a human-readable constraint for the agent, not a semantic verifier of arbitrary content.

Installation registers five tools, a status command, and a blueprint. Registration does not open the mailbox or start work. Native unload removes those registrations. The optional Desktop pane uses its own read-only backend namespace and does not own workflow state.
