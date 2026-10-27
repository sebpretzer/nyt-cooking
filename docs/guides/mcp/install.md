# Install the MCP server

Install the NYT Cooking MCP server and connect it to an AI assistant.

## Prerequisites

- A paid [NYT Cooking](https://cooking.nytimes.com/) subscription
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- An AI assistant that supports MCP servers

## Connect your assistant

Every assistant below starts the server with the same command:

```bash
uvx --from "nyt-cooking[mcp] @ git+https://github.com/sebpretzer/nyt-cooking" nyt-cooking-mcp
```

=== "Claude Code"

    ```bash
    claude mcp add nyt-cooking -- uvx --from "nyt-cooking[mcp] @ git+https://github.com/sebpretzer/nyt-cooking" nyt-cooking-mcp
    ```

=== "Claude Desktop"

    ```json title="claude_desktop_config.json"
    {
      "mcpServers": {
        "nyt-cooking": {
          "command": "uvx",
          "args": [
            "--from",
            "nyt-cooking[mcp] @ git+https://github.com/sebpretzer/nyt-cooking",
            "nyt-cooking-mcp"
          ]
        }
      }
    }
    ```

=== "VS Code"

    ```bash
    code --add-mcp '{"name":"nyt-cooking","type":"stdio","command":"uvx","args":["--from","nyt-cooking[mcp] @ git+https://github.com/sebpretzer/nyt-cooking","nyt-cooking-mcp"]}'
    ```

=== "Codex CLI"

    ```bash
    codex mcp add nyt-cooking -- uvx --from "nyt-cooking[mcp] @ git+https://github.com/sebpretzer/nyt-cooking" nyt-cooking-mcp
    ```

=== "Gemini CLI"

    ```bash
    gemini mcp add -s user nyt-cooking uvx -- --from "nyt-cooking[mcp] @ git+https://github.com/sebpretzer/nyt-cooking" nyt-cooking-mcp
    ```
