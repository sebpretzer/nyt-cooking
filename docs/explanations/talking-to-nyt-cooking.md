# How nyt-cooking talks to NYT Cooking

nyt-cooking calls the same endpoints the NYT Cooking website uses, the way a browser signed in to your account would.

## Unofficial APIs

These APIs aren't officially supported by NYT, as the [disclaimer](../index.md) says, so NYT can change them without notice. To look like the website, nyt-cooking sends the headers the web app sends, including a browser `User-Agent`. You can override the `User-Agent`, the URLs and the GraphQL headers through [`Settings`](../reference/settings.md).

## Where requests go

nyt-cooking talks to three NYT endpoints:

- **NYT Cooking's REST API** at `cooking.nytimes.com`, for recipes, search, the recipe box, folders and recently viewed recipes.
- **NYT's GraphQL API** at `samizdat-graphql.nytimes.com`, for recipe comments. [`get_recipe_comments`](../reference/client.md#nyt_cooking.client.client.Client.get_recipe_comments) sends it a `communityComments` query. GraphQL can return errors in the response body, so the client checks the body first and raises a `ValueError` with NYT's message.
- **NYT's identity endpoint** at `a.nytimes.com`, for the [subscription check](#the-subscription-check).

The GraphQL API also expects an `nyt-token` header. It's the public key the website sends to every visitor, so it isn't a secret and isn't tied to your account.

## Signing in with a cookie

nyt-cooking signs in with the `NYT-S` session cookie from a browser signed in to cooking.nytimes.com. It takes only the cookie, not your username or password, and sends it with every request. To find and save yours, see the credentials guides for [Python](../guides/python/credentials.md) and [MCP](../guides/mcp/credentials.md).

A cookie passed straight to `Client` is used for that client only and never saved. If no cookie is passed, set, or saved, loading `Settings` raises a `ValidationError` before any request is made.

## The subscription check

Before anything else, creating a `Client` asks NYT's identity endpoint who the cookie belongs to. It raises a `ValueError` if:

- NYT doesn't recognise the cookie, usually because it has expired.
- The account has no active subscription that includes NYT Cooking.

This means a `Client` only exists for a signed-in subscriber, and a bad cookie fails right away instead of partway through a call. The same check returns your NYT account ID, which some recipe box and folder endpoints need in their URL.

`Settings.save_credentials` saves a cookie without checking it, so create a `Client` with it first. The MCP server's `auth_login` runs the check before it saves.
