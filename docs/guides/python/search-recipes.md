# Search recipes

Find NYT Cooking recipes with the Python client.

??? info "Prerequisites"

    Make sure to [set up your credentials](credentials.md) first.

## Search

Call [`search_recipes_paginated`](../../reference/client.md#nyt_cooking.client.client.Client.search_recipes_paginated), which returns each match's title, author, total time and ID. Set `max_results` to limit how many it returns, or leave it unset to get every match, up to NYT's limit of 960.

```python
from nyt_cooking.client import Client

with Client() as client:
    results = client.search_recipes_paginated("lemon pasta", max_results=20)

for result in results.results:
    print(result)
```

which will output:

```text
Creamy Lemon Pasta (Barbara Kafka, 30 minutes) [8355]
Fresh Lemon and Chile Pasta (Andy Baraghani, 20 minutes) [1025508]
Summer Pasta With Zucchini, Ricotta and Basil (David Tanis, 30 minutes) [1017463]
Lemon Pesto Pasta (Anna Francese Gass, 30 minutes) [1024253]
Lemon Ricotta Pasta Bake (Adrianna Adarme, 1 hour) [782328372]
...
```

## Narrow the results

Tags must match NYT's names exactly, and a tag NYT doesn't know matches nothing. To find the tags for your search, and how many results each one leaves, call [`search_filters`](../../reference/client.md#nyt_cooking.client.client.Client.search_filters):

```python
import json

from nyt_cooking.client import Client

with Client() as client:
    filters = client.search_filters("lemon pasta")

print(json.dumps(filters.tags, indent=2))
```

which will output:

```json
{
  "appetizer": 16,
  "dairy-free": 21,
  "dessert": 1,
  "dinner": 256,
  "easy": 135,
  ...
  "vegetarian": 125,
  ...
}
```

Then pass a [`SearchCriteria`](../../reference/models/search.md#nyt_cooking.client.models.search.SearchCriteria) to narrow by:

- Tags, such as `vegetarian`, `dinner` or `one pot`
- Total time
- Top-rated recipes only
- Sort order: best match, highest rated, or most recent

```python
from nyt_cooking.client import Client
from nyt_cooking.client.models import SearchCriteria, SearchSort

with Client() as client:
    results = client.search_recipes_paginated(
        "lemon pasta",
        max_results=20,
        criteria=SearchCriteria(
            tags=["vegetarian", "one pot"],
            max_minutes=30,
            sort=SearchSort.RATING,
        ),
    )

for result in results.results:
    print(result)
```

which will output:

```text
Crispy Gnocchi With Spinach and Feta (Hetty Lui McKinnon, 25 minutes) [1025701]
One-Pan Orzo With Spinach and Feta (Melissa Clark, 30 minutes) [1021485]
Lemon-Garlic Linguine (Ali Slagle, 30 minutes) [1025371]
Creamy Cabbage Pastina (Samantha Seneviratne, 20 minutes) [777657658]
One-Pot Pasta With Ricotta and Lemon (Ali Slagle, 15 minutes) [1020290]
...
```

## Read a recipe

Pass a result's ID to [`get_recipe`](../../reference/client.md#nyt_cooking.client.client.Client.get_recipe), which returns the ingredients, steps, times and rating:

```python
with Client() as client:
    recipe = client.get_recipe(results.results[1].id)

print(recipe)
```

which will output:

```text
One-Pan Orzo With Spinach and Feta

By Melissa Clark | 30 minutes | 4 servings | 4.5/5 (23313 ratings)

Similar to spanakorizo, a Greek spinach and rice dish...

Ingredients
- 2 tablespoons unsalted butter
- 4 large scallions, trimmed and thinly sliced
- 2 large garlic cloves, minced
...

Steps
1. Heat a 10-inch skillet over medium, then melt butter, 30 seconds to 1 minute. ...
...

https://cooking.nytimes.com/recipes/1021485-one-pan-orzo-with-spinach-and-feta
```
