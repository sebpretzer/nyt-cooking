try:
    import fastmcp  # noqa: F401
except ImportError as e:
    msg = (
        "nyt_cooking.mcp requires fastmcp, which is in the 'mcp' extra. Install "
        "it with `uv add 'nyt-cooking[mcp]'`."
    )
    raise ImportError(msg) from e
