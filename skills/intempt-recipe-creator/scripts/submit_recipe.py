#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_recipe

SUBMIT_URL = "https://intempt.com/recipes/api/submit"
USER_AGENT = "intempt-recipe-creator/1 (+https://github.com/intempt/recipe-creator)"
WEB_FORM = "https://intempt.com/recipes/submit"
CONSENT_VERSION = "intempt-recipes-v1"
CONSENT_TEXT = (
    "Intempt may review your recipe and, if it meets the bar, publish it with your attribution in the "
    "Intempt Collective Marketplace and in the public intempt/recipe-creator repository; may edit it for "
    "clarity and to run on the Intempt engine while the substance stays yours; your attribution and "
    "content may persist in git history after removal."
)
PROFILE_FIELDS = [("company", "company"), ("byline", "byline"), ("linkedin", "linkedin_url"), ("avatar_url", "avatar_url")]


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def canonical(profile):
    return json.dumps({k: profile[k] for k in sorted(profile) if profile[k] is not None}, separators=(",", ":"), ensure_ascii=False)


def confirm_code(recipe_sha, profile):
    return sha256_hex(f"{recipe_sha}\n{canonical(profile)}".encode("utf-8"))[:16]


def state_dir():
    root = os.environ.get("XDG_STATE_HOME") or os.path.join(os.path.expanduser("~"), ".local", "state")
    return os.path.join(root, "intempt-recipe-creator")


def build(args):
    with open(args.file, "rb") as handle:
        raw_bytes = handle.read()
    recipe_md = raw_bytes.decode("utf-8")
    creator = {"name": args.name, "email": args.email}
    for flag, field in PROFILE_FIELDS:
        value = getattr(args, flag)
        if value is not None:
            creator[field] = value
    recipe_sha = sha256_hex(recipe_md.encode("utf-8"))
    profile = dict(creator)
    profile["feedback"] = args.feedback
    return recipe_md, creator, recipe_sha, confirm_code(recipe_sha, profile)


def preview(args):
    result = validate_recipe.validate(args.file)
    if not result["valid"]:
        print(f"Not ready: {args.file} has {len(result['problems'])} problem(s).", file=sys.stderr)
        for problem in result["problems"]:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    recipe_md, creator, recipe_sha, code = build(args)
    status = "Install now" if result["availability"] == "install_now" else "Coming soon, waiting on: " + ", ".join(result["waitingOn"])
    print("Preview only. Nothing has been sent.")
    print()
    print("Recipe")
    print(f"  file:          {os.path.abspath(args.file)}")
    print(f"  size:          {result['bytes']} bytes")
    print(f"  sha256:        {recipe_sha}")
    print(f"  availability:  {status}")
    print()
    print("Creator")
    for field, value in creator.items():
        print(f"  {(field + ':').ljust(14)} {value}")
    if args.feedback is not None:
        print()
        print(f"Feedback: {args.feedback}")
    print()
    print(f"Sends to: {os.environ.get('INTEMPT_RECIPE_SUBMIT_URL') or SUBMIT_URL}")
    print()
    print("By sending, you confirm you have the right to submit this recipe and you agree:")
    print(f"  {CONSENT_TEXT}")
    print()
    print(f"Confirm code: {code}")
    print("It only works while the file and the fields above stay exactly as shown.")
    return 0


def send(args):
    if not args.rights_confirmed:
        print("Not sending: add --rights-confirmed only after the person said yes to the consent text.", file=sys.stderr)
        return 2
    result = validate_recipe.validate(args.file)
    if not result["valid"]:
        print("Not sending: the recipe no longer validates. Preview again.", file=sys.stderr)
        return 1
    recipe_md, creator, recipe_sha, code = build(args)
    if args.confirm != code:
        print("Not sending: the confirm code does not match. The file or the creator fields changed after the preview. Preview again.", file=sys.stderr)
        return 2
    request_id = str(uuid.uuid4())
    payload = {
        "recipe_md": recipe_md,
        "creator": creator,
        "consent": True,
        "consent_version": CONSENT_VERSION,
        "rights_confirmed": True,
        "source": "agent",
        "source_filename": os.path.basename(args.file),
        "sha256": recipe_sha,
        "request_id": request_id,
    }
    if args.feedback is not None:
        payload["feedback"] = args.feedback
    url = os.environ.get("INTEMPT_RECIPE_SUBMIT_URL") or SUBMIT_URL
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status, body_text = response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        status, body_text = err.code, err.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError) as err:
        print(f"Could not reach {url}: {err}. Nothing was received. Try again later or use {WEB_FORM}", file=sys.stderr)
        return 5
    try:
        body = json.loads(body_text)
    except ValueError:
        body = {}
    if status == 400:
        print("Intempt rejected the recipe:", file=sys.stderr)
        for problem in body.get("problems") or [body.get("error", "no reason given")]:
            print(f"  - {problem}", file=sys.stderr)
        return 4
    if status == 403:
        print(f"The submission endpoint only accepts this from a browser right now (403). Upload the same file at {WEB_FORM}", file=sys.stderr)
        return 4
    if status == 429:
        print("Too many submissions. Wait ten minutes, preview again and retry.", file=sys.stderr)
        return 5
    if status >= 500:
        print(f"The submission endpoint failed with {status}: {body.get('message', '')} Nothing was stored. Try later or use {WEB_FORM}", file=sys.stderr)
        return 5
    if status < 200 or status >= 300:
        print(f"The submission endpoint refused the request with {status}.", file=sys.stderr)
        return 4
    submission_id = body.get("submission_id")
    if not isinstance(submission_id, str) or not submission_id:
        print(f"The endpoint answered {status} without a submission id. request_id {request_id}", file=sys.stderr)
        return 1
    receipt = {
        "submission_id": submission_id,
        "sha256": body.get("sha256", recipe_sha),
        "request_id": request_id,
        "received_at": body.get("received_at"),
        "recipe": body.get("recipe"),
    }
    receipt_path = os.path.join(state_dir(), f"receipt-{submission_id if submission_id.replace('_', '').isalnum() else request_id}.json")
    try:
        os.makedirs(os.path.dirname(receipt_path), mode=0o700, exist_ok=True)
        with open(receipt_path, "w", encoding="utf-8") as handle:
            json.dump(receipt, handle, indent=2)
        saved = f"Receipt saved to {receipt_path}"
    except OSError:
        saved = "Could not save a receipt file. Copy the id above."
    print(f"Submitted. Submission id: {submission_id}")
    print("Keep this id. It is your receipt.")
    print(saved)
    print("It is not published yet. A person reviews it within two business days.")
    return 0


def main(argv):
    parser = argparse.ArgumentParser(prog="submit_recipe.py")
    sub = parser.add_subparsers(dest="mode", required=True)
    for mode in ("preview", "send"):
        p = sub.add_parser(mode)
        p.add_argument("file")
        p.add_argument("--name", required=True)
        p.add_argument("--email", required=True)
        p.add_argument("--company")
        p.add_argument("--byline")
        p.add_argument("--linkedin")
        p.add_argument("--avatar-url", dest="avatar_url")
        p.add_argument("--feedback")
        if mode == "send":
            p.add_argument("--confirm", required=True)
            p.add_argument("--rights-confirmed", action="store_true")
    args = parser.parse_args(argv)
    if validate_recipe.yaml is None:
        print("PyYAML is missing. Install it with: python3 -m pip install --user pyyaml", file=sys.stderr)
        return 2
    return preview(args) if args.mode == "preview" else send(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
