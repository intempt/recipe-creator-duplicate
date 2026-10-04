---
id: REPLACE-with-kebab-case-id
title: Replace with the recipe name, in your voice
slash_command: /REPLACE-with-kebab-case-id
group: Segments
owner: REPLACE-with-your-kebab-case-handle
summary: >-
  Replace with one sentence, at most 200 characters, saying what the recipe finds or builds.
description: >-
  Replace with who this recipe is for.
version: 1.0.0
prerequisites:
  events:
    - value: replace_with_the_event_name
      severity: blocking
inputs:
  - input: Replace with something only the installer has
    what_the_installer_supplies: Replace with what they give at run time
    if_missing: Replace with what happens without it
does_not_claim:
  - Replace with where a threshold came from when nothing measured it.
touches:
  reads:
    - Replace with each event, attribute or connection the steps read
  writes:
    - Replace with one line per step, for example A new segment, from step 1 "Step title"
  never:
    - Nothing runs until you approve the plan in Blu.
steps:
  - id: s1
    title: Replace with an action, under 40 characters
    summary: >-
      Replace with the concrete rule in one sentence.
    builds: segment
    description: >-
      Replace with the one instruction the engine runs. Say users or accounts, name the exact
      event, attribute and value, and write out every threshold and window.
  - id: s2
    title: Replace with the next action
    summary: >-
      Replace with the concrete rule in one sentence.
    builds: email_html
    description: >-
      Replace with the instruction. Name the earlier step by its title, for example the users in
      Replace with the step 1 title.
    dependsOn:
      - s1
outputs:
  - key: replace_with_output_key
    producedByStep: s1
    type: segment
    description: Replace with what step 1 leaves behind.
---
