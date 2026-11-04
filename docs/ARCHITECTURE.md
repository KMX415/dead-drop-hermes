# Architecture

Hermes tools → bounded workflow → host `ctx.call_mcp` → existing Dead Drop server → private GitHub mailbox → peer agent.

The adapter does not fork or vendor the engine. `COMPATIBILITY.json` records the exact engine and Hermes revisions used for component tests, not an automatic production dependency update. Runtime credential ownership stays with the existing server and its host. The plugin never reads the server's token or configuration files.

The workflow stores an immutable connection binding and a write journal in profile-local SQLite. It commits each exact payload and attempt before the remote operation. A crash can leave an uncertain result; a later retry reuses the same request key, allowing Dead Drop's existing deduplication to converge. A lease prevents ordinary overlapping attempts. This is not distributed exactly-once execution for arbitrary external work.

Incoming messages are retained only after exact recipient, peer and kind filtering. An answer needs an observed confirmed parent question from that peer. Outgoing replies to answers or updates are rejected. Scope text is a human-readable constraint for the agent, not a semantic verifier of arbitrary content.

Installation registers five tools, a status command, and a blueprint. Registration does not open the mailbox or start work. Native unload removes those registrations. The optional Desktop pane uses its own read-only backend namespace and does not own workflow state.

No changes to the main Dead Drop checkout, no NUC configuration, and no new scheduler or model provider are required by this repository's development tests.
