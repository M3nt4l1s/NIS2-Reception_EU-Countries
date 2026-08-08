#!/usr/bin/env python3
import html, json, re, sys
import yaml
from datetime import date

def load_profiles():
    try:
        p = yaml.safe_load(open("data/profiles.yml", encoding="utf-8")) or {}
    except FileNotFoundError:
        return {}, {}
    return p.get("countries") or {}, p.get("_defaults") or {}


def todo(v):
    """Curated values render as 'Da verificare' when unset — never blank."""
    return None if v in (None, "", "TODO") else v

START, END = "<!-- CARDS:START -->", "<!-- CARDS:END -->"


DIRECTIVE_IN_FORCE = "2023-01-17"


def _in_window(v, today):
    """True se la data cade fra l'entrata in vigore della direttiva e oggi.
    Scarta anche il sentinella '1001-01-01' che EUR-Lex usa per 'data ignota'."""
    return bool(v) and DIRECTIVE_IN_FORCE <= str(v)[:10] <= today


def is_transposed(c, today):
    """Stato di trasposizione, derivato SOLO dai dati EUR-Lex: nessun campo
    compilato a mano. Vero se lo Stato ha dichiarato completa la trasposizione,
    oppure se almeno una misura notificata porta una data (entrata in vigore,
    pubblicazione in gazzetta o notifica) successiva alla direttiva.

    L'OR sui tre campi e' necessario: Italia e Portogallo hanno oj_date
    sentinella ed entry_into_force assente, e si riconoscono solo dalla data di
    notifica; Bulgaria, Estonia e Slovenia hanno notifiche del 2004-2020 perche'
    sono leggi preesistenti emendate, e si riconoscono dall'entrata in vigore."""
    if c.get("declared_complete"):
        return True
    return any(_in_window(m.get("entry_into_force"), today)
               or _in_window(m.get("oj_date"), today)
               or _in_window(m.get("notified"), today)
               for m in c["measures"])

STATUS_LABEL = {
    "trasposta": "Trasposta",
    "non-trasposta": "Non trasposta",
    "fuori-ue": "Fuori dall'UE",
}

def flag(iso):
    """ISO alpha-2 -> regional indicator emoji. 'at' -> 🇦🇹"""
    return "".join(chr(0x1F1E6 + ord(ch) - ord("a")) for ch in iso.lower())


def e(s):
    return html.escape(s or "", quote=True)


def fmt(d):
    if not d:
        return "—"
    s = d.isoformat() if hasattr(d, "isoformat") else str(d)
    y, m, dd = s[:10].split("-")
    return "%s.%s.%s" % (dd, m, y)


def meta(label, value, verified):
    mark = "verified" if verified else "curated"
    shown = e(str(value)) if value else '<span class="todo">Da verificare</span>'
    return ('<div class="meta-item"><span class="meta-label">%s</span>'
            '<span class="meta-value %s">%s</span></div>' % (e(label), mark, shown))


def card(c, prof, dflt):
    p = prof.get(c["iso"], {}) or {}
    eif = todo((p.get("entry_into_force") or {}).get("date"))
    reg = todo((p.get("registration") or {}).get("deadline"))
    inc = dict(dflt.get("incident_notification") or {})
    inc.update(p.get("incident_notification") or {})
    fw = p.get("framework") or {}
    desc = todo(p.get("description"))

    api_eif = next((m["entry_into_force"] for m in reversed(c["measures"])
                    if m.get("entry_into_force")), None)

    if p.get("non_eu"):
        stato = "fuori-ue"
    elif is_transposed(c, date.today().isoformat()):
        stato = "trasposta"
    else:
        stato = "non-trasposta"

    metas = "".join([
        meta("Entrata in vigore", fmt(eif or api_eif) if (eif or api_eif) else None,
             verified=(not eif and bool(api_eif))),
        meta("Scadenza registrazione", fmt(reg) if reg else None, False),
        meta("Notifica incidenti", "%sh / %sh / %sg" % (
            inc.get("early_warning_hours", "—"),
            inc.get("notification_hours", "—"),
            inc.get("final_report_days", "—")), False),
        meta("Framework", todo(fw.get("name")), False),
        meta("Obblighi essenziali", todo(fw.get("obligations_essential")), False),
        meta("Obblighi importanti", todo(fw.get("obligations_important")), False),
    ])

    basis = todo(fw.get("counting_basis"))
    basis_html = ('<p class="basis">Base di conteggio: %s</p>' % e(basis)) if basis else ""

    desc_html = ('<p class="descrizione">%s</p>' % e(desc).replace("\n", "<br>")) if desc \
                else '<p class="descrizione todo">Descrizione da redigere.</p>'

    recent = [m for m in c["measures"] if m["notified"] and m["notified"] >= "2023-01-16"]
    rows = []
    for m in recent:
        link = ('<a class="source-link" href="%s" target="_blank" rel="noopener noreferrer">Testo ufficiale</a>'
                % e(m["url"])) if m["url"] else ""
        titolo = e(m.get("title_it") or m["title"]) or "<em>senza titolo</em>"
        orig = ('<span class="m-orig">%s</span>' % e(m["title"])) if m.get("title_it") else ""
        rows.append('<li class="measure"><span class="m-date">%s</span>'
                    '<span class="m-title">%s</span>%s %s</li>'
                    % (fmt(m["notified"]), titolo, orig, link))
    if not rows:
        rows = ['<li class="measure todo">%s</li>' % (
            "Paese terzo: nessuna misura di recepimento NIS2, per definizione."
            if stato == "fuori-ue" else
            "Nessuna misura notificata dall'entrata in vigore della direttiva.")]

    pre = c["measure_count"] - c["measures_since_directive"]
    pre_html = ('<p class="pre-existing">Altre %d misura/e precedono la direttiva, '
                'notificate come trasposizione parziale.</p>' % pre) if pre > 0 else ""

    reviewed = p.get("reviewed_on")
    rev_html = ('<p class="reviewed">Analisi verificata il %s</p>' % e(str(reviewed))) if reviewed else ""

    return """      <div class="country-card" data-iso="%s" data-status="%s"
           data-measures="%d" data-date="%s">
        <div class="card-header">
          <span class="country-flag">%s</span>
          <div class="country-info"><span class="country-name">%s</span></div>
          <span class="status-badge %s">%s</span>
        </div>
        %s
        <div class="card-meta">%s</div>
        %s
        <div class="card-details"><div class="details-content">
          <ul class="measure-list">%s</ul>
          %s%s
        </div></div>
      </div>""" % (
        c["iso"], stato, c["measures_since_directive"], c["last_notification"] or "",
        flag(c["iso"]), e(c["name"]), stato, STATUS_LABEL[stato],
        desc_html, metas, basis_html, "".join(rows), pre_html, rev_html)

def main():
    data = json.load(open("data/measures.json", encoding="utf-8"))
    profiles, defaults = load_profiles()
    countries = sorted(data["countries"].values(), key=lambda c: c["name"])
    for iso, p in sorted(profiles.items()):
        if (p or {}).get("non_eu"):
            countries.append({
                "iso": iso, "name": p.get("name_it", iso.upper()),
                "status": "non-eu", "declared_complete": False,
                "measure_count": 0, "measures_since_directive": 0,
                "first_notification": None, "last_notification": None,
                "measures": [],
            })

    cards = "\n".join(card(c, profiles, defaults) for c in countries)

    src = open("index.html", encoding="utf-8").read()
    if START not in src or END not in src:
        sys.exit("markers not found in index.html")

    block = "%s\n%s\n      %s" % (START, cards, END)
    src = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, src, flags=re.S)

    src = re.sub(r'(<span id="last-updated">).*?(</span>)',
                 lambda m: m.group(1) + data["fetched_at"][:10] + m.group(2), src)

    open("index.html", "w", encoding="utf-8").write(src)
    print("wrote %d cards (data fetched %s)" % (len(countries), data["fetched_at"]))


if __name__ == "__main__":
    main()
