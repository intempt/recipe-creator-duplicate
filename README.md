# Intempt recipe creator

Write a go-to-market recipe with your AI agent and submit it to the
[Intempt Collective Marketplace](https://intempt.com/recipes).

A recipe is one `recipe.md` file: a plan Blu runs step by step inside the installer's own Intempt
workspace, using their access. Nothing runs until they approve it. This repository holds the agent
skill that helps you write one, a blank template, and the recipes that have been published.

## Two prompts

Paste these into Claude Code, Codex, Cursor or whatever agent you already use, one at a time:

```
Set up the Intempt recipe creator by following the steps in https://github.com/intempt/recipe-creator
```

```
Create an Intempt recipe
```

The first installs the skill. The second starts it. Keep the link out of the second prompt: a link
tells the agent to go and read files, and it then improvises instead of following the installed
skill.

## Setup steps, for the AI agent

You are an AI agent and the user asked you to set up the Intempt recipe creator. Follow these steps
in order. Run each command yourself. Do not start writing a recipe during setup.

### 1. Download this repository

```
mkdir -p "$HOME/.intempt"
if [ -d "$HOME/.intempt/recipe-creator/.git" ]; then
  git -C "$HOME/.intempt/recipe-creator" pull --ff-only
else
  git clone --depth 1 https://github.com/intempt/recipe-creator.git "$HOME/.intempt/recipe-creator"
fi
```

If `git` is not installed, download the archive instead:

```
mkdir -p "$HOME/.intempt/recipe-creator"
curl -fsSL https://codeload.github.com/intempt/recipe-creator/tar.gz/main \
  | tar xz -C "$HOME/.intempt/recipe-creator" --strip-components=1
```

The skill is now at `$HOME/.intempt/recipe-creator/skills/intempt-recipe-creator/SKILL.md`.

### 2. Install the skill for your agent

Do the one part that matches you.

**Claude Code.** Copy the skill folder into your skills folder:

```
mkdir -p "$HOME/.claude/skills/intempt-recipe-creator"
cp -R "$HOME/.intempt/recipe-creator/skills/intempt-recipe-creator/." "$HOME/.claude/skills/intempt-recipe-creator/"
```

**Codex.** Add the pointer below to `$HOME/.codex/AGENTS.md`. Create the file if it does not exist.
Skip this if the pointer is already there.

**Cursor and any other agent.** Add the pointer below to `AGENTS.md` in the root of the project
folder the user is working in. Create the file if it does not exist. Skip this if the pointer is
already there.

The pointer:

```
## Intempt recipe creator

When the user says "Create an Intempt recipe", or asks to write, validate or submit an Intempt
recipe, read $HOME/.intempt/recipe-creator/skills/intempt-recipe-creator/SKILL.md and follow it
step by step. Its folder holds the scripts and references it names.
```

Write `$HOME` as the real absolute path when you add the pointer.

### 3. Check Python and PyYAML

The validator and the submit script need Python 3 and PyYAML.

```
python3 -c "import yaml; print('pyyaml ok')"
```

If that fails, install PyYAML:

```
python3 -m pip install --user pyyaml
```

### 4. Check the install works

```
python3 "$HOME/.intempt/recipe-creator/skills/intempt-recipe-creator/scripts/validate_recipe.py" \
  "$HOME/.intempt/recipe-creator/skills/intempt-recipe-creator/references/example-recipe.md"
```

It must print `valid` and `Availability: Install now`. If it does not, tell the user which step
failed and stop.

### 5. Hand back to the user

Tell the user, in one or two lines, that setup is done and that they should now send:

```
Create an Intempt recipe
```

In Claude Code, if the skill does not load when they send it, ask them to start a new session.

## Three ways in

Pick by what you already have. All three land in the same review queue.

| You have | What to do |
|---|---|
| A finished recipe.md | Give it to your agent with the two prompts above to validate and submit it. You do not need to start over. |
| Something you built in Intempt | A segment or attribute that already works in your workspace. The recipe creator reads its setup, never its rows, and interviews you for the judgement behind it. |
| Just an idea | No file, nothing built, just a play you know works. The recipe creator starts from a conversation and drafts the recipe with you. |

You can submit three ways:

1. **Your AI agent**, with the two prompts above. It previews exactly what it will send and waits
   for your yes before anything leaves your machine.
2. **The Intempt CLI**, where your version includes the `recipe` command:

   ```
   intempt login
   intempt recipe new my-recipe
   intempt recipe validate recipe.md
   intempt recipe submit recipe.md
   ```

3. **The web form**: upload your recipe.md at https://intempt.com/recipes/submit.

The [submission guide](https://intempt.com/recipes/submission-guide) has the full rules: what makes
a strong recipe, Install now and Coming soon, what gets turned down, and API keys.

## What is in this repository

| Path | What it is |
|---|---|
| `skills/intempt-recipe-creator/SKILL.md` | The agent skill. |
| `skills/intempt-recipe-creator/scripts/validate_recipe.py` | Checks a recipe.md against the same rules as the submit form and the CLI. |
| `skills/intempt-recipe-creator/scripts/submit_recipe.py` | Previews a submission, then sends it only with a confirm code and an explicit consent flag. |
| `skills/intempt-recipe-creator/references/` | What a step can build, and a worked example. |
| `templates/recipe.md` | A blank recipe to fill in by hand. |
| `recipes/` | Published recipes, at `recipes/<author-name>/<recipe>/`. |

## What happens after you submit

You get a submission ID on screen. Save it. It is how you and we refer to the same submission.

A person reads it. Somya Nayak, who runs the Intempt Collective, reviews submissions for safety,
usefulness and whether they run, and replies within two business days during early access. Some
submissions merge into a similar recipe, some come back for another pass, and some do not publish.
A no comes with the reason.

Published recipes appear in the Intempt Collective Marketplace with your name on them, and in this
repository at `recipes/<your-name>/<recipe>/`. Creators on the
[Build track](https://intempt.com/partner#build) earn when other teams run their published recipes.

## Rights and consent

- **Your copyright.** You keep it. Submitting grants Intempt a licence to review, edit and, if it
  meets the bar, publish your recipe with attribution.
- **Your byline.** Published recipes carry your name and live at a permanent path built from it:
  `recipes/<your-name>/<recipe>/` in this repository and on intempt.com.
- **Licence.** Published recipes are distributed under this repository's [licence](LICENSE)
  (MIT) with attribution preserved. Copyright in each recipe stays with its author.
- **Withdrawal.** There is no self-service button yet, so it goes through a person. Email
  hey@intempt.com with "Recipe withdrawal, for Somya" and your submission ID.

Every submission, from any of the three ways in, asks you to agree to this text:

> Intempt may review your recipe and, if it meets the bar, publish it with your attribution in the
> Intempt Collective Marketplace and in the public intempt/recipe-creator repository; may edit it
> for clarity and to run on the Intempt engine while the substance stays yours; your attribution
> and content may persist in git history after removal.

Early access, so expect details to move. If a rule changes, we will say so here and in the
submission guide.
