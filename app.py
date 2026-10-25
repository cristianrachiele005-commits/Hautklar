"""Hautklar: Pflegeprodukt scannen und sofort sehen, ob es passt und ob es günstiger geht.

Starten mit:  streamlit run app.py
"""

from html import escape as e
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import logik as L

st.set_page_config(page_title="Hautklar", layout="centered")

FARBEN = {
    "gruen": {"bg": "#E6F3EC", "fg": "#1D6B46", "rand": "#B9DEC9"},
    "orange": {"bg": "#FCEFDD", "fg": "#8A4A06", "rand": "#F2D2A4"},
    "rot": {"bg": "#FBE9E7", "fg": "#A12A1F", "rand": "#F1C3BD"},
    "grau": {"bg": "#F1F0F4", "fg": "#5E5868", "rand": "#E4E1EA"},
}
# Stufe: (Farbe Punkt, Farbe Text, Label)
STUFEN = {
    "top": ("#1D6B46", "#1D6B46", "Gut für dich"),
    "gut": ("#3C9A6A", "#1D6B46", "Gut"),
    "neutral": ("#8C8695", "#5E5868", "Neutral"),
    "unbekannt": ("#C9C3D3", "#5E5868", "Keine Infos"),
    "achtung": ("#B42318", "#A12A1F", "Achtung"),
}
STUFEN_REIHENFOLGE = ["achtung", "top", "gut", "neutral", "unbekannt"]

CSS = """
<style>
.block-container {max-width: 540px; padding-top: 4.5rem; padding-bottom: 3rem;}
div.stButton > button {border-radius: 28px; min-height: 48px; font-weight: 700;}
.hk-logo {display:flex; align-items:center; gap:10px; font-weight:800; font-size:20px; margin-bottom:12px; color:#1E1A24;}
.hk-logo .b {width:34px; height:34px; border-radius:11px; background:#6B3FA0; display:inline-flex; align-items:center; justify-content:center;}
.hk-h1 {font-size:32px; line-height:1.15; font-weight:800; letter-spacing:-0.5px; margin:8px 0 10px; color:#1E1A24;}
.hk-lead {font-size:16px; line-height:1.5; color:#5E5868; margin:0 0 16px;}
.hk-card {background:#FFFFFF; border:1px solid #E4E1EA; border-radius:20px; padding:18px; margin:10px 0;}
.hk-feld {border-radius:20px; padding:18px; margin:12px 0; border:1px solid;}
.hk-kopf {display:flex; justify-content:space-between; align-items:center; gap:8px; margin-bottom:8px;}
.hk-label {font-size:12px; font-weight:800; letter-spacing:0.6px; text-transform:uppercase; color:#3B3544;}
.hk-pill {padding:5px 12px; border-radius:999px; background:#FFFFFF; font-size:13px; font-weight:800; white-space:nowrap;}
.hk-titel {font-size:18px; font-weight:800; margin:2px 0 6px; color:#1E1A24;}
.hk-text {font-size:15px; line-height:1.45; color:#3B3544; margin:0;}
.hk-klein {font-size:13px; color:#5E5868; margin:8px 0 0;}
.hk-alt {display:flex; gap:12px; align-items:center; justify-content:space-between; background:#FFFFFF; border-radius:14px; padding:12px 14px; margin-top:10px;}
.hk-spar {background:#E6F3EC; color:#1D6B46; border-radius:10px; padding:8px 12px; font-weight:800; font-size:14px; margin-top:6px;}
.hk-zutat {display:flex; gap:12px; align-items:flex-start; padding:10px 0; border-top:1px solid #EEEBF2;}
.hk-punkt {width:10px; height:10px; border-radius:5px; margin-top:6px; flex:none;}
.hk-chip {display:inline-block; padding:7px 14px; border-radius:999px; background:#FFFFFF; border:1px solid #E4E1EA; font-size:14px; font-weight:600; margin:0 6px 6px 0; color:#1E1A24;}
.hk-banner {background:#1D6B46; color:#FFFFFF; border-radius:16px; padding:14px 16px; font-weight:700; font-size:15px; margin:12px 0;}
.hk-frage {font-size:24px; line-height:1.25; font-weight:800; margin:16px 0 4px; color:#1E1A24;}
.hk-hinweis {font-size:15px; color:#5E5868; margin:0 0 8px;}
.hk-regel {display:flex; gap:12px; align-items:flex-start; margin:12px 0 0;}
.hk-haken {width:26px; height:26px; flex:none; border-radius:13px; background:#E6F3EC; color:#1D6B46; display:flex; align-items:center; justify-content:center; font-weight:800;}
</style>
"""

TROPFEN_SVG = (
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.2" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2.7l5.7 5.7a8 8 0 1 1-11.3 0z"></path></svg>'
)


# ---------------------------------------------------------------- Daten und Zustand

@st.cache_data
def lade_daten():
    return L.lade_json("produkte.json"), L.lade_json("inhaltsstoffe.json")


PRODUKTE, REGELN = lade_daten()
INDEX = L.baue_index(REGELN)

for schluessel, wert in {"seite": "start", "schritt": 0, "antworten": [None] * 5, "produkt": None}.items():
    st.session_state.setdefault(schluessel, wert)


def html(code):
    st.markdown(code, unsafe_allow_html=True)


def gehe(seite, **werte):
    st.session_state.seite = seite
    for k, v in werte.items():
        st.session_state[k] = v


def profil():
    antworten = st.session_state.antworten
    if None in antworten:
        return None
    return L.erstelle_profil(antworten)


def logo():
    html(f'<div class="hk-logo"><span class="b">{TROPFEN_SVG}</span>Hautklar</div>')


def kopfzeile(titel, zurueck_zu):
    c1, c2 = st.columns([1, 3], vertical_alignment="center")
    c1.button("Zurück", on_click=gehe, args=(zurueck_zu,), key=f"zurueck_{titel}")
    c2.markdown(f"**{titel}**")


# ---------------------------------------------------------------- Seite: Start

def seite_start():
    logo()
    html(
        '<div class="hk-h1">Scannen. Verstehen. Sparen.</div>'
        '<p class="hk-lead">Scanne dein Pflegeprodukt und sieh sofort, was drin ist, '
        'ob es zu deiner Haut passt und ob es das Gleiche günstiger gibt.</p>'
    )
    pr = profil()
    if pr:
        chips = "".join(f'<span class="hk-chip">{e(c)}</span>' for c in (pr["empfindlich"], "Ziel: " + pr["ziel"]))
        html(
            '<div class="hk-card"><div class="hk-label" style="color:#6B3FA0">Dein Hauttyp</div>'
            f'<div class="hk-titel" style="font-size:22px;margin:4px 0 10px">{e(pr["hauttyp"])}</div>{chips}</div>'
        )
        st.button("Produkt scannen", type="primary", use_container_width=True, on_click=gehe, args=("scan",))
        st.button("Hauttyp ändern", use_container_width=True, on_click=gehe, args=("fragen",), kwargs={"schritt": 0})
    else:
        html(
            '<div style="margin-bottom:18px">'
            f'<span class="hk-pill" style="background:{FARBEN["gruen"]["bg"]};color:{FARBEN["gruen"]["fg"]};margin-right:8px">Passt zu dir</span>'
            f'<span class="hk-pill" style="background:{FARBEN["orange"]["bg"]};color:{FARBEN["orange"]["fg"]}">Gibt es günstiger</span>'
            '</div>'
        )
        st.button("Hauttyp bestimmen", type="primary", use_container_width=True,
                  on_click=gehe, args=("fragen",), kwargs={"schritt": 0})
        st.caption("5 kurze Fragen, dauert 1 Minute. Danach merkt sich die App deinen Hauttyp.")


# ---------------------------------------------------------------- Seite: Fragen

def frage_zurueck():
    if st.session_state.schritt > 0:
        st.session_state.schritt -= 1
    else:
        st.session_state.seite = "start"


def frage_weiter():
    if st.session_state.schritt < len(L.FRAGEN) - 1:
        st.session_state.schritt += 1
    else:
        st.session_state.seite = "profil"


def seite_fragen():
    i = st.session_state.schritt
    frage = L.FRAGEN[i]
    st.progress((i + 1) / len(L.FRAGEN), text=f"Frage {i + 1} von {len(L.FRAGEN)}")
    html(f'<div class="hk-frage">{e(frage["frage"])}</div><p class="hk-hinweis">{e(frage["hinweis"])}</p>')

    wahl = st.radio(frage["frage"], frage["optionen"], index=st.session_state.antworten[i],
                    key=f"frage_{i}", label_visibility="collapsed")
    if wahl is not None:
        st.session_state.antworten[i] = frage["optionen"].index(wahl)

    c1, c2 = st.columns(2)
    c1.button("Zurück", use_container_width=True, on_click=frage_zurueck)
    letzte = i == len(L.FRAGEN) - 1
    c2.button("Profil anzeigen" if letzte else "Weiter", type="primary", use_container_width=True,
              disabled=wahl is None, on_click=frage_weiter)


# ---------------------------------------------------------------- Seite: Profil

def seite_profil():
    pr = profil()
    if pr is None:
        gehe("fragen", schritt=0)
        st.rerun()
    logo()
    chips = "".join(f'<span class="hk-chip">{e(c)}</span>' for c in (pr["empfindlich"], "Ziel: " + pr["ziel"], pr["budget_label"]))
    regeln = "".join(
        f'<div class="hk-regel"><span class="hk-haken">✓</span><div><b>{e(t)}</b><br>'
        f'<span style="color:#5E5868;font-size:14px">{e(x)}</span></div></div>'
        for t, x in pr["regeln"]
    )
    html(
        '<div class="hk-label" style="color:#6B3FA0">Dein Hautprofil</div>'
        f'<div class="hk-h1">{e(pr["hauttyp"])}</div>'
        f'<div>{chips}</div>'
        f'<div class="hk-card"><div class="hk-titel">Darauf achten wir bei dir</div>{regeln}</div>'
    )
    st.button("Produkt scannen", type="primary", use_container_width=True, on_click=gehe, args=("scan",))
    st.button("Hauttyp ändern", use_container_width=True, on_click=gehe, args=("fragen",), kwargs={"schritt": 0})


# ---------------------------------------------------------------- Seite: Scannen

SCANNER = components.declare_component("hautklar_scanner", path=str(Path(__file__).parent / "komponenten" / "scanner"))


def api_schluessel():
    try:
        schluessel = str(st.secrets["ANTHROPIC_API_KEY"])
    except Exception:
        return None
    # Leerzeichen, Zeilenumbrüche und Anführungszeichen vom Handy entfernen
    schluessel = schluessel.strip().strip('"“”„\'‘’').strip()
    return schluessel or None


@st.cache_data(show_spinner=False)
def ki_lesen(bild_bytes, schluessel):
    return L.lese_zutatenliste(bild_bytes, schluessel)


def zeige_produkt(produkt):
    st.session_state.produkt = produkt
    st.session_state.offener_barcode = None
    st.session_state.offenes_produkt = None
    st.session_state.seite = "ergebnis"
    st.rerun()


def neu_scannen():
    st.session_state.offener_barcode = None
    st.session_state.offenes_produkt = None
    st.session_state.scan_runde = st.session_state.get("scan_runde", 0) + 1


def lade_barcode(code):
    produkt = L.suche_lokal(code, PRODUKTE)
    if produkt is None:
        with st.spinner("Produkt wird gesucht"):
            produkt = L.suche_open_beauty_facts(code)
    if produkt and produkt.get("inci"):
        zeige_produkt(produkt)
    # Unbekannt oder ohne Zutatenliste: Foto der Zutatenliste verlangen
    st.session_state.offener_barcode = code
    st.session_state.offenes_produkt = produkt


def foto_bereich(key, barcode=None):
    foto = st.file_uploader("Foto der Zutatenliste", type=["jpg", "jpeg", "png", "webp"], key=key)
    if foto is None:
        return
    schluessel = api_schluessel()
    if not schluessel:
        st.error("Der API Schlüssel fehlt. Trage ANTHROPIC_API_KEY in Streamlit unter Settings bei Secrets ein.")
        return
    with st.spinner("Zutatenliste wird gelesen"):
        ergebnis = ki_lesen(foto.getvalue(), schluessel)
    if isinstance(ergebnis, str):
        st.warning(ergebnis)
        return
    ergebnis = dict(ergebnis)
    vorher = st.session_state.get("offenes_produkt") or {}
    if barcode:
        ergebnis["barcode"] = barcode
    for feld_name in ("marke", "name", "ml", "bild"):
        if vorher.get(feld_name) and (not ergebnis.get(feld_name) or ergebnis[feld_name] == "Gescanntes Produkt"):
            ergebnis[feld_name] = vorher[feld_name]
    zeige_produkt(ergebnis)


def seite_scan():
    kopfzeile("Produkt scannen", "profil")
    tab_scan, tab_foto, tab_mehr = st.tabs(["Barcode scannen", "Zutatenliste", "Weitere"])

    with tab_scan:
        offen = st.session_state.get("offener_barcode")
        if not offen:
            wert = SCANNER(key=f"scanner_{st.session_state.get('scan_runde', 0)}", default=None)
            if wert and wert.get("zeit") != st.session_state.get("letzter_scan"):
                st.session_state.letzter_scan = wert.get("zeit")
                lade_barcode(str(wert.get("code", "")).strip())
                offen = st.session_state.get("offener_barcode")
        if offen:
            st.info(f"Den Barcode {offen} kennen wir noch nicht. Fotografiere die Rückseite mit der Zutatenliste, dann prüfen wir das Produkt.")
            foto_bereich(key=f"foto_nach_scan_{offen}", barcode=offen)
            st.button("Nochmals scannen", use_container_width=True, on_click=neu_scannen)

    with tab_foto:
        st.write("Fotografiere die Rückseite mit der Liste der Inhaltsstoffe. Das klappt mit jedem Produkt.")
        foto_bereich(key="foto_direkt")

    with tab_mehr:
        st.markdown("**Barcode eintippen**")
        code = st.text_input("Barcode Nummer", placeholder="z.B. 7610000000011", label_visibility="collapsed")
        if st.button("Suchen", use_container_width=True, key="suchen"):
            code = "".join(c for c in code if c.isdigit())
            if code:
                lade_barcode(code)
                st.info("Den Barcode kennen wir noch nicht. Fotografiere die Zutatenliste im Tab Barcode scannen.")
            else:
                st.warning("Bitte eine Nummer eingeben.")

        st.markdown("**Zutatenliste einfügen**")
        name = st.text_input("Produktname", placeholder="z.B. Mein Serum")
        text = st.text_area("Zutatenliste", placeholder="Aqua, Glycerin, Niacinamide, Parfum, ...", height=110)
        c1, c2 = st.columns(2)
        preis = c1.number_input("Preis in CHF", min_value=0.0, step=0.5, value=0.0)
        ml = c2.number_input("Menge in ml", min_value=0.0, step=5.0, value=0.0)
        kategorie = st.selectbox("Kategorie", L.KATEGORIEN)
        if st.button("Prüfen", use_container_width=True, key="pruefen"):
            inci = L.zutaten_aus_text(text)
            if not inci:
                st.warning("Bitte eine Zutatenliste einfügen.")
            else:
                zeige_produkt({"barcode": "manuell", "marke": "", "name": name or "Eigenes Produkt",
                               "kategorie": kategorie, "ml": ml or None, "preis": preis or None,
                               "inci": inci, "quelle": "Eigene Eingabe"})

        st.markdown("**Demo Produkte**")
        wahl = st.selectbox("Beispielprodukt", PRODUKTE, label_visibility="collapsed",
                            format_func=lambda p: f"{p['marke']} {p['name']} ({L.chf(p['preis'])})")
        if st.button("Dieses Produkt prüfen", use_container_width=True, key="demo"):
            zeige_produkt(dict(wahl, quelle="Hautklar Datenbank"))


# ---------------------------------------------------------------- Seite: Ergebnis

def feld(titel_label, bewertung, inhalt_extra=""):
    f = FARBEN[bewertung["farbe"]]
    hinweis = f'<p class="hk-klein">{e(bewertung["hinweis"])}</p>' if bewertung.get("hinweis") else ""
    return (
        f'<div class="hk-feld" style="background:{f["bg"]};border-color:{f["rand"]}">'
        f'<div class="hk-kopf"><span class="hk-label">{titel_label}</span>'
        f'<span class="hk-pill" style="color:{f["fg"]}">{e(bewertung["label"])}</span></div>'
        f'<div class="hk-titel">{e(bewertung["titel"])}</div>'
        f'<p class="hk-text">{e(bewertung["text"])}</p>{hinweis}{inhalt_extra}</div>'
    )


def alternativen_html(alternativen):
    teile = []
    for a in alternativen:
        p = a["produkt"]
        farbe = FARBEN[a["eignung"]["farbe"]]["fg"]
        teile.append(
            '<div class="hk-alt"><div>'
            f'<div style="font-size:12px;color:#5E5868;font-weight:600">{e(p["marke"])}</div>'
            f'<div style="font-size:15px;font-weight:800;color:#1E1A24">{e(p["name"])}</div>'
            f'<div style="font-size:13px;color:#5E5868">{p["ml"]:g} ml · {e(a["gleich_text"])}</div>'
            f'<div style="font-size:13px;font-weight:700;color:{farbe}">{e(a["eignung"]["label"])}</div>'
            '</div>'
            f'<div style="font-size:17px;font-weight:800;color:#1E1A24;white-space:nowrap">{L.chf(p["preis"])}</div>'
            '</div>'
            f'<div class="hk-spar">Du sparst {L.chf(a["ersparnis"])} auf die gleiche Menge</div>'
        )
    return "".join(teile)


def ergaenzen(produkt):
    """Fehlen Preis, Menge oder Kategorie, kann man sie hier eintragen."""
    with st.container(border=True):
        st.markdown("**Preis und Menge ergänzen**")
        st.caption("Dann können wir die Preis Leistung beurteilen.")
        c1, c2 = st.columns(2)
        preis = c1.number_input("Preis in CHF", min_value=0.0, step=0.5, value=float(produkt.get("preis") or 0.0), key="erg_preis")
        ml = c2.number_input("Menge in ml", min_value=0.0, step=5.0, value=float(produkt.get("ml") or 0.0), key="erg_ml")
        kat = produkt.get("kategorie")
        kategorie = st.selectbox("Kategorie", L.KATEGORIEN, index=L.KATEGORIEN.index(kat) if kat in L.KATEGORIEN else 0, key="erg_kat")
        if st.button("Vergleichen", type="primary", use_container_width=True, key="erg_los"):
            st.session_state.produkt = dict(produkt, preis=preis or None, ml=ml or None, kategorie=kategorie)
            st.rerun()


def seite_ergebnis():
    pr = profil()
    produkt = st.session_state.produkt
    if produkt is None:
        gehe("scan")
        st.rerun()
    if pr is None:
        st.info("Beantworte zuerst die 5 Fragen, damit wir sagen können, ob das Produkt zu dir passt.")
        st.button("Hauttyp bestimmen", type="primary", use_container_width=True, on_click=gehe, args=("fragen",), kwargs={"schritt": 0})
        return

    kopfzeile("Ergebnis", "scan")
    analyse = L.analysiere(produkt["inci"], pr, INDEX)
    eignung = L.bewerte_eignung(analyse, pr)
    preis = L.bewerte_preis(produkt, PRODUKTE, pr, INDEX)

    # Produktbeschreibung
    if produkt.get("bild"):
        st.image(produkt["bild"], width=110)
    menge = f'{produkt["ml"]:g} ml' if produkt.get("ml") else "Menge unbekannt"
    betrag = L.chf(produkt["preis"]) if produkt.get("preis") else "Preis unbekannt"
    wirk = L.wirkstoffe(analyse)
    kurz = f"Wirkstoffe: {L.aufzaehlung(wirk)}." if wirk else "Keine bekannten Wirkstoffe gefunden."
    if eignung.get("achtung"):
        kurz += f" Achtung bei: {L.aufzaehlung(eignung['achtung'])}."
    html(
        f'<div style="font-size:13px;font-weight:600;color:#5E5868">{e(produkt.get("marke") or "")}</div>'
        f'<div style="font-size:24px;font-weight:800;line-height:1.2;color:#1E1A24">{e(produkt["name"])}</div>'
        f'<div style="font-size:15px;color:#5E5868;margin:2px 0 10px">{menge} · <b style="color:#1E1A24">{betrag}</b></div>'
        f'<p class="hk-text">{e(kurz)}</p>'
        f'<p class="hk-klein">Quelle: {e(produkt.get("quelle", ""))}</p>'
    )

    if not produkt.get("preis") or not produkt.get("ml") or not produkt.get("kategorie"):
        ergaenzen(produkt)

    if eignung["farbe"] == "gruen" and preis["farbe"] == "gruen":
        html('<div class="hk-banner">✓ Top Wahl: passt zu dir und ist preislich gut</div>')

    # Die zwei Felder
    html(feld("Preis Leistung", preis, alternativen_html(preis.get("alternativen", []))))
    for nr, a in enumerate(preis.get("alternativen", [])):
        st.button(f"{a['produkt']['name']} ansehen", key=f"alt_{nr}", use_container_width=True,
                  on_click=gehe, args=("ergebnis",), kwargs={"produkt": dict(a["produkt"], quelle="Hautklar Datenbank")})
    html(feld("Geeignet für dich", eignung,
              f'<p class="hk-klein">Basis: {e(pr["hauttyp"])}, {e(pr["empfindlich"].lower())}</p>'))

    # Was drin ist
    sortiert = sorted(analyse, key=lambda z: STUFEN_REIHENFOLGE.index(z["stufe"]))
    zeilen = []
    for z in sortiert:
        punkt, textfarbe, label = STUFEN[z["stufe"]]
        unterzeile = z["name"] + ": " + z["info"] if z["name"] != z["zutat"] else z["info"]
        zeilen.append(
            f'<div class="hk-zutat"><span class="hk-punkt" style="background:{punkt}"></span>'
            f'<div style="flex:1"><div style="font-weight:700;color:#1E1A24">{e(z["zutat"])}</div>'
            f'<div style="font-size:14px;color:#5E5868">{e(unterzeile)}</div></div>'
            f'<span style="font-size:12px;font-weight:800;color:{textfarbe};white-space:nowrap">{label}</span></div>'
        )
    html(f'<div class="hk-card"><div class="hk-titel">Was drin ist</div>{"".join(zeilen)}</div>')

    st.button("Nächstes Produkt scannen", type="primary", use_container_width=True, on_click=gehe, args=("scan",))
    st.button("Mein Hautprofil", use_container_width=True, on_click=gehe, args=("profil",))
    st.caption("Prototyp mit Beispieldaten. Ersetzt keine Beratung durch eine Fachperson.")


# ---------------------------------------------------------------- Start

html(CSS)
SEITEN = {
    "start": seite_start,
    "fragen": seite_fragen,
    "profil": seite_profil,
    "scan": seite_scan,
    "ergebnis": seite_ergebnis,
}
SEITEN[st.session_state.seite]()

# Hauttyp auf dem Handy speichern und beim nächsten Besuch wieder laden
SPEICHER = components.declare_component("hautklar_speicher", path=str(Path(__file__).parent / "komponenten" / "speicher"))


def gueltige_antworten(wert):
    return (isinstance(wert, list) and len(wert) == len(L.FRAGEN)
            and all(isinstance(x, int) and 0 <= x < len(L.FRAGEN[i]["optionen"]) for i, x in enumerate(wert)))


_antworten = st.session_state.antworten
_gespeichert = SPEICHER(wert=list(_antworten) if None not in _antworten else None, key="speicher", default=None)
if not st.session_state.get("profil_geladen") and gueltige_antworten(_gespeichert):
    st.session_state.profil_geladen = True
    if None in _antworten:
        st.session_state.antworten = list(_gespeichert)
        st.rerun()
