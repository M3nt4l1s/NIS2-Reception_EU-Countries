#!/usr/bin/env python3
"""
Source of truth: https://publications.europa.eu/webapi/rdf/sparql
Directive (EU) 2022/2555, CELEX 32022L2555.
"""
import json, os, urllib.parse, urllib.request
from datetime import datetime, timezone

ENDPOINT = "https://publications.europa.eu/webapi/rdf/sparql"
CELEX = "32022L2555"
DIRECTIVE_IN_FORCE = "2023-01-17"

EU27 = {
    "AUT": ("at", "Austria"),     "BEL": ("be", "Belgio"),      "BGR": ("bg", "Bulgaria"),
    "HRV": ("hr", "Croazia"),     "CYP": ("cy", "Cipro"),       "CZE": ("cz", "Cechia"),
    "DNK": ("dk", "Danimarca"),   "EST": ("ee", "Estonia"),     "FIN": ("fi", "Finlandia"),
    "FRA": ("fr", "Francia"),     "DEU": ("de", "Germania"),    "GRC": ("gr", "Grecia"),
    "HUN": ("hu", "Ungheria"),    "IRL": ("ie", "Irlanda"),     "ITA": ("it", "Italia"),
    "LVA": ("lv", "Lettonia"),    "LTU": ("lt", "Lituania"),    "LUX": ("lu", "Lussemburgo"),
    "MLT": ("mt", "Malta"),       "NLD": ("nl", "Paesi Bassi"), "POL": ("pl", "Polonia"),
    "PRT": ("pt", "Portogallo"),  "ROU": ("ro", "Romania"),     "SVK": ("sk", "Slovacchia"),
    "SVN": ("si", "Slovenia"),    "ESP": ("es", "Spagna"),      "SWE": ("se", "Svezia"),
}

QUERY = """
PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
SELECT ?country ?nim
       (SAMPLE(?title) AS ?t) (MIN(?notified) AS ?notif)
       (MIN(?oj) AS ?ojdate) (MIN(?eif) AS ?entry)
       (SAMPLE(?link) AS ?url) (SAMPLE(?decl) AS ?declaration)
WHERE {
  ?w cdm:resource_legal_id_celex "%s"^^<http://www.w3.org/2001/XMLSchema#string> .
  ?nim cdm:measure_national_implementing_implements_resource_legal ?w ;
       cdm:measure_national_implementing_implemented_by_country ?country .
  OPTIONAL { ?nim cdm:work_title ?title }
  OPTIONAL { ?nim cdm:measure_national_implementing_date_notification ?notified }
  OPTIONAL { ?nim cdm:measure_national_implementing_date_official_journal ?oj }
  OPTIONAL { ?nim <http://publications.europa.eu/ontology/cdm#resource_legal_date_entry-into-force> ?eif }
  OPTIONAL { ?nim cdm:measure_national_implementing_national_website_link ?link }
  OPTIONAL { ?nim <http://publications.europa.eu/ontology/cdm#measure_national_implementing_declaration_transposition_member-state> ?decl }
}
GROUP BY ?country ?nim
""" % CELEX


def val(binding, key):
    v = binding.get(key)
    return v["value"] if v else None


def day(s):
    return s[:10] if s else None


def fetch():
    url = ENDPOINT + "?" + urllib.parse.urlencode({
        "query": QUERY, "format": "application/sparql-results+json"})
    req = urllib.request.Request(url, headers={"Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)["results"]["bindings"]


def main():
    rows = fetch()
    old_titles = {}
    if os.path.exists("data/measures.json"):
        prev = json.load(open("data/measures.json", encoding="utf-8"))
        for c in prev.get("countries", {}).values():
            for m in c.get("measures", []):
                if m.get("title_it") and m.get("celex_uri"):
                    old_titles[m["celex_uri"]] = m["title_it"]
    print("fetched %d measures" % len(rows))

    countries = {}
    for a3, (a2, name) in EU27.items():
        countries[a2] = {
            "iso": a2, "iso3": a3, "name": name,
            "status": "not-notified", "declared_complete": False,
            "measure_count": 0, "measures_since_directive": 0,
            "first_notification": None, "last_notification": None,
            "measures": [],
        }

    for b in rows:
        a3 = val(b, "country").rsplit("/", 1)[-1]
        if a3 not in EU27:
            continue                     
        c = countries[EU27[a3][0]]
        notified = day(val(b, "notif"))
        decl = val(b, "declaration")

        c["measures"].append({
            "title": val(b, "t"),
            "notified": notified,
            "oj_date": day(val(b, "ojdate")),
            "entry_into_force": day(val(b, "entry")),
            "url": val(b, "url"),
            "celex_uri": val(b, "nim"),
        })
        c["measure_count"] += 1
        if notified and notified >= DIRECTIVE_IN_FORCE:
            c["measures_since_directive"] += 1
        if decl and decl.endswith("_CPL"):
            c["declared_complete"] = True

    for c in countries.values():
        dates = sorted(m["notified"] for m in c["measures"] if m["notified"])
        c["first_notification"] = dates[0] if dates else None
        c["last_notification"] = dates[-1] if dates else None
        c["measures"].sort(key=lambda m: m["notified"] or "")
        if c["declared_complete"]:
            c["status"] = "declared-complete"
        elif c["measures_since_directive"]:
            c["status"] = "notified"
        else:
            c["status"] = "not-notified"
    
    for c in countries.values():
        for m in c["measures"]:
            if m.get("celex_uri") in old_titles:
                m["title_it"] = old_titles[m["celex_uri"]]
    out = {
        "directive": "Directive (EU) 2022/2555 (NIS2)",
        "celex": CELEX,
        "source": ENDPOINT,
        "source_note": ("Derived solely from national implementing measures notified to the "
                        "European Commission. Absence of a completion declaration does not "
                        "mean transposition is incomplete."),
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "countries": countries,
    }

    os.makedirs("data", exist_ok=True)
    with open("data/measures.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, sort_keys=True)

    for s in ("declared-complete", "notified", "not-notified"):
        names = [c["name"] for c in countries.values() if c["status"] == s]
        print("%-18s %2d  %s" % (s, len(names), ", ".join(sorted(names))))


if __name__ == "__main__":
    main()