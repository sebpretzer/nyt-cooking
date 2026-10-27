# Search recipes

Find NYT Cooking recipes by asking your assistant.

??? info "Prerequisites"

    Make sure to [set up your credentials](credentials.md) first.

## Search

Ask your assistant for recipes, such as:

```text
Find me lemon pasta recipes on NYT Cooking.
```

It calls [`search_recipes`](../../reference/mcp.md#search_recipes), which returns each match's title, author, total time and ID:

```json
{
  "query": "lemon pasta",
  "results": [
    {
      "id": 8355,
      "name": "Creamy Lemon Pasta",
      "byline": "Barbara Kafka",
      "total_time": "30 minutes",
      "image": {...},
      "has_video": false,
      "url": "https://cooking.nytimes.com/recipes/8355"
    },
    {
      "id": 1025508,
      "name": "Fresh Lemon and Chile Pasta",
      "byline": "Andy Baraghani",
      "total_time": "20 minutes",
      ...
    },
    ...
  ],
  "pagination": {
    "total": 312,
    "page": 1,
    "max_page": 7
  }
}
```

## Narrow the results

Ask for limits in the same request, such as:

```text
Find vegetarian one-pot lemon pasta recipes under 30 minutes, highest rated first.
```

You can narrow by:

- Tags, such as `vegetarian`, `dinner` or `one pot`
- Total time
- Top-rated recipes only
- Sort order: best match, highest rated, or most recent

Your assistant calls [`get_search_filters`](../../reference/mcp.md#get_search_filters) first to find the tags that match your search:

```json
{
  "query": "lemon pasta",
  "total": 312,
  "tags": {
    "appetizer": 16,
    "dairy-free": 21,
    "dessert": 1,
    "dinner": 256,
    "easy": 135,
    ...
    "vegetarian": 125,
    ...
  },
  "cook_times": {
    "20": 57,
    "30": 172,
    "45": 252,
    "60": 289
  },
  "top_rated": 135
}
```

Then it calls [`search_recipes`](../../reference/mcp.md#search_recipes) with those limits:

```json
{
  "query": "lemon pasta",
  "results": [
    {
      "id": 1025701,
      "name": "Crispy Gnocchi With Spinach and Feta",
      "byline": "Hetty Lui McKinnon",
      "total_time": "25 minutes",
      ...
    },
    {
      "id": 1021485,
      "name": "One-Pan Orzo With Spinach and Feta",
      "byline": "Melissa Clark",
      "total_time": "30 minutes",
      ...
    },
    ...
  ],
  "pagination": {
    "total": 11,
    "page": 1,
    "max_page": 1
  }
}
```

## Read a recipe

Ask for one of the results, such as:

```text
Show me the second one.
```

It calls [`get_recipe`](../../reference/mcp.md#get_recipe), which returns the ingredients, steps, times and rating:

```json
{
  "id": 1021485,
  "name": "One-Pan Orzo With Spinach and Feta",
  "byline": "Melissa Clark",
  "url": "https://cooking.nytimes.com/recipes/1021485-one-pan-orzo-with-spinach-and-feta",
  "servings": "4 servings",
  "total_time": {
    "display": "30 minutes",
    "minutes": 30
  },
  ...
  "rating": {
    "value": 4.5,
    "total": 23313
  },
  "description": "Similar to spanakorizo, a Greek spinach and rice dish...",
  "ingredients": [
    {
      "name": "",
      "ingredients": [
        {
          "quantity": "2",
          "text": "tablespoons unsalted butter"
        },
        {
          "quantity": "4",
          "text": "large scallions, trimmed and thinly sliced"
        },
        ...
      ]
    }
  ],
  "steps": [
    {
      "name": "",
      "steps": [
        {
          "number": 1,
          "description": "Heat a 10-inch skillet over medium, then melt butter, 30 seconds to 1 minute. ..."
        },
        ...
      ]
    }
  ]
}
```
