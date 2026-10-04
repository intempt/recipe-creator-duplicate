#!/usr/bin/env python3
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    yaml = None

MAX_RECIPE_BYTES = 250 * 1024
BODY_MARKER = "<!-- generated from the frontmatter by scripts/rebuild_bodies.py; edit the frontmatter -->"
INTAKE_REQUIRED = ["id", "title", "slash_command", "group", "owner", "summary"]

SECRETS = [
    (re.compile(r"\bsk-(live|test|proj)?-?[A-Za-z0-9]{16,}"), "an API secret key"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "an AWS access key"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"), "a GitHub token"),
    (re.compile(r"\bxox[abpors]-[A-Za-z0-9-]{10,}"), "a Slack token"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "a private key"),
    (re.compile(r"\b(api[_-]?key|secret|password|token)\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{16,}", re.I), "a credential assignment"),
]
INVISIBLE = re.compile("[\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff]")
DASHES = re.compile("[\u2013\u2014]")

BUILDABLE = {
    "email_html": "a designed marketing email (HTML)",
    "email_plain": "a plain-text email",
    "image": "an image",
    "sms": "an SMS text message",
    "push": "a push notification",
    "slack": "a Slack message",
    "json": "a JSON content asset",
    "avatar": "a brand avatar",
    "pose": "a brand pose",
    "scene": "a brand scene",
    "design_system": "a brand design system",
    "segment": "a segment of users or accounts",
    "event": "an event definition",
    "attribute": "an attribute on users or accounts",
}
COMING_SOON = {
    "dashboard": "a dashboard",
    "report": "an insights, funnel, retention or paths report",
    "journey": "a journey",
    "workflow": "a workflow and its steps",
    "experiment": "an A/B experiment",
    "personalization": "a website personalization",
    "recommendation": "a product recommendation",
    "video": "a video",
    "page": "a landing page",
    "content": "a generic content asset",
    "snippet": "a reusable content snippet",
    "agent": "a custom agent",
    "meeting": "a meeting action",
    "meeting_type": "a meeting type",
    "account": "an account update",
    "task": "a task",
}
GROUPS = [
    "Segments", "Creative", "Content", "Reports", "Dashboards", "Workflows", "Journeys",
    "Experiments", "Personalizations", "Recommendations", "Meetings", "Agents",
]

KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SLASH = re.compile(r"^/[a-z0-9]+(-[a-z0-9]+)*$")
BRACES = re.compile(r"\{\{|\}\}")
FRONTMATTER_CONTRACT = re.compile(r"^---\n([\s\S]*?)\n---\n?([\s\S]*)$")
FRONTMATTER_INTAKE = re.compile(r"^---\n([\s\S]*?)\n---\n?")

REQUIRED_TOP = ["id", "title", "slash_command", "group", "owner", "summary", "steps"]
REQUIRED_STEP = ["id", "title", "summary", "builds", "description"]
ALLOWED_STEP = {"id", "title", "summary", "builds", "description", "dependsOn"}
TOUCHES_KEYS = ["reads", "writes", "never"]
INPUT_KEYS = ["input", "what_the_installer_supplies", "if_missing"]
SUMMARY_MAX = 200
STEP_TITLE_MAX = 60


def is_blank(value):
    if value is None or value is False or value == "" or (isinstance(value, (int, float)) and not isinstance(value, bool) and value == 0):
        return True
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def text(value):
    if is_blank(value):
        return ""
    if value is True:
        return "true"
    return str(value)


def as_list(value):
    if is_blank(value):
        return []
    return value if isinstance(value, list) else [value]


def intake_scalar(fm, key):
    line = re.search(r"^" + re.escape(key) + r":[ \t]*(.*)$", fm, re.M)
    if not line:
        return ""
    value = line.group(1).strip()
    if value and not re.match(r"^[>|][-+]?$", value):
        return re.sub(r"^[\"']|[\"']$", "", value)
    rest = fm[fm.index(line.group(0)) + len(line.group(0)):]
    block = re.match(r"^\n((?:[ \t]+.*\n?)+)", rest)
    return re.sub(r"\s+", " ", block.group(1).strip()) if block else ""


def intake_problems(source):
    problems = []
    if len(source.encode("utf-8")) > MAX_RECIPE_BYTES:
        problems.append("The file is over 250 KB.")
    match = FRONTMATTER_INTAKE.match(source)
    if not match:
        problems.append("The file has no YAML frontmatter. A recipe.md starts with --- and the recipe fields.")
        return problems
    fm = match.group(1)
    for key in INTAKE_REQUIRED:
        if not intake_scalar(fm, key):
            problems.append(f"The frontmatter has no {key}.")
    steps_at = re.search(r"^steps:", fm, re.M)
    tail = fm[steps_at.start():] if steps_at else ""
    if not re.findall(r"^[ \t]*- id: s\d+", tail, re.M):
        problems.append("The recipe has no steps. Each step starts with - id: s1, s2 and so on.")
    for pattern, label in SECRETS:
        if pattern.search(source):
            problems.append(f"The file contains what looks like {label}. Remove secrets before submitting.")
    if INVISIBLE.search(source):
        problems.append("The file contains invisible characters. Everything a recipe does has to be readable.")
    if re.search(r"<!--[\s\S]*?-->", source.replace(BODY_MARKER, "")):
        problems.append("The file contains a hidden comment. Everything a recipe does has to be readable on the page.")
    return problems


def string_list_problems(value, label):
    if not isinstance(value, list) or len(value) == 0:
        return [f"{label} must be a non-empty list"]
    problems = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            problems.append(f"{label} has an empty or non-text entry")
        elif DASHES.search(item):
            problems.append(f"{label} has an em-dash or en-dash")
    return problems


def declaration_problems(front):
    problems = []
    touches = front.get("touches")
    if not isinstance(touches, dict):
        problems.append("touches is required: reads, writes and never, each a list")
    else:
        for unknown in sorted(k for k in touches if k not in TOUCHES_KEYS):
            problems.append(f"touches has unknown key '{unknown}'")
        for key in TOUCHES_KEYS:
            problems.extend(string_list_problems(touches.get(key), f"touches.{key}"))
    if "does_not_claim" in front:
        problems.extend(string_list_problems(front.get("does_not_claim"), "does_not_claim"))
    if "inputs" in front:
        inputs = front.get("inputs")
        if not isinstance(inputs, list) or len(inputs) == 0:
            problems.append("inputs must be a non-empty list when present")
        else:
            for n, row in enumerate(inputs, start=1):
                if not isinstance(row, dict):
                    problems.append(f"inputs row {n} is not a mapping")
                    continue
                for unknown in sorted(k for k in row if k not in INPUT_KEYS):
                    problems.append(f"inputs row {n} has unknown key '{unknown}'")
                for key in INPUT_KEYS:
                    value = row.get(key)
                    if not isinstance(value, str) or not value.strip():
                        problems.append(f"inputs row {n}: {key} is required")
                    elif DASHES.search(value):
                        problems.append(f"inputs row {n}: {key} has an em-dash or en-dash")
    return problems


def tree_folders(path):
    resolved = os.path.abspath(path)
    id_dir = os.path.dirname(resolved)
    owner_dir = os.path.dirname(id_dir)
    recipes_dir = os.path.dirname(owner_dir)
    if os.path.basename(resolved) != "recipe.md" or os.path.basename(recipes_dir) != "recipes":
        return None
    return os.path.basename(id_dir), os.path.basename(owner_dir)


def contract_problems(front, path):
    problems = []
    tree = tree_folders(path)
    for key in REQUIRED_TOP:
        if is_blank(front.get(key)):
            problems.append(f"{key} is required")
    rid = text(front.get("id"))
    if rid and not KEBAB.match(rid):
        problems.append(f"id '{rid}' must be kebab-case")
    if rid and tree and tree[0] != rid:
        problems.append(f"folder '{tree[0]}' must equal id '{rid}'")
    owner = text(front.get("owner"))
    if owner and tree and tree[1] != owner:
        problems.append(f"owner '{owner}' must equal the owner folder '{tree[1]}'")
    if owner and not KEBAB.match(owner):
        problems.append(f"owner '{owner}' must be kebab-case")
    slash = text(front.get("slash_command"))
    if slash and not SLASH.match(slash):
        problems.append(f"slash_command '{slash}' must match /kebab-case")
    summary = text(front.get("summary")).strip()
    if len(summary) > SUMMARY_MAX:
        problems.append(f"summary is {len(summary)} chars, max {SUMMARY_MAX}")
    seen = []
    for index, step in enumerate(as_list(front.get("steps")), start=1):
        where = f"step {index}"
        if not isinstance(step, dict):
            problems.append(f"{where} is not a mapping")
            continue
        for key in REQUIRED_STEP:
            if not text(step.get(key)).strip():
                problems.append(f"{where}: {key} is required")
        sid = step.get("id")
        if sid != f"s{index}":
            problems.append(f"{where}: id must be s{index}, steps are numbered in order")
        if len(text(step.get("title"))) > STEP_TITLE_MAX:
            problems.append(f"{where}: title over {STEP_TITLE_MAX} chars")
        builds = step.get("builds")
        if not is_blank(builds):
            name = str(builds)
            if name not in BUILDABLE and name not in COMING_SOON:
                problems.append(f"{where}: builds '{name}' is not a known entity")
        if BRACES.search(text(step.get("description"))):
            problems.append(f"{where}: description has curly braces; name the earlier step by its title instead")
        for dep in as_list(step.get("dependsOn")):
            if dep not in seen:
                problems.append(f"{where}: dependsOn '{dep}' is not an earlier step")
        for unknown in sorted(k for k in step if k not in ALLOWED_STEP):
            problems.append(f"{where}: unknown field '{unknown}'; command, entity, kind and arguments come from the step check, not the file")
        seen.append(sid)
    problems.extend(declaration_problems(front))
    keys = []
    for output in as_list(front.get("outputs")):
        o = output if isinstance(output, dict) else {}
        key = o.get("key")
        if is_blank(key):
            problems.append("an output has no key")
        elif key in keys:
            problems.append(f"output key '{key}' is declared twice")
        keys.append(key)
        if o.get("producedByStep") not in seen:
            problems.append(f"output '{key}': producedByStep must name a step id")
    return problems


def availability(front):
    waiting = sorted({str(s.get("builds")) for s in as_list(front.get("steps")) if isinstance(s, dict) and s.get("builds") is not None and str(s.get("builds")) not in BUILDABLE})
    return ("install_now" if not waiting else "coming_soon"), waiting


def warnings_for(source, front):
    warnings = []
    if DASHES.search(source):
        warnings.append("The file has an em-dash or en-dash. Use a colon, a comma or a full stop.")
    group = text(front.get("group"))
    if group and group not in GROUPS:
        warnings.append(f"group '{group}' is not one of the Marketplace groups: {', '.join(GROUPS)}")
    for index, step in enumerate(as_list(front.get("steps")), start=1):
        if isinstance(step, dict) and re.search(r"\[[A-Za-z][^\]]*\]", text(step.get("description"))):
            warnings.append(f"step {index}: description has a bracket placeholder; write the real value or add an inputs row")
    return warnings


def validate(path):
    with open(path, "r", encoding="utf-8", newline="") as handle:
        raw = handle.read()
    problems = intake_problems(raw)
    normalized = raw.replace("\r\n", "\n").replace("\r", "\n")
    match = FRONTMATTER_CONTRACT.match(normalized)
    front = None
    if not match:
        problems.append("no YAML frontmatter")
    else:
        try:
            front = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError as err:
            problems.append(f"YAML error: {err}")
        if front is not None and not isinstance(front, dict):
            problems.append("frontmatter must be a YAML mapping")
            front = None
    if front is not None:
        problems.extend(contract_problems(front, path))
    seen = set()
    unique = [p for p in problems if not (p in seen or seen.add(p))]
    status, waiting = availability(front) if front is not None else (None, [])
    return {
        "valid": len(unique) == 0,
        "problems": unique,
        "warnings": warnings_for(raw, front) if front is not None else [],
        "availability": status,
        "waitingOn": waiting,
        "bytes": len(raw.encode("utf-8")),
    }


def main(argv):
    args = [a for a in argv if a != "--json"]
    as_json = "--json" in argv
    if len(args) != 1:
        print("Usage: validate_recipe.py <recipe.md> [--json]", file=sys.stderr)
        return 2
    if yaml is None:
        print("PyYAML is missing. Install it with: python3 -m pip install --user pyyaml", file=sys.stderr)
        return 2
    path = args[0]
    try:
        result = validate(path)
    except OSError as err:
        print(f"Cannot read {path}: {err}", file=sys.stderr)
        return 2
    if as_json:
        print(json.dumps(result, indent=2))
        return 0 if result["valid"] else 1
    if result["valid"]:
        print(f"{os.path.abspath(path)}: valid")
        label = "Install now" if result["availability"] == "install_now" else "Coming soon, waiting on: " + ", ".join(result["waitingOn"])
        print(f"Availability: {label}")
    else:
        count = len(result["problems"])
        print(f"{os.path.abspath(path)}: {count} problem{'' if count == 1 else 's'}")
        for problem in result["problems"]:
            print(f"  - {problem}")
    for warning in result["warnings"]:
        print(f"  warning: {warning}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
