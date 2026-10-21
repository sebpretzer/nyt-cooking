# MCP Tools

| Tool | Name | Behavior |
| --- | --- | --- |
| [Get Search Filters](#get_search_filters) | `get_search_filters` | Read-only |
| [Search Recipes](#search_recipes) | `search_recipes` | Read-only |
| [Get Recipe](#get_recipe) | `get_recipe` | Read-only |
| [Get Recipe Comments](#get_recipe_comments) | `get_recipe_comments` | Read-only |
| [Get Recipe Box](#get_recipe_box) | `get_recipe_box` | Read-only |
| [Get Recently Viewed](#get_recently_viewed) | `get_recently_viewed` | Read-only |
| [Get Folders](#get_folders) | `get_folders` | Read-only |
| [Get Folder Recipes](#get_folder_recipes) | `get_folder_recipes` | Read-only |
| [Add Folder](#add_folder) | `add_folder` | Non-destructive |
| [Rename Folder](#rename_folder) | `rename_folder` | Destructive |
| [Remove Folder](#remove_folder) | `remove_folder` | Destructive |
| [Get Recipe Save Status](#get_recipe_save_status) | `get_recipe_save_status` | Read-only |
| [Add Recipe](#add_recipe) | `add_recipe` | Non-destructive |
| [Remove Recipe](#remove_recipe) | `remove_recipe` | Destructive |
| [Log In](#auth_login) | `auth_login` | Destructive |
| [Log Out](#auth_logout) | `auth_logout` | Destructive |
| [Get Login Status](#get_auth_status) | `get_auth_status` | Read-only |

## Get Search Filters { #get_search_filters }

`get_search_filters` · Read-only

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

**Parameters**

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `query` | <code>string</code> | no | <code>&quot;&quot;</code> | Search terms, such as a dish, ingredient or cuisine. |
| `criteria` | <code>object &#124; null</code> | no | <code>null</code> | Limits already chosen, such as tags from an earlier call. Leave unset on the first call. |
| `criteria.tags` | <code>array of string</code> | no | | Tags every result must have, such as `healthy`, `dinner` or `one pot`, from `get_search_filters`. Only those names match: a misspelled or invented tag matches nothing, with no error, so 0 results can mean a bad tag. Tags combine with AND, so each one narrows the results |
| `criteria.max_minutes` | <code>integer &#124; null</code> | no | <code>null</code> | Longest total time in minutes, inclusive. There is no minimum |
| `criteria.top_rated` | <code>boolean</code> | no | <code>false</code> | Whether to keep only top-rated recipes |
| `criteria.sort` | <code>&quot;rating&quot; &#124; &quot;firstPublished&quot; &#124; null</code> | no | <code>null</code> | `rating` for highest rated or `firstPublished` for most recent. Leave unset for best match |

**Returns**

[`SearchFilters`][nyt_cooking.client.models.search.SearchFilters]

## Search Recipes { #search_recipes }

`search_recipes` · Read-only

Search NYT Cooking for recipes.

Returns each match's ID, title, author and total time, plus the total number
of matches. Pass an ID to `get_recipe` for ingredients and steps.

To filter, call `get_search_filters` with the same `query` first and use the
tag names it returns in `criteria`. Tags combine with AND, so each one narrows
the results, and a misspelled or invented tag returns 0 results rather than an
error.

NYT stops at 960 results, however many match, so `max_results` above that
returns no more.

**Parameters**

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `query` | <code>string</code> | yes | | Search terms, such as a dish, ingredient or cuisine. |
| `max_results` | <code>integer</code> | no | <code>48</code> | Most recipes to return. |
| `criteria` | <code>object &#124; null</code> | no | <code>null</code> | Tags, a time limit, top-rated only, sort order to narrow by. Leave unset for no limits. |
| `criteria.tags` | <code>array of string</code> | no | | Tags every result must have, such as `healthy`, `dinner` or `one pot`, from `get_search_filters`. Only those names match: a misspelled or invented tag matches nothing, with no error, so 0 results can mean a bad tag. Tags combine with AND, so each one narrows the results |
| `criteria.max_minutes` | <code>integer &#124; null</code> | no | <code>null</code> | Longest total time in minutes, inclusive. There is no minimum |
| `criteria.top_rated` | <code>boolean</code> | no | <code>false</code> | Whether to keep only top-rated recipes |
| `criteria.sort` | <code>&quot;rating&quot; &#124; &quot;firstPublished&quot; &#124; null</code> | no | <code>null</code> | `rating` for highest rated or `firstPublished` for most recent. Leave unset for best match |

**Returns**

[`SearchResults`][nyt_cooking.client.models.search.SearchResults]

## Get Recipe { #get_recipe }

`get_recipe` · Read-only

Get a full NYT Cooking recipe.

Includes the ingredients and steps (both grouped under any headings the recipe
uses), times, servings, rating and introduction.

**Parameters**

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `recipe_id` | <code>integer</code> | yes | | NYT Cooking recipe ID, from `search_recipes`, `get_recipe_box` or a recipe URL such as `/recipes/1019049-...`. |

**Returns**

[`Recipe`][nyt_cooking.client.models.recipes.Recipe]

## Get Recipe Comments { #get_recipe_comments }

`get_recipe_comments` · Read-only

Get the public reader comments on an NYT Cooking recipe.

Readers use comments to share substitutions, fixes and results, and NYT Cooking
staff sometimes reply to answer questions; their comments are marked
`is_staff`. Each comment includes all of its replies.

Comments come newest first. Set `helpful_only` to get only the comments readers
picked as most helpful, most helpful first, as on the recipe page's "Most
Helpful" tab. `total` counts every comment on the recipe, replies included,
and `helpful_total` the most helpful ones.

**Parameters**

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `recipe_id` | <code>integer</code> | yes | | NYT Cooking recipe ID, from `search_recipes`, `get_recipe_box` or a recipe URL such as `/recipes/1019049-...`. |
| `max_results` | <code>integer</code> | no | <code>20</code> | Most top-level comments to return, replies aside. |
| `helpful_only` | <code>boolean</code> | no | <code>false</code> | Whether to get only the most helpful comments. |

**Returns**

[`Comments`][nyt_cooking.client.models.comments.Comments]

## Get Recipe Box { #get_recipe_box }

`get_recipe_box` · Read-only

List the recipes the user has saved to their NYT Cooking recipe box.

Pass `folder_id` to list one folder's recipes.

**Parameters**

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `max_results` | <code>integer</code> | no | <code>48</code> | Most saved recipes to return. |
| `folder_id` | <code>integer &#124; null</code> | no | <code>null</code> | NYT Cooking folder ID, from `get_folders`. Leave unset for the whole recipe box. |

**Returns**

[`RecipeBox`][nyt_cooking.client.models.recipes.RecipeBox]

## Get Recently Viewed { #get_recently_viewed }

`get_recently_viewed` · Read-only

List the recipes the user has recently viewed on NYT Cooking.

Most recent first.

**Parameters**

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `max_results` | <code>integer</code> | no | <code>20</code> | Most recently viewed recipes to return. |

**Returns**

[`RecentlyViewed`][nyt_cooking.client.models.recipes.RecentlyViewed]

## Get Folders { #get_folders }

`get_folders` · Read-only

List the folders in the user's NYT Cooking recipe box.

Alphabetical, with each folder's ID and number of recipes.

**Returns**

[`Folders`][nyt_cooking.client.models.folders.Folders]

## Get Folder Recipes { #get_folder_recipes }

`get_folder_recipes` · Read-only

List every recipe in a folder of the user's NYT Cooking recipe box.

**Parameters**

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `folder_id` | <code>integer</code> | yes | | NYT Cooking folder ID, from `get_folders`. |

**Returns**

[`RecipeBox`][nyt_cooking.client.models.recipes.RecipeBox]

## Add Folder { #add_folder }

`add_folder` · Non-destructive

Add an empty folder to the user's NYT Cooking recipe box.

**Parameters**

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `name` | <code>string</code> | yes | | Name of the new folder. |

**Returns**

[`Folder`][nyt_cooking.client.models.folders.Folder]

## Rename Folder { #rename_folder }

`rename_folder` · Destructive

Rename a folder in the user's NYT Cooking recipe box.

**Parameters**

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `folder_id` | <code>integer</code> | yes | | NYT Cooking folder ID, from `get_folders`. |
| `name` | <code>string</code> | yes | | New name for the folder. |

**Returns**

[`Folder`][nyt_cooking.client.models.folders.Folder]

## Remove Folder { #remove_folder }

`remove_folder` · Destructive

Remove a folder from the user's NYT Cooking recipe box, deleting it.

The folder's recipes stay saved to the recipe box.

**Parameters**

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `folder_id` | <code>integer</code> | yes | | NYT Cooking folder ID, from `get_folders`. |

**Returns**

[`Folders`][nyt_cooking.client.models.folders.Folders]

## Get Recipe Save Status { #get_recipe_save_status }

`get_recipe_save_status` · Read-only

Check whether a recipe is saved to the user's NYT Cooking recipe box.

Also lists the recipe box folders it is in.

**Parameters**

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `recipe_id` | <code>integer</code> | yes | | NYT Cooking recipe ID, from `search_recipes`, `get_recipe_box` or a recipe URL such as `/recipes/1019049-...`. |

**Returns**

[`SavedRecipe`][nyt_cooking.client.models.folders.SavedRecipe]

## Add Recipe { #add_recipe }

`add_recipe` · Non-destructive

Add a recipe to the user's NYT Cooking recipe box, or to a folder in it.

Without `folder_id`, the recipe is saved to the recipe box. With `folder_id`, it
is also added to that folder, since every recipe in a folder is saved to the
recipe box. Adding a recipe that is already saved, or already in the folder,
changes nothing.

**Parameters**

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `recipe_id` | <code>integer</code> | yes | | NYT Cooking recipe ID, from `search_recipes`, `get_recipe_box` or a recipe URL such as `/recipes/1019049-...`. |
| `folder_id` | <code>integer &#124; null</code> | no | <code>null</code> | NYT Cooking folder ID to also add the recipe to, from `get_folders`. Leave unset to add it to the recipe box only. |

**Returns**

[`SavedRecipe`][nyt_cooking.client.models.folders.SavedRecipe]

## Remove Recipe { #remove_recipe }

`remove_recipe` · Destructive

Remove a recipe from the user's NYT Cooking recipe box, or from one folder.

Without `folder_id`, the recipe is removed from the recipe box and from every
folder it is in. Removing a recipe that is not saved changes nothing. With
`folder_id`, the recipe is removed from that folder only, and stays saved to the
recipe box and its other folders; it fails if the recipe is not in the folder.

**Parameters**

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `recipe_id` | <code>integer</code> | yes | | NYT Cooking recipe ID, from `get_recipe_box`, `get_folder_recipes` or `get_recipe_save_status`. |
| `folder_id` | <code>integer &#124; null</code> | no | <code>null</code> | NYT Cooking folder ID to remove the recipe from, from `get_recipe_save_status` or `get_folders`. Leave unset to remove it from the recipe box and every folder. |

**Returns**

[`SavedRecipe`][nyt_cooking.client.models.folders.SavedRecipe]

## Log In { #auth_login }

`auth_login` · Destructive

Check the user's NYT Cooking cookie and save it if NYT accepts it.

The user copies the cookie from their browser while signed in to cooking.nytimes.com
(developer tools, then cookies, then `NYT-S`). NYT must recognise it as an account
with an active NYT Cooking subscription; otherwise this fails, and nothing is saved.

**Parameters**

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `cookie` | <code>string</code> | yes | | Value of the `NYT-S` cookie. |

**Returns**

[`IsAuthenticated`][nyt_cooking.client.models.auth.IsAuthenticated]

## Log Out { #auth_logout }

`auth_logout` · Destructive

Remove the saved NYT Cooking cookie.

Returns whether the user is still logged in afterwards, which is only true when
a cookie is also configured outside the saved login, such as in the
`NYT_COOKING_COOKIE` environment variable.

**Returns**

[`IsAuthenticated`][nyt_cooking.client.models.auth.IsAuthenticated]

## Get Login Status { #get_auth_status }

`get_auth_status` · Read-only

Check with NYT whether the user is logged in with an NYT Cooking subscription.

Returns false when no cookie is saved, NYT no longer recognises it, or the
account's NYT Cooking subscription has lapsed.

**Returns**

[`IsAuthenticated`][nyt_cooking.client.models.auth.IsAuthenticated]
