# Stale SQLite Connection After Index Rebuild

**Date**: 2026-02-23
**Scope**: Bug fix — new meetings not appearing in API after pipeline refresh

---

## Problem

After running a `refresh` pipeline job (export new meetings + rebuild index), the new meetings appeared in the worker logs as successfully indexed but were **not visible** via `GET /api/meetings`. The API kept returning stale data.

## Root Cause

A classic **stale file descriptor** bug caused by the interaction of three things:

1. **`build_index.py --rebuild`** deleted the SQLite database file (`SEARCH_DB_PATH.unlink()`) and created a new one.
2. **`dependencies.py`** cached a `SearchDB` singleton (`_search_db`) with a persistent `sqlite3.Connection` to the original file.
3. **Unix file semantics**: deleting an open file removes the directory entry but the file descriptor remains valid, pointing to the now-orphaned inode. The backend kept reading from the old (deleted) database indefinitely.

### Timeline of the Bug

```
Worker (rebuild)                          Backend (API)
─────────────────                         ─────────────
                                          SearchDB() → opens db file (inode A)
                                          _search_db cached with conn to inode A
SEARCH_DB_PATH.unlink()  ← deletes inode A from directory
SearchDB() → creates new db file (inode B)
indexes 576 meetings into inode B
                                          GET /api/meetings → reads inode A (empty/stale)
                                          ❌ new meetings not visible
```

## Fix

### Changed File

**`scripts/build_index.py`** (lines 123–128)

**Before** — delete file, create new one:
```python
if args.rebuild and SEARCH_DB_PATH.exists():
    log.info("Removing existing database for rebuild...")
    SEARCH_DB_PATH.unlink()

db = SearchDB()
db.initialize()
```

**After** — clear tables in-place, keep same file:
```python
db = SearchDB()
db.initialize()

if args.rebuild:
    log.info("Clearing existing data for rebuild...")
    conn = db._connect()
    for table in ["search_index", "notes", "summaries", "transcripts", "meetings"]:
        conn.execute(f"DELETE FROM {table}")
    conn.commit()
```

### Why This Works

- The database file is never deleted, so the inode stays the same.
- The backend's cached `SearchDB` connection reads from the same inode.
- SQLite WAL mode ensures the backend sees committed writes from the worker.
- `DELETE FROM` + re-insert achieves the same result as dropping and recreating the database.

## Key Lesson

**Never delete and recreate a file that another process holds open.** On Unix, this silently creates two independent files — the old process keeps the orphaned inode, the new process writes to a fresh one. Instead, truncate or clear the contents in-place so all file descriptors see the updated data.

This pattern applies broadly:
- SQLite databases shared across processes → clear tables, don't unlink
- Log files with open readers → truncate (`> file`), don't `rm` + `touch`
- Config files watched by services → write in-place, don't delete + recreate
