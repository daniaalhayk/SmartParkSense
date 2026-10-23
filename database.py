import sqlite3
import pandas as pd
import config

# الاتصال بقاعدة البيانات
def _conn():
    return sqlite3.connect(config.DB_FILE)

# تهيئة الجداول
def init_db():
    with _conn() as c:
        c.execute("CREATE TABLE IF NOT EXISTS snapshots(ts TEXT, occupied INTEGER, total INTEGER, source TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS space_states(ts TEXT, space_id INTEGER, occupied INTEGER, source TEXT)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_snap_ts ON snapshots(ts)")

# حفظ بيانات الإشغال
def insert_snapshots(rows):
    with _conn() as c:
        c.executemany("INSERT INTO snapshots VALUES (?,?,?,?)", rows)

# حفظ حالة كل موقف
def insert_space_states(rows):
    with _conn() as c:
        c.executemany("INSERT INTO space_states VALUES (?,?,?,?)", rows)

# تفريغ البيانات
def clear(source=None):
    with _conn() as c:
        if source:
            c.execute("DELETE FROM snapshots WHERE source=?", (source,))
            c.execute("DELETE FROM space_states WHERE source=?", (source,))
        else:
            c.execute("DELETE FROM snapshots")
            c.execute("DELETE FROM space_states")

# استرجاع البيانات
def load_snapshots(source=None):
    init_db()
    q, params = "SELECT * FROM snapshots", ()
    if source and source != "all":
        q, params = q + " WHERE source=?", (source,)
    with _conn() as c:
        df = pd.read_sql_query(q + " ORDER BY ts", c, params=params)
    if not df.empty:
        df["ts"] = pd.to_datetime(df["ts"])
        df["ratio"] = df["occupied"] / df["total"].clip(lower=1)
    return df

# استرجاع أحدث حالة للمواقف
def latest_space_states(source="video"):
    init_db()
    with _conn() as c:
        row = c.execute("SELECT MAX(ts) FROM space_states WHERE source=?", (source,)).fetchone()
        if not row or not row[0]: return pd.DataFrame(columns=["space_id", "occupied"])
        return pd.read_sql_query("SELECT space_id, occupied FROM space_states WHERE ts=? AND source=? ORDER BY space_id", c, params=(row[0], source))

# استرجاع المصادر المتاحة
def sources():
    init_db()
    with _conn() as c:
        return [r[0] for r in c.execute("SELECT DISTINCT source FROM snapshots")]
