# What a step can build

Every step has one `builds` value. It must be one of the names below, exactly as written.

## Install now

The engine builds these today. A recipe where every step is on this list is **Install now**.

| builds | What it makes |
|---|---|
| `segment` | a segment of users or accounts |
| `attribute` | an attribute on users or accounts |
| `event` | an event definition |
| `email_html` | a designed marketing email |
| `email_plain` | a plain-text email |
| `sms` | an SMS text message |
| `push` | a push notification |
| `slack` | a Slack message |
| `image` | an image |
| `json` | a JSON content asset |
| `avatar` | a brand avatar |
| `pose` | a brand pose |
| `scene` | a brand scene |
| `design_system` | a brand design system |

## Coming soon

The engine does not build these from a recipe yet. A recipe with any step on this list is
**Coming soon**. It still publishes, marked Coming soon, and names what it waits on. It switches to
Install now when the engine catches up.

| builds | What it makes |
|---|---|
| `dashboard` | a dashboard |
| `report` | an insights, funnel, retention or paths report |
| `journey` | a journey |
| `workflow` | a workflow and its steps |
| `experiment` | an A/B experiment |
| `personalization` | a website personalization |
| `recommendation` | a product recommendation |
| `video` | a video |
| `page` | a landing page |
| `content` | a generic content asset |
| `snippet` | a reusable content snippet |
| `agent` | a custom agent |
| `meeting` | a meeting action |
| `meeting_type` | a meeting type |
| `account` | an account update |
| `task` | a task |

## Never swap to look runnable

If the play needs a journey, the step says `builds: journey` and the recipe is Coming soon. Do not
change it to `segment` or `email_html` so it shows Install now. If the Install now part is useful
on its own, offer it to the author as a second, smaller recipe.

## Marketplace groups

`group` is one of: Segments, Creative, Content, Reports, Dashboards, Workflows, Journeys,
Experiments, Personalizations, Recommendations, Meetings, Agents. Pick the one that matches what
the recipe mostly builds. The reviewer can change it.
