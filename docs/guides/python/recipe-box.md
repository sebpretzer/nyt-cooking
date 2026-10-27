# Manage your recipe box

Save recipes and organize them into folders with the Python client.

??? info "Prerequisites"

    Make sure to [set up your credentials](credentials.md) first.

## List your recipe box

Call [`get_recipe_box_paginated`](../../reference/client.md#nyt_cooking.client.client.Client.get_recipe_box_paginated), which returns each saved recipe's title, author, total time and ID. Set `max_results` to limit how many it returns, or leave it unset to get every saved recipe.

```python
from nyt_cooking.client import Client

with Client() as client:
    box = client.get_recipe_box_paginated(max_results=20)

for recipe in box.recipes:
    print(recipe)
```

which will output:

```text
Creamy Lemon Pasta (Barbara Kafka, 30 minutes) [8355]
...
```

## Save a recipe

Pass a recipe's ID to [`save_recipe`](../../reference/client.md#nyt_cooking.client.client.Client.save_recipe), which returns whether the recipe is saved and which folders it is in:

```python
from nyt_cooking.client import Client

with Client() as client:
    print(client.save_recipe(1021485))
```

which will output:

```text
One-Pan Orzo With Spinach and Feta [1021485]: saved
```

Saving a recipe that is already saved changes nothing.

## Organize recipes into folders

Create a folder with [`create_folder`](../../reference/client.md#nyt_cooking.client.client.Client.create_folder), then pass its ID to `save_recipe`:

```python
from nyt_cooking.client import Client

with Client() as client:
    folder = client.create_folder("Weeknight Dinners")
    print(client.save_recipe(1021485, folder_id=folder.id))
```

which will output:

```text
One-Pan Orzo With Spinach and Feta [1021485]: saved, in Weeknight Dinners
```

Adding a recipe to a folder also saves it to your recipe box.

To see your folders, call [`get_folders`](../../reference/client.md#nyt_cooking.client.client.Client.get_folders). To see a folder's recipes, pass its ID to [`get_folder_recipes`](../../reference/client.md#nyt_cooking.client.client.Client.get_folder_recipes):

```python
from nyt_cooking.client import Client

with Client() as client:
    folders = client.get_folders().folders
    for folder in folders:
        print(folder)
    weeknight = next(f for f in folders if f.name == "Weeknight Dinners")
    print(client.get_folder_recipes(weeknight.id).recipes[0])
```

which will output:

```text
Soups (12 recipes) [52817364]
...
Weeknight Dinners (1 recipe) [141592653]
...
One-Pan Orzo With Spinach and Feta (Melissa Clark, 30 minutes) [1021485]
```

To rename or delete a folder, call [`rename_folder`](../../reference/client.md#nyt_cooking.client.client.Client.rename_folder) or [`delete_folder`](../../reference/client.md#nyt_cooking.client.client.Client.delete_folder). Deleting a folder keeps its recipes saved to your recipe box.

## Remove a recipe

Pass a recipe's ID to [`unsave_recipe`](../../reference/client.md#nyt_cooking.client.client.Client.unsave_recipe), which removes it from your recipe box and every folder it is in:

```python
from nyt_cooking.client import Client

with Client() as client:
    print(client.unsave_recipe(1021485))
```

which will output:

```text
One-Pan Orzo With Spinach and Feta [1021485]: not saved
```

To take it out of one folder only, pass `folder_id`.
