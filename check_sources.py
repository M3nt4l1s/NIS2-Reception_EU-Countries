#!/usr/bin/env python3

import hashlib, json, os, urllib.request, yaml
import subprocess
import re
import html as htmlmod
from datetime import datetime, timezone


STATE = "data/source_state.json"
UA = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/139.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,it;q=0.8",
    "Upgrade-Insecure-Requests": "1",
}


_SCRIPT  = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
_COMMENT = re.compile(r"<!--.*?-->", re.S)
_TAGS    = re.compile(r"<[^>]+>")
_WS      = re.compile(r"\s+")


def normalize(raw):
    """Solo il testo visibile: niente script, stile, commenti, tag, spazi doppi."""
    text = raw.decode("utf-8", "ignore")
    text = _SCRIPT.sub(" ", text)
    text = _COMMENT.sub(" ", text)
    text = _TAGS.sub(" ", text)
    return _WS.sub(" ", htmlmod.unescape(text)).strip()


def fetch(url):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.read()
    except Exception:
        out = subprocess.run(
            ["curl", "-sL", "--max-time", "45", "-A", UA["User-Agent"], url],
            capture_output=True)
        if out.returncode != 0 or not out.stdout:
            raise
        return out.stdout


def digest(url):
    return hashlib.sha256(normalize(fetch(url)).encode("utf-8")).hexdigest()


def main():
    sources = yaml.safe_load(open("data/sources.yml", encoding="utf-8")) or {}
    old = json.load(open(STATE, encoding="utf-8")) if os.path.exists(STATE) else {}
    new, changed, manual = {}, [], []

    for iso, cfg in sources.items():
        if cfg.get("monitor") == "manual":
            manual.append(iso)
            continue
        for url in (cfg.get("urls") or []) + ([cfg["feed"]] if cfg.get("feed") else []):
            try:
                h = digest(url)
            except Exception as ex:
                print("  ! %s %s -> %s" % (iso, url, ex))
                new[url] = old.get(url)
                continue
            new[url] = {"hash": h,
                        "checked": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
            if old.get(url) and old[url]["hash"] != h:
                changed.append((iso, url))

    json.dump(new, open(STATE, "w", encoding="utf-8"), indent=2, sort_keys=True)
    print("controllate %d fonti, %d modificate" % (len(new), len(changed)))
    for iso, url in changed:
        print("  MODIFICATA %s  %s" % (iso, url))
    if manual:
        print("da controllare a mano: %s" % ", ".join(sorted(manual)))


if __name__ == "__main__":
    main()