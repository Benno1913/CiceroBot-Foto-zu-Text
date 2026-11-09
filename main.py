import argparse
import csv
import re
from pathlib import Path

import pytesseract
from PIL import Image


SPALTEN = [
    "Anzahl Vokabeln",
    "Wortart",
    "Grundform",
    "Mittelspalte",
    "Perfektstamm",
    "Deutsche Übersetzung",
    "Deklination/Konjugation",
    "Wortstamm",
    "OCR-Text zur Kontrolle",
]


def zeile_zu_datensatz(text):
    """Liest eine OCR-Zeile aus. Eindeutig getrennte Felder werden zugeordnet."""
    text = re.sub(r"^\s*[-•*]\s*", "", text).strip()

    if not text:
        return None

    # Eine Zeile mit 7 Feldern, z. B.:
    # Verb | rogare | rogo, rogavi, rogatum | rogav | fragen | a | roga
    trenner = "|" if text.count("|") >= 6 else ";" if text.count(";") >= 6 else None

    if trenner:
        felder = [feld.strip() for feld in text.strip("|; ").split(trenner)]

        if len(felder) == 7:
            return {
                "Wortart": felder[0],
                "Grundform": felder[1],
                "Mittelspalte": felder[2],
                "Perfektstamm": felder[3],
                "Deutsche Übersetzung": felder[4],
                "Deklination/Konjugation": felder[5],
                "Wortstamm": felder[6],
                "OCR-Text zur Kontrolle": "",
            }

    # Ohne klar erkennbare Trennzeichen bleibt der erkannte Text zur Prüfung erhalten.
    return {
        "Wortart": "",
        "Grundform": "",
        "Mittelspalte": "",
        "Perfektstamm": "",
        "Deutsche Übersetzung": "",
        "Deklination/Konjugation": "",
        "Wortstamm": "",
        "OCR-Text zur Kontrolle": text,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Liest ein Vokabelbild aus und erstellt eine CSV-Datei."
    )
    parser.add_argument("bild", help="Pfad zum Bild, zum Beispiel vokabeln.jpg")
    args = parser.parse_args()

    bild_pfad = Path(args.bild)

    if not bild_pfad.exists():
        raise SystemExit(f"Bild nicht gefunden: {bild_pfad}")

    bild = Image.open(bild_pfad).convert("RGB")

    # OCR erkennt hier vor allem deutsche und englische Buchstaben.
    erkannter_text = pytesseract.image_to_string(
        bild,
        lang="deu+eng",
        config="--psm 6",
    )

    # Erkannte Zeilen zusätzlich als Textdatei speichern.
    Path("ocr_text.txt").write_text(erkannter_text, encoding="utf-8")

    datensaetze = []
    for zeile in erkannter_text.splitlines():
        datensatz = zeile_zu_datensatz(zeile)
        if datensatz:
            datensaetze.append(datensatz)

    if not datensaetze:
        raise SystemExit(
            "Es wurde kein Text erkannt. Prüfe, ob das Bild scharf und gut lesbar ist."
        )

    anzahl = len(datensaetze)

    with open("vokabeln.csv", "w", newline="", encoding="utf-8-sig") as datei:
        writer = csv.DictWriter(datei, fieldnames=SPALTEN)
        writer.writeheader()

        for datensatz in datensaetze:
            datensatz["Anzahl Vokabeln"] = anzahl
            writer.writerow(datensatz)

    print(f"Fertig: {anzahl} Zeilen erkannt.")
    print("Ergebnisse: vokabeln.csv und ocr_text.txt")


if __name__ == "__main__":
    main()
