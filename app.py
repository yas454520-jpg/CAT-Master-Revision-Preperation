import os
import json
import base64
import random
from datetime import date, datetime, timedelta
from pathlib import Path

import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
DATA_DIR.mkdir(exist_ok=True)

DEFAULT_SETTINGS = {
    "rc": {
        "M1": {"easy": 20, "medium": 20},
        "M2": {"easy": 20, "medium": 20},
        "M3": {"easy": 20, "medium": 20},
        "M4": {"easy": 20, "medium": 20},
        "M5": {"easy": 20, "medium": 20},
    },
    "dilr": {
        "M1": {"di": 20, "lr": 20},
        "M2": {"di": 20, "lr": 20},
        "M3": {"di": 20, "lr": 20},
        "M4": {"di": 20, "lr": 20},
    },
    "cr_bank": 1000,
    "va_bank": 500,
}

# GitHub configuration is read ONLY from environment variables.
# Never put a GitHub token in this file or in static JavaScript.
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")  # e.g. username/private-cat-tracker
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
GITHUB_DATA_DIR = os.getenv("GITHUB_DATA_DIR", "cat_data")

DATA_FILES = {
    "settings": "settings.json",
    "daily": "daily.json",
    "revision": "revision.json",
}


def github_enabled():
    return bool(GITHUB_TOKEN and GITHUB_REPO)


def local_path(kind):
    return DATA_DIR / DATA_FILES[kind]


def read_local(kind, default):
    path = local_path(kind)
    if not path.exists():
        write_local(kind, default)
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_local(kind, data):
    local_path(kind).write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def github_url(path):
    return f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"


def github_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def github_read(kind, default):
    path = f"{GITHUB_DATA_DIR}/{DATA_FILES[kind]}"
    try:
        r = requests.get(
            github_url(path),
            headers=github_headers(),
            params={"ref": GITHUB_BRANCH},
            timeout=12,
        )
        if r.status_code == 404:
            github_write(kind, default, "Initialize CAT tracker data")
            return default
        r.raise_for_status()
        payload = r.json()
        content = base64.b64decode(payload["content"]).decode("utf-8")
        return json.loads(content)
    except Exception:
        # Local cache remains useful during development if GitHub is temporarily unavailable.
        return read_local(kind, default)


def github_write(kind, data, message):
    path = f"{GITHUB_DATA_DIR}/{DATA_FILES[kind]}"
    content = json.dumps(data, indent=2, ensure_ascii=False)
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")

    sha = None
    try:
        r = requests.get(
            github_url(path),
            headers=github_headers(),
            params={"ref": GITHUB_BRANCH},
            timeout=12,
        )
        if r.ok:
            sha = r.json().get("sha")
    except Exception:
        pass

    payload = {
        "message": message,
        "content": encoded,
        "branch": GITHUB_BRANCH,
    }
    if sha:
        payload["sha"] = sha

    r = requests.put(
        github_url(path),
        headers=github_headers(),
        json=payload,
        timeout=15,
    )
    r.raise_for_status()
    write_local(kind, data)
    return True


def read_data(kind, default):
    if github_enabled():
        return github_read(kind, default)
    return read_local(kind, default)


def write_data(kind, data, message):
    if github_enabled():
        return github_write(kind, data, message)
    write_local(kind, data)
    return True


def today_key():
    return date.today().isoformat()


def clean_number(value, fallback=0, minimum=0):
    try:
        n = int(value)
        return max(minimum, n)
    except (TypeError, ValueError):
        return fallback


def generate_unique(prefix, module, difficulty, limit, count, used):
    if limit < 1:
        return []
    count = min(count, limit)
    candidates = list(range(1, limit + 1))
    random.shuffle(candidates)
    out = []
    for n in candidates:
        item = f"{module}({difficulty}){n:02d}"
        if item not in used:
            used.add(item)
            out.append(item)
        if len(out) == count:
            break
    return out


def generate_practice(settings):
    used = set()
    modules = list(settings["rc"].keys())

    # Strict 2 Easy + 2 Medium. Modules are sampled without replacement
    # when possible, so a daily set has good module diversity.
    random.shuffle(modules)
    easy_modules = modules[:2]
    remaining = [m for m in modules if m not in easy_modules]
    random.shuffle(remaining)
    medium_modules = remaining[:2]

    rc = []
    for m in easy_modules:
        rc += generate_unique(
            "RC", m, "E", settings["rc"][m]["easy"], 1, used
        )
    for m in medium_modules:
        rc += generate_unique(
            "RC", m, "M", settings["rc"][m]["medium"], 1, used
        )

    cr_bank = clean_number(settings.get("cr_bank"), 1000, 1)
    va_bank = clean_number(settings.get("va_bank"), 500, 1)

    cr_count = min(10, cr_bank)
    va_count = min(5, va_bank)

    cr_numbers = random.sample(range(1, cr_bank + 1), cr_count)
    va_numbers = random.sample(range(1, va_bank + 1), va_count)

    # Balanced DILR: 2 DI + 2 LR, using M1-M4.
    dilr = []
    di_modules = list(settings["dilr"].keys())
    lr_modules = list(settings["dilr"].keys())
    random.shuffle(di_modules)
    random.shuffle(lr_modules)

    for i in range(2):
        m = di_modules[i % len(di_modules)]
        limit = clean_number(settings["dilr"][m]["di"], 0)
        if limit:
            n = random.randint(1, limit)
            dilr.append(f"{m}(DI){n:02d}")

    for i in range(2):
        m = lr_modules[i % len(lr_modules)]
        limit = clean_number(settings["dilr"][m]["lr"], 0)
        if limit:
            n = random.randint(1, limit)
            dilr.append(f"{m}(LR){n:02d}")

    return {
        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "date": today_key(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "rc": [{"label": x, "completed": False, "accuracy": ""} for x in rc],
        "cr": [{"label": f"CR Q{n}", "completed": False, "accuracy": ""} for n in cr_numbers],
        "va": [{"label": f"VA Q{n}", "completed": False, "accuracy": ""} for n in va_numbers],
        "dilr": [{"label": x, "completed": False, "accuracy": ""} for x in dilr],
    }


def find_today(daily, set_id=None):
    today_sets = daily.get(today_key(), [])
    if set_id:
        for s in today_sets:
            if s["id"] == set_id:
                return s
    return today_sets[-1] if today_sets else None


def all_items(practice):
    for section in ("rc", "cr", "va", "dilr"):
        for item in practice.get(section, []):
            yield section, item


def accuracy_value(value):
    if isinstance(value, (int, float)):
        return max(0, min(100, float(value)))
    text = str(value or "").strip()
    if not text:
        return None
    if "/" in text:
        try:
            a, b = text.split("/", 1)
            a, b = float(a.strip()), float(b.strip())
            if b > 0:
                return max(0, min(100, a / b * 100))
        except Exception:
            return None
    try:
        return max(0, min(100, float(text)))
    except Exception:
        return None


def metrics_for_day(daily, revisions, day_key):
    sets = daily.get(day_key, [])
    counts = {"varc": 0, "dilr": 0, "qa": 0}
    scores = []

    for practice in sets:
        for section, item in all_items(practice):
            if item.get("completed"):
                if section == "dilr":
                    counts["dilr"] += 1
                else:
                    counts["varc"] += 1
            acc = accuracy_value(item.get("accuracy"))
            if item.get("completed") and acc is not None:
                scores.append(acc)

    for r in revisions:
        if r.get("date") == day_key:
            counts["qa"] += 1
            acc = accuracy_value(r.get("accuracy"))
            if acc is not None:
                scores.append(acc)

    return {
        "varc": counts["varc"],
        "dilr": counts["dilr"],
        "qa": counts["qa"],
        "accuracy": round(sum(scores) / len(scores), 1) if scores else None,
    }


@app.get("/")
def index():
    return render_template("index.html", today=today_key())


@app.get("/api/bootstrap")
def bootstrap():
    settings = read_data("settings", DEFAULT_SETTINGS)
    daily = read_data("daily", {})
    revision = read_data("revision", [])
    return jsonify({
        "today": today_key(),
        "settings": settings,
        "daily": daily,
        "revision": revision,
        "github_enabled": github_enabled(),
    })


@app.post("/api/settings")
def save_settings():
    payload = request.get_json(force=True)
    settings = {
        "rc": {},
        "dilr": {},
        "cr_bank": clean_number(payload.get("cr_bank"), 1000, 1),
        "va_bank": clean_number(payload.get("va_bank"), 500, 1),
    }

    for m in ["M1", "M2", "M3", "M4", "M5"]:
        raw = payload.get("rc", {}).get(m, {})
        settings["rc"][m] = {
            "easy": clean_number(raw.get("easy"), 20, 0),
            "medium": clean_number(raw.get("medium"), 20, 0),
        }

    for m in ["M1", "M2", "M3", "M4"]:
        raw = payload.get("dilr", {}).get(m, {})
        settings["dilr"][m] = {
            "di": clean_number(raw.get("di"), 20, 0),
            "lr": clean_number(raw.get("lr"), 20, 0),
        }

    write_data("settings", settings, f"Update CAT tracker settings - {today_key()}")
    return jsonify({"ok": True, "settings": settings})


@app.post("/api/generate")
def generate():
    settings = read_data("settings", DEFAULT_SETTINGS)
    daily = read_data("daily", {})
    practice = generate_practice(settings)
    daily.setdefault(today_key(), []).append(practice)
    write_data("daily", daily, f"Generate CAT practice set - {today_key()}")
    return jsonify({"ok": True, "practice": practice})


@app.patch("/api/practice/<set_id>")
def update_practice(set_id):
    payload = request.get_json(force=True)
    daily = read_data("daily", {})
    practice = None

    for day_sets in daily.values():
        for s in day_sets:
            if s["id"] == set_id:
                practice = s
                break
        if practice:
            break

    if not practice:
        return jsonify({"ok": False, "error": "Practice set not found"}), 404

    section = payload.get("section")
    index = payload.get("index")
    if section not in ("rc", "cr", "va", "dilr"):
        return jsonify({"ok": False, "error": "Invalid section"}), 400

    try:
        index = int(index)
        item = practice[section][index]
    except Exception:
        return jsonify({"ok": False, "error": "Invalid item"}), 400

    if "completed" in payload:
        item["completed"] = bool(payload["completed"])
    if "accuracy" in payload:
        item["accuracy"] = str(payload["accuracy"])[:20]

    write_data("daily", daily, f"Update practice item - {today_key()}")
    return jsonify({"ok": True, "item": item})


@app.post("/api/revision")
def add_revision():
    payload = request.get_json(force=True)
    chapter = str(payload.get("chapter", "")).strip()
    if not chapter:
        return jsonify({"ok": False, "error": "Chapter is required"}), 400

    created = today_key()
    stage = payload.get("stage", "New Concept")
    if stage == "New Concept":
        next_revision = (date.today() + timedelta(days=7)).isoformat()
    elif stage == "Revision 1 (7-Day)":
        next_revision = (date.today() + timedelta(days=30)).isoformat()
    else:
        next_revision = ""

    revision = read_data("revision", [])
    entry = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "date": created,
        "chapter": chapter,
        "subtopic": str(payload.get("subtopic", "")).strip(),
        "category": payload.get("category", "Arithmetic"),
        "stage": stage,
        "accuracy": str(payload.get("accuracy", "")).strip(),
        "study_minutes": clean_number(payload.get("study_minutes"), 0, 0),
        "notes": str(payload.get("notes", "")).strip(),
        "next_revision": next_revision,
    }
    revision.append(entry)
    write_data("revision", revision, f"Add QA revision - {created}")
    return jsonify({"ok": True, "entry": entry})


@app.patch("/api/revision/<entry_id>")
def update_revision(entry_id):
    payload = request.get_json(force=True)
    revision = read_data("revision", [])
    entry = next((x for x in revision if x["id"] == entry_id), None)
    if not entry:
        return jsonify({"ok": False, "error": "Revision entry not found"}), 404

    for key in ("chapter", "subtopic", "category", "stage", "accuracy", "notes"):
        if key in payload:
            entry[key] = str(payload[key])
    if "study_minutes" in payload:
        entry["study_minutes"] = clean_number(payload["study_minutes"], 0, 0)

    stage = entry.get("stage")
    if stage == "New Concept":
        entry["next_revision"] = (datetime.fromisoformat(entry["date"]).date() + timedelta(days=7)).isoformat()
    elif stage == "Revision 1 (7-Day)":
        entry["next_revision"] = (datetime.fromisoformat(entry["date"]).date() + timedelta(days=30)).isoformat()
    else:
        entry["next_revision"] = ""

    write_data("revision", revision, f"Update QA revision - {today_key()}")
    return jsonify({"ok": True, "entry": entry})


@app.post("/api/eod")
def save_eod():
    payload = request.get_json(force=True)
    daily = read_data("daily", {})
    day = today_key()
    eod = daily.setdefault("_eod", {})
    existing = eod.get(day, {})
    eod[day] = {
        "reflection": str(payload.get("reflection", "")),
        "study_minutes": clean_number(payload.get("study_minutes"), existing.get("study_minutes", 0), 0),
        "saved_at": datetime.now().isoformat(timespec="seconds"),
    }
    write_data("daily", daily, f"Save EOD log - {day}")
    return jsonify({"ok": True, "eod": eod[day]})


@app.get("/api/analytics")
def analytics():
    daily = read_data("daily", {})
    revision = read_data("revision", [])
    end = date.today()
    history = []

    for offset in range(13, -1, -1):
        d = end - timedelta(days=offset)
        key = d.isoformat()
        m = metrics_for_day(daily, revision, key)
        eod = daily.get("_eod", {}).get(key, {})
        study = sum(
            int(r.get("study_minutes", 0) or 0)
            for r in revision if r.get("date") == key
        ) + int(eod.get("study_minutes", 0) or 0)
        history.append({
            "date": key,
            "label": d.strftime("%d %b"),
            "accuracy": m["accuracy"],
            "study_minutes": study,
            "varc": m["varc"],
            "dilr": m["dilr"],
            "qa": m["qa"],
        })

    # Current streak: consecutive days with any completed/logged activity.
    streak = 0
    cursor = end
    while True:
        key = cursor.isoformat()
        m = metrics_for_day(daily, revision, key)
        has_activity = (
            m["varc"] + m["dilr"] + m["qa"] > 0
            or key in daily.get("_eod", {})
        )
        if not has_activity:
            break
        streak += 1
        cursor -= timedelta(days=1)

    today_metrics = metrics_for_day(daily, revision, today_key())
    today_study = sum(
        int(r.get("study_minutes", 0) or 0)
        for r in revision if r.get("date") == today_key()
    ) + int(daily.get("_eod", {}).get(today_key(), {}).get("study_minutes", 0) or 0)

    due = [
        r for r in revision
        if r.get("next_revision") and r["next_revision"] <= today_key()
        and r.get("stage") != "Mastered"
    ]

    category_minutes = {}
    for r in revision:
        cat = r.get("category", "Other")
        category_minutes[cat] = category_minutes.get(cat, 0) + int(r.get("study_minutes", 0) or 0)

    return jsonify({
        "today": {
            **today_metrics,
            "study_minutes": today_study,
        },
        "history": history,
        "streak": streak,
        "due_revisions": due,
        "category_minutes": category_minutes,
        "eod": daily.get("_eod", {}).get(today_key(), {}),
    })


@app.post("/api/seed-demo")
def seed_demo():
    # Optional local demo data so the dashboard is easy to preview.
    # This endpoint can be removed before deployment if desired.
    daily = read_data("daily", {})
    revision = read_data("revision", [])
    d = date.today()

    for i in range(6, 0, -1):
        key = (d - timedelta(days=i)).isoformat()
        if key not in daily:
            daily[key] = [{
                "id": f"demo-{key}",
                "date": key,
                "created_at": key,
                "rc": [
                    {"label": "M1(E)04", "completed": True, "accuracy": "80%"},
                    {"label": "M3(M)18", "completed": True, "accuracy": "3/4"},
                ],
                "cr": [{"label": "CR Q142", "completed": True, "accuracy": "70%"}],
                "va": [{"label": "VA Q21", "completed": True, "accuracy": "80%"}],
                "dilr": [{"label": "M2(DI)03", "completed": True, "accuracy": "75%"}],
            }]
            daily.setdefault("_eod", {})[key] = {
                "reflection": "Demo entry",
                "study_minutes": 120 + i * 5,
                "saved_at": key,
            }

    if not revision:
        revision.append({
            "id": "demo-revision",
            "date": (d - timedelta(days=6)).isoformat(),
            "chapter": "Time & Work",
            "subtopic": "Efficiency ratios",
            "category": "Arithmetic",
            "stage": "Revision 1 (7-Day)",
            "accuracy": "82%",
            "study_minutes": 45,
            "notes": "Demo entry",
            "next_revision": (d + timedelta(days=24)).isoformat(),
        })

    write_data("daily", daily, "Seed demo CAT tracker data")
    write_data("revision", revision, "Seed demo CAT revision data")
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
