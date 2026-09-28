"""
austausch.py
------------
Daten aus einer Datei einlesen und in eine Datei schreiben.

    exportieren(...)  schreibt alle Datensätze in eine CSV-Datei
    importieren(...)  liest eine CSV-Datei ein und fügt Zeilen an oder gleicht sie ab

CSV ist eine einfache Textdatei, in der die Werte durch ein Zeichen getrennt
sind. Jedes Tabellenprogramm (Excel, Numbers, LibreOffice) kann sie öffnen.

Beim Import werden die Spalten der Datei über ihre Überschrift den Feldern der
Datenbank zugeordnet. Spalten, die es noch nicht gibt, können auf Wunsch als
neue Textfelder angelegt werden. Datensätze werden angehängt oder über
eindeutige Schlüsselwerte abgeglichen.
"""

import csv
import io
import os

import datenbank
import sprache

# So viele Datensätze werden beim Schreiben auf einmal geholt.
# Dadurch liegen nie alle 10.000 gleichzeitig im Speicher.
BLOCK = 500

# Trennzeichen für neue Dateien. Das Semikolon funktioniert in jedem
# Tabellenprogramm; beim Einlesen wird ohnehin selbst erkannt, welches
# Zeichen die Datei benutzt.
TRENNZEICHEN = ";"


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def dateiname_saeubern(name):
    """
    Macht aus einem Datenbanknamen einen Dateinamen, den jedes System annimmt.
    Windows erlaubt zum Beispiel kein : ? * " < > | im Dateinamen.
    """
    sauber = ""
    for zeichen in name:
        if zeichen in '\\/:*?"<>|':
            sauber = sauber + "-"
        else:
            sauber = sauber + zeichen
    sauber = sauber.strip().strip(".")
    if sauber == "":
        sauber = "Data"
    return sauber


def exportieren(fenster, datenbank_id, datenbank_name):
    """
    Fragt nach einem Dateinamen und schreibt alle Datensätze hinein.
    Gibt die Anzahl der geschriebenen Zeilen zurück (oder None bei Abbruch).
    """
    from tkinter import filedialog, messagebox

    felder = datenbank.felder_liste(datenbank_id)
    if not felder:
        messagebox.showinfo(sprache.text("nichts_zu_speichern"),
                            sprache.text("datenbank_ohne_felder"))
        return None

    pfad = filedialog.asksaveasfilename(
        parent=fenster,
        title=sprache.text("datei_speichern_titel"),
        defaultextension=".csv",
        initialfile=dateiname_saeubern(datenbank_name) + ".csv",
        filetypes=[(sprache.text("csv_datei"), "*.csv"),
                   (sprache.text("alle_dateien"), "*.*")]
    )
    if not pfad:
        return None

    return datei_schreiben(pfad, datenbank_id, felder)


def datei_schreiben(pfad, datenbank_id, felder=None):
    """Schreibt eine CSV-Datei ohne Dialog; wird auch für Prüfungen gebraucht."""
    if felder is None:
        felder = datenbank.felder_liste(datenbank_id)
    if not felder:
        return 0

    anzahl = datenbank.anzahl_datensaetze(datenbank_id)

    # "utf-8-sig" schreibt eine kleine Kennung an den Anfang der Datei.
    # Daran erkennt Excel, dass Umlaute enthalten sind.
    # newline="" ist bei CSV nötig, sonst entstehen leere Zwischenzeilen.
    with open(pfad, "w", encoding="utf-8-sig", newline="") as datei:
        schreiber = csv.writer(datei, delimiter=TRENNZEICHEN)

        # Erste Zeile: die Namen der Felder als Überschriften
        ueberschriften = []
        for feld in felder:
            ueberschriften.append(feld["anzeigename"])
        schreiber.writerow(ueberschriften)

        # Danach die Datensätze - blockweise, damit der Speicher nicht volläuft
        geschrieben = 0
        while geschrieben < anzahl:
            # felder ist hier schon bekannt und wird mitgegeben - sonst würde
            # die Feldliste für jeden Block erneut aus der Datenbank geholt.
            zeilen = datenbank.datensaetze_suchen(
                datenbank_id, limit=BLOCK, offset=geschrieben, felder=felder
            )
            if not zeilen:
                break
            for zeile in zeilen:
                werte = []
                for feld in felder:
                    werte.append(datenbank.text_fuer_anzeige(feld["typ"], zeile[feld["spalte"]]))
                schreiber.writerow(werte)
            geschrieben = geschrieben + len(zeilen)

    return geschrieben


# ---------------------------------------------------------------------------
# Import: Datei einlesen
# ---------------------------------------------------------------------------

def datei_einlesen(pfad):
    """
    Liest eine CSV-Datei und gibt die Überschriften und die Zeilen zurück.
    Trennzeichen und Textkodierung werden selbst erkannt.
    """
    text = None
    # Erst die übliche Kodierung versuchen, dann die ältere von Windows.
    for kodierung in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            with open(pfad, "r", encoding=kodierung, newline="") as datei:
                text = datei.read()
            break
        except UnicodeDecodeError:
            continue

    if text is None:
        raise ValueError(sprache.text("datei_konnte_nicht_gelesen_werden"))
    if text.strip() == "":
        raise ValueError(sprache.text("datei_ist_leer"))

    # Parse the first non-empty CSV record for each supported separator.
    # This ignores separators inside quoted headings and supports a quoted
    # heading that spans more than one physical line.
    kandidat = []
    for rang, zeichen in enumerate((TRENNZEICHEN, ",", "\t")):
        try:
            leser = csv.reader(io.StringIO(text, newline=""), delimiter=zeichen,
                               strict=True)
            erste_zeile = next((zeile for zeile in leser if zeile), [])
        except csv.Error:
            continue
        kandidat.append((len(erste_zeile), -rang, zeichen))

    if not kandidat:
        raise ValueError(sprache.text("datei_csv_fehler"))
    trenner = max(kandidat)[2]

    # StringIO lässt den Text wie eine geöffnete Datei aussehen. Das ist wichtig,
    # damit mehrzeilige Werte (Text in Anführungszeichen mit Zeilenumbruch darin)
    # richtig zusammengesetzt werden.
    try:
        leser = csv.reader(io.StringIO(text, newline=""), delimiter=trenner,
                           strict=True)
        alle_zeilen = list(leser)
    except csv.Error as fehler:
        raise ValueError(sprache.text("datei_csv_fehler")) from fehler

    if not alle_zeilen:
        raise ValueError(sprache.text("datei_ohne_zeilen"))

    while alle_zeilen and not alle_zeilen[0]:
        alle_zeilen.pop(0)
    if not alle_zeilen:
        raise ValueError(sprache.text("datei_ohne_zeilen"))

    ueberschriften = [eintrag.strip() for eintrag in alle_zeilen[0]]
    gesehen = set()
    for ueberschrift in ueberschriften:
        schluessel = datenbank.text_vergleichsschluessel(ueberschrift)
        if schluessel and schluessel in gesehen:
            raise ValueError(sprache.text("csv_doppelte_ueberschriften") % ueberschrift)
        if schluessel:
            gesehen.add(schluessel)

    # Leere Zeilen am Ende weglassen
    datenzeilen = []
    for nummer, zeile in enumerate(alle_zeilen[1:], start=2):
        if any(wert.strip() != "" for wert in zeile):
            if len(zeile) != len(ueberschriften):
                raise ValueError(sprache.text("csv_zeilenbreite")
                                 % (nummer, len(zeile), len(ueberschriften)))
            datenzeilen.append(zeile)

    for nummer, ueberschrift in enumerate(ueberschriften):
        if not ueberschrift and any(zeile[nummer].strip() for zeile in datenzeilen):
            raise ValueError(sprache.text("csv_leere_ueberschrift") % (nummer + 1))

    return ueberschriften, datenzeilen


# Die Umwandlung eines Textes in einen Wert steht in datenbank.py
# (wert_aus_text) - sie wird auch beim Umstellen einer Feldart gebraucht.


# ---------------------------------------------------------------------------
# Import: Ablauf mit Rückfrage
# ---------------------------------------------------------------------------

def importieren(fenster, datenbank_id, datenbank_name):
    """
    Fragt nach einer Datei, zeigt was passieren wird und fügt die Zeilen an.
    Gibt die Anzahl der eingefügten Datensätze zurück (oder None bei Abbruch).
    """
    from tkinter import filedialog, messagebox

    pfad = filedialog.askopenfilename(
        parent=fenster,
        title=sprache.text("datei_waehlen_titel"),
        filetypes=[(sprache.text("csv_datei"), "*.csv"),
                   (sprache.text("textdatei"), "*.txt"),
                   (sprache.text("alle_dateien"), "*.*")]
    )
    if not pfad:
        return None

    try:
        ueberschriften, zeilen = datei_einlesen(pfad)
    except (ValueError, OSError) as fehler:
        messagebox.showwarning(sprache.text("datei_nicht_lesbar"), str(fehler))
        return None

    if not zeilen:
        messagebox.showinfo(sprache.text("nichts_gefunden"),
                            sprache.text("datei_ohne_datensaetze"))
        return None

    felder = datenbank.felder_liste(datenbank_id)
    urspruengliche_felder = list(felder)

    # Welche Spalte der Datei passt zu welchem Feld? Verglichen wird der Name.
    bekannt = []       # (überschrift, feld)
    unbekannt = []     # Überschriften ohne passendes Feld
    for ueberschrift in ueberschriften:
        passende_felder = [
            feld for feld in felder
            if datenbank.text_vergleichsschluessel(feld["anzeigename"])
            == datenbank.text_vergleichsschluessel(ueberschrift)
        ]
        if len(passende_felder) > 1:
            messagebox.showwarning(
                sprache.text("import_titel"),
                sprache.text("csv_feld_uneindeutig") % ueberschrift,
                parent=fenster,
            )
            return None
        if passende_felder:
            bekannt.append((ueberschrift, passende_felder[0]))
        elif ueberschrift != "":
            unbekannt.append(ueberschrift)

    if not bekannt and not unbekannt:
        messagebox.showwarning(sprache.text("keine_spalten_erkannt"),
                               sprache.text("erste_zeile_ohne_ueberschriften"))
        return None

    # Rückfrage: Was wird übernommen, und woran werden vorhandene erkannt?
    antwort = import_dialog(fenster, os.path.basename(pfad), datenbank_name,
                            len(zeilen), bekannt, unbekannt)
    if antwort is None:
        return None

    neue_felder_anlegen = antwort["neue_felder"]
    schluessel_name = antwort["schluessel"]
    schluessel_feld_id = None
    for ueberschrift, feld in bekannt:
        if (datenbank.text_vergleichsschluessel(feld["anzeigename"])
                == datenbank.text_vergleichsschluessel(schluessel_name)):
            schluessel_feld_id = feld["id"]
            break
    try:
        return datenbank.csv_datensaetze_uebernehmen(
            datenbank_id, ueberschriften, zeilen, neue_felder_anlegen,
            unbekannt, schluessel_feld_id, urspruengliche_felder)
    except ValueError as fehler:
        messagebox.showwarning(sprache.text("import_titel"), str(fehler), parent=fenster)
        return None


def schluessel_optionen_erstellen(bekannt):
    """Erstellt eindeutige Beschriftungen für die Schlüssel-Auswahl."""
    namen = [sprache.text("abgleichen_keins")]
    schluessel = {datenbank.text_vergleichsschluessel(namen[0])}
    for ueberschrift, feld in bekannt:
        name = feld["anzeigename"]
        if datenbank.text_vergleichsschluessel(name) in schluessel:
            name = name + " (" + str(feld["id"]) + ")"
            while datenbank.text_vergleichsschluessel(name) in schluessel:
                name = name + " "
        namen.append(name)
        schluessel.add(datenbank.text_vergleichsschluessel(name))
    return namen


def schluessel_auswahl_aufloesen(index, bekannt):
    """Löst den Auswahlindex auf, ohne Beschriftungstexte zu vergleichen."""
    if index <= 0 or index > len(bekannt):
        return ""
    return bekannt[index - 1][1]["anzeigename"]


def import_dialog(fenster, dateiname, datenbank_name, anzahl_zeilen, bekannt, unbekannt):
    """
    Zeigt vor dem Einlesen, was passieren wird.

    Rückgabe:
      ein Wörterbuch mit "neue_felder" (ja/nein) und "schluessel"
      (Name des Feldes zum Wiedererkennen, oder "" für einfaches Anhängen)
      None, wenn abgebrochen wurde
    """
    import tkinter as tk
    from tkinter import ttk
    import design
    import dialoge

    ergebnis = {"antwort": None}

    dialog = dialoge.dialog_oeffnen(fenster, sprache.text("import_titel"))
    dialoge.kopfzeile(dialog, sprache.text("import_titel"),
                      sprache.text("import_erklaerung") % (dateiname, datenbank_name))

    inhalt = tk.Frame(dialog, background=design.FLAECHE)
    inhalt.pack(fill="both", expand=True, padx=24, pady=(18, 0))

    tk.Label(inhalt, text=sprache.text("werden_angehaengt") % anzahl_zeilen,
             font=design.SCHRIFT_FETT, background=design.FLAECHE,
             foreground=design.TEXT, anchor="w").pack(fill="x")
    tk.Label(inhalt, text=sprache.text("bestehende_bleiben"),
             font=design.SCHRIFT_KLEIN, background=design.FLAECHE,
             foreground=design.TEXT_LEISE, anchor="w").pack(fill="x", pady=(2, 14))

    passende = []
    for ueberschrift, feld in bekannt:
        passende.append(feld["anzeigename"])

    dialoge.beschriftung(inhalt, sprache.text("diese_spalten_kommen")).pack(anchor="w")
    tk.Label(inhalt, text=", ".join(passende) if passende else sprache.text("keine"),
             font=design.SCHRIFT, background=design.FLAECHE, foreground=design.TEXT,
             anchor="w", justify="left", wraplength=420).pack(fill="x", pady=(2, 12))

    # Woran sollen vorhandene Datensätze wiedererkannt werden?
    dialoge.beschriftung(inhalt, sprache.text("abgleichen_feld")).pack(anchor="w")

    schluessel_namen = schluessel_optionen_erstellen(bekannt)

    auswahl_schluessel = ttk.Combobox(inhalt, values=schluessel_namen, state="readonly",
                                      font=design.SCHRIFT, width=1)
    auswahl_schluessel.current(0)
    auswahl_schluessel.pack(fill="x", pady=(4, 2))

    tk.Label(inhalt, text=sprache.text("abgleichen_erklaerung"), font=design.SCHRIFT_KLEIN,
             background=design.FLAECHE, foreground=design.TEXT_LEISE,
             anchor="w", justify="left").pack(fill="x", pady=(0, 12))

    neue_felder = tk.BooleanVar(value=bool(unbekannt))

    if unbekannt:
        dialoge.beschriftung(inhalt, sprache.text("diese_spalten_fehlen")).pack(anchor="w")
        tk.Label(inhalt, text=", ".join(unbekannt), font=design.SCHRIFT,
                 background=design.FLAECHE, foreground=design.TEXT,
                 anchor="w", justify="left", wraplength=420).pack(fill="x", pady=(2, 6))
        ttk.Checkbutton(inhalt, text=sprache.text("als_textfelder_anlegen"),
                        variable=neue_felder).pack(anchor="w", pady=(0, 6))

    def einlesen():
        gewaehlt = schluessel_auswahl_aufloesen(auswahl_schluessel.current(), bekannt)
        ergebnis["antwort"] = {"neue_felder": bool(neue_felder.get()),
                               "schluessel": gewaehlt}
        dialog.destroy()

    dialoge.knopfleiste(dialog, sprache.text("importieren"), einlesen)
    dialog.bind("<Escape>", lambda ereignis: dialog.destroy())

    dialoge.dialog_zeigen(dialog, fenster)
    fenster.wait_window(dialog)
    return ergebnis["antwort"]
