# Search limitations

NYT Cooking's search has a couple of limitations that affect which recipes you get back.

## 960 max results

NYT returns at most 960 results for a search, however many recipes match. When a search hits the cap, its `total` reports 960 rather than the true number of matches.

That means recipes past the first 960 are left out, and there's no way to tell how many.

To avoid this, narrow the search until `total` is under 960. Tags, time limits and other criteria all shrink a search, and the search filters show how much each one would. To find out more, check out the search guides for [Python](../guides/python/search-recipes.md) and [MCP](../guides/mcp/search-recipes.md).

## Collections, repeats and overflow

NYT's search results include collections, curated groups of recipes, alongside recipes. `nyt-cooking` returns only recipes, so a page can hold fewer recipes than the page size, and `total`, which counts collections too, can be a little higher than the number of recipes you get back.

Larger searches can also repeat a few recipes across pages. And when a search hits the cap, NYT puts some extra recipes on the page after the last one, roughly one for each collection in the results.

So paging through a search yourself can return repeats and, for capped searches, miss the recipes after the last page.

[`search_recipes_paginated`](../reference/client.md#nyt_cooking.client.client.Client.search_recipes_paginated) handles this. It drops repeated recipes and keeps going past the last page until it has every result or a page adds nothing new. [`search_recipes`](../reference/client.md#nyt_cooking.client.client.Client.search_recipes) returns a single page exactly as NYT sends it, minus collections.

??? note "Why a search returns fewer recipes than `total`"

    `total` counts collections and repeated recipes. Once `nyt-cooking` leaves out collections and drops repeats, a search ends up with a few less unique recipes than `total` reports.
