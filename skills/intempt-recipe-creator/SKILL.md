---
name: intempt-recipe-creator
description: |
  Create an Intempt recipe and submit it to the Intempt Collective Marketplace. Use when someone
  says "Create an Intempt recipe", "write an Intempt recipe", "turn my segment into a recipe",
  "validate my recipe.md" or "submit my recipe to Intempt". It interviews the author, writes a
  recipe.md the Intempt engine can run, validates it against the submission rules, shows it, and
  submits only after the author says yes to the consent text. Not for running a recipe: Blu does
  that inside Intempt.
---

# Intempt recipe creator

A recipe is one `recipe.md` file. YAML frontmatter lists the steps. Each step's `description` is the
one instruction the Intempt engine runs inside the installer's own workspace. The engine reads it
once and decides what to build. So the job is writing descriptions with nothing left to guess, and
being honest about what the recipe cannot do yet.

`SKILL_DIR` below is the folder that holds this file. Resolve it to an absolute path before running
anything. Scripts live in `SKILL_DIR/scripts`, references in `SKILL_DIR/references`.

Shape of the flow: **ask where they are starting, write the whole draft, then ask only what the
draft could not settle.** People fix a document faster than they answer a questionnaire.

## Step 1: Say what happens next

Two sentences, then go on without waiting:

> I'll ask where you're starting from, then write a full draft for you to correct. Nothing is
> sent anywhere until you see exactly what will be sent and say yes.

## Step 2: One question. Where are you starting from?

If they already said, state the route and do not ask again.

| Answer | Route |
|---|---|
| **A finished recipe.md** | Read their file. Go to Step 6 (validate). Fix only what fails, and ask before changing their logic. |
| **Something I built in Intempt** | A segment or attribute that already works in their workspace. Step 3. |
| **Just an idea** | Interview. Step 4. |

## Step 3: Read the workspace setup, never the rows

Only this route touches Intempt. Check the CLI is signed in:

```
intempt whoami
```

If that fails, ask them to run `intempt login`. Say the organization and project out loud and confirm
it is the right one before reading anything.

Read setup only: the segment's rules, the event names, the attribute names. Allowed reads are
listing segments, listing events and their attributes, and listing attribute columns. Run
`intempt --help` to find the exact read commands in their CLI version. Never read a user or account
record, never list segment members, and never create, update, delete or run anything. If a
segment's rules are not visible to you, ask them to paste the rules.

Then go to Step 4 with what you read. The interview is shorter because the setup answers the
"which event, which window" questions.

## Step 4: Draft the whole recipe

Read `references/entities.md` and `references/example-recipe.md` first. Then write the complete
file at `recipes/<owner>/<id>/recipe.md` in the current working folder:

- `owner`: the author's handle in kebab-case, for example `jane-doe` or their company. Published
  recipes live at `recipes/<author-name>/<recipe>/`, so this becomes their public path.
- `id`: the recipe name in kebab-case, same as the folder.

Ask for the play in one open question if you do not have it yet: "Tell me the play: who it is for,
what has to happen, and why it works." Then draft.

A complete draft has these fields.

| Field | Required | Rule |
|---|---|---|
| `id` | yes | kebab-case: lowercase letters and digits joined by single hyphens. Equals the folder name. |
| `title` | yes | A real name in the author's voice, not the id. |
| `slash_command` | yes | `/` plus kebab-case, usually `/<id>`. |
| `group` | yes | One Marketplace group from `references/entities.md`. |
| `owner` | yes | kebab-case. Equals the owner folder. |
| `summary` | yes | One sentence, at most 200 characters. Public. |
| `description` | no | Who the recipe is for. |
| `version` | no | `1.0.0` for a first submission. |
| `classification` | no | `product`, `mode`, `complexity`, `tags`. |
| `prerequisites` | no | Every event and every integration the steps rely on, each with `severity: blocking`. |
| `inputs` | no | Rows of `input`, `what_the_installer_supplies`, `if_missing`. Anything only the installer has. |
| `does_not_claim` | no | One plain sentence per thing nothing measured. |
| `touches` | yes | `reads`, `writes` and `never`, each a non-empty list of plain sentences. |
| `steps` | yes | At least one. Rules below. |
| `outputs` | no | One per thing the recipe leaves behind: `key`, `producedByStep`, `type`, `description`. |

Each step has exactly these keys and no others:

| Key | Required | Rule |
|---|---|---|
| `id` | yes | `s1`, `s2`, `s3` in order. Write each step as a line starting `- id: s1`. |
| `title` | yes | At most 60 characters, ideally under 40. An action. |
| `summary` | yes | The concrete rule in one sentence. Public. |
| `builds` | yes | One name from `references/entities.md`. |
| `description` | yes | The instruction the engine runs. Never published. Rules in Step 5. |
| `dependsOn` | when used | List of earlier step ids whose result this step uses. |

Never add `command`, `entity`, `kind`, `arguments`, `modelConfig`, `prompt` or `bindsAs` to a step.
The engine works those out from the description.

Derive `touches` from the steps yourself. Never ask the author for it. `writes` has one line per
step naming what it creates. `never` always includes "Nothing runs until you approve the plan in
Blu." On the idea route, `does_not_claim` always says the thresholds came from the author's
interview, not from measured data.

Leave the body under the closing `---` empty. Intempt's tooling generates it. Do not add HTML
comments anywhere: the submit form refuses any file with a hidden comment.

**Every claim in the draft is one of three things: something the author said, something you read
from their workspace setup, or a `does_not_claim` line.** There is no fourth kind. Do not invent an
event, an attribute, a value, a result or a product capability. If you are not sure the engine can
build something, it is Coming soon, not Install now.

## Step 5: Write every step description to the bar

The test: could two installers following this description end up with different things built? If
yes, it is not done. Every description:

- says users or accounts;
- names the exact event, attribute and value, as the author gave them;
- writes out every threshold, window and schedule as a number;
- does one thing. "Build a segment and email it" is two steps;
- names an earlier step by its title and lists it in `dependsOn`;
- has no curly braces, no bracket placeholders like `[Product]`, no rationale, and no other
  vendors' or model names.

Anything only the author's workspace has (a journey, a form, a link, a channel) becomes an `inputs`
row, and the description says "the link chosen for this run".

No secrets ever. A key or token never goes in the file. If the recipe needs Shopify, HubSpot, Slack
or another connector, declare it under `prerequisites` so Blu asks the installer to connect it.

No real customer data. No customer names, emails, ids or lists in the file.

## Step 6: At most three questions, one per message

Only ask when the answer changes what gets written:

- a threshold or window with no stated reason;
- a value only they know, like their event name;
- an edge the draft cannot settle, like what happens when data is missing.

Each question carries one sentence of context. "Just draft it" ends the questions; whatever is left
becomes a `does_not_claim` line. "It was arbitrary" is a fine answer and gets recorded as one.

## Step 7: Install now or Coming soon, honestly

Look up each step's `builds` in `references/entities.md`. Every step on the Install now list: the
recipe is Install now. Any step on the Coming soon list: it is Coming soon, waiting on that builder.
Say which in the conversation. Never change what a step builds to make it look runnable.

## Step 8: Validate

```
python3 "$SKILL_DIR/scripts/validate_recipe.py" recipes/<owner>/<id>/recipe.md
```

It checks the same rules as the submit form and the Intempt CLI. Exit `0` is valid, `1` lists
problems, `2` means a usage error or missing PyYAML (`python3 -m pip install --user pyyaml`). If the
Intempt CLI on this machine has the `recipe` command, `intempt recipe validate <file>` is an
equivalent check.

Fix every problem and run it again until it says valid. Treat warnings as things to fix too. Never
change the author's logic to clear a problem without asking.

## Step 9: Show it, then one stop with both ways to submit

One message with all of this:

- the full file, or its path if they can open it;
- that it validated, and whether it is Install now or Coming soon;
- that they are the last reviewer before it goes, and a person at Intempt reads it next;
- the two ways to submit:
  1. upload the file at https://intempt.com/recipes/submit, or
  2. send it from here.

Sending is never required. "Not now" is a complete answer. Do not ask twice.

If they want to send it from here, collect: full name and work email (required), and optionally
company, byline, LinkedIn URL and avatar URL (both must be `https://`). Then preview:

```
python3 "$SKILL_DIR/scripts/submit_recipe.py" preview recipes/<owner>/<id>/recipe.md \
  --name "Full Name" --email you@company.com [--company "Company"] [--byline "Byline"] \
  [--linkedin https://...] [--avatar-url https://...] [--feedback "Notes for the reviewer"]
```

Show the preview to them as printed, including this consent text word for word:

> Intempt may review your recipe and, if it meets the bar, publish it with your attribution in the
> Intempt Collective Marketplace and in the public intempt/recipe-creator repository; may edit it
> for clarity and to run on the Intempt engine while the substance stays yours; your attribution
> and content may persist in git history after removal.

Ask: "Do you have the right to submit this recipe, and do you agree to that text?" Only an explicit
yes counts. Anything else means do not send.

After a yes, run the send with the exact same fields and the confirm code from the preview:

```
python3 "$SKILL_DIR/scripts/submit_recipe.py" send recipes/<owner>/<id>/recipe.md \
  --name "Full Name" --email you@company.com [same optional fields] \
  --confirm <code from the preview> --rights-confirmed
```

Report what it prints. On success that is a submission ID: tell them to keep it. Never say the
recipe was accepted or published. It was received. If the send fails with a 403 or the service is
unavailable, tell them to upload the same file at https://intempt.com/recipes/submit.

## After submitting

- A person reads every submission and replies within two business days during early access.
- Some submissions merge into a similar recipe, some come back for another pass, some do not
  publish. A no comes with the reason.
- To withdraw a submission, email hey@intempt.com with "Recipe withdrawal, for Somya" and the
  submission ID.
- The full rules: https://intempt.com/recipes/submission-guide

## Rules

- Never sign in or read Intempt unless the route needs it.
- Never create, update, delete or run anything in the author's Intempt workspace.
- Never read a user or account record.
- Never state a claim that the author did not supply, that you did not read, or that is not a
  `does_not_claim` line.
- Never ask more than three questions, or two in one message.
- Never mark a recipe Install now by changing what a step builds.
- Never submit without an explicit yes to the consent text in this conversation.
- Never put a secret, a hidden comment, an invisible character or real customer data in the file.
