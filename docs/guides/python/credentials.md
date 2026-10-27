# Set up Python credentials

Give the Python client your NYT Cooking cookie.

??? info "Prerequisites"

    [Install the Python client](install.md) first.

## Find your cookie

Sign in to [cooking.nytimes.com](https://cooking.nytimes.com/), then copy the value of the `NYT-S` cookie from your browser's developer tools:

=== "Chrome"

    Open DevTools, then go to **Application** > **Cookies** > `https://cooking.nytimes.com`. See [View, add, edit, and delete cookies](https://developer.chrome.com/docs/devtools/application/cookies).

=== "Firefox"

    Open the Web Developer Tools, then go to **Storage** > **Cookies** > `https://cooking.nytimes.com`. See [Storage Inspector](https://firefox-source-docs.mozilla.org/devtools-user/storage_inspector/).

=== "Safari"

    Turn on [features for web developers](https://developer.apple.com/documentation/safari-developer-tools/enabling-developer-features), open Web Inspector, then go to **Storage** > **Cookies**. See [Inspecting overview](https://support.apple.com/guide/safari-developer/dev1a8227029/mac).

## Save the cookie

Save it to your system keychain:

```python
from nyt_cooking.client import Settings

Settings.save_credentials("0^CB...")
```

Or set it in a `.env` file in your project:

```bash title=".env"
NYT_COOKING_COOKIE="0^CB..."
```

??? tip "Using the MCP server too?"

    The Python client and the MCP server share the same saved login. If you use both, we recommend saving the cookie to your system keychain rather than a `.env` file. It's the most secure option, and it's where the [MCP server](../mcp/credentials.md) saves its login.
