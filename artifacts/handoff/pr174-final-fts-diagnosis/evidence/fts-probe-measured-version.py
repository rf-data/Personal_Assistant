"""Local-only synthetic instrumentation. Never emits SQL, parameters or contents."""
import functools
import inspect
import json
import os
import sqlite3
import time
from pathlib import Path

EVENTS = []
CURRENT = None
ORIGINAL_CONNECT = sqlite3.connect
INSTALLED = False
CLOCK = time.monotonic


def mark(phase):
    if CURRENT is None:
        return
    now = CLOCK()
    prior = CURRENT.pop('_phase_start', now)
    previous = CURRENT.get('_phase')
    if previous:
        CURRENT['phases'][previous] = CURRENT['phases'].get(previous, 0) + now - prior
    CURRENT['_phase'] = phase
    CURRENT['_phase_start'] = now
    CURRENT['boundaries'].append(dict(phase=phase, elapsed=now-CURRENT['start'], remaining=CURRENT['deadline']-now))


def failure(exc, operation):
    if CURRENT is None:
        return
    now = CLOCK()
    CURRENT.setdefault('sqlite_errors', []).append(dict(
        exception_class=type(exc).__module__+'.'+type(exc).__name__,
        # Only SQLite's enumerated error name; never arbitrary error text.
        sqlite_errorcode=getattr(exc,'sqlite_errorcode',None),
        sqlite_errorname=getattr(exc,'sqlite_errorname',None),
        phase=CURRENT.get('_phase'), operation=operation,
        message=str(exc) if str(exc) in {'interrupted','database is locked','database disk image is malformed'} else '<redacted>',
        elapsed=now-CURRENT['start'], remaining=CURRENT['deadline']-now,
    ))


class Cursor(sqlite3.Cursor):
    def fetchall(self):
        try:
            return super().fetchall()
        except sqlite3.Error as exc:
            failure(exc, 'fetchall')
            raise
    def fetchone(self):
        try:
            return super().fetchone()
        except sqlite3.Error as exc:
            failure(exc, 'fetchone')
            raise
    def __next__(self):
        try:
            return super().__next__()
        except sqlite3.Error as exc:
            failure(exc, 'cursor_next')
            raise


class Connection(sqlite3.Connection):
    def deserialize(self, data, **kwargs):
        mark('deserialize')
        try:
            return super().deserialize(data, **kwargs)
        except sqlite3.Error as exc:
            failure(exc, 'deserialize')
            raise
    def execute(self, sql, parameters=(), /):
        # Categorization uses unexpanded statements internally, never logs them.
        if sql == 'PRAGMA query_only=ON':
            mark('query_only')
        elif ' WHERE fts MATCH ?' in sql:
            mark('match_bm25')
        try:
            return self.cursor(factory=Cursor).execute(sql, parameters)
        except sqlite3.Error as exc:
            failure(exc, ('pragma_integrity_check' if sql == 'PRAGMA integrity_check' else 'fts_integrity_check' if sql == "INSERT INTO fts(fts,rank) VALUES('integrity-check',1)" else 'match_bm25' if ' WHERE fts MATCH ?' in sql else 'other_execute'))
            raise


def save():
    target = os.environ.get('FTS_PROBE_OUTPUT')
    if target:
        Path(target).write_text(json.dumps(EVENTS, indent=2)+'\n')


def install():
    global INSTALLED
    if INSTALLED:
        return
    INSTALLED = True
    from src.tools_rag import content_fts as fts
    from src.tools_rag.content_index import ContentIndex
    from src.tools_rag.content_index_files import IndexFiles
    # Instrument only FTS connections. Never replace ContentStore's SQLite connection.
    class Proxy:
        def __getattr__(self, name):
            return getattr(sqlite3,name)
        def connect(self, *a, **kw):
            if CURRENT is not None:
                CURRENT['sqlite_entry_remaining'] = CURRENT['deadline'] - CLOCK()
            kw['factory'] = Connection
            return ORIGINAL_CONNECT(*a, **kw)
    fts.sqlite3 = Proxy()
    src = inspect.getsource(fts._check)
    src = src.replace('    if (', "    _probe_mark('schema_integrity')\n    if (", 1)
    src = src.replace('    if dict(db.execute', "    _probe_mark('backend_metadata')\n    if dict(db.execute", 1)
    src = src.replace('    ordered = sorted(', "    _probe_mark('record_comparison')\n    ordered = sorted(", 1)
    src = src.replace('    if (\n        db.execute("SELECT rowid,text', '    _probe_mark(\'fts_projection\')\n    if (\n        db.execute("SELECT rowid,text', 1)
    src = src.replace('    db.execute("INSERT INTO fts(fts,rank)', '    _probe_mark(\'fts_integrity\')\n    db.execute("INSERT INTO fts(fts,rank)', 1)
    fts.__dict__['_probe_mark'] = mark
    # Reject any accidental semantic edit: removing timing calls must recover
    # exactly the original function's AST, including every integrity check.
    import ast
    baseline = ast.parse(inspect.getsource(fts._check))
    measured_ast = ast.parse(src)
    class StripMarks(ast.NodeTransformer):
        def visit_Expr(self, node):
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == '_probe_mark':
                return None
            return self.generic_visit(node)
    assert ast.dump(StripMarks().visit(measured_ast)) == ast.dump(baseline)
    exec(compile(src, '<synthetic_fts_probe>', 'exec'), fts.__dict__)
    from src.content_store import index_projection as projection
    for name in ('_load', '_selection', '_records'):
        def wrap(original, name):
            @functools.wraps(original)
            def measured(*a, **kw):
                start = CLOCK()
                try:
                    return original(*a, **kw)
                finally:
                    if CURRENT is not None:
                        stats = CURRENT.setdefault('projection_subphases', {})
                        stats[name] = stats.get(name, 0) + CLOCK()-start
            return measured
        setattr(projection, name, wrap(getattr(projection,name), name))
    old_search = ContentIndex._search
    @functools.wraps(old_search)
    def search(self, *a, **kw):
        global CURRENT
        deadline = a[-1] if a else kw['deadline']
        CURRENT = dict(start=CLOCK(), deadline=deadline, phases={}, boundaries=[], kind='search')
        event = CURRENT
        mark('pre_partition')
        try:
            value = old_search(self, *a, **kw)
            event['outcome'] = 'ok'
            return value
        except Exception as exc:
            event['outcome'] = type(exc).__name__
            raise
        finally:
            mark('end')
            event['total'] = CLOCK()-event['start']
            event['remaining'] = deadline-CLOCK()
            event.pop('_phase_start',None)
            event.pop('_phase',None)
            EVENTS.append(event)
            CURRENT = None
    ContentIndex._search = search
    old_read = IndexFiles.read
    @functools.wraps(old_read)
    def read(self, relative, **kw):
        if CURRENT is None or not relative.endswith('.sqlite3'):
            return old_read(self,relative,**kw)
        mark('index_file_load')
        try:
            return old_read(self,relative,**kw)
        finally:
            mark('file_hash_and_partition_dispatch')
    IndexFiles.read = read
    old_database = fts.search_database
    @functools.wraps(old_database)
    def database(data, records, match, content_types, deadline):
        if CURRENT is not None:
            CURRENT['records'] = len(records)
            CURRENT['bytes'] = len(data)
            CURRENT['partition_entry_remaining'] = deadline-CLOCK()
        adapter_start = CLOCK()
        event = CURRENT
        try:
            return old_database(data,records,match,content_types,deadline)
        finally:
            if event is not None:
                event['fts_adapter_seconds'] = CLOCK() - adapter_start
            mark('post_partition')
    fts.search_database = database

    # Public timer brackets validation/lock acquisition, result delivery and close.
    # Diagnostic persistence happens only after the public timer stops.
    from contextlib import contextmanager
    old_public = ContentIndex.search_lexical
    @contextmanager
    @functools.wraps(old_public)
    def public(self, *a, **kw):
        begin = CLOCK()
        prior_count = len(EVENTS)
        event = None
        try:
            with old_public(self, *a, **kw) as page:
                event = EVENTS[-1] if len(EVENTS) > prior_count else None
                if event is not None:
                    event['public_prepare_seconds'] = CLOCK() - begin
                yield page
            if event is not None:
                event['public_outcome'] = 'ok'
        except Exception as exc:
            event = EVENTS[-1] if len(EVENTS) > prior_count else None
            if event is not None:
                event['public_outcome'] = type(exc).__name__
                event['public_fts_error_contract_ok'] = (
                    type(exc).__name__ == 'Unavailable'
                    and str(exc) == 'FTS query/database unavailable'
                    and exc.__suppress_context__ is True
                    and isinstance(exc.__context__, sqlite3.Error)
                )
                event['public_native_context_code'] = getattr(exc.__context__, 'sqlite_errorcode', None)
            raise
        finally:
            if event is not None:
                event['public_total_seconds'] = CLOCK() - begin
                event['search_ordinal'] = len(EVENTS)
            save()
    ContentIndex.search_lexical = public
    old_export = ContentIndex._export
    @functools.wraps(old_export)
    def export(self, *a, **kw):
        begin = CLOCK()
        event = CURRENT
        try:
            return old_export(self, *a, **kw)
        finally:
            if event is not None:
                event['live_projection_seconds'] = event.get('live_projection_seconds', 0) + CLOCK() - begin
    ContentIndex._export = export
