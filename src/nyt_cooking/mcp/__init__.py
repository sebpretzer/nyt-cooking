try:
    import fastmcp  # noqa: F401
except ImportError as e:
    msg = (
        "nyt_cooking.mcp requires fastmcp, which is in the 'mcp' dependency "
        "group. Install it with `uv sync --group mcp`."
    )
    raise ImportError(msg) from e
