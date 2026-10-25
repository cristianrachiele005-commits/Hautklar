"""Logik von Hautklar: Hautprofil, Analyse der Inhaltsstoffe, Preis Leistung, Barcode.

Diese Datei braucht kein Streamlit, damit man sie einfach testen kann.
"""

import json
import re
import statistics
from pathlib import Path

DATEN = Path(__file__).parent / "daten"

# ---------------------------------------------------------------- Fragen

FRAGEN = [
    {
        "frage": "Wie fühlt sich deine Haut am Mittag an?",
        "hinweis": "Ohne Pflege am Morgen, ganz ehrlich.",
        "optionen": ["Spannt und ist trocken", "Glänzt überall", "Glänzt nur auf Stirn, Nase und Kinn", "Fühlt sich angenehm an"],
    },
    {
        "frage": "Wie reagiert deine Haut auf neue Produkte?",
        "hinweis": "Zum Beispiel Rötungen, Brennen oder Jucken.",
        "optionen": ["Oft gerötet oder brennt", "Manchmal", "Eigentlich nie"],
    },
    {
        "frage": "Wie oft hast du Pickel oder Unreinheiten?",
        "hinweis": "So warnen wir dich vor Stoffen, die Poren verstopfen.",
        "optionen": ["Oft", "Ab und zu", "Selten"],
    },
    {
        "frage": "Was ist dir am wichtigsten?",
        "hinweis": "Wähle dein Hauptziel.",
        "optionen": ["Mehr Feuchtigkeit", "Weniger Pickel", "Anti Aging", "Ebenmässiger Teint"],
    },
    {
        "frage": "Wie viel gibst du pro Produkt aus?",
        "hinweis": "Damit wir dir passende Alternativen zeigen.",
        "optionen": ["Bis CHF 15", "CHF 15 bis 40", "Über CHF 40"],
    },
]

HAUTTYPEN = ["Trockene Haut", "Fettige Haut", "Mischhaut", "Normale Haut"]
EMPFINDLICH = ["Sehr empfindlich", "Leicht empfindlich", "Robust"]
ZIELE = ["Mehr Feuchtigkeit", "Weniger Pickel", "Anti Aging", "Ebenmässiger Teint"]
ZIEL_TAGS = ["feuchtigkeit", "pickel", "aging", "teint"]
BUDGET_LABEL = ["Budget bis CHF 15", "Budget CHF 15 bis 40", "Budget über CHF 40"]
BUDGET_GRENZE = [15, 40, None]
KATEGORIEN = ["Serum", "Feuchtigkeitscreme", "Pickel und Unreinheiten", "Reinigung", "Sonnenschutz", "Andere"]


def lade_json(name):
    with open(DATEN / name, encoding="utf-8") as f:
        return json.load(f)


def chf(betrag):
    return f"CHF {betrag:.2f}"


# ---------------------------------------------------------------- Profil

def erstelle_profil(antworten):
    """antworten: Liste mit 5 Zahlen (Index der gewählten Option)."""
    typ, sens, unrein, ziel, budget = antworten
    tags = {"alle", ZIEL_TAGS[ziel]}
    if sens < 2:
        tags.add("empfindlich")
    if sens == 0:
        tags.add("sehr_empfindlich")
    if typ == 0:
        tags.add("trocken")
    if typ in (1, 2):
        tags.add("fettig")
    if unrein < 2:
        tags.add("unrein")
    if "trocken" in tags and "empfindlich" in tags:
        tags.add("trocken_empfindlich")

    regeln = []
    if "empfindlich" in tags:
        regeln.append(("Kein Alkohol, kein Parfum", "Diese Stoffe reizen empfindliche Haut am häufigsten."))
    if "unrein" in tags:
        regeln.append(("Nichts, was Poren verstopft", "Wir warnen dich bei schweren Ölen wie Kokosöl."))
    if typ == 0:
        regeln.append(("Viel Feuchtigkeit", "Glycerin, Hyaluron und Ceramide sind gut für dich."))
    if typ in (1, 2):
        regeln.append(("Leichte Texturen", "Niacinamid und Zink helfen gegen Glanz."))
    regeln.append(("Preis Leistung im Blick", "Gibt es das Gleiche günstiger, sagen wir es dir sofort."))

    return {
        "hauttyp": HAUTTYPEN[typ],
        "empfindlich": EMPFINDLICH[sens],
        "ziel": ZIELE[ziel],
        "budget_label": BUDGET_LABEL[budget],
        "budget_grenze": BUDGET_GRENZE[budget],
        "tags": sorted(tags),
        "regeln": regeln,
    }


# ---------------------------------------------------------------- Inhaltsstoffe

def normalisiere(name):
    n = name.lower().replace("*", "").strip()
    n = re.sub(r"\s+", " ", n)
    return n.strip(" .")


def zutaten_aus_text(text):
    """Macht aus einer Zutatenliste (Text) eine Liste einzelner Zutaten."""
    if not text:
        return []
    text = re.sub(r"(?i)^\s*(ingredients|ingrédients|inhaltsstoffe|zutaten|inci)\s*:", "", text)
    text = re.sub(r"\([^)]*\)", "", text)  # Klammern wie "Aqua (Water)" entfernen
    teile = re.split(r"[,;•\n]", text)
    return [t.strip(" .*_") for t in teile if t.strip(" .*_")]


def baue_index(regeln):
    index = {}
    for regel in regeln:
        for key in regel["keys"]:
            index[normalisiere(key)] = regel
    return index


def analysiere(inci, profil, index):
    """Bewertet jede Zutat für dieses Profil.

    Stufen: achtung, top (gut für dich), gut, neutral, unbekannt
    """
    tags = set(profil["tags"])
    ergebnis = []
    for zutat in inci:
        regel = index.get(normalisiere(zutat))
        if regel is None:
            ergebnis.append({"zutat": zutat, "name": zutat, "info": "Noch keine Infos in unserer Datenbank", "stufe": "unbekannt", "wirkstoff": None})
            continue
        if tags & set(regel.get("warn_wenn", [])):
            stufe = "achtung"
        elif tags & set(regel.get("gut_fuer", [])):
            stufe = "top"
        else:
            stufe = regel.get("basis", "neutral")
        ergebnis.append({
            "zutat": zutat,
            "name": regel["name"],
            "info": regel["info"],
            "stufe": stufe,
            "wirkstoff": regel.get("wirkstoff"),
        })
    return ergebnis


def wirkstoffe(analyse):
    gesehen = []
    for z in analyse:
        if z["wirkstoff"] and z["wirkstoff"] not in gesehen:
            gesehen.append(z["wirkstoff"])
    return gesehen


def aufzaehlung(namen):
    namen = list(namen)
    if len(namen) <= 1:
        return "".join(namen)
    return ", ".join(namen[:-1]) + " und " + namen[-1]


# ---------------------------------------------------------------- Geeignet für dich

def bewerte_eignung(analyse, profil):
    if not analyse:
        return {"farbe": "grau", "label": "Unklar", "titel": "Keine Zutatenliste gefunden",
                "text": "Ohne Zutatenliste können wir nicht sagen, ob das Produkt zu dir passt."}

    achtung = [z for z in analyse if z["stufe"] == "achtung"]
    top = [z for z in analyse if z["stufe"] == "top"]
    tags = set(profil["tags"])

    if not achtung:
        text = "Keine kritischen Stoffe für deine Haut."
        if top:
            namen = list(dict.fromkeys(z["name"] for z in top))[:3]
            text += f" {aufzaehlung(namen)} {'passt' if len(namen) == 1 else 'passen'} genau zu dir."
        return {"farbe": "gruen", "label": "Passt zu dir", "titel": "Gut für deine Haut", "text": text, "achtung": []}

    namen = list(dict.fromkeys(z["zutat"] for z in achtung))
    if len(achtung) == 1 and "sehr_empfindlich" not in tags:
        z = achtung[0]
        return {"farbe": "orange", "label": "Mit Vorsicht", "titel": "Geht, aber nicht perfekt",
                "text": f"Enthält {z['zutat']}. {z['info']}.", "achtung": namen}

    return {"farbe": "rot", "label": "Achtung", "titel": "Nicht ideal für deine Haut",
            "text": f"Enthält {aufzaehlung(namen)}. Bei deinem Hauttyp ({profil['hauttyp']}, {profil['empfindlich'].lower()}) "
                    f"kann das zu Rötungen, Brennen oder Pickeln führen.",
            "achtung": namen}


# ---------------------------------------------------------------- Preis Leistung

def bewerte_preis(produkt, alle_produkte, profil, index):
    preis, ml = produkt.get("preis"), produkt.get("ml")
    if not preis or not ml:
        return {"farbe": "grau", "label": "Preis fehlt", "titel": "Wie viel kostet es?",
                "text": "Gib Preis und Menge ein, dann vergleichen wir mit ähnlichen Produkten.", "alternativen": []}

    pro_ml = preis / ml
    eigene = analysiere(produkt["inci"], profil, index)
    eigene_wirk = set(wirkstoffe(eigene))
    kategorie = produkt.get("kategorie")
    gleiche_kat = [p for p in alle_produkte if p.get("kategorie") == kategorie and p.get("barcode") != produkt.get("barcode")]

    hinweis = ""
    grenze = profil.get("budget_grenze")
    if grenze and preis > grenze:
        hinweis = f"Liegt über deinem Budget von CHF {grenze}."

    alternativen = []
    for p in gleiche_kat:
        p_pro_ml = p["preis"] / p["ml"]
        if p_pro_ml >= pro_ml * 0.85:
            continue
        p_analyse = analysiere(p["inci"], profil, index)
        p_wirk = set(wirkstoffe(p_analyse))
        if not eigene_wirk:
            continue
        gleich = eigene_wirk & p_wirk
        abdeckung = len(gleich) / len(eigene_wirk)
        if abdeckung < 0.75:
            continue
        eignung = bewerte_eignung(p_analyse, profil)
        alternativen.append({
            "produkt": p,
            "abdeckung": abdeckung,
            "gleich_text": ("Gleicher Wirkstoff" if len(eigene_wirk) == 1 and abdeckung == 1
                            else f"Alle {len(eigene_wirk)} Wirkstoffe gleich" if abdeckung == 1
                            else f"{len(gleich)} von {len(eigene_wirk)} Wirkstoffen gleich"),
            "ersparnis": preis - p_pro_ml * ml,
            "eignung": eignung,
            "achtung_anzahl": len(eignung.get("achtung", [])),
            "pro_ml": p_pro_ml,
        })
    alternativen.sort(key=lambda a: (a["achtung_anzahl"], -a["abdeckung"], a["pro_ml"]))
    alternativen = alternativen[:3]

    if alternativen:
        n = len(alternativen)
        return {"farbe": "orange", "label": "Gibt es günstiger", "titel": "Gleiche Wirkung für weniger Geld",
                "text": f"Wir haben {n} {'Produkt' if n == 1 else 'Produkte'} mit den gleichen Wirkstoffen gefunden.",
                "hinweis": hinweis, "alternativen": alternativen}

    if not gleiche_kat:
        return {"farbe": "grau", "label": "Noch kein Vergleich", "titel": "Zu wenig Vergleichsprodukte",
                "text": f"Für die Kategorie {kategorie} haben wir noch keine Vergleichsprodukte.",
                "hinweis": hinweis, "alternativen": []}

    schnitt = statistics.median([p["preis"] / p["ml"] for p in gleiche_kat] + [pro_ml])
    if pro_ml <= schnitt * 1.1:
        return {"farbe": "gruen", "label": "Guter Preis", "titel": "Fairer Preis für die Qualität",
                "text": "Wir haben kein günstigeres Produkt mit gleicher Wirkung gefunden.",
                "hinweis": hinweis, "alternativen": []}
    return {"farbe": "orange", "label": "Eher teuer", "titel": "Teurer als ähnliche Produkte",
            "text": f"Ähnliche Produkte kosten im Schnitt {chf(schnitt * 10)} pro 10 ml, dieses {chf(pro_ml * 10)}.",
            "hinweis": hinweis, "alternativen": []}


# ---------------------------------------------------------------- Produkt suchen

def suche_lokal(barcode, produkte):
    for p in produkte:
        if p["barcode"] == barcode:
            return dict(p, quelle="Hautklar Datenbank")
    return None


def ml_aus_text(text):
    if not text:
        return None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*ml", text.lower())
    return float(m.group(1).replace(",", ".")) if m else None


def suche_open_beauty_facts(barcode):
    """Sucht ein Produkt in der freien Datenbank Open Beauty Facts."""
    try:
        import requests
        r = requests.get(
            f"https://world.openbeautyfacts.org/api/v2/product/{barcode}.json",
            headers={"User-Agent": "Hautklar/0.1 (Prototyp)"},
            timeout=8,
        )
        daten = r.json()
    except Exception:
        return None
    if daten.get("status") != 1:
        return None
    p = daten.get("product", {})
    text = (p.get("ingredients_text_de") or p.get("ingredients_text_en")
            or p.get("ingredients_text_fr") or p.get("ingredients_text") or "")
    return {
        "barcode": barcode,
        "marke": (p.get("brands") or "").split(",")[0].strip(),
        "name": p.get("product_name") or "Unbekanntes Produkt",
        "kategorie": None,
        "ml": ml_aus_text(p.get("quantity")),
        "preis": None,
        "inci": zutaten_aus_text(text),
        "bild": p.get("image_front_url"),
        "quelle": "Open Beauty Facts",
    }


# ---------------------------------------------------------------- Barcode lesen

def _texte(wert):
    if isinstance(wert, str):
        yield wert
    elif isinstance(wert, (list, tuple)):
        for w in wert:
            yield from _texte(w)


def lese_barcode(bild_bytes):
    """Liest einen Barcode aus einem Foto. Gibt die Nummer oder None zurück."""
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None
    bild = cv2.imdecode(np.frombuffer(bild_bytes, np.uint8), cv2.IMREAD_COLOR)
    if bild is None:
        return None
    klasse = getattr(getattr(cv2, "barcode", None), "BarcodeDetector", None) or getattr(cv2, "barcode_BarcodeDetector", None)
    if klasse is None:
        return None
    detektor = klasse()
    grau = cv2.cvtColor(bild, cv2.COLOR_BGR2GRAY)
    varianten = [bild, grau]
    if max(bild.shape[:2]) > 1600:
        faktor = 1600 / max(bild.shape[:2])
        varianten.append(cv2.resize(grau, None, fx=faktor, fy=faktor))
    for variante in varianten:
        for methode in ("detectAndDecodeMulti", "detectAndDecode"):
            f = getattr(detektor, methode, None)
            if f is None:
                continue
            try:
                resultat = f(variante)
            except Exception:
                continue
            for t in _texte(resultat):
                if t and t.strip().isdigit():
                    return t.strip()
    return None
