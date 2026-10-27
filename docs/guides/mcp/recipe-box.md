# Manage your recipe box

Save recipes and organize them into folders by asking your assistant.

??? info "Prerequisites"

    [Set up your credentials](credentials.md) first.

## List your recipe box

Ask your assistant for your saved recipes, such as:

```text
Show me my NYT Cooking recipe box.
```

It calls [`get_recipe_box`](../../reference/mcp.md#get_recipe_box), which returns each saved recipe's title, author, total time and ID:

```json
{
  "recipes": [
    {
      "id": 8355,
      "name": "Creamy Lemon Pasta",
      "byline": "Barbara Kafka",
      "url": "https://cooking.nytimes.com/recipes/8355-creamy-lemon-pasta",
      "servings": "4 servings",
      "total_time": {
        "display": "30 minutes",
        "minutes": 30
      },
      "image": {...},
      "has_video": false
    },
    ...
  ],
  "pagination": {
    "total": 120,
    "page": 1,
    "max_page": 3
  }
}
```

## Save a recipe

Ask your assistant to save a recipe, such as:

```text
Save One-Pan Orzo With Spinach and Feta to my recipe box.
```

It calls [`add_recipe`](../../reference/mcp.md#add_recipe), which returns whether the recipe is saved and which folders it is in:

```json
{
  "id": 1021485,
  "name": "One-Pan Orzo With Spinach and Feta",
  "saved": true,
  "folders": []
}
```

Saving a recipe that is already saved changes nothing.

## Organize recipes into folders

Ask your assistant to create a folder and add recipes to it, such as:

```text
Make a folder called Weeknight Dinners and add the orzo to it.
```

It calls [`add_folder`](../../reference/mcp.md#add_folder), then [`add_recipe`](../../reference/mcp.md#add_recipe) with the new folder's ID:

```json
{
  "id": 1021485,
  "name": "One-Pan Orzo With Spinach and Feta",
  "saved": true,
  "folders": [
    {
      "id": 141592653,
      "name": "Weeknight Dinners",
      "description": null,
      "recipe_count": 1,
      "url": "https://cooking.nytimes.com/recipe-box/141592653"
    }
  ]
}
```

Adding a recipe to a folder also saves it to your recipe box.

To see a folder's recipes, ask for them, such as:

```text
Show me my Weeknight Dinners folder.
```

It calls [`get_folders`](../../reference/mcp.md#get_folders) to find the folder:

```json
{
  "folders": [
    {
      "id": 52817364,
      "name": "Soups",
      "description": null,
      "recipe_count": 12,
      "url": "https://cooking.nytimes.com/recipe-box/52817364"
    },
    ...
    {
      "id": 141592653,
      "name": "Weeknight Dinners",
      "description": null,
      "recipe_count": 1,
      "url": "https://cooking.nytimes.com/recipe-box/141592653"
    },
    ...
  ]
}
```

Then it calls [`get_folder_recipes`](../../reference/mcp.md#get_folder_recipes), which returns the folder's recipes in the same format as `get_recipe_box`.

You can also ask your assistant to rename or remove a folder, which calls [`rename_folder`](../../reference/mcp.md#rename_folder) or [`remove_folder`](../../reference/mcp.md#remove_folder). Removing a folder keeps its recipes saved to your recipe box.

## Remove a recipe

Ask your assistant to remove a recipe, such as:

```text
Remove the orzo from my recipe box.
```

It calls [`remove_recipe`](../../reference/mcp.md#remove_recipe), which removes the recipe from your recipe box and every folder it is in:

```json
{
  "id": 1021485,
  "name": "One-Pan Orzo With Spinach and Feta",
  "saved": false,
  "folders": []
}
```

To take it out of one folder only, name the folder, such as "Remove the orzo from Weeknight Dinners."
