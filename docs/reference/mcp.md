# MCP Tools

<style>
:root,
[data-md-color-scheme="default"] {
  --doc-symbol-tool-fg-color: #1b7c83;
  --doc-symbol-server-fg-color: var(--doc-symbol-module-fg-color);
}

[data-md-color-scheme="slate"] {
  --doc-symbol-tool-fg-color: #56d4dd;
  --doc-symbol-server-fg-color: var(--doc-symbol-module-fg-color);
}

a code.doc-symbol-tool,
code.doc-symbol-tool {
  color: var(--doc-symbol-tool-fg-color);
}

.md-content code.doc-symbol-tool::after {
  content: "tool";
}

.md-sidebar code.doc-symbol-tool::after {
  content: "t";
}

a code.doc-symbol-server,
code.doc-symbol-server {
  color: var(--doc-symbol-server-fg-color);
}

.md-content code.doc-symbol-server::after {
  content: "server";
}

.md-sidebar code.doc-symbol-server::after {
  content: "srv";
}
</style>

## <code class="doc-symbol doc-symbol-heading doc-symbol-server"></code> nyt-cooking { #nyt-cooking data-toc-label='<code class="doc-symbol doc-symbol-toc doc-symbol-server"></code>&nbsp;nyt-cooking' }

Every NYT Cooking tool needs the user to be logged in with an NYT Cooking subscription. If a tool fails because they are not, ask the user for the `NYT-S` cookie from a browser signed in to cooking.nytimes.com with an NYT Cooking subscription, and call `auth_login`.

<span class="doc-section-title">Tools:</span>

| Name | Description |
| --- | --- |
| [`get_search_filters`](#get_search_filters) | List the tags and time limits worth filtering a recipe search by. |
| [`search_recipes`](#search_recipes) | Search NYT Cooking for recipes. |
| [`get_recipe`](#get_recipe) | Get a full NYT Cooking recipe. |
| [`get_recipe_comments`](#get_recipe_comments) | Get the public reader comments on an NYT Cooking recipe. |
| [`get_recipe_box`](#get_recipe_box) | List the recipes the user has saved to their NYT Cooking recipe box. |
| [`get_recently_viewed`](#get_recently_viewed) | List the recipes the user has recently viewed on NYT Cooking. |
| [`get_folders`](#get_folders) | List the folders in the user's NYT Cooking recipe box. |
| [`get_folder_recipes`](#get_folder_recipes) | List every recipe in a folder of the user's NYT Cooking recipe box. |
| [`add_folder`](#add_folder) | Add an empty folder to the user's NYT Cooking recipe box. |
| [`rename_folder`](#rename_folder) | Rename a folder in the user's NYT Cooking recipe box. |
| [`remove_folder`](#remove_folder) | Remove a folder from the user's NYT Cooking recipe box, deleting it. |
| [`get_recipe_save_status`](#get_recipe_save_status) | Check whether a recipe is saved to the user's NYT Cooking recipe box. |
| [`add_recipe`](#add_recipe) | Add a recipe to the user's NYT Cooking recipe box, or to a folder in it. |
| [`remove_recipe`](#remove_recipe) | Remove a recipe from the user's NYT Cooking recipe box, or from one folder. |
| [`auth_login`](#auth_login) | Check the user's NYT Cooking cookie and save it if NYT accepts it. |
| [`auth_logout`](#auth_logout) | Remove the saved NYT Cooking cookie. |
| [`get_auth_status`](#get_auth_status) | Check with NYT whether the user is logged in with an NYT Cooking subscription. |

### <code class="doc-symbol doc-symbol-heading doc-symbol-tool"></code> get_search_filters <span class="doc doc-labels"><small class="doc doc-label doc-label-read-only"><code>read-only</code></small></span> { #get_search_filters data-toc-label='<code class="doc-symbol doc-symbol-toc doc-symbol-tool"></code>&nbsp;get_search_filters' }

<div class="doc-signature highlight"><pre><span></span><code><span class="n">get_search_filters</span><span class="p">(</span>
    <span class="n">query</span><span class="p">:</span> <span class="n">string</span> <span class="o">=</span> <span class="s2">""</span><span class="p">,</span>
    <span class="n">criteria</span><span class="p">:</span> <span class="nb">object</span> <span class="o">|</span> <span class="n">null</span> <span class="o">=</span> <span class="n">null</span><span class="p">,</span>
<span class="p">)</span> <span class="o">-&gt;</span> <span class="n"><autoref identifier="nyt_cooking.client.models.search.SearchFilters" optional>SearchFilters</autoref></span>
</code></pre></div>

List the tags and time limits worth filtering a recipe search by.

Call this before filtering `search_recipes`. It takes the same `query` as
`search_recipes`, and the counts are for that query, so only tags with at
least one result are returned. An empty `query` returns every tag NYT Cooking
has.

Tag names are returned exactly as `search_recipes` expects them, such as
`five ingredient` or `sheet-pan`. Pass `criteria` to see what is left once it
is applied: counts shrink as filters are added, so use this to check that
another tag would still leave results.

Also returns the number of results within each total-time limit (in minutes)
and the number that are top rated.

<span class="doc-section-title">Parameters:</span>

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `query` | <code>string</code> | Search terms, such as a dish, ingredient or cuisine. | <code>&quot;&quot;</code> |
| `criteria` | <code>object &#124; null</code> | Limits already chosen, such as tags from an earlier call. Leave unset on the first call. | <code>null</code> |
| `criteria.tags` | <code>array of string</code> | Tags every result must have, such as `healthy`, `dinner` or `one pot`, from `get_search_filters`. Only those names match: a misspelled or invented tag matches nothing, with no error, so 0 results can mean a bad tag. Tags combine with AND, so each one narrows the results | |
| `criteria.max_minutes` | <code>integer &#124; null</code> | Longest total time in minutes, inclusive. There is no minimum | <code>null</code> |
| `criteria.top_rated` | <code>boolean</code> | Whether to keep only top-rated recipes | <code>false</code> |
| `criteria.sort` | <code>&quot;rating&quot; &#124; &quot;firstPublished&quot; &#124; null</code> | `rating` for highest rated or `firstPublished` for most recent. Leave unset for best match | <code>null</code> |

<span class="doc-section-title">Returns:</span>

| Type | Description |
| --- | --- |
| [`SearchFilters`][nyt_cooking.client.models.search.SearchFilters] | The tags, time limits and top-rated count, each with how many results it leaves. |

<details markdown>
<summary>Show input schema:</summary>

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "default": "",
      "type": "string",
      "description": "Search terms, such as a dish, ingredient or cuisine."
    },
    "criteria": {
      "anyOf": [
        {
          "additionalProperties": false,
          "description": "Limits that narrow a recipe search.\n\nLeave a field unset to apply no limit of that kind. Unknown fields are\nrejected, so a misspelled limit is an error instead of being ignored.",
          "properties": {
            "tags": {
              "description": "Tags every result must have, such as `healthy`, `dinner` or `one pot`, from `get_search_filters`. Only those names match: a misspelled or invented tag matches nothing, with no error, so 0 results can mean a bad tag. Tags combine with AND, so each one narrows the results",
              "items": {
                "type": "string"
              },
              "type": "array"
            },
            "max_minutes": {
              "anyOf": [
                {
                  "minimum": 0,
                  "type": "integer"
                },
                {
                  "type": "null"
                }
              ],
              "default": null,
              "description": "Longest total time in minutes, inclusive. There is no minimum"
            },
            "top_rated": {
              "default": false,
              "description": "Whether to keep only top-rated recipes",
              "type": "boolean"
            },
            "sort": {
              "anyOf": [
                {
                  "description": "How NYT Cooking orders search results.\n\nLeave the sort unset for best match, which is the default.",
                  "enum": [
                    "rating",
                    "firstPublished"
                  ],
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "default": null,
              "description": "`rating` for highest rated or `firstPublished` for most recent. Leave unset for best match"
            }
          },
          "type": "object"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Limits already chosen, such as tags from\nan earlier call. Leave unset on the first call."
    }
  }
}
```

</details>

<details markdown>
<summary>Show output schema:</summary>

```json
{
  "description": "The filters available for a search, with how many results each leaves.\n\nThe counts are for the query and filters that were searched, so they shrink\nas filters are added. Tags with no results are left out, as is `drinks`, which\nNYT counts but matches nothing when used as a tag.",
  "properties": {
    "query": {
      "description": "The search query",
      "type": "string"
    },
    "total": {
      "description": "Number of results for the query and filters searched",
      "type": "integer"
    },
    "tags": {
      "additionalProperties": {
        "type": "integer"
      },
      "description": "Results left by each tag, keyed by the exact name to pass as a search tag, such as `one pot` or `sheet-pan`",
      "type": "object"
    },
    "cook_times": {
      "additionalProperties": {
        "type": "integer"
      },
      "description": "Results left by each total-time limit, keyed by minutes",
      "type": "object"
    },
    "top_rated": {
      "default": 0,
      "description": "Results left by limiting the search to top-rated recipes",
      "type": "integer"
    }
  },
  "required": [
    "query",
    "total",
    "tags"
  ],
  "type": "object"
}
```

</details>

<details class="mkdocstrings-source" markdown>
<summary>Source code in <code>src/nyt_cooking/mcp/server.py</code></summary>

```python linenums="48"
@mcp.tool(title="Get Search Filters", annotations={"readOnlyHint": True})
def get_search_filters(
    query: str = "",
    criteria: SearchCriteria | None = None,
    client: Client = SessionClient,
) -> SearchFilters:
    """List the tags and time limits worth filtering a recipe search by.

    Call this before filtering `search_recipes`. It takes the same `query` as
    `search_recipes`, and the counts are for that query, so only tags with at
    least one result are returned. An empty `query` returns every tag NYT Cooking
    has.

    Tag names are returned exactly as `search_recipes` expects them, such as
    `five ingredient` or `sheet-pan`. Pass `criteria` to see what is left once it
    is applied: counts shrink as filters are added, so use this to check that
    another tag would still leave results.

    Also returns the number of results within each total-time limit (in minutes)
    and the number that are top rated.

    Args:
        query (str): Search terms, such as a dish, ingredient or cuisine.
        criteria (SearchCriteria | None): Limits already chosen, such as tags from
            an earlier call. Leave unset on the first call.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        SearchFilters: The tags, time limits and top-rated count, each with how
            many results it leaves.
    """
    return client.search_filters(query, criteria)
```

</details>

### <code class="doc-symbol doc-symbol-heading doc-symbol-tool"></code> search_recipes <span class="doc doc-labels"><small class="doc doc-label doc-label-read-only"><code>read-only</code></small></span> { #search_recipes data-toc-label='<code class="doc-symbol doc-symbol-toc doc-symbol-tool"></code>&nbsp;search_recipes' }

<div class="doc-signature highlight"><pre><span></span><code><span class="n">search_recipes</span><span class="p">(</span>
    <span class="n">query</span><span class="p">:</span> <span class="n">string</span><span class="p">,</span>
    <span class="n">max_results</span><span class="p">:</span> <span class="n">integer</span> <span class="o">=</span> <span class="mi">48</span><span class="p">,</span>
    <span class="n">criteria</span><span class="p">:</span> <span class="nb">object</span> <span class="o">|</span> <span class="n">null</span> <span class="o">=</span> <span class="n">null</span><span class="p">,</span>
<span class="p">)</span> <span class="o">-&gt;</span> <span class="n"><autoref identifier="nyt_cooking.client.models.search.SearchResults" optional>SearchResults</autoref></span>
</code></pre></div>

Search NYT Cooking for recipes.

Returns each match's ID, title, author and total time, plus the total number
of matches. Pass an ID to `get_recipe` for ingredients and steps.

To filter, call `get_search_filters` with the same `query` first and use the
tag names it returns in `criteria`. Tags combine with AND, so each one narrows
the results, and a misspelled or invented tag returns 0 results rather than an
error.

NYT stops at 960 results, however many match, so `max_results` above that
returns no more.

<span class="doc-section-title">Parameters:</span>

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `query` | <code>string</code> | Search terms, such as a dish, ingredient or cuisine. | *required* |
| `max_results` | <code>integer</code> | Most recipes to return. | <code>48</code> |
| `criteria` | <code>object &#124; null</code> | Tags, a time limit, top-rated only, sort order to narrow by. Leave unset for no limits. | <code>null</code> |
| `criteria.tags` | <code>array of string</code> | Tags every result must have, such as `healthy`, `dinner` or `one pot`, from `get_search_filters`. Only those names match: a misspelled or invented tag matches nothing, with no error, so 0 results can mean a bad tag. Tags combine with AND, so each one narrows the results | |
| `criteria.max_minutes` | <code>integer &#124; null</code> | Longest total time in minutes, inclusive. There is no minimum | <code>null</code> |
| `criteria.top_rated` | <code>boolean</code> | Whether to keep only top-rated recipes | <code>false</code> |
| `criteria.sort` | <code>&quot;rating&quot; &#124; &quot;firstPublished&quot; &#124; null</code> | `rating` for highest rated or `firstPublished` for most recent. Leave unset for best match | <code>null</code> |

<span class="doc-section-title">Returns:</span>

| Type | Description |
| --- | --- |
| [`SearchResults`][nyt_cooking.client.models.search.SearchResults] | The matching recipes. |

<details markdown>
<summary>Show input schema:</summary>

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "description": "Search terms, such as a dish, ingredient or cuisine."
    },
    "max_results": {
      "default": 48,
      "type": "integer",
      "description": "Most recipes to return."
    },
    "criteria": {
      "anyOf": [
        {
          "additionalProperties": false,
          "description": "Limits that narrow a recipe search.\n\nLeave a field unset to apply no limit of that kind. Unknown fields are\nrejected, so a misspelled limit is an error instead of being ignored.",
          "properties": {
            "tags": {
              "description": "Tags every result must have, such as `healthy`, `dinner` or `one pot`, from `get_search_filters`. Only those names match: a misspelled or invented tag matches nothing, with no error, so 0 results can mean a bad tag. Tags combine with AND, so each one narrows the results",
              "items": {
                "type": "string"
              },
              "type": "array"
            },
            "max_minutes": {
              "anyOf": [
                {
                  "minimum": 0,
                  "type": "integer"
                },
                {
                  "type": "null"
                }
              ],
              "default": null,
              "description": "Longest total time in minutes, inclusive. There is no minimum"
            },
            "top_rated": {
              "default": false,
              "description": "Whether to keep only top-rated recipes",
              "type": "boolean"
            },
            "sort": {
              "anyOf": [
                {
                  "description": "How NYT Cooking orders search results.\n\nLeave the sort unset for best match, which is the default.",
                  "enum": [
                    "rating",
                    "firstPublished"
                  ],
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "default": null,
              "description": "`rating` for highest rated or `firstPublished` for most recent. Leave unset for best match"
            }
          },
          "type": "object"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Tags, a time limit, top-rated only, sort\norder to narrow by. Leave unset for no limits."
    }
  },
  "required": [
    "query"
  ]
}
```

</details>

<details markdown>
<summary>Show output schema:</summary>

```json
{
  "description": "Recipes matching a search query.",
  "properties": {
    "query": {
      "description": "The search query",
      "type": "string"
    },
    "results": {
      "description": "Matching recipes",
      "items": {
        "description": "A recipe returned by a search.",
        "properties": {
          "id": {
            "description": "NYT Cooking recipe ID, such as `1023921`",
            "type": "integer"
          },
          "name": {
            "description": "Recipe title",
            "type": "string"
          },
          "byline": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "default": null,
            "description": "Recipe author(s)"
          },
          "total_time": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "default": null,
            "description": "Total time, such as `1 1/2 hours`"
          },
          "image": {
            "anyOf": [
              {
                "description": "A recipe image, available in several crops.",
                "properties": {
                  "caption": {
                    "anyOf": [
                      {
                        "type": "string"
                      },
                      {
                        "type": "null"
                      }
                    ],
                    "default": null,
                    "description": "Image caption"
                  },
                  "credit": {
                    "anyOf": [
                      {
                        "type": "string"
                      },
                      {
                        "type": "null"
                      }
                    ],
                    "default": null,
                    "description": "Photographer credit"
                  },
                  "crops": {
                    "description": "Available sizes of the image",
                    "items": {
                      "description": "One size of a recipe image.",
                      "properties": {
                        "name": {
                          "description": "NYT's name for the crop, such as `superJumbo`",
                          "type": "string"
                        },
                        "url": {
                          "description": "URL of the image file",
                          "type": "string"
                        },
                        "width": {
                          "description": "Width in pixels",
                          "type": "integer"
                        },
                        "height": {
                          "description": "Height in pixels",
                          "type": "integer"
                        }
                      },
                      "required": [
                        "name",
                        "url",
                        "width",
                        "height"
                      ],
                      "type": "object"
                    },
                    "type": "array"
                  }
                },
                "type": "object"
              },
              {
                "type": "null"
              }
            ],
            "default": null,
            "description": "Recipe photo"
          },
          "has_video": {
            "default": false,
            "description": "Whether a video exists",
            "type": "boolean"
          },
          "url": {
            "description": "Recipe page on cooking.nytimes.com.",
            "readOnly": true,
            "type": "string"
          }
        },
        "required": [
          "id",
          "name",
          "url"
        ],
        "type": "object"
      },
      "type": "array"
    },
    "pagination": {
      "description": "Position within all matches",
      "properties": {
        "total": {
          "description": "Total number of results across all pages",
          "type": "integer"
        },
        "page": {
          "description": "This page's number, starting at 1",
          "type": "integer"
        },
        "max_page": {
          "description": "Number of the last page",
          "type": "integer"
        }
      },
      "required": [
        "total",
        "page",
        "max_page"
      ],
      "type": "object"
    }
  },
  "required": [
    "query",
    "pagination"
  ],
  "type": "object"
}
```

</details>

<details class="mkdocstrings-source" markdown>
<summary>Source code in <code>src/nyt_cooking/mcp/server.py</code></summary>

```python linenums="82"
@mcp.tool(title="Search Recipes", annotations={"readOnlyHint": True})
def search_recipes(
    query: str,
    max_results: int = 48,
    criteria: SearchCriteria | None = None,
    client: Client = SessionClient,
) -> SearchResults:
    """Search NYT Cooking for recipes.

    Returns each match's ID, title, author and total time, plus the total number
    of matches. Pass an ID to `get_recipe` for ingredients and steps.

    To filter, call `get_search_filters` with the same `query` first and use the
    tag names it returns in `criteria`. Tags combine with AND, so each one narrows
    the results, and a misspelled or invented tag returns 0 results rather than an
    error.

    NYT stops at 960 results, however many match, so `max_results` above that
    returns no more.

    Args:
        query (str): Search terms, such as a dish, ingredient or cuisine.
        max_results (int): Most recipes to return.
        criteria (SearchCriteria | None): Tags, a time limit, top-rated only, sort
            order to narrow by. Leave unset for no limits.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        SearchResults: The matching recipes.
    """
    return client.search_recipes_paginated(
        query,
        max_results=max_results,
        criteria=criteria,
    )
```

</details>

### <code class="doc-symbol doc-symbol-heading doc-symbol-tool"></code> get_recipe <span class="doc doc-labels"><small class="doc doc-label doc-label-read-only"><code>read-only</code></small></span> { #get_recipe data-toc-label='<code class="doc-symbol doc-symbol-toc doc-symbol-tool"></code>&nbsp;get_recipe' }

<div class="doc-signature highlight"><pre><span></span><code><span class="n">get_recipe</span><span class="p">(</span><span class="n">recipe_id</span><span class="p">:</span> <span class="n">integer</span><span class="p">)</span> <span class="o">-&gt;</span> <span class="n"><autoref identifier="nyt_cooking.client.models.recipes.Recipe" optional>Recipe</autoref></span>
</code></pre></div>

Get a full NYT Cooking recipe.

Includes the ingredients and steps (both grouped under any headings the recipe
uses), times, servings, rating and introduction.

<span class="doc-section-title">Parameters:</span>

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `recipe_id` | <code>integer</code> | NYT Cooking recipe ID, from `search_recipes`, `get_recipe_box` or a recipe URL such as `/recipes/1019049-...`. | *required* |

<span class="doc-section-title">Returns:</span>

| Type | Description |
| --- | --- |
| [`Recipe`][nyt_cooking.client.models.recipes.Recipe] | The recipe. |

<details markdown>
<summary>Show input schema:</summary>

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "recipe_id": {
      "type": "integer",
      "description": "NYT Cooking recipe ID, from `search_recipes`,\n`get_recipe_box` or a recipe URL such as `/recipes/1019049-...`."
    }
  },
  "required": [
    "recipe_id"
  ]
}
```

</details>

<details markdown>
<summary>Show output schema:</summary>

```json
{
  "description": "A full recipe, including its ingredients and steps.",
  "properties": {
    "id": {
      "description": "NYT Cooking recipe ID, such as `1019049`",
      "type": "integer"
    },
    "name": {
      "description": "Recipe title",
      "type": "string"
    },
    "byline": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Recipe author(s)"
    },
    "url": {
      "description": "Recipe page on cooking.nytimes.com",
      "type": "string"
    },
    "servings": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Yield, such as `2 to 4 servings`"
    },
    "total_time": {
      "anyOf": [
        {
          "description": "A length of time, as NYT both displays and measures it.",
          "properties": {
            "display": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "default": null,
              "description": "Human-readable time, such as `1 1/2 hours`"
            },
            "minutes": {
              "anyOf": [
                {
                  "type": "number"
                },
                {
                  "type": "null"
                }
              ],
              "default": null,
              "description": "Time in minutes"
            }
          },
          "type": "object"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Total time to make the recipe"
    },
    "image": {
      "anyOf": [
        {
          "description": "A recipe image, available in several crops.",
          "properties": {
            "caption": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "default": null,
              "description": "Image caption"
            },
            "credit": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "default": null,
              "description": "Photographer credit"
            },
            "crops": {
              "description": "Available sizes of the image",
              "items": {
                "description": "One size of a recipe image.",
                "properties": {
                  "name": {
                    "description": "NYT's name for the crop, such as `superJumbo`",
                    "type": "string"
                  },
                  "url": {
                    "description": "URL of the image file",
                    "type": "string"
                  },
                  "width": {
                    "description": "Width in pixels",
                    "type": "integer"
                  },
                  "height": {
                    "description": "Height in pixels",
                    "type": "integer"
                  }
                },
                "required": [
                  "name",
                  "url",
                  "width",
                  "height"
                ],
                "type": "object"
              },
              "type": "array"
            }
          },
          "type": "object"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Recipe photo"
    },
    "has_video": {
      "default": false,
      "description": "Whether a video exists",
      "type": "boolean"
    },
    "prep_time": {
      "anyOf": [
        {
          "description": "A length of time, as NYT both displays and measures it.",
          "properties": {
            "display": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "default": null,
              "description": "Human-readable time, such as `1 1/2 hours`"
            },
            "minutes": {
              "anyOf": [
                {
                  "type": "number"
                },
                {
                  "type": "null"
                }
              ],
              "default": null,
              "description": "Time in minutes"
            }
          },
          "type": "object"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Preparation time"
    },
    "cook_time": {
      "anyOf": [
        {
          "description": "A length of time, as NYT both displays and measures it.",
          "properties": {
            "display": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "default": null,
              "description": "Human-readable time, such as `1 1/2 hours`"
            },
            "minutes": {
              "anyOf": [
                {
                  "type": "number"
                },
                {
                  "type": "null"
                }
              ],
              "default": null,
              "description": "Time in minutes"
            }
          },
          "type": "object"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Cooking time"
    },
    "rating": {
      "anyOf": [
        {
          "description": "Average reader rating of a recipe.",
          "properties": {
            "value": {
              "description": "Average rating out of 5",
              "type": "number"
            },
            "total": {
              "description": "Number of ratings",
              "type": "integer"
            }
          },
          "required": [
            "value",
            "total"
          ],
          "type": "object"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Average reader rating"
    },
    "description": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "The recipe's introduction"
    },
    "ingredients": {
      "description": "Ingredients, grouped by heading",
      "items": {
        "description": "Ingredients under one heading of a recipe.",
        "properties": {
          "name": {
            "default": "",
            "description": "Heading, such as `For the topping`; empty for the main list",
            "type": "string"
          },
          "ingredients": {
            "description": "Ingredients under this heading",
            "items": {
              "description": "A single ingredient line.",
              "properties": {
                "quantity": {
                  "default": "",
                  "description": "Amount, such as `4`; empty when part of the text",
                  "type": "string"
                },
                "text": {
                  "description": "The rest of the line, such as `ounces thick-cut bacon`",
                  "type": "string"
                }
              },
              "required": [
                "text"
              ],
              "type": "object"
            },
            "type": "array"
          }
        },
        "type": "object"
      },
      "type": "array"
    },
    "steps": {
      "description": "Method, grouped by heading",
      "items": {
        "description": "Steps under one heading of a recipe.",
        "properties": {
          "name": {
            "default": "",
            "description": "Heading, such as `For the dough`; empty for the main method",
            "type": "string"
          },
          "steps": {
            "description": "Steps under this heading",
            "items": {
              "description": "A single numbered step of a recipe.",
              "properties": {
                "number": {
                  "description": "Step number",
                  "type": "integer"
                },
                "description": {
                  "description": "What to do in this step",
                  "type": "string"
                }
              },
              "required": [
                "number",
                "description"
              ],
              "type": "object"
            },
            "type": "array"
          }
        },
        "type": "object"
      },
      "type": "array"
    }
  },
  "required": [
    "id",
    "name",
    "url"
  ],
  "type": "object"
}
```

</details>

<details class="mkdocstrings-source" markdown>
<summary>Source code in <code>src/nyt_cooking/mcp/server.py</code></summary>

```python linenums="119"
@mcp.tool(title="Get Recipe", annotations={"readOnlyHint": True})
def get_recipe(recipe_id: int, client: Client = SessionClient) -> Recipe:
    """Get a full NYT Cooking recipe.

    Includes the ingredients and steps (both grouped under any headings the recipe
    uses), times, servings, rating and introduction.

    Args:
        recipe_id (int): NYT Cooking recipe ID, from `search_recipes`,
            `get_recipe_box` or a recipe URL such as `/recipes/1019049-...`.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        Recipe: The recipe.
    """
    return client.get_recipe(recipe_id)
```

</details>

### <code class="doc-symbol doc-symbol-heading doc-symbol-tool"></code> get_recipe_comments <span class="doc doc-labels"><small class="doc doc-label doc-label-read-only"><code>read-only</code></small></span> { #get_recipe_comments data-toc-label='<code class="doc-symbol doc-symbol-toc doc-symbol-tool"></code>&nbsp;get_recipe_comments' }

<div class="doc-signature highlight"><pre><span></span><code><span class="n">get_recipe_comments</span><span class="p">(</span>
    <span class="n">recipe_id</span><span class="p">:</span> <span class="n">integer</span><span class="p">,</span>
    <span class="n">max_results</span><span class="p">:</span> <span class="n">integer</span> <span class="o">=</span> <span class="mi">20</span><span class="p">,</span>
    <span class="n">helpful_only</span><span class="p">:</span> <span class="n">boolean</span> <span class="o">=</span> <span class="n">false</span><span class="p">,</span>
<span class="p">)</span> <span class="o">-&gt;</span> <span class="n"><autoref identifier="nyt_cooking.client.models.comments.Comments" optional>Comments</autoref></span>
</code></pre></div>

Get the public reader comments on an NYT Cooking recipe.

Readers use comments to share substitutions, fixes and results, and NYT Cooking
staff sometimes reply to answer questions; their comments are marked
`is_staff`. Each comment includes all of its replies.

Comments come newest first. Set `helpful_only` to get only the comments readers
picked as most helpful, most helpful first, as on the recipe page's "Most
Helpful" tab. `total` counts every comment on the recipe, replies included,
and `helpful_total` the most helpful ones.

<span class="doc-section-title">Parameters:</span>

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `recipe_id` | <code>integer</code> | NYT Cooking recipe ID, from `search_recipes`, `get_recipe_box` or a recipe URL such as `/recipes/1019049-...`. | *required* |
| `max_results` | <code>integer</code> | Most top-level comments to return, replies aside. | <code>20</code> |
| `helpful_only` | <code>boolean</code> | Whether to get only the most helpful comments. | <code>false</code> |

<span class="doc-section-title">Returns:</span>

| Type | Description |
| --- | --- |
| [`Comments`][nyt_cooking.client.models.comments.Comments] | The comments, with the recipe's comment totals. |

<details markdown>
<summary>Show input schema:</summary>

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "recipe_id": {
      "type": "integer",
      "description": "NYT Cooking recipe ID, from `search_recipes`,\n`get_recipe_box` or a recipe URL such as `/recipes/1019049-...`."
    },
    "max_results": {
      "default": 20,
      "type": "integer",
      "description": "Most top-level comments to return, replies aside."
    },
    "helpful_only": {
      "default": false,
      "type": "boolean",
      "description": "Whether to get only the most helpful comments."
    }
  },
  "required": [
    "recipe_id"
  ]
}
```

</details>

<details markdown>
<summary>Show output schema:</summary>

```json
{
  "$defs": {
    "Comment": {
      "description": "A public comment on a recipe, with any replies to it.",
      "properties": {
        "id": {
          "description": "NYT comment ID, such as `150214450`",
          "type": "string"
        },
        "text": {
          "description": "The comment, with its line breaks",
          "type": "string"
        },
        "author": {
          "$ref": "#/$defs/CommentAuthor",
          "description": "Who wrote the comment"
        },
        "submitted_at": {
          "description": "When the comment was posted",
          "format": "date-time",
          "type": "string"
        },
        "helpful_count": {
          "default": 0,
          "description": "How many readers marked the comment helpful",
          "type": "integer"
        },
        "replies": {
          "description": "Replies to the comment, oldest first",
          "items": {
            "$ref": "#/$defs/Comment"
          },
          "type": "array"
        }
      },
      "required": [
        "id",
        "text",
        "author",
        "submitted_at"
      ],
      "type": "object"
    },
    "CommentAuthor": {
      "description": "Who wrote a recipe comment, as they chose to sign it.",
      "properties": {
        "name": {
          "description": "Display name",
          "type": "string"
        },
        "location": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Stated location"
        },
        "title": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Job title, given for NYT staff"
        },
        "is_staff": {
          "default": false,
          "description": "Whether the author is NYT Cooking staff",
          "type": "boolean"
        }
      },
      "required": [
        "name"
      ],
      "type": "object"
    }
  },
  "description": "A page of a recipe's public comments.\n\nValidates the `communityComments` field of NYT's GraphQL response, where each\ncomment arrives as an edge holding the comment and its replies.\n\n??? example \"Example\"\n    ```python\n    from nyt_cooking.client.models import Comments\n\n    comments = Comments.model_validate(\n        {\n            \"summary\": {\"totalCount\": 1, \"totalReadersPicks\": 0},\n            \"pageInfo\": {\"endCursor\": \"abc\", \"hasNextPage\": False},\n            \"edges\": [\n                {\n                    \"node\": {\n                        \"comment\": {\n                            \"id\": \"1\",\n                            \"text\": \"Less broth.<br/>More mint.\",\n                            \"submittedAt\": \"2026-04-07T20:21:13Z\",\n                            \"recommendedCount\": 3,\n                            \"author\": {\"name\": \"muriel\"},\n                        },\n                        \"replies\": [],\n                    },\n                },\n            ],\n        },\n    )\n    print(comments.comments[0], comments.next_cursor)\n    ```\n\n    will output:\n    ```text\n    muriel (3 helpful): Less broth.\n    More mint. None\n    ```",
  "properties": {
    "comments": {
      "description": "Top-level comments, each with its replies",
      "items": {
        "$ref": "#/$defs/Comment"
      },
      "type": "array"
    },
    "total": {
      "default": 0,
      "description": "Number of comments on the recipe, replies included",
      "type": "integer"
    },
    "helpful_total": {
      "default": 0,
      "description": "Number of comments readers picked as most helpful",
      "type": "integer"
    },
    "next_cursor": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Cursor for the next page, or `None` on the last page"
    }
  },
  "type": "object"
}
```

</details>

<details class="mkdocstrings-source" markdown>
<summary>Source code in <code>src/nyt_cooking/mcp/server.py</code></summary>

```python linenums="137"
@mcp.tool(title="Get Recipe Comments", annotations={"readOnlyHint": True})
def get_recipe_comments(
    recipe_id: int,
    max_results: int = 20,
    *,
    helpful_only: bool = False,
    client: Client = SessionClient,
) -> Comments:
    """Get the public reader comments on an NYT Cooking recipe.

    Readers use comments to share substitutions, fixes and results, and NYT Cooking
    staff sometimes reply to answer questions; their comments are marked
    `is_staff`. Each comment includes all of its replies.

    Comments come newest first. Set `helpful_only` to get only the comments readers
    picked as most helpful, most helpful first, as on the recipe page's "Most
    Helpful" tab. `total` counts every comment on the recipe, replies included,
    and `helpful_total` the most helpful ones.

    Args:
        recipe_id (int): NYT Cooking recipe ID, from `search_recipes`,
            `get_recipe_box` or a recipe URL such as `/recipes/1019049-...`.
        max_results (int): Most top-level comments to return, replies aside.
        helpful_only (bool): Whether to get only the most helpful comments.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        Comments: The comments, with the recipe's comment totals.
    """
    return client.get_recipe_comments_paginated(
        recipe_id,
        max_results=max_results,
        helpful_only=helpful_only,
    )
```

</details>

### <code class="doc-symbol doc-symbol-heading doc-symbol-tool"></code> get_recipe_box <span class="doc doc-labels"><small class="doc doc-label doc-label-read-only"><code>read-only</code></small></span> { #get_recipe_box data-toc-label='<code class="doc-symbol doc-symbol-toc doc-symbol-tool"></code>&nbsp;get_recipe_box' }

<div class="doc-signature highlight"><pre><span></span><code><span class="n">get_recipe_box</span><span class="p">(</span>
    <span class="n">max_results</span><span class="p">:</span> <span class="n">integer</span> <span class="o">=</span> <span class="mi">48</span><span class="p">,</span>
    <span class="n">folder_id</span><span class="p">:</span> <span class="n">integer</span> <span class="o">|</span> <span class="n">null</span> <span class="o">=</span> <span class="n">null</span><span class="p">,</span>
<span class="p">)</span> <span class="o">-&gt;</span> <span class="n"><autoref identifier="nyt_cooking.client.models.recipes.RecipeBox" optional>RecipeBox</autoref></span>
</code></pre></div>

List the recipes the user has saved to their NYT Cooking recipe box.

Pass `folder_id` to list one folder's recipes.

<span class="doc-section-title">Parameters:</span>

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `max_results` | <code>integer</code> | Most saved recipes to return. | <code>48</code> |
| `folder_id` | <code>integer &#124; null</code> | NYT Cooking folder ID, from `get_folders`. Leave unset for the whole recipe box. | <code>null</code> |

<span class="doc-section-title">Returns:</span>

| Type | Description |
| --- | --- |
| [`RecipeBox`][nyt_cooking.client.models.recipes.RecipeBox] | The saved recipes and the total number saved. |

<details markdown>
<summary>Show input schema:</summary>

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "max_results": {
      "default": 48,
      "type": "integer",
      "description": "Most saved recipes to return."
    },
    "folder_id": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "NYT Cooking folder ID, from `get_folders`. Leave\nunset for the whole recipe box."
    }
  }
}
```

</details>

<details markdown>
<summary>Show output schema:</summary>

```json
{
  "description": "Recipes saved to a user's recipe box.",
  "properties": {
    "recipes": {
      "description": "Saved recipes",
      "items": {
        "description": "The headline details of a recipe, as listed in a recipe box.",
        "properties": {
          "id": {
            "description": "NYT Cooking recipe ID, such as `1019049`",
            "type": "integer"
          },
          "name": {
            "description": "Recipe title",
            "type": "string"
          },
          "byline": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "default": null,
            "description": "Recipe author(s)"
          },
          "url": {
            "description": "Recipe page on cooking.nytimes.com",
            "type": "string"
          },
          "servings": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "default": null,
            "description": "Yield, such as `2 to 4 servings`"
          },
          "total_time": {
            "anyOf": [
              {
                "description": "A length of time, as NYT both displays and measures it.",
                "properties": {
                  "display": {
                    "anyOf": [
                      {
                        "type": "string"
                      },
                      {
                        "type": "null"
                      }
                    ],
                    "default": null,
                    "description": "Human-readable time, such as `1 1/2 hours`"
                  },
                  "minutes": {
                    "anyOf": [
                      {
                        "type": "number"
                      },
                      {
                        "type": "null"
                      }
                    ],
                    "default": null,
                    "description": "Time in minutes"
                  }
                },
                "type": "object"
              },
              {
                "type": "null"
              }
            ],
            "default": null,
            "description": "Total time to make the recipe"
          },
          "image": {
            "anyOf": [
              {
                "description": "A recipe image, available in several crops.",
                "properties": {
                  "caption": {
                    "anyOf": [
                      {
                        "type": "string"
                      },
                      {
                        "type": "null"
                      }
                    ],
                    "default": null,
                    "description": "Image caption"
                  },
                  "credit": {
                    "anyOf": [
                      {
                        "type": "string"
                      },
                      {
                        "type": "null"
                      }
                    ],
                    "default": null,
                    "description": "Photographer credit"
                  },
                  "crops": {
                    "description": "Available sizes of the image",
                    "items": {
                      "description": "One size of a recipe image.",
                      "properties": {
                        "name": {
                          "description": "NYT's name for the crop, such as `superJumbo`",
                          "type": "string"
                        },
                        "url": {
                          "description": "URL of the image file",
                          "type": "string"
                        },
                        "width": {
                          "description": "Width in pixels",
                          "type": "integer"
                        },
                        "height": {
                          "description": "Height in pixels",
                          "type": "integer"
                        }
                      },
                      "required": [
                        "name",
                        "url",
                        "width",
                        "height"
                      ],
                      "type": "object"
                    },
                    "type": "array"
                  }
                },
                "type": "object"
              },
              {
                "type": "null"
              }
            ],
            "default": null,
            "description": "Recipe photo"
          },
          "has_video": {
            "default": false,
            "description": "Whether a video exists",
            "type": "boolean"
          }
        },
        "required": [
          "id",
          "name",
          "url"
        ],
        "type": "object"
      },
      "type": "array"
    },
    "pagination": {
      "description": "Position within the recipe box, or the folder searched",
      "properties": {
        "total": {
          "description": "Total number of results across all pages",
          "type": "integer"
        },
        "page": {
          "description": "This page's number, starting at 1",
          "type": "integer"
        },
        "max_page": {
          "description": "Number of the last page",
          "type": "integer"
        }
      },
      "required": [
        "total",
        "page",
        "max_page"
      ],
      "type": "object"
    }
  },
  "required": [
    "pagination"
  ],
  "type": "object"
}
```

</details>

<details class="mkdocstrings-source" markdown>
<summary>Source code in <code>src/nyt_cooking/mcp/server.py</code></summary>

```python linenums="173"
@mcp.tool(title="Get Recipe Box", annotations={"readOnlyHint": True})
def get_recipe_box(
    max_results: int = 48,
    folder_id: int | None = None,
    client: Client = SessionClient,
) -> RecipeBox:
    """List the recipes the user has saved to their NYT Cooking recipe box.

    Pass `folder_id` to list one folder's recipes.

    Args:
        max_results (int): Most saved recipes to return.
        folder_id (int | None): NYT Cooking folder ID, from `get_folders`. Leave
            unset for the whole recipe box.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        RecipeBox: The saved recipes and the total number saved.
    """
    return client.get_recipe_box_paginated(
        max_results=max_results,
        folder_id=folder_id,
    )
```

</details>

### <code class="doc-symbol doc-symbol-heading doc-symbol-tool"></code> get_recently_viewed <span class="doc doc-labels"><small class="doc doc-label doc-label-read-only"><code>read-only</code></small></span> { #get_recently_viewed data-toc-label='<code class="doc-symbol doc-symbol-toc doc-symbol-tool"></code>&nbsp;get_recently_viewed' }

<div class="doc-signature highlight"><pre><span></span><code><span class="n">get_recently_viewed</span><span class="p">(</span><span class="n">max_results</span><span class="p">:</span> <span class="n">integer</span> <span class="o">=</span> <span class="mi">20</span><span class="p">)</span> <span class="o">-&gt;</span> <span class="n"><autoref identifier="nyt_cooking.client.models.recipes.RecentlyViewed" optional>RecentlyViewed</autoref></span>
</code></pre></div>

List the recipes the user has recently viewed on NYT Cooking.

Most recent first.

<span class="doc-section-title">Parameters:</span>

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `max_results` | <code>integer</code> | Most recently viewed recipes to return. | <code>20</code> |

<span class="doc-section-title">Returns:</span>

| Type | Description |
| --- | --- |
| [`RecentlyViewed`][nyt_cooking.client.models.recipes.RecentlyViewed] | The recently viewed recipes. |

<details markdown>
<summary>Show input schema:</summary>

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "max_results": {
      "default": 20,
      "type": "integer",
      "description": "Most recently viewed recipes to return."
    }
  }
}
```

</details>

<details markdown>
<summary>Show output schema:</summary>

```json
{
  "description": "Recipes a user has recently opened, most recent first.",
  "properties": {
    "recipes": {
      "description": "Recently viewed recipes",
      "items": {
        "description": "The headline details of a recipe, as listed in a recipe box.",
        "properties": {
          "id": {
            "description": "NYT Cooking recipe ID, such as `1019049`",
            "type": "integer"
          },
          "name": {
            "description": "Recipe title",
            "type": "string"
          },
          "byline": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "default": null,
            "description": "Recipe author(s)"
          },
          "url": {
            "description": "Recipe page on cooking.nytimes.com",
            "type": "string"
          },
          "servings": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "default": null,
            "description": "Yield, such as `2 to 4 servings`"
          },
          "total_time": {
            "anyOf": [
              {
                "description": "A length of time, as NYT both displays and measures it.",
                "properties": {
                  "display": {
                    "anyOf": [
                      {
                        "type": "string"
                      },
                      {
                        "type": "null"
                      }
                    ],
                    "default": null,
                    "description": "Human-readable time, such as `1 1/2 hours`"
                  },
                  "minutes": {
                    "anyOf": [
                      {
                        "type": "number"
                      },
                      {
                        "type": "null"
                      }
                    ],
                    "default": null,
                    "description": "Time in minutes"
                  }
                },
                "type": "object"
              },
              {
                "type": "null"
              }
            ],
            "default": null,
            "description": "Total time to make the recipe"
          },
          "image": {
            "anyOf": [
              {
                "description": "A recipe image, available in several crops.",
                "properties": {
                  "caption": {
                    "anyOf": [
                      {
                        "type": "string"
                      },
                      {
                        "type": "null"
                      }
                    ],
                    "default": null,
                    "description": "Image caption"
                  },
                  "credit": {
                    "anyOf": [
                      {
                        "type": "string"
                      },
                      {
                        "type": "null"
                      }
                    ],
                    "default": null,
                    "description": "Photographer credit"
                  },
                  "crops": {
                    "description": "Available sizes of the image",
                    "items": {
                      "description": "One size of a recipe image.",
                      "properties": {
                        "name": {
                          "description": "NYT's name for the crop, such as `superJumbo`",
                          "type": "string"
                        },
                        "url": {
                          "description": "URL of the image file",
                          "type": "string"
                        },
                        "width": {
                          "description": "Width in pixels",
                          "type": "integer"
                        },
                        "height": {
                          "description": "Height in pixels",
                          "type": "integer"
                        }
                      },
                      "required": [
                        "name",
                        "url",
                        "width",
                        "height"
                      ],
                      "type": "object"
                    },
                    "type": "array"
                  }
                },
                "type": "object"
              },
              {
                "type": "null"
              }
            ],
            "default": null,
            "description": "Recipe photo"
          },
          "has_video": {
            "default": false,
            "description": "Whether a video exists",
            "type": "boolean"
          }
        },
        "required": [
          "id",
          "name",
          "url"
        ],
        "type": "object"
      },
      "type": "array"
    }
  },
  "type": "object"
}
```

</details>

<details class="mkdocstrings-source" markdown>
<summary>Source code in <code>src/nyt_cooking/mcp/server.py</code></summary>

```python linenums="198"
@mcp.tool(title="Get Recently Viewed", annotations={"readOnlyHint": True})
def get_recently_viewed(
    max_results: int = 20,
    client: Client = SessionClient,
) -> RecentlyViewed:
    """List the recipes the user has recently viewed on NYT Cooking.

    Most recent first.

    Args:
        max_results (int): Most recently viewed recipes to return.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        RecentlyViewed: The recently viewed recipes.
    """
    return client.get_recently_viewed(max_results=max_results)
```

</details>

### <code class="doc-symbol doc-symbol-heading doc-symbol-tool"></code> get_folders <span class="doc doc-labels"><small class="doc doc-label doc-label-read-only"><code>read-only</code></small></span> { #get_folders data-toc-label='<code class="doc-symbol doc-symbol-toc doc-symbol-tool"></code>&nbsp;get_folders' }

<div class="doc-signature highlight"><pre><span></span><code><span class="n">get_folders</span><span class="p">()</span> <span class="o">-&gt;</span> <span class="n"><autoref identifier="nyt_cooking.client.models.folders.Folders" optional>Folders</autoref></span>
</code></pre></div>

List the folders in the user's NYT Cooking recipe box.

Alphabetical, with each folder's ID and number of recipes.

<span class="doc-section-title">Returns:</span>

| Type | Description |
| --- | --- |
| [`Folders`][nyt_cooking.client.models.folders.Folders] | The recipe box folders. |

<details markdown>
<summary>Show input schema:</summary>

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

</details>

<details markdown>
<summary>Show output schema:</summary>

```json
{
  "description": "The folders in a user's recipe box, in alphabetical order.",
  "properties": {
    "folders": {
      "description": "Recipe box folders",
      "items": {
        "description": "A folder in a user's recipe box.",
        "properties": {
          "id": {
            "description": "NYT Cooking folder ID, such as `39869445`",
            "type": "integer"
          },
          "name": {
            "description": "Folder name",
            "type": "string"
          },
          "description": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "default": null,
            "description": "Folder description"
          },
          "recipe_count": {
            "default": 0,
            "description": "Number of recipes in the folder",
            "type": "integer"
          },
          "url": {
            "description": "Folder page in the recipe box on cooking.nytimes.com.",
            "readOnly": true,
            "type": "string"
          }
        },
        "required": [
          "id",
          "name",
          "url"
        ],
        "type": "object"
      },
      "type": "array"
    }
  },
  "type": "object"
}
```

</details>

<details class="mkdocstrings-source" markdown>
<summary>Source code in <code>src/nyt_cooking/mcp/server.py</code></summary>

```python linenums="217"
@mcp.tool(title="Get Folders", annotations={"readOnlyHint": True})
def get_folders(client: Client = SessionClient) -> Folders:
    """List the folders in the user's NYT Cooking recipe box.

    Alphabetical, with each folder's ID and number of recipes.

    Args:
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        Folders: The recipe box folders.
    """
    return client.get_folders()
```

</details>

### <code class="doc-symbol doc-symbol-heading doc-symbol-tool"></code> get_folder_recipes <span class="doc doc-labels"><small class="doc doc-label doc-label-read-only"><code>read-only</code></small></span> { #get_folder_recipes data-toc-label='<code class="doc-symbol doc-symbol-toc doc-symbol-tool"></code>&nbsp;get_folder_recipes' }

<div class="doc-signature highlight"><pre><span></span><code><span class="n">get_folder_recipes</span><span class="p">(</span><span class="n">folder_id</span><span class="p">:</span> <span class="n">integer</span><span class="p">)</span> <span class="o">-&gt;</span> <span class="n"><autoref identifier="nyt_cooking.client.models.recipes.RecipeBox" optional>RecipeBox</autoref></span>
</code></pre></div>

List every recipe in a folder of the user's NYT Cooking recipe box.

<span class="doc-section-title">Parameters:</span>

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `folder_id` | <code>integer</code> | NYT Cooking folder ID, from `get_folders`. | *required* |

<span class="doc-section-title">Returns:</span>

| Type | Description |
| --- | --- |
| [`RecipeBox`][nyt_cooking.client.models.recipes.RecipeBox] | The folder's recipes and how many it holds. |

<details markdown>
<summary>Show input schema:</summary>

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "folder_id": {
      "type": "integer",
      "description": "NYT Cooking folder ID, from `get_folders`."
    }
  },
  "required": [
    "folder_id"
  ]
}
```

</details>

<details markdown>
<summary>Show output schema:</summary>

```json
{
  "description": "Recipes saved to a user's recipe box.",
  "properties": {
    "recipes": {
      "description": "Saved recipes",
      "items": {
        "description": "The headline details of a recipe, as listed in a recipe box.",
        "properties": {
          "id": {
            "description": "NYT Cooking recipe ID, such as `1019049`",
            "type": "integer"
          },
          "name": {
            "description": "Recipe title",
            "type": "string"
          },
          "byline": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "default": null,
            "description": "Recipe author(s)"
          },
          "url": {
            "description": "Recipe page on cooking.nytimes.com",
            "type": "string"
          },
          "servings": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "default": null,
            "description": "Yield, such as `2 to 4 servings`"
          },
          "total_time": {
            "anyOf": [
              {
                "description": "A length of time, as NYT both displays and measures it.",
                "properties": {
                  "display": {
                    "anyOf": [
                      {
                        "type": "string"
                      },
                      {
                        "type": "null"
                      }
                    ],
                    "default": null,
                    "description": "Human-readable time, such as `1 1/2 hours`"
                  },
                  "minutes": {
                    "anyOf": [
                      {
                        "type": "number"
                      },
                      {
                        "type": "null"
                      }
                    ],
                    "default": null,
                    "description": "Time in minutes"
                  }
                },
                "type": "object"
              },
              {
                "type": "null"
              }
            ],
            "default": null,
            "description": "Total time to make the recipe"
          },
          "image": {
            "anyOf": [
              {
                "description": "A recipe image, available in several crops.",
                "properties": {
                  "caption": {
                    "anyOf": [
                      {
                        "type": "string"
                      },
                      {
                        "type": "null"
                      }
                    ],
                    "default": null,
                    "description": "Image caption"
                  },
                  "credit": {
                    "anyOf": [
                      {
                        "type": "string"
                      },
                      {
                        "type": "null"
                      }
                    ],
                    "default": null,
                    "description": "Photographer credit"
                  },
                  "crops": {
                    "description": "Available sizes of the image",
                    "items": {
                      "description": "One size of a recipe image.",
                      "properties": {
                        "name": {
                          "description": "NYT's name for the crop, such as `superJumbo`",
                          "type": "string"
                        },
                        "url": {
                          "description": "URL of the image file",
                          "type": "string"
                        },
                        "width": {
                          "description": "Width in pixels",
                          "type": "integer"
                        },
                        "height": {
                          "description": "Height in pixels",
                          "type": "integer"
                        }
                      },
                      "required": [
                        "name",
                        "url",
                        "width",
                        "height"
                      ],
                      "type": "object"
                    },
                    "type": "array"
                  }
                },
                "type": "object"
              },
              {
                "type": "null"
              }
            ],
            "default": null,
            "description": "Recipe photo"
          },
          "has_video": {
            "default": false,
            "description": "Whether a video exists",
            "type": "boolean"
          }
        },
        "required": [
          "id",
          "name",
          "url"
        ],
        "type": "object"
      },
      "type": "array"
    },
    "pagination": {
      "description": "Position within the recipe box, or the folder searched",
      "properties": {
        "total": {
          "description": "Total number of results across all pages",
          "type": "integer"
        },
        "page": {
          "description": "This page's number, starting at 1",
          "type": "integer"
        },
        "max_page": {
          "description": "Number of the last page",
          "type": "integer"
        }
      },
      "required": [
        "total",
        "page",
        "max_page"
      ],
      "type": "object"
    }
  },
  "required": [
    "pagination"
  ],
  "type": "object"
}
```

</details>

<details class="mkdocstrings-source" markdown>
<summary>Source code in <code>src/nyt_cooking/mcp/server.py</code></summary>

```python linenums="232"
@mcp.tool(title="Get Folder Recipes", annotations={"readOnlyHint": True})
def get_folder_recipes(folder_id: int, client: Client = SessionClient) -> RecipeBox:
    """List every recipe in a folder of the user's NYT Cooking recipe box.

    Args:
        folder_id (int): NYT Cooking folder ID, from `get_folders`.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        RecipeBox: The folder's recipes and how many it holds.
    """
    return client.get_folder_recipes(folder_id)
```

</details>

### <code class="doc-symbol doc-symbol-heading doc-symbol-tool"></code> add_folder <span class="doc doc-labels"><small class="doc doc-label doc-label-non-destructive"><code>non-destructive</code></small></span> { #add_folder data-toc-label='<code class="doc-symbol doc-symbol-toc doc-symbol-tool"></code>&nbsp;add_folder' }

<div class="doc-signature highlight"><pre><span></span><code><span class="n">add_folder</span><span class="p">(</span><span class="n">name</span><span class="p">:</span> <span class="n">string</span><span class="p">)</span> <span class="o">-&gt;</span> <span class="n"><autoref identifier="nyt_cooking.client.models.folders.Folder" optional>Folder</autoref></span>
</code></pre></div>

Add an empty folder to the user's NYT Cooking recipe box.

<span class="doc-section-title">Parameters:</span>

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `name` | <code>string</code> | Name of the new folder. | *required* |

<span class="doc-section-title">Returns:</span>

| Type | Description |
| --- | --- |
| [`Folder`][nyt_cooking.client.models.folders.Folder] | The new folder. |

<details markdown>
<summary>Show input schema:</summary>

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string",
      "description": "Name of the new folder."
    }
  },
  "required": [
    "name"
  ]
}
```

</details>

<details markdown>
<summary>Show output schema:</summary>

```json
{
  "description": "A folder in a user's recipe box.",
  "properties": {
    "id": {
      "description": "NYT Cooking folder ID, such as `39869445`",
      "type": "integer"
    },
    "name": {
      "description": "Folder name",
      "type": "string"
    },
    "description": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Folder description"
    },
    "recipe_count": {
      "default": 0,
      "description": "Number of recipes in the folder",
      "type": "integer"
    },
    "url": {
      "description": "Folder page in the recipe box on cooking.nytimes.com.",
      "readOnly": true,
      "type": "string"
    }
  },
  "required": [
    "id",
    "name",
    "url"
  ],
  "type": "object"
}
```

</details>

<details class="mkdocstrings-source" markdown>
<summary>Source code in <code>src/nyt_cooking/mcp/server.py</code></summary>

```python linenums="246"
@mcp.tool(title="Add Folder", annotations={"destructiveHint": False})
def add_folder(name: str, client: Client = SessionClient) -> Folder:
    """Add an empty folder to the user's NYT Cooking recipe box.

    Args:
        name (str): Name of the new folder.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        Folder: The new folder.
    """
    name = _folder_name(name)
    return client.create_folder(name)
```

</details>

### <code class="doc-symbol doc-symbol-heading doc-symbol-tool"></code> rename_folder <span class="doc doc-labels"><small class="doc doc-label doc-label-destructive"><code>destructive</code></small></span> { #rename_folder data-toc-label='<code class="doc-symbol doc-symbol-toc doc-symbol-tool"></code>&nbsp;rename_folder' }

<div class="doc-signature highlight"><pre><span></span><code><span class="n">rename_folder</span><span class="p">(</span><span class="n">folder_id</span><span class="p">:</span> <span class="n">integer</span><span class="p">,</span> <span class="n">name</span><span class="p">:</span> <span class="n">string</span><span class="p">)</span> <span class="o">-&gt;</span> <span class="n"><autoref identifier="nyt_cooking.client.models.folders.Folder" optional>Folder</autoref></span>
</code></pre></div>

Rename a folder in the user's NYT Cooking recipe box.

<span class="doc-section-title">Parameters:</span>

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `folder_id` | <code>integer</code> | NYT Cooking folder ID, from `get_folders`. | *required* |
| `name` | <code>string</code> | New name for the folder. | *required* |

<span class="doc-section-title">Returns:</span>

| Type | Description |
| --- | --- |
| [`Folder`][nyt_cooking.client.models.folders.Folder] | The renamed folder. |

<details markdown>
<summary>Show input schema:</summary>

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "folder_id": {
      "type": "integer",
      "description": "NYT Cooking folder ID, from `get_folders`."
    },
    "name": {
      "type": "string",
      "description": "New name for the folder."
    }
  },
  "required": [
    "folder_id",
    "name"
  ]
}
```

</details>

<details markdown>
<summary>Show output schema:</summary>

```json
{
  "description": "A folder in a user's recipe box.",
  "properties": {
    "id": {
      "description": "NYT Cooking folder ID, such as `39869445`",
      "type": "integer"
    },
    "name": {
      "description": "Folder name",
      "type": "string"
    },
    "description": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Folder description"
    },
    "recipe_count": {
      "default": 0,
      "description": "Number of recipes in the folder",
      "type": "integer"
    },
    "url": {
      "description": "Folder page in the recipe box on cooking.nytimes.com.",
      "readOnly": true,
      "type": "string"
    }
  },
  "required": [
    "id",
    "name",
    "url"
  ],
  "type": "object"
}
```

</details>

<details class="mkdocstrings-source" markdown>
<summary>Source code in <code>src/nyt_cooking/mcp/server.py</code></summary>

```python linenums="261"
@mcp.tool(title="Rename Folder", annotations={"destructiveHint": True})
def rename_folder(folder_id: int, name: str, client: Client = SessionClient) -> Folder:
    """Rename a folder in the user's NYT Cooking recipe box.

    Args:
        folder_id (int): NYT Cooking folder ID, from `get_folders`.
        name (str): New name for the folder.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        Folder: The renamed folder.
    """
    name = _folder_name(name)
    return client.rename_folder(folder_id, name)
```

</details>

### <code class="doc-symbol doc-symbol-heading doc-symbol-tool"></code> remove_folder <span class="doc doc-labels"><small class="doc doc-label doc-label-destructive"><code>destructive</code></small></span> { #remove_folder data-toc-label='<code class="doc-symbol doc-symbol-toc doc-symbol-tool"></code>&nbsp;remove_folder' }

<div class="doc-signature highlight"><pre><span></span><code><span class="n">remove_folder</span><span class="p">(</span><span class="n">folder_id</span><span class="p">:</span> <span class="n">integer</span><span class="p">)</span> <span class="o">-&gt;</span> <span class="n"><autoref identifier="nyt_cooking.client.models.folders.Folders" optional>Folders</autoref></span>
</code></pre></div>

Remove a folder from the user's NYT Cooking recipe box, deleting it.

The folder's recipes stay saved to the recipe box.

<span class="doc-section-title">Parameters:</span>

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `folder_id` | <code>integer</code> | NYT Cooking folder ID, from `get_folders`. | *required* |

<span class="doc-section-title">Returns:</span>

| Type | Description |
| --- | --- |
| [`Folders`][nyt_cooking.client.models.folders.Folders] | The folders left in the recipe box. |

<details markdown>
<summary>Show input schema:</summary>

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "folder_id": {
      "type": "integer",
      "description": "NYT Cooking folder ID, from `get_folders`."
    }
  },
  "required": [
    "folder_id"
  ]
}
```

</details>

<details markdown>
<summary>Show output schema:</summary>

```json
{
  "description": "The folders in a user's recipe box, in alphabetical order.",
  "properties": {
    "folders": {
      "description": "Recipe box folders",
      "items": {
        "description": "A folder in a user's recipe box.",
        "properties": {
          "id": {
            "description": "NYT Cooking folder ID, such as `39869445`",
            "type": "integer"
          },
          "name": {
            "description": "Folder name",
            "type": "string"
          },
          "description": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "default": null,
            "description": "Folder description"
          },
          "recipe_count": {
            "default": 0,
            "description": "Number of recipes in the folder",
            "type": "integer"
          },
          "url": {
            "description": "Folder page in the recipe box on cooking.nytimes.com.",
            "readOnly": true,
            "type": "string"
          }
        },
        "required": [
          "id",
          "name",
          "url"
        ],
        "type": "object"
      },
      "type": "array"
    }
  },
  "type": "object"
}
```

</details>

<details class="mkdocstrings-source" markdown>
<summary>Source code in <code>src/nyt_cooking/mcp/server.py</code></summary>

```python linenums="277"
@mcp.tool(title="Remove Folder", annotations={"destructiveHint": True})
def remove_folder(folder_id: int, client: Client = SessionClient) -> Folders:
    """Remove a folder from the user's NYT Cooking recipe box, deleting it.

    The folder's recipes stay saved to the recipe box.

    Args:
        folder_id (int): NYT Cooking folder ID, from `get_folders`.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        Folders: The folders left in the recipe box.
    """
    return client.delete_folder(folder_id)
```

</details>

### <code class="doc-symbol doc-symbol-heading doc-symbol-tool"></code> get_recipe_save_status <span class="doc doc-labels"><small class="doc doc-label doc-label-read-only"><code>read-only</code></small></span> { #get_recipe_save_status data-toc-label='<code class="doc-symbol doc-symbol-toc doc-symbol-tool"></code>&nbsp;get_recipe_save_status' }

<div class="doc-signature highlight"><pre><span></span><code><span class="n">get_recipe_save_status</span><span class="p">(</span><span class="n">recipe_id</span><span class="p">:</span> <span class="n">integer</span><span class="p">)</span> <span class="o">-&gt;</span> <span class="n"><autoref identifier="nyt_cooking.client.models.folders.SavedRecipe" optional>SavedRecipe</autoref></span>
</code></pre></div>

Check whether a recipe is saved to the user's NYT Cooking recipe box.

Also lists the recipe box folders it is in.

<span class="doc-section-title">Parameters:</span>

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `recipe_id` | <code>integer</code> | NYT Cooking recipe ID, from `search_recipes`, `get_recipe_box` or a recipe URL such as `/recipes/1019049-...`. | *required* |

<span class="doc-section-title">Returns:</span>

| Type | Description |
| --- | --- |
| [`SavedRecipe`][nyt_cooking.client.models.folders.SavedRecipe] | Whether the recipe is saved, and its folders. |

<details markdown>
<summary>Show input schema:</summary>

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "recipe_id": {
      "type": "integer",
      "description": "NYT Cooking recipe ID, from `search_recipes`,\n`get_recipe_box` or a recipe URL such as `/recipes/1019049-...`."
    }
  },
  "required": [
    "recipe_id"
  ]
}
```

</details>

<details markdown>
<summary>Show output schema:</summary>

```json
{
  "description": "Whether a recipe is saved to the user's recipe box, and in which folders.\n\nValidates NYT's recipe interactions response, whose `collection_ids` are\nmatched against the user's folders, passed as the `folders` validation\ncontext. IDs that are not among them, such as the hidden collection behind\nthe whole recipe box, are dropped.\n\n??? example \"Example\"\n    ```python\n    from nyt_cooking.client.models import Folder, SavedRecipe\n\n    stew = Folder(id=38433723, name=\"Stew\")\n    saved = SavedRecipe.model_validate(\n        {\n            \"id\": 4735,\n            \"name\": \"Beef Stew\",\n            \"saved\": True,\n            \"collection_ids\": [1, 38433723],\n        },\n        context={\"folders\": [stew]},\n    )\n    print(saved)\n    ```\n\n    will output:\n    ```text\n    Beef Stew [4735]: saved, in Stew\n    ```",
  "properties": {
    "id": {
      "description": "NYT Cooking recipe ID, such as `1019049`",
      "type": "integer"
    },
    "name": {
      "description": "Recipe title",
      "type": "string"
    },
    "saved": {
      "description": "Whether the recipe is saved to the recipe box",
      "type": "boolean"
    },
    "folders": {
      "description": "Recipe box folders the recipe is in",
      "items": {
        "description": "A folder in a user's recipe box.",
        "properties": {
          "id": {
            "description": "NYT Cooking folder ID, such as `39869445`",
            "type": "integer"
          },
          "name": {
            "description": "Folder name",
            "type": "string"
          },
          "description": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "default": null,
            "description": "Folder description"
          },
          "recipe_count": {
            "default": 0,
            "description": "Number of recipes in the folder",
            "type": "integer"
          },
          "url": {
            "description": "Folder page in the recipe box on cooking.nytimes.com.",
            "readOnly": true,
            "type": "string"
          }
        },
        "required": [
          "id",
          "name",
          "url"
        ],
        "type": "object"
      },
      "type": "array"
    }
  },
  "required": [
    "id",
    "name",
    "saved"
  ],
  "type": "object"
}
```

</details>

<details class="mkdocstrings-source" markdown>
<summary>Source code in <code>src/nyt_cooking/mcp/server.py</code></summary>

```python linenums="293"
@mcp.tool(title="Get Recipe Save Status", annotations={"readOnlyHint": True})
def get_recipe_save_status(
    recipe_id: int,
    client: Client = SessionClient,
) -> SavedRecipe:
    """Check whether a recipe is saved to the user's NYT Cooking recipe box.

    Also lists the recipe box folders it is in.

    Args:
        recipe_id (int): NYT Cooking recipe ID, from `search_recipes`,
            `get_recipe_box` or a recipe URL such as `/recipes/1019049-...`.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        SavedRecipe: Whether the recipe is saved, and its folders.
    """
    return client.get_saved_recipe(recipe_id)
```

</details>

### <code class="doc-symbol doc-symbol-heading doc-symbol-tool"></code> add_recipe <span class="doc doc-labels"><small class="doc doc-label doc-label-non-destructive"><code>non-destructive</code></small></span> { #add_recipe data-toc-label='<code class="doc-symbol doc-symbol-toc doc-symbol-tool"></code>&nbsp;add_recipe' }

<div class="doc-signature highlight"><pre><span></span><code><span class="n">add_recipe</span><span class="p">(</span>
    <span class="n">recipe_id</span><span class="p">:</span> <span class="n">integer</span><span class="p">,</span>
    <span class="n">folder_id</span><span class="p">:</span> <span class="n">integer</span> <span class="o">|</span> <span class="n">null</span> <span class="o">=</span> <span class="n">null</span><span class="p">,</span>
<span class="p">)</span> <span class="o">-&gt;</span> <span class="n"><autoref identifier="nyt_cooking.client.models.folders.SavedRecipe" optional>SavedRecipe</autoref></span>
</code></pre></div>

Add a recipe to the user's NYT Cooking recipe box, or to a folder in it.

Without `folder_id`, the recipe is saved to the recipe box. With `folder_id`, it
is also added to that folder, since every recipe in a folder is saved to the
recipe box. Adding a recipe that is already saved, or already in the folder,
changes nothing.

<span class="doc-section-title">Parameters:</span>

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `recipe_id` | <code>integer</code> | NYT Cooking recipe ID, from `search_recipes`, `get_recipe_box` or a recipe URL such as `/recipes/1019049-...`. | *required* |
| `folder_id` | <code>integer &#124; null</code> | NYT Cooking folder ID to also add the recipe to, from `get_folders`. Leave unset to add it to the recipe box only. | <code>null</code> |

<span class="doc-section-title">Returns:</span>

| Type | Description |
| --- | --- |
| [`SavedRecipe`][nyt_cooking.client.models.folders.SavedRecipe] | Whether the recipe is saved, and its folders, afterwards. |

<details markdown>
<summary>Show input schema:</summary>

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "recipe_id": {
      "type": "integer",
      "description": "NYT Cooking recipe ID, from `search_recipes`,\n`get_recipe_box` or a recipe URL such as `/recipes/1019049-...`."
    },
    "folder_id": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "NYT Cooking folder ID to also add the recipe to,\nfrom `get_folders`. Leave unset to add it to the recipe box only."
    }
  },
  "required": [
    "recipe_id"
  ]
}
```

</details>

<details markdown>
<summary>Show output schema:</summary>

```json
{
  "description": "Whether a recipe is saved to the user's recipe box, and in which folders.\n\nValidates NYT's recipe interactions response, whose `collection_ids` are\nmatched against the user's folders, passed as the `folders` validation\ncontext. IDs that are not among them, such as the hidden collection behind\nthe whole recipe box, are dropped.\n\n??? example \"Example\"\n    ```python\n    from nyt_cooking.client.models import Folder, SavedRecipe\n\n    stew = Folder(id=38433723, name=\"Stew\")\n    saved = SavedRecipe.model_validate(\n        {\n            \"id\": 4735,\n            \"name\": \"Beef Stew\",\n            \"saved\": True,\n            \"collection_ids\": [1, 38433723],\n        },\n        context={\"folders\": [stew]},\n    )\n    print(saved)\n    ```\n\n    will output:\n    ```text\n    Beef Stew [4735]: saved, in Stew\n    ```",
  "properties": {
    "id": {
      "description": "NYT Cooking recipe ID, such as `1019049`",
      "type": "integer"
    },
    "name": {
      "description": "Recipe title",
      "type": "string"
    },
    "saved": {
      "description": "Whether the recipe is saved to the recipe box",
      "type": "boolean"
    },
    "folders": {
      "description": "Recipe box folders the recipe is in",
      "items": {
        "description": "A folder in a user's recipe box.",
        "properties": {
          "id": {
            "description": "NYT Cooking folder ID, such as `39869445`",
            "type": "integer"
          },
          "name": {
            "description": "Folder name",
            "type": "string"
          },
          "description": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "default": null,
            "description": "Folder description"
          },
          "recipe_count": {
            "default": 0,
            "description": "Number of recipes in the folder",
            "type": "integer"
          },
          "url": {
            "description": "Folder page in the recipe box on cooking.nytimes.com.",
            "readOnly": true,
            "type": "string"
          }
        },
        "required": [
          "id",
          "name",
          "url"
        ],
        "type": "object"
      },
      "type": "array"
    }
  },
  "required": [
    "id",
    "name",
    "saved"
  ],
  "type": "object"
}
```

</details>

<details class="mkdocstrings-source" markdown>
<summary>Source code in <code>src/nyt_cooking/mcp/server.py</code></summary>

```python linenums="313"
@mcp.tool(title="Add Recipe", annotations={"destructiveHint": False})
def add_recipe(
    recipe_id: int,
    folder_id: int | None = None,
    client: Client = SessionClient,
) -> SavedRecipe:
    """Add a recipe to the user's NYT Cooking recipe box, or to a folder in it.

    Without `folder_id`, the recipe is saved to the recipe box. With `folder_id`, it
    is also added to that folder, since every recipe in a folder is saved to the
    recipe box. Adding a recipe that is already saved, or already in the folder,
    changes nothing.

    Args:
        recipe_id (int): NYT Cooking recipe ID, from `search_recipes`,
            `get_recipe_box` or a recipe URL such as `/recipes/1019049-...`.
        folder_id (int | None): NYT Cooking folder ID to also add the recipe to,
            from `get_folders`. Leave unset to add it to the recipe box only.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        SavedRecipe: Whether the recipe is saved, and its folders, afterwards.
    """
    return client.save_recipe(recipe_id, folder_id)
```

</details>

### <code class="doc-symbol doc-symbol-heading doc-symbol-tool"></code> remove_recipe <span class="doc doc-labels"><small class="doc doc-label doc-label-destructive"><code>destructive</code></small></span> { #remove_recipe data-toc-label='<code class="doc-symbol doc-symbol-toc doc-symbol-tool"></code>&nbsp;remove_recipe' }

<div class="doc-signature highlight"><pre><span></span><code><span class="n">remove_recipe</span><span class="p">(</span>
    <span class="n">recipe_id</span><span class="p">:</span> <span class="n">integer</span><span class="p">,</span>
    <span class="n">folder_id</span><span class="p">:</span> <span class="n">integer</span> <span class="o">|</span> <span class="n">null</span> <span class="o">=</span> <span class="n">null</span><span class="p">,</span>
<span class="p">)</span> <span class="o">-&gt;</span> <span class="n"><autoref identifier="nyt_cooking.client.models.folders.SavedRecipe" optional>SavedRecipe</autoref></span>
</code></pre></div>

Remove a recipe from the user's NYT Cooking recipe box, or from one folder.

Without `folder_id`, the recipe is removed from the recipe box and from every
folder it is in. Removing a recipe that is not saved changes nothing. With
`folder_id`, the recipe is removed from that folder only, and stays saved to the
recipe box and its other folders; it fails if the recipe is not in the folder.

<span class="doc-section-title">Parameters:</span>

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `recipe_id` | <code>integer</code> | NYT Cooking recipe ID, from `get_recipe_box`, `get_folder_recipes` or `get_recipe_save_status`. | *required* |
| `folder_id` | <code>integer &#124; null</code> | NYT Cooking folder ID to remove the recipe from, from `get_recipe_save_status` or `get_folders`. Leave unset to remove it from the recipe box and every folder. | <code>null</code> |

<span class="doc-section-title">Returns:</span>

| Type | Description |
| --- | --- |
| [`SavedRecipe`][nyt_cooking.client.models.folders.SavedRecipe] | Whether the recipe is saved, and its folders, afterwards. |

<details markdown>
<summary>Show input schema:</summary>

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "recipe_id": {
      "type": "integer",
      "description": "NYT Cooking recipe ID, from `get_recipe_box`,\n`get_folder_recipes` or `get_recipe_save_status`."
    },
    "folder_id": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "NYT Cooking folder ID to remove the recipe from,\nfrom `get_recipe_save_status` or `get_folders`. Leave unset to remove it\nfrom the recipe box and every folder."
    }
  },
  "required": [
    "recipe_id"
  ]
}
```

</details>

<details markdown>
<summary>Show output schema:</summary>

```json
{
  "description": "Whether a recipe is saved to the user's recipe box, and in which folders.\n\nValidates NYT's recipe interactions response, whose `collection_ids` are\nmatched against the user's folders, passed as the `folders` validation\ncontext. IDs that are not among them, such as the hidden collection behind\nthe whole recipe box, are dropped.\n\n??? example \"Example\"\n    ```python\n    from nyt_cooking.client.models import Folder, SavedRecipe\n\n    stew = Folder(id=38433723, name=\"Stew\")\n    saved = SavedRecipe.model_validate(\n        {\n            \"id\": 4735,\n            \"name\": \"Beef Stew\",\n            \"saved\": True,\n            \"collection_ids\": [1, 38433723],\n        },\n        context={\"folders\": [stew]},\n    )\n    print(saved)\n    ```\n\n    will output:\n    ```text\n    Beef Stew [4735]: saved, in Stew\n    ```",
  "properties": {
    "id": {
      "description": "NYT Cooking recipe ID, such as `1019049`",
      "type": "integer"
    },
    "name": {
      "description": "Recipe title",
      "type": "string"
    },
    "saved": {
      "description": "Whether the recipe is saved to the recipe box",
      "type": "boolean"
    },
    "folders": {
      "description": "Recipe box folders the recipe is in",
      "items": {
        "description": "A folder in a user's recipe box.",
        "properties": {
          "id": {
            "description": "NYT Cooking folder ID, such as `39869445`",
            "type": "integer"
          },
          "name": {
            "description": "Folder name",
            "type": "string"
          },
          "description": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "default": null,
            "description": "Folder description"
          },
          "recipe_count": {
            "default": 0,
            "description": "Number of recipes in the folder",
            "type": "integer"
          },
          "url": {
            "description": "Folder page in the recipe box on cooking.nytimes.com.",
            "readOnly": true,
            "type": "string"
          }
        },
        "required": [
          "id",
          "name",
          "url"
        ],
        "type": "object"
      },
      "type": "array"
    }
  },
  "required": [
    "id",
    "name",
    "saved"
  ],
  "type": "object"
}
```

</details>

<details class="mkdocstrings-source" markdown>
<summary>Source code in <code>src/nyt_cooking/mcp/server.py</code></summary>

```python linenums="339"
@mcp.tool(title="Remove Recipe", annotations={"destructiveHint": True})
def remove_recipe(
    recipe_id: int,
    folder_id: int | None = None,
    client: Client = SessionClient,
) -> SavedRecipe:
    """Remove a recipe from the user's NYT Cooking recipe box, or from one folder.

    Without `folder_id`, the recipe is removed from the recipe box and from every
    folder it is in. Removing a recipe that is not saved changes nothing. With
    `folder_id`, the recipe is removed from that folder only, and stays saved to the
    recipe box and its other folders; it fails if the recipe is not in the folder.

    Args:
        recipe_id (int): NYT Cooking recipe ID, from `get_recipe_box`,
            `get_folder_recipes` or `get_recipe_save_status`.
        folder_id (int | None): NYT Cooking folder ID to remove the recipe from,
            from `get_recipe_save_status` or `get_folders`. Leave unset to remove it
            from the recipe box and every folder.
        client (Client): The NYT Cooking client, supplied by FastMCP.

    Returns:
        SavedRecipe: Whether the recipe is saved, and its folders, afterwards.
    """
    return client.unsave_recipe(recipe_id, folder_id)
```

</details>

### <code class="doc-symbol doc-symbol-heading doc-symbol-tool"></code> auth_login <span class="doc doc-labels"><small class="doc doc-label doc-label-destructive"><code>destructive</code></small></span> { #auth_login data-toc-label='<code class="doc-symbol doc-symbol-toc doc-symbol-tool"></code>&nbsp;auth_login' }

<div class="doc-signature highlight"><pre><span></span><code><span class="n">auth_login</span><span class="p">(</span><span class="n">cookie</span><span class="p">:</span> <span class="n">string</span><span class="p">)</span> <span class="o">-&gt;</span> <span class="n"><autoref identifier="nyt_cooking.client.models.auth.IsAuthenticated" optional>IsAuthenticated</autoref></span>
</code></pre></div>

Check the user's NYT Cooking cookie and save it if NYT accepts it.

The user copies the cookie from their browser while signed in to cooking.nytimes.com
(developer tools, then cookies, then `NYT-S`). NYT must recognise it as an account
with an active NYT Cooking subscription; otherwise this fails, and nothing is saved.

<span class="doc-section-title">Parameters:</span>

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `cookie` | <code>string</code> | Value of the `NYT-S` cookie. | *required* |

<span class="doc-section-title">Returns:</span>

| Type | Description |
| --- | --- |
| [`IsAuthenticated`][nyt_cooking.client.models.auth.IsAuthenticated] | That the user is now logged in. |

<span class="doc-section-title">Raises:</span>

| Type | Description |
| --- | --- |
| `ToolError` | If the cookie is empty, or NYT does not accept it. |

<details markdown>
<summary>Show input schema:</summary>

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "cookie": {
      "type": "string",
      "description": "Value of the `NYT-S` cookie."
    }
  },
  "required": [
    "cookie"
  ]
}
```

</details>

<details markdown>
<summary>Show output schema:</summary>

```json
{
  "description": "Whether NYT recognises the current login as an NYT Cooking subscriber.",
  "properties": {
    "authenticated": {
      "description": "True when NYT recognises the cookie as an account with an active NYT Cooking subscription",
      "type": "boolean"
    }
  },
  "required": [
    "authenticated"
  ],
  "type": "object"
}
```

</details>

<details class="mkdocstrings-source" markdown>
<summary>Source code in <code>src/nyt_cooking/mcp/server.py</code></summary>

```python linenums="374"
@mcp.tool(title="Log In", annotations={"destructiveHint": True})
def auth_login(cookie: str) -> IsAuthenticated:
    """Check the user's NYT Cooking cookie and save it if NYT accepts it.

    The user copies the cookie from their browser while signed in to cooking.nytimes.com
    (developer tools, then cookies, then `NYT-S`). NYT must recognise it as an account
    with an active NYT Cooking subscription; otherwise this fails, and nothing is saved.

    Args:
        cookie (str): Value of the `NYT-S` cookie.

    Returns:
        IsAuthenticated: That the user is now logged in.

    Raises:
        ToolError: If the cookie is empty, or NYT does not accept it.
    """
    cookie = cookie.strip()
    if not cookie:
        msg = "The NYT-S cookie is required."
        raise ToolError(msg)
    try:
        Client(cookie).close()
    except ValueError as exc:
        msg = f"{exc} The cookie was not saved."
        raise ToolError(msg) from exc
    Settings.save_credentials(cookie)
    return IsAuthenticated(authenticated=True)
```

</details>

### <code class="doc-symbol doc-symbol-heading doc-symbol-tool"></code> auth_logout <span class="doc doc-labels"><small class="doc doc-label doc-label-destructive"><code>destructive</code></small></span> { #auth_logout data-toc-label='<code class="doc-symbol doc-symbol-toc doc-symbol-tool"></code>&nbsp;auth_logout' }

<div class="doc-signature highlight"><pre><span></span><code><span class="n">auth_logout</span><span class="p">()</span> <span class="o">-&gt;</span> <span class="n"><autoref identifier="nyt_cooking.client.models.auth.IsAuthenticated" optional>IsAuthenticated</autoref></span>
</code></pre></div>

Remove the saved NYT Cooking cookie.

Returns whether the user is still logged in afterwards, which is only true when
a cookie is also configured outside the saved login, such as in the
`NYT_COOKING_COOKIE` environment variable.

<span class="doc-section-title">Returns:</span>

| Type | Description |
| --- | --- |
| [`IsAuthenticated`][nyt_cooking.client.models.auth.IsAuthenticated] | Whether the user is still logged in. |

<details markdown>
<summary>Show input schema:</summary>

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

</details>

<details markdown>
<summary>Show output schema:</summary>

```json
{
  "description": "Whether NYT recognises the current login as an NYT Cooking subscriber.",
  "properties": {
    "authenticated": {
      "description": "True when NYT recognises the cookie as an account with an active NYT Cooking subscription",
      "type": "boolean"
    }
  },
  "required": [
    "authenticated"
  ],
  "type": "object"
}
```

</details>

<details class="mkdocstrings-source" markdown>
<summary>Source code in <code>src/nyt_cooking/mcp/server.py</code></summary>

```python linenums="404"
@mcp.tool(title="Log Out", annotations={"destructiveHint": True})
def auth_logout() -> IsAuthenticated:
    """Remove the saved NYT Cooking cookie.

    Returns whether the user is still logged in afterwards, which is only true when
    a cookie is also configured outside the saved login, such as in the
    `NYT_COOKING_COOKIE` environment variable.

    Returns:
        IsAuthenticated: Whether the user is still logged in.
    """
    Settings.clear_credentials()
    return get_auth_status()
```

</details>

### <code class="doc-symbol doc-symbol-heading doc-symbol-tool"></code> get_auth_status <span class="doc doc-labels"><small class="doc doc-label doc-label-read-only"><code>read-only</code></small></span> { #get_auth_status data-toc-label='<code class="doc-symbol doc-symbol-toc doc-symbol-tool"></code>&nbsp;get_auth_status' }

<div class="doc-signature highlight"><pre><span></span><code><span class="n">get_auth_status</span><span class="p">()</span> <span class="o">-&gt;</span> <span class="n"><autoref identifier="nyt_cooking.client.models.auth.IsAuthenticated" optional>IsAuthenticated</autoref></span>
</code></pre></div>

Check with NYT whether the user is logged in with an NYT Cooking subscription.

Returns false when no cookie is saved, NYT no longer recognises it, or the
account's NYT Cooking subscription has lapsed.

<span class="doc-section-title">Returns:</span>

| Type | Description |
| --- | --- |
| [`IsAuthenticated`][nyt_cooking.client.models.auth.IsAuthenticated] | Whether the user is logged in. |

<details markdown>
<summary>Show input schema:</summary>

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

</details>

<details markdown>
<summary>Show output schema:</summary>

```json
{
  "description": "Whether NYT recognises the current login as an NYT Cooking subscriber.",
  "properties": {
    "authenticated": {
      "description": "True when NYT recognises the cookie as an account with an active NYT Cooking subscription",
      "type": "boolean"
    }
  },
  "required": [
    "authenticated"
  ],
  "type": "object"
}
```

</details>

<details class="mkdocstrings-source" markdown>
<summary>Source code in <code>src/nyt_cooking/mcp/server.py</code></summary>

```python linenums="419"
@mcp.tool(title="Get Login Status", annotations={"readOnlyHint": True})
def get_auth_status() -> IsAuthenticated:
    """Check with NYT whether the user is logged in with an NYT Cooking subscription.

    Returns false when no cookie is saved, NYT no longer recognises it, or the
    account's NYT Cooking subscription has lapsed.

    Returns:
        IsAuthenticated: Whether the user is logged in.
    """
    try:
        Client().close()
    except ValueError:
        return IsAuthenticated(authenticated=False)
    return IsAuthenticated(authenticated=True)
```

</details>
