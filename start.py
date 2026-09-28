"""
start.py
--------
Startdatei des Programms.

Sie macht zwei Dinge:
  1. Datenbank vorbereiten (beim ersten Start wird daten.db angelegt)
  2. Fenster öffnen

Beim allerersten Start ist das Programm leer. Es legt von sich aus nichts an -
welche Datenbanken es gibt, entscheidet allein der Nutzer. Ab dem zweiten Start
wird die zuletzt geöffnete wieder aufgeschlagen (siehe Einstellungen).

Starten:
  Windows:        python start.py
  macOS / Linux:  python3 start.py
"""

import sqlite3

import datenbank

# tkinter gehört zu Python, fehlt aber in manchen Installationen.
# Dann soll eine verständliche Meldung erscheinen statt einer langen Fehlerausgabe.
try:
    import oberflaeche
except ImportError as fehler:
    if getattr(fehler, "name", None) not in ("tkinter", "_tkinter"):
        raise
    print("The window cannot be opened because tkinter is missing from this")
    print("Python installation. The README explains how to fix that under")
    print("'Running from source'.")
    raise SystemExit(1)

# Verwaltungstabellen anlegen, falls sie noch nicht existieren.
# Schlägt das fehl (zum Beispiel weil der Ordner schreibgeschützt ist),
# hat ein Start des Fensters keinen Sinn.
try:
    datenbank.datenbank_vorbereiten()
except sqlite3.Error as fehler:
    print("The database could not be opened:")
    print("  " + str(fehler))
    print("File: " + datenbank.DATENBANK_DATEI)
    raise SystemExit(1)

# Fenster anzeigen. Das Programm läuft, bis das Fenster geschlossen wird.
oberflaeche.fenster_starten()
