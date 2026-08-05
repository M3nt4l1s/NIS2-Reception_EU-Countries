#!/usr/bin/env python3
import json, os, sys, urllib.parse, urllib.request

KEY = os.environ.get("DEEPL_API_KEY")
URL = "https://api-free.deepl.com/v2/translate" 
BATCH = 40


def translate(texts):
    body = [("target_lang", "IT")] + [("text", t) for t in texts]
    req = urllib.request.Request(
        URL, data=urllib.parse.urlencode(body).encode(),
        headers={"Authorization": "DeepL-Auth-Key " + KEY,
                 "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return [t["text"] for t in json.load(r)["translations"]]


def main():
    if not KEY:
        sys.exit("manca DEEPL_API_KEY")
    data = json.load(open("data/measures.json", encoding="utf-8"))
    todo = [m for c in data["countries"].values() for m in c["measures"]
            if m.get("title") and not m.get("title_it")]
    print("da tradurre: %d" % len(todo))

    for i in range(0, len(todo), BATCH):
        chunk = todo[i:i + BATCH]
        for m, t in zip(chunk, translate([m["title"] for m in chunk])):
            m["title_it"] = t
        print("  %d/%d" % (min(i + BATCH, len(todo)), len(todo)))

    json.dump(data, open("data/measures.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2, sort_keys=True)
    print("fatto")


if __name__ == "__main__":
    main()