---
id: lapsed-buyer-winback
title: Win back buyers who went quiet
slash_command: /lapsed-buyer-winback
group: Segments
owner: example-author
summary: >-
  Finds customers who bought twice or more but not in the last 60 days, then writes them a short
  plain email asking what changed.
description: >-
  For ecommerce teams with repeat buyers who want to bring back the ones who stopped ordering.
version: 1.0.0
classification:
  product:
    - segments
    - marketing
  mode:
    - ecommerce
  complexity: quick
  tags:
    - winback
    - retention
prerequisites:
  events:
    - value: order_completed
      severity: blocking
inputs:
  - input: Sender name
    what_the_installer_supplies: The first name the email is signed with
    if_missing: The email is signed with the brand name.
does_not_claim:
  - The 60-day window and the two-order floor came from the author's interview, not from your order data.
  - Nothing here measures how many lapsed buyers come back.
touches:
  reads:
    - The order_completed event in your project
    - The sender name you supply when you run it
  writes:
    - A new segment, from step 1 "Find lapsed repeat buyers"
    - A new plain-text email, from step 2 "Ask what changed"
  never:
    - Nothing runs until you approve the plan in Blu.
    - It never sends the email. Sending is a separate choice you make in Intempt.
steps:
  - id: s1
    title: Find lapsed repeat buyers
    summary: >-
      Users with two or more order_completed events in total and none in the last 60 days.
    builds: segment
    description: |-
      Build a segment of users named "Lapsed repeat buyers".
      Include users who did the order_completed event at least 2 times in total.
      Exclude users who did the order_completed event in the last 60 days.
      Refresh the segment daily.
  - id: s2
    title: Ask what changed
    summary: >-
      A four-sentence plain email that asks one question and offers no discount.
    builds: email_plain
    description: |-
      Write a plain-text email for the users in Find lapsed repeat buyers.
      Subject line under 40 characters: "Quick question".
      Four sentences in the brand voice: thank them for their past orders, say it has been a while,
      ask what made them stop ordering, and say a reply goes to a real person.
      Sign it with the sender name chosen for this run. No discount, no button.
    dependsOn:
      - s1
outputs:
  - key: lapsed_repeat_buyers
    producedByStep: s1
    type: segment
    description: Repeat buyers with no order in the last 60 days.
  - key: winback_email
    producedByStep: s2
    type: email_plain
    description: The plain email for that segment.
---
