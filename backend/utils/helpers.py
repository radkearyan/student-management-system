def dict_from_row(row):
    """Convert a sqlite3.Row object to a standard dict."""
    return dict(row) if row else None
