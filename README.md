# Hautklar

Pflegeprodukt scannen und sofort sehen, was drin ist, ob es zur eigenen Haut passt und ob es das Gleiche günstiger gibt.

## Starten

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Ablauf

1. **5 Fragen** zum Hauttyp (trocken, fettig, empfindlich, Pickel, Ziel, Budget)
2. **Hautprofil** mit den Punkten, auf die die App achtet
3. **Scannen**: Foto vom Barcode, Barcode eintippen, Zutatenliste einfügen oder Demo Produkt
4. **Ergebnis** mit zwei Feldern:
   * **Preis Leistung**: sucht Produkte mit den gleichen Wirkstoffen, die günstiger sind
   * **Geeignet für dich**: warnt vor Stoffen, die für deinen Hauttyp schlecht sind

## Dateien

| Datei | Inhalt |
|---|---|
| `app.py` | Die Oberfläche (Streamlit) |
| `logik.py` | Hautprofil, Bewertung der Inhaltsstoffe, Preisvergleich, Barcode lesen |
| `daten/inhaltsstoffe.json` | Regeln pro Inhaltsstoff: wann gut, wann Achtung |
| `daten/produkte.json` | Demo Produkte mit Preisen in CHF (erfundene Beispiele) |

## Daten

* Unbekannte Barcodes werden in der freien Datenbank **Open Beauty Facts** gesucht (Zutaten, ohne Preise).
* Preise kommen im Moment nur aus `produkte.json`. Für echte Vergleiche braucht es eine Preisquelle (Shops, Partner oder Eingaben der Nutzerinnen).
* Die Regeln in `inhaltsstoffe.json` sind ein Startpunkt und sollten von einer Fachperson geprüft werden.

## Barcode Erkennung

Läuft mit OpenCV (`opencv-python-headless` ab Version 4.8). Auf dem Handy am besten den Tab **Foto** nehmen, dann öffnet sich die Rückkamera.
