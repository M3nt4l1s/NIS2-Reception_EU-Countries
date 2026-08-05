import re
EU = {"at":"Austria","be":"Belgium","bg":"Bulgaria","hr":"Croatia","cy":"Cyprus",
      "cz":"Czech Republic","dk":"Denmark","ee":"Estonia","fi":"Finland","fr":"France",
      "de":"Germany","gr":"Greece","hu":"Hungary","ie":"Ireland","it":"Italy",
      "lv":"Latvia","lt":"Lithuania","lu":"Luxembourg","mt":"Malta","nl":"Netherlands",
      "pl":"Poland","pt":"Portugal","ro":"Romania","sk":"Slovakia","si":"Slovenia",
      "es":"Spain","se":"Sweden"}

src = open("world-map.svg", encoding="utf-8").read()
found = {}
for tag in re.findall(r"<path\b[^>]*>", src, re.S):
    i = re.search(r'id="([^"]+)"', tag)
    d = re.search(r'\bd="([^"]+)"', tag)
    if i and d and i.group(1) in EU:
        found[i.group(1)] = d.group(1)

for m in re.finditer(r'<g\b[^>]*\bid="([^"]+)"[^>]*>(.*?)</g>', src, re.S):
    gid, body = m.group(1), m.group(2)
    if gid in EU and gid not in found:
        ds = re.findall(r'\bd="([^"]+)"', body)
        if ds:
            found[gid] = " ".join(ds)

with open("eu-paths.html", "w", encoding="utf-8") as f:
    for iso, name in EU.items():
        if iso not in found:
            print("MISSING:", iso, name)
            continue
        f.write(f'<path class="eu-country" data-iso="{iso}" '
                f'd="{found[iso]}"><title>{name}</title></path>\n')

print(f"wrote {len(found)}/27 paths to eu-paths.html")