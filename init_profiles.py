#!/usr/bin/env python3

import json, os, yaml

OUT = "data/profiles.yml"

DEFAULTS = {
    "incident_notification": {
        "early_warning_hours": 24,      # Art. 23(4)(a)
        "notification_hours": 72,       # Art. 23(4)(b)
        "final_report_days": 30,        # Art. 23(4)(d)
        "source": "https://eur-lex.europa.eu/eli/dir/2022/2555/oj",
        "note": "Termini della direttiva; gli Stati membri possono essere piu' severi.",
    }
}


def main():
    data = json.load(open("data/measures.json", encoding="utf-8"))
    srcs = yaml.safe_load(open("data/sources.yml", encoding="utf-8")) or {}

    doc = {}
    if os.path.exists(OUT):
        doc = yaml.safe_load(open(OUT, encoding="utf-8")) or {}
    doc.setdefault("_defaults", DEFAULTS)
    countries = doc.setdefault("countries", {})

    added = 0
    for iso, c in sorted(data["countries"].items()):
        if iso in countries:
            continue
        cfg = srcs.get(iso) or {}
        hint = max([m["entry_into_force"] for m in c["measures"]
                    if m.get("entry_into_force") and m["notified"]
                    and m["notified"] >= "2023-01-16"] or [None])
        countries[iso] = {
            "name_it": c["name"],
            "authority": cfg.get("authority", "TODO"),
            "description": "TODO — redigere in italiano con fonti proprie.",
            "entry_into_force": {
                "date": "TODO",
                "hint_eurlex": hint,
                "source": (cfg.get("urls") or ["TODO"])[0],
            },
            "registration": {"deadline": "TODO", "note": "TODO", "source": "TODO"},
            "framework": {
                "name": "TODO", "implementation_deadline": "TODO",
                "obligations_essential": "TODO", "obligations_important": "TODO",
                "counting_basis": "TODO — definisci cosa conti",
                "source": "TODO",
            },
            "reviewed_on": None,
        }
        added += 1

    with open(OUT, "w", encoding="utf-8") as f:
        yaml.safe_dump(doc, f, allow_unicode=True, sort_keys=True, default_flow_style=False)
    print("profiles.yml: %d paesi totali, %d aggiunti" % (len(countries), added))


if __name__ == "__main__":
    main()