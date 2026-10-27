# Set up MCP credentials

Log the MCP server in to your NYT Cooking account.

??? info "Prerequisites"

    [Install the MCP server](install.md) first.

## Find your cookie

Sign in to [cooking.nytimes.com](https://cooking.nytimes.com/), then copy the value of the `NYT-S` cookie from your browser's developer tools:

=== "Chrome"

    Open DevTools, then go to **Application** > **Cookies** > `https://cooking.nytimes.com`. See [View, add, edit, and delete cookies](https://developer.chrome.com/docs/devtools/application/cookies).

=== "Firefox"

    Open the Web Developer Tools, then go to **Storage** > **Cookies** > `https://cooking.nytimes.com`. See [Storage Inspector](https://firefox-source-docs.mozilla.org/devtools-user/storage_inspector/).

=== "Safari"

    Turn on [features for web developers](https://developer.apple.com/documentation/safari-developer-tools/enabling-developer-features), open Web Inspector, then go to **Storage** > **Cookies**. See [Inspecting overview](https://support.apple.com/guide/safari-developer/dev1a8227029/mac).

## Log in

Ask your assistant to log in to NYT Cooking and paste the cookie when it asks. It calls [`auth_login`](../../reference/mcp.md#auth_login), which checks the cookie with NYT and saves it to your system keychain.

To check that you're logged in, ask your assistant, which calls [`get_auth_status`](../../reference/mcp.md#get_auth_status).

??? tip "Using the Python client too?"

    The MCP server and the Python client share the same saved login. Once you log in here, the [Python client](../python/credentials.md) uses the same cookie from your system keychain.
