# Code conventions

nyt-cooking follows a set of conventions so that its interface is consistent and predictable. All code changes should follow them. They mainly cover how [the client and the MCP server are kept apart](#client-and-mcp-server), the [Pydantic models](#pydantic-models) and the [client structure](#client-structure).

## Client and MCP server

The package is split into two loosely coupled submodules with a unidirectional dependency:

```text
nyt_cooking
├── client
│   ├── client.py
│   ├── settings.py
│   ├── models
│   └── queries
└── mcp
    └── server.py
```

- `nyt_cooking.client` talks to NYT Cooking. It knows nothing about MCP and never imports from `nyt_cooking.mcp`.
- `nyt_cooking.mcp` is a thin layer on top of the client. It imports the `Client` and its models, and nothing in it talks to NYT Cooking directly.

This lets the client work on its own: `fastmcp` is only needed for the MCP server, so it's in the optional `mcp` extra, which [installing the MCP server](../guides/mcp/install.md) includes.

## Pydantic models

### When to use Pydantic models

All data going in or out of the library uses [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/). Every NYT Cooking response is validated into a model, and inputs with more than a couple of values, such as search criteria, are models too. Settings use [Pydantic settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).

The MCP server relies on the same models. FastMCP builds each tool's input and output schemas from them, so assistants see the same fields and descriptions as Python users.

### Model organization

All models live in `nyt_cooking/client/models`, one file per area of NYT Cooking. Types shared across areas, such as `Duration` and `Pagination`, go in `base.py`.

```text
nyt_cooking/client/models
├── auth.py
├── base.py
├── comments.py
├── folders.py
├── recipes.py
└── search.py
```

Every response model subclasses `CookingModel`, a translation layer between NYT's responses and the library, so the rest of the code works with clean Python objects instead of NYT's raw data.

### Naming models

Models are named after the NYT Cooking object they hold, without a request method or API version:

- `Recipe()`
- `Folder()`
- `Comment()`

Collections use the plural, or a name for what they hold:

- `Folders()`
- `Comments()`
- `RecipeBox()`

Inputs are named for what they describe, such as `SearchCriteria()`.

## Client structure

Most of the library's functionality is in the [`Client`](../reference/client.md) class. It manages the connection to NYT Cooking, handles signing in, and gives a high-level interface to the API.

### Settings

The `Client` loads its configuration from the [`Settings`](../reference/settings.md) class. Settings that every part of the client uses live at the top level. Settings that only one API needs are kept separate, so each is used in one place only and the APIs stay loosely coupled.

### Function naming

Functions are named with a verb followed by the object they act on, such as `get_recipe`, `search_recipes` or `rename_folder`. A function that collects results across several pages has the same name plus `_paginated`, such as `search_recipes_paginated`.

### Function inputs and outputs

IDs are their own arguments and accept an `int` or a `str`. Inputs with several related values are passed as a single model, such as `criteria` for searches.

Every function that calls NYT Cooking returns a model.
