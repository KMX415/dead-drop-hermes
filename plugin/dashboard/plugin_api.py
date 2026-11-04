"""Read-only metadata. No credentials, mailbox calls, or message bodies."""
from contextlib import closing
import json
import sqlite3
from fastapi import APIRouter
from plugins.plugin_storage import plugin_data_dir
router=APIRouter()
@router.get("/status")
def status():
    path=plugin_data_dir("dead-drop-hermes") / "exchanges.sqlite3"
    if not path.exists(): return {"state":"No exchanges yet","recent":[]}
    try:
        with closing(sqlite3.connect(path.as_uri()+"?mode=ro",uri=True,timeout=2)) as db:
            db.row_factory=sqlite3.Row
            rows=[dict(r) for r in db.execute("SELECT key,tool,attempts,result IS NOT NULL AS completed,error,updated FROM writes ORDER BY updated DESC LIMIT 20")]
        return {"state":"Local delivery evidence","recent":rows}
    except sqlite3.Error:
        return {"state":"State unavailable; delivery unconfirmed","recent":[]}
