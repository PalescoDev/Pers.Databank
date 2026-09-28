"""
datenbank.py
------------
Alles, was mit der SQLite-Datenbank zu tun hat. Nur diese Datei schreibt SQL.

Wie ist das aufgebaut?

In der Datei daten.db liegen drei Arten von Tabellen:

  datenbanken   Liste aller angelegten Datenbanken (Kunden, Produkte, ...)
  felder        welche Felder (Spalten) jede Datenbank hat und welchen Typ sie haben
  daten_1, daten_2, ...   je eine echte Tabelle pro Datenbank mit den Datensätzen

Die ersten beiden Tabellen sind das "Inhaltsverzeichnis". Wenn der Nutzer eine
neue Datenbank oder ein neues Feld anlegt, wird dort ein Eintrag ergänzt und
zusätzlich die echte Tabelle angepasst.

Wichtig für die Sicherheit:
Tabellen- und Spaltennamen kann man in SQL nicht als Fragezeichen (?) übergeben.
Deshalb werden sie NIE direkt aus einer Eingabe übernommen, sondern immer aus
der Tabelle "felder" gelesen - dort stehen nur geprüfte Namen. Alle Werte
laufen weiterhin über Fragezeichen (parametrisierte Abfragen).
"""

import datetime
import math
import os
import sqlite3
import sys
import unicodedata

import sprache

# Wo soll die Datenbankdatei liegen?
if getattr(sys, "frozen", False):
    # Das Programm läuft als fertige Anwendung (Doppelklick). Deren Ordner ist
    # schreibgeschützt, deshalb kommt die Datenbank in einen eigenen Ordner
    # im Benutzerverzeichnis - unter Windows und macOS gleichermaßen.
    ORDNER = os.path.join(os.path.expanduser("~"), "Pers.Databank")
    if not os.path.exists(ORDNER):
        os.makedirs(ORDNER)
else:
    # Normaler Start über "python start.py": Die Datei liegt neben dem Programm.
    ORDNER = os.path.dirname(os.path.abspath(__file__))

# os.path.join setzt den Pfad passend für das Betriebssystem zusammen.
DATENBANK_DATEI = os.path.join(ORDNER, "daten.db")

# Die möglichen Feldtypen - die Namen, die das Programm intern benutzt.
# Wie sie beim Nutzer heißen, steht in sprache.py unter "typ_text", "typ_zahl", ...
FELDTYPEN = ["text", "zahl", "janein", "datum", "auswahl", "langtext"]


def typ_anzeigename(typ):
    """Wie ein Feldtyp in der eingestellten Sprache heißt."""
    return sprache.text("typ_" + typ)


def ja_text():
    """Das Wort für ein angehaktes Ja/Nein-Feld - in Tabelle und Filter gleich."""
    return sprache.text("ja")


def nein_text():
    """Das Gegenstück dazu."""
    return sprache.text("nein")


# Welcher SQLite-Typ gehört zu welchem Feldtyp?
SQL_TYPEN = {
    "text": "TEXT",
    "zahl": "REAL",
    "janein": "INTEGER",
    "datum": "TEXT",
    "auswahl": "TEXT",
    "langtext": "TEXT",
}

# Nach diesen Feldtypen kann man sinnvoll filtern (feste, wiederkehrende Werte).
FILTERBARE_TYPEN = ["auswahl", "janein", "text", "datum"]

# Hier merkt sich das Programm die offene Verbindung zur Datenbank.
offene_verbindung = None


# ---------------------------------------------------------------------------
# Verbindung
# ---------------------------------------------------------------------------

def verbindung_holen():
    """
    Gibt die Verbindung zur Datenbank zurück.

    Beim ersten Aufruf wird sie geöffnet, danach immer dieselbe wiederverwendet.
    Das spart bei jeder Abfrage das erneute Öffnen der Datei.
    """
    global offene_verbindung

    if offene_verbindung is None:
        # timeout: Ist die Datei gerade von einem anderen Programm gesperrt,
        # wartet SQLite höchstens 2 Sekunden und meldet dann einen Fehler.
        offene_verbindung = sqlite3.connect(DATENBANK_DATEI, timeout=2)
        # Damit wir Spalten über ihren Namen lesen können, z.B. zeile["name"]
        offene_verbindung.row_factory = sqlite3.Row

    return offene_verbindung


def datenbank_schliessen():
    """Schließt die Verbindung. Wird beim Beenden des Programms aufgerufen."""
    global offene_verbindung

    if offene_verbindung is not None:
        offene_verbindung.close()
        offene_verbindung = None


def datenbank_vorbereiten():
    """
    Legt die beiden Verwaltungstabellen an, falls sie noch nicht existieren.
    Beim allerersten Start entsteht dadurch die Datei daten.db automatisch.
    """
    verbindung = verbindung_holen()

    # "with" schreibt die Änderungen am Ende automatisch fest (commit).
    # Geht etwas schief, wird alles zurückgenommen (rollback).
    with verbindung:
        verbindung.execute("""
            CREATE TABLE IF NOT EXISTS datenbanken (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                name    TEXT NOT NULL UNIQUE,
                tabelle TEXT NOT NULL UNIQUE
            )
        """)
        verbindung.execute("""
            CREATE TABLE IF NOT EXISTS felder (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                datenbank_id INTEGER NOT NULL,
                anzeigename  TEXT NOT NULL,
                spalte       TEXT NOT NULL,
                typ          TEXT NOT NULL,
                optionen     TEXT,
                position     INTEGER NOT NULL
            )
        """)
        verbindung.execute(
            "CREATE INDEX IF NOT EXISTS index_felder ON felder (datenbank_id, position)"
        )
        # Die Einstellungen des Programms: je eine Zeile mit Name und Wert.
        # Sie liegen bewusst in derselben Datei wie die Daten - so kommt keine
        # zweite Datei dazu, und beim Kopieren von daten.db wandern sie mit.
        verbindung.execute("""
            CREATE TABLE IF NOT EXISTS einstellungen (
                schluessel TEXT PRIMARY KEY,
                wert       TEXT NOT NULL
            )
        """)


# ---------------------------------------------------------------------------
# Einstellungen (welche es gibt, steht in einstellungen.py)
# ---------------------------------------------------------------------------

def einstellungen_lesen():
    """Gibt alle gespeicherten Einstellungen als Wörterbuch zurück."""
    verbindung = verbindung_holen()
    cursor = verbindung.execute("SELECT schluessel, wert FROM einstellungen")
    zeilen = cursor.fetchall()
    cursor.close()

    gespeichert = {}
    for zeile in zeilen:
        gespeichert[zeile["schluessel"]] = zeile["wert"]
    return gespeichert


def einstellung_speichern(schluessel, wert):
    """
    Schreibt eine Einstellung.

    "INSERT OR REPLACE" legt sie an, wenn es sie noch nicht gibt, und
    überschreibt sie sonst - beides mit einem einzigen Befehl.
    """
    verbindung = verbindung_holen()
    with verbindung:
        verbindung.execute(
            "INSERT OR REPLACE INTO einstellungen (schluessel, wert) VALUES (?, ?)",
            (str(schluessel), str(wert))
        )


# ---------------------------------------------------------------------------
# Namen prüfen und umwandeln
# ---------------------------------------------------------------------------

def spaltenname_bilden(anzeigename, schon_vergeben):
    """
    Macht aus einem Feldnamen des Nutzers einen sicheren Spaltennamen.

    Beispiel: "Fällig am?"  ->  "faellig_am"

    Erlaubt sind nur Buchstaben, Ziffern und Unterstriche. Dadurch kann über
    einen Feldnamen kein fremdes SQL eingeschleust werden. Ist der Name schon
    vergeben, wird eine Zahl angehängt.
    """
    umlaute = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}

    text = anzeigename.strip().lower()
    for alt, neu in umlaute.items():
        text = text.replace(alt, neu)

    sauber = ""
    for zeichen in text:
        # isascii() sorgt dafür, dass wirklich nur einfache Buchstaben durchkommen
        if zeichen.isascii() and (zeichen.isalnum() or zeichen == "_"):
            sauber = sauber + zeichen
        else:
            sauber = sauber + "_"

    while "__" in sauber:
        sauber = sauber.replace("__", "_")
    sauber = sauber.strip("_")

    # Ein Spaltenname muss mit einem Buchstaben beginnen.
    if sauber == "" or not sauber[0].isalpha():
        sauber = "feld_" + sauber
    sauber = sauber[:40]

    # "id" ist schon für die laufende Nummer belegt.
    if sauber == "id":
        sauber = "feld_id"

    # Bei Doppelungen eine Zahl anhängen: name, name_2, name_3, ...
    endgueltig = sauber
    nummer = 2
    while endgueltig in schon_vergeben:
        endgueltig = sauber + "_" + str(nummer)
        nummer = nummer + 1

    return endgueltig


def text_vergleichsschluessel(text):
    """Vergleicht Namen unabhängig von Großschreibung und Mac-Unicode-Form."""
    nfc = unicodedata.normalize("NFC", str(text))
    return unicodedata.normalize("NFC", nfc.casefold())


def feldname_pruefen(anzeigename, vorhandene_namen):
    """
    Prüft den Feldnamen, den der Nutzer eingegeben hat.
    Bei einem Problem wird ein ValueError mit einer verständlichen Meldung ausgelöst.
    """
    name = unicodedata.normalize("NFC", anzeigename.strip())

    if name == "":
        raise ValueError(sprache.text("feldname_fehlt"))
    if len(name) > 40:
        raise ValueError(sprache.text("feldname_zu_lang"))

    for vorhanden in vorhandene_namen:
        if text_vergleichsschluessel(vorhanden) == text_vergleichsschluessel(name):
            raise ValueError(sprache.text("feldname_vergeben") % vorhanden)

    return name


def datenbankname_pruefen(name, ausser_id=None):
    """
    Prüft den Namen einer Datenbank.

    ausser_id ist beim Umbenennen die Nummer der Datenbank selbst - ihr
    eigener bisheriger Name soll ja nicht als "schon vergeben" gelten.
    """
    name = unicodedata.normalize("NFC", name.strip())

    if name == "":
        raise ValueError(sprache.text("datenbankname_fehlt"))
    if len(name) > 40:
        raise ValueError(sprache.text("datenbankname_zu_lang"))

    # SQLite's built-in lower() only folds ASCII characters. Compare in Python
    # so names such as Äpfel/äpfel are treated consistently on every platform.
    for vorhanden in datenbanken_liste():
        if (text_vergleichsschluessel(vorhanden["name"])
                == text_vergleichsschluessel(name)
                and vorhanden["id"] != ausser_id):
            raise ValueError(sprache.text("datenbankname_vergeben") % vorhanden["name"])

    return name


def typ_pruefen(typ):
    """Prüft, ob der Feldtyp bekannt ist."""
    if typ not in FELDTYPEN:
        raise ValueError(sprache.text("unbekannte_feldart") % str(typ))
    return typ


# ---------------------------------------------------------------------------
# Datenbanken (im Programm: die Einträge in der Seitenleiste)
# ---------------------------------------------------------------------------

def datenbanken_liste():
    """Gibt alle angelegten Datenbanken zurück, alphabetisch sortiert."""
    verbindung = verbindung_holen()
    cursor = verbindung.execute("SELECT id, name, tabelle FROM datenbanken ORDER BY name")
    zeilen = cursor.fetchall()
    cursor.close()
    return zeilen


def datenbank_holen(datenbank_id):
    """Gibt eine einzelne Datenbank zurück (oder None)."""
    verbindung = verbindung_holen()
    cursor = verbindung.execute(
        "SELECT id, name, tabelle FROM datenbanken WHERE id = ?", (datenbank_id,)
    )
    zeile = cursor.fetchone()
    cursor.close()
    return zeile


def datenbank_anlegen(name, felder):
    """
    Legt eine neue Datenbank an.

    name    Name für die Seitenleiste, z.B. "Kunden"
    felder  Liste von Feldern, jedes als (anzeigename, typ, optionen)

    Es entsteht ein Eintrag in "datenbanken", je ein Eintrag in "felder"
    und eine echte Tabelle daten_<nummer> für die Datensätze.
    """
    name = datenbankname_pruefen(name)

    if not felder:
        raise ValueError(sprache.text("datenbank_braucht_feld"))

    # Erst alle Felder prüfen, bevor irgendetwas geschrieben wird.
    geprueft = []
    namen_bisher = []
    spalten_bisher = []
    for anzeigename, typ, optionen in felder:
        sauberer_name = feldname_pruefen(anzeigename, namen_bisher)
        typ_pruefen(typ)
        optionen = optionen_pruefen(typ, optionen)
        spalte = spaltenname_bilden(sauberer_name, spalten_bisher)

        namen_bisher.append(sauberer_name)
        spalten_bisher.append(spalte)
        geprueft.append((sauberer_name, spalte, typ, optionen))

    verbindung = verbindung_holen()
    with verbindung:
        cursor = verbindung.execute(
            "INSERT INTO datenbanken (name, tabelle) VALUES (?, ?)", (name, "vorlaeufig")
        )
        neue_id = cursor.lastrowid
        cursor.close()

        # Der Tabellenname wird aus der Nummer gebildet, nicht aus dem Text des
        # Nutzers. Damit ist er immer eindeutig und sicher.
        tabelle = "daten_" + str(neue_id)
        verbindung.execute("UPDATE datenbanken SET tabelle = ? WHERE id = ?", (tabelle, neue_id))

        # Die Tabelle beginnt nur mit der laufenden Nummer.
        # Die eigentlichen Felder werden gleich danach angehängt.
        verbindung.execute(
            'CREATE TABLE "' + tabelle + '" (id INTEGER PRIMARY KEY AUTOINCREMENT)'
        )

        position = 0
        for anzeigename, spalte, typ, optionen in geprueft:
            verbindung.execute(
                "INSERT INTO felder (datenbank_id, anzeigename, spalte, typ, optionen, position)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (neue_id, anzeigename, spalte, typ, optionen, position)
            )
            spalte_anhaengen(verbindung, tabelle, spalte, typ)
            position = position + 1

    return neue_id


def datenbank_umbenennen(datenbank_id, neuer_name):
    """
    Gibt einer Datenbank einen anderen Namen.

    Der Name der echten Tabelle (daten_1, daten_2, ...) bleibt dabei
    unverändert - er wird aus der laufenden Nummer gebildet und nie angezeigt.
    Deshalb rührt das Umbenennen die Daten selbst überhaupt nicht an.
    """
    eintrag = datenbank_holen(datenbank_id)
    if eintrag is None:
        raise ValueError(sprache.text("datenbank_gibt_es_nicht"))

    name = datenbankname_pruefen(neuer_name, datenbank_id)

    verbindung = verbindung_holen()
    with verbindung:
        verbindung.execute("UPDATE datenbanken SET name = ? WHERE id = ?", (name, datenbank_id))


def datenbank_loeschen(datenbank_id):
    """Löscht eine Datenbank mit allen Datensätzen und Feldern."""
    eintrag = datenbank_holen(datenbank_id)
    if eintrag is None:
        return

    verbindung = verbindung_holen()
    with verbindung:
        verbindung.execute('DROP TABLE IF EXISTS "' + eintrag["tabelle"] + '"')
        verbindung.execute("DELETE FROM felder WHERE datenbank_id = ?", (datenbank_id,))
        verbindung.execute("DELETE FROM datenbanken WHERE id = ?", (datenbank_id,))


# ---------------------------------------------------------------------------
# Felder (die Spalten einer Datenbank)
# ---------------------------------------------------------------------------

def optionen_pruefen(typ, optionen):
    """
    Prüft die Auswahlmöglichkeiten eines Auswahlfeldes.
    Sie werden als eine Zeichenkette gespeichert, eine Möglichkeit pro Zeile.
    """
    if typ != "auswahl":
        return None

    if optionen is None:
        optionen = ""

    liste = []
    for zeile in optionen.split("\n"):
        zeile = zeile.strip()
        if zeile != "" and zeile not in liste:
            liste.append(zeile)

    if len(liste) < 2:
        raise ValueError(sprache.text("auswahl_braucht_werte"))

    return "\n".join(liste)


def optionen_liste(feld):
    """Gibt die Auswahlmöglichkeiten eines Feldes als Liste zurück."""
    if feld["typ"] != "auswahl" or not feld["optionen"]:
        return []
    return feld["optionen"].split("\n")


def felder_liste(datenbank_id):
    """Gibt alle Felder einer Datenbank in der richtigen Reihenfolge zurück."""
    verbindung = verbindung_holen()
    cursor = verbindung.execute(
        "SELECT id, anzeigename, spalte, typ, optionen FROM felder"
        " WHERE datenbank_id = ? ORDER BY position, id",
        (datenbank_id,)
    )
    zeilen = cursor.fetchall()
    cursor.close()
    return zeilen


def feld_holen(datenbank_id, feld_id):
    """Sucht ein einzelnes Feld heraus (oder None)."""
    for feld in felder_liste(datenbank_id):
        if feld["id"] == feld_id:
            return feld
    return None


def spalte_anhaengen(verbindung, tabelle, spalte, typ):
    """
    Hängt eine neue Spalte an eine bestehende Tabelle an.

    ALTER TABLE ... ADD COLUMN fügt die Spalte nur hinzu. Vorhandene Datensätze
    bleiben unverändert erhalten und haben in der neuen Spalte zunächst nichts
    stehen. Es gehen also keine Daten verloren.
    """
    verbindung.execute(
        'ALTER TABLE "' + tabelle + '" ADD COLUMN "' + spalte + '" ' + SQL_TYPEN[typ]
    )
    # Ein Index macht Sortieren und Filtern auch bei vielen Datensätzen schnell.
    # Bei langen Texten lohnt sich das nicht, deshalb dort keiner.
    if typ != "langtext":
        verbindung.execute(
            'CREATE INDEX IF NOT EXISTS "index_' + tabelle + '_' + spalte + '"'
            ' ON "' + tabelle + '" ("' + spalte + '")'
        )


def feld_hinzufuegen(datenbank_id, anzeigename, typ, optionen=None):
    """
    Fügt einer bestehenden Datenbank ein neues Feld hinzu.
    Bestehende Datensätze bleiben dabei vollständig erhalten.
    """
    eintrag = datenbank_holen(datenbank_id)
    if eintrag is None:
        raise ValueError(sprache.text("datenbank_gibt_es_nicht"))

    vorhandene_felder = felder_liste(datenbank_id)
    vorhandene_namen = []
    vorhandene_spalten = []
    for feld in vorhandene_felder:
        vorhandene_namen.append(feld["anzeigename"])
        vorhandene_spalten.append(feld["spalte"])

    name = feldname_pruefen(anzeigename, vorhandene_namen)
    typ_pruefen(typ)
    optionen = optionen_pruefen(typ, optionen)
    spalte = spaltenname_bilden(name, vorhandene_spalten)
    position = len(vorhandene_felder)

    verbindung = verbindung_holen()
    with verbindung:
        spalte_anhaengen(verbindung, eintrag["tabelle"], spalte, typ)
        verbindung.execute(
            "INSERT INTO felder (datenbank_id, anzeigename, spalte, typ, optionen, position)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (datenbank_id, name, spalte, typ, optionen, position)
        )


def import_felder_anlegen(datenbank_id, ueberschriften, erwartete_felder):
    """Legt die beim Import gewünschten Textfelder vollständig oder gar nicht an."""
    verbindung = verbindung_holen()
    with verbindung:
        verbindung.execute("BEGIN IMMEDIATE")
        eintrag = datenbank_holen(datenbank_id)
        felder = felder_liste(datenbank_id)
        if eintrag is None:
            raise ValueError(sprache.text("import_schema_geaendert"))
        _import_felder_pruefen(felder, erwartete_felder)
        return _import_felder_in_transaktion(
            verbindung, eintrag, felder, ueberschriften, datenbank_id)


def _import_felder_in_transaktion(verbindung, eintrag, felder, ueberschriften,
                                  datenbank_id):
    """Validiert und ergänzt Importfelder in einer bereits offenen Transaktion."""
    namen = [feld["anzeigename"] for feld in felder]
    spalten = [feld["spalte"] for feld in felder]
    neu = []
    for ueberschrift in ueberschriften:
        name = feldname_pruefen(ueberschrift, namen)
        spalte = spaltenname_bilden(name, spalten)
        namen.append(name)
        spalten.append(spalte)
        neu.append((name, spalte))

    for nummer, (name, spalte) in enumerate(neu, start=len(felder)):
        spalte_anhaengen(verbindung, eintrag["tabelle"], spalte, "text")
        verbindung.execute(
            "INSERT INTO felder (datenbank_id, anzeigename, spalte, typ, optionen, position)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (datenbank_id, name, spalte, "text", None, nummer)
        )
    return felder_liste(datenbank_id)


def feld_umbenennen(datenbank_id, feld_id, neuer_name):
    """
    Ändert die Überschrift eines Feldes.

    Der Spaltenname in der echten Tabelle bleibt, wie er ist. Ihn mitzuändern
    hieße, die Spalte umzubenennen und den Index neu zu bauen - viel Aufwand
    für einen Namen, den niemand zu sehen bekommt. Alle Werte bleiben also
    unangetastet an Ort und Stelle.
    """
    if datenbank_holen(datenbank_id) is None:
        raise ValueError(sprache.text("datenbank_gibt_es_nicht"))

    felder = felder_liste(datenbank_id)

    # Die Namen der anderen Felder - der eigene darf natürlich bleiben.
    andere_namen = []
    gefunden = False
    for feld in felder:
        if feld["id"] == feld_id:
            gefunden = True
        else:
            andere_namen.append(feld["anzeigename"])

    if not gefunden:
        raise ValueError(sprache.text("feld_gibt_es_nicht"))

    name = feldname_pruefen(neuer_name, andere_namen)

    verbindung = verbindung_holen()
    with verbindung:
        verbindung.execute("UPDATE felder SET anzeigename = ? WHERE id = ?", (name, feld_id))


def feld_loeschen(datenbank_id, feld_id):
    """
    Entfernt ein Feld aus einer Datenbank - mit allem, was darin gespeichert ist.

    Das letzte verbleibende Feld lässt sich nicht entfernen, sonst gäbe es eine
    Datenbank ohne jede Spalte. Die anderen Felder und alle Datensätze bleiben
    unverändert erhalten.
    """
    eintrag = datenbank_holen(datenbank_id)
    if eintrag is None:
        raise ValueError(sprache.text("datenbank_gibt_es_nicht"))

    felder = felder_liste(datenbank_id)
    if len(felder) <= 1:
        raise ValueError(sprache.text("letztes_feld"))

    zu_loeschen = None
    for feld in felder:
        if feld["id"] == feld_id:
            zu_loeschen = feld
    if zu_loeschen is None:
        raise ValueError(sprache.text("feld_gibt_es_nicht"))

    verbindung = verbindung_holen()
    with verbindung:
        spalte_entfernen(verbindung, eintrag["tabelle"], zu_loeschen["spalte"], felder)
        verbindung.execute("DELETE FROM felder WHERE id = ?", (feld_id,))


def feld_verschieben(datenbank_id, feld_id, um):
    """
    Schiebt ein Feld in der Reihenfolge nach vorn (um = -1) oder nach hinten (+1).
    Gibt True zurück, wenn sich etwas geändert hat.

    Dabei werden alle Felder neu durchnummeriert. Das räumt nebenbei doppelte
    Positionsnummern auf, die entstehen konnten, wenn ein Feld gelöscht und
    danach ein neues angelegt wurde.
    """
    felder = list(felder_liste(datenbank_id))

    stelle = -1
    nummer = 0
    for feld in felder:
        if feld["id"] == feld_id:
            stelle = nummer
        nummer = nummer + 1

    if stelle < 0:
        raise ValueError(sprache.text("feld_gibt_es_nicht"))

    ziel = stelle + um
    if ziel < 0 or ziel >= len(felder):
        return False      # ganz außen, es geht nicht weiter

    felder[stelle], felder[ziel] = felder[ziel], felder[stelle]

    verbindung = verbindung_holen()
    with verbindung:
        nummer = 0
        for feld in felder:
            verbindung.execute("UPDATE felder SET position = ? WHERE id = ?",
                               (nummer, feld["id"]))
            nummer = nummer + 1
    return True


def typ_umstellung_zaehlen(datenbank_id, feld_id, neuer_typ, optionen=None):
    """
    Sieht vor einer Umstellung nach, wie viele Werte sie nicht überstehen.
    Zurück kommt (gefuellt, verloren). Es wird nichts verändert.
    """
    eintrag = datenbank_holen(datenbank_id)
    feld = feld_holen(datenbank_id, feld_id)
    if eintrag is None or feld is None:
        return 0, 0

    verbindung = verbindung_holen()
    cursor = verbindung.execute(
        'SELECT "' + feld["spalte"] + '" AS wert FROM "' + eintrag["tabelle"] + '"'
        ' WHERE "' + feld["spalte"] + '" IS NOT NULL'
    )

    gefuellt = 0
    verloren = 0
    if neuer_typ == "auswahl" and optionen is not None:
        # While the dialog is being edited, its options may be temporarily
        # incomplete. Normalize the values that are present without blocking
        # the live loss estimate; the save path performs the full validation.
        optionen = "\n".join(dict.fromkeys(
            zeile.strip() for zeile in str(optionen).split("\n") if zeile.strip()
        ))
    for zeile in cursor.fetchall():
        text = text_fuer_anzeige(feld["typ"], zeile["wert"])
        if text == "":
            continue
        gefuellt = gefuellt + 1
        if wert_aus_text(neuer_typ, text, optionen) is None:
            verloren = verloren + 1
    cursor.close()

    return gefuellt, verloren


def feld_typ_aendern(datenbank_id, feld_id, neuer_typ, optionen=None):
    """
    Stellt ein Feld auf eine andere Art um - aus Text wird zum Beispiel Zahl.

    SQLite kann die Art einer Spalte nicht nachträglich ändern. Deshalb
    entsteht eine neue Spalte, die Werte wandern umgewandelt hinüber, und die
    alte Spalte fällt weg. Welche Spalte zu einem Feld gehört, steht ohnehin
    in der Tabelle "felder" - zu sehen bekommt man von dem Wechsel nichts.

    Werte, die nicht zur neuen Art passen, bleiben leer. Wie viele das sind,
    sagt typ_umstellung_zaehlen() vorher.
    """
    eintrag = datenbank_holen(datenbank_id)
    if eintrag is None:
        raise ValueError(sprache.text("datenbank_gibt_es_nicht"))

    feld = feld_holen(datenbank_id, feld_id)
    if feld is None:
        raise ValueError(sprache.text("feld_gibt_es_nicht"))

    typ_pruefen(neuer_typ)
    optionen = optionen_pruefen(neuer_typ, optionen)

    verbindung = verbindung_holen()

    if neuer_typ == feld["typ"]:
        # Gleiche Art - dann haben sich höchstens die Möglichkeiten eines
        # Auswahlfeldes geändert. Werte, die nicht mehr zur Auswahl gehören,
        # werden wie bei einer Typumstellung geleert.
        with verbindung:
            if neuer_typ == "auswahl":
                cursor = verbindung.execute(
                    'SELECT id, "' + feld["spalte"] + '" AS wert FROM "'
                    + eintrag["tabelle"] + '" WHERE "' + feld["spalte"] + '" IS NOT NULL'
                )
                ungueltige_ids = []
                for zeile in cursor.fetchall():
                    text = text_fuer_anzeige(feld["typ"], zeile["wert"])
                    if wert_aus_text(neuer_typ, text, optionen) is None:
                        ungueltige_ids.append((zeile["id"],))
                cursor.close()
                if ungueltige_ids:
                    verbindung.executemany(
                        'UPDATE "' + eintrag["tabelle"] + '" SET "'
                        + feld["spalte"] + '" = NULL WHERE id = ?', ungueltige_ids
                    )
            verbindung.execute("UPDATE felder SET optionen = ? WHERE id = ?",
                               (optionen, feld_id))
        return

    # Ein Name für die neue Spalte, der noch nicht vergeben ist.
    felder = []
    for anderes in felder_liste(datenbank_id):
        felder.append({schluessel: anderes[schluessel]
                       for schluessel in ("id", "anzeigename", "spalte", "typ", "optionen")})
    vorhandene_spalten = [anderes["spalte"] for anderes in felder]
    neue_spalte = spaltenname_bilden(feld["anzeigename"], vorhandene_spalten)

    with verbindung:
        spalte_anhaengen(verbindung, eintrag["tabelle"], neue_spalte, neuer_typ)

        cursor = verbindung.execute(
            'SELECT id, "' + feld["spalte"] + '" AS wert FROM "' + eintrag["tabelle"] + '"'
        )
        umgewandelt = []
        for zeile in cursor.fetchall():
            text = text_fuer_anzeige(feld["typ"], zeile["wert"])
            umgewandelt.append((wert_aus_text(neuer_typ, text, optionen), zeile["id"]))
        cursor.close()

        if umgewandelt:
            verbindung.executemany(
                'UPDATE "' + eintrag["tabelle"] + '" SET "' + neue_spalte + '" = ? WHERE id = ?',
                umgewandelt
            )

        felder_neu = []
        for anderes in felder:
            if anderes["id"] == feld_id:
                anderes["spalte"] = neue_spalte
                anderes["typ"] = neuer_typ
            felder_neu.append(anderes)
        spalte_entfernen(verbindung, eintrag["tabelle"], feld["spalte"], felder_neu)
        verbindung.execute(
            "UPDATE felder SET typ = ?, spalte = ?, optionen = ? WHERE id = ?",
            (neuer_typ, neue_spalte, optionen, feld_id)
        )


def spalte_entfernen(verbindung, tabelle, spalte, felder):
    """Entfernt eine Spalte auch dann, wenn SQLite noch kein DROP COLUMN kennt."""
    if sqlite3.sqlite_version_info >= (3, 35, 0):
        verbindung.execute(
            'DROP INDEX IF EXISTS "index_' + tabelle + "_" + spalte + '"'
        )
        verbindung.execute(
            'ALTER TABLE "' + tabelle + '" DROP COLUMN "' + spalte + '"'
        )
        return

    verbleibende = [feld for feld in felder if feld["spalte"] != spalte]
    ersatztabelle = tabelle + "_umbau"
    letzte_id = verbindung.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = ?", (tabelle,)
    ).fetchone()
    hoechste_id = letzte_id[0] if letzte_id is not None else 0
    verbindung.execute('DROP TABLE IF EXISTS "' + ersatztabelle + '"')

    definitionen = ["id INTEGER PRIMARY KEY AUTOINCREMENT"]
    for feld in verbleibende:
        definitionen.append('"' + feld["spalte"] + '" ' + SQL_TYPEN[feld["typ"]])
    verbindung.execute(
        'CREATE TABLE "' + ersatztabelle + '" (' + ", ".join(definitionen) + ")"
    )

    spalten = ["id"] + ['"' + feld["spalte"] + '"' for feld in verbleibende]
    spalten_sql = ", ".join(spalten)
    verbindung.execute(
        'INSERT INTO "' + ersatztabelle + '" (' + spalten_sql + ')'
        ' SELECT ' + spalten_sql + ' FROM "' + tabelle + '"'
    )
    verbindung.execute('DROP TABLE "' + tabelle + '"')
    verbindung.execute(
        'ALTER TABLE "' + ersatztabelle + '" RENAME TO "' + tabelle + '"'
    )
    if letzte_id is not None:
        aktualisiert = verbindung.execute(
            "UPDATE sqlite_sequence SET seq = MAX(seq, ?) WHERE name = ?",
            (hoechste_id, tabelle)
        )
        if aktualisiert.rowcount == 0:
            verbindung.execute(
                "INSERT INTO sqlite_sequence (name, seq) VALUES (?, ?)",
                (tabelle, hoechste_id)
            )

    # Beim Neuaufbau verschwinden auch die Tabellenindizes. Stelle sie wieder her.
    for feld in verbleibende:
        if feld["typ"] != "langtext":
            verbindung.execute(
                'CREATE INDEX IF NOT EXISTS "index_' + tabelle + "_" + feld["spalte"] + '"'
                ' ON "' + tabelle + '" ("' + feld["spalte"] + '")'
            )


# ---------------------------------------------------------------------------
# Werte umwandeln (Eingabe <-> Datenbank <-> Anzeige)
# ---------------------------------------------------------------------------

def wert_aus_eingabe(typ, eingabe, optionen=None):
    """
    Wandelt das, was der Nutzer eingetippt hat, in den Wert für die Datenbank um.
    Passt die Eingabe nicht zum Feldtyp, gibt es einen ValueError mit Erklärung.
    """
    if typ == "janein":
        # Hier kommt schon True oder False aus dem Ankreuzfeld.
        if eingabe:
            return 1
        return 0

    if typ in ("text", "langtext"):
        text = str(eingabe).replace("\r\n", "\n").replace("\r", "\n")
        if text == "":
            return None
        return text

    text = str(eingabe).strip()

    if text == "":
        return None   # leeres Feld bedeutet: nichts gespeichert

    if typ == "zahl":
        # In Deutschland schreibt man 3,5 - SQLite rechnet mit 3.5
        try:
            zahl = float(text.replace(",", "."))
        except ValueError:
            raise ValueError(sprache.text("keine_zahl") % text)
        if not math.isfinite(zahl):
            raise ValueError(sprache.text("keine_zahl") % text)
        return zahl

    if typ == "datum":
        pruefe_datum(text)
        return text

    if typ == "auswahl":
        if optionen is None:
            moeglichkeiten = []
        elif isinstance(optionen, str):
            moeglichkeiten = optionen.split("\n")
        else:
            moeglichkeiten = list(optionen)
        if text not in moeglichkeiten:
            raise ValueError(sprache.text("keine_auswahl") % text)

    return text


def pruefe_datum(text):
    """Prüft, ob ein Datum die Form JJJJ-MM-TT hat (z.B. 2026-08-11)."""
    teile = text.split("-")
    fehler = ValueError(sprache.text("kein_datum") % text)

    if len(teile) != 3:
        raise fehler
    if len(teile[0]) != 4 or len(teile[1]) != 2 or len(teile[2]) != 2:
        raise fehler

    for teil in teile:
        if not teil.isdigit():
            raise fehler

    # Ob es den Tag wirklich gibt, weiß datetime besser als jede eigene Regel:
    # Den 31. Februar gibt es nicht, den 29. nur im Schaltjahr.
    try:
        datetime.date(int(teile[0]), int(teile[1]), int(teile[2]))
    except ValueError:
        raise fehler


def wert_aus_text(typ, text, optionen=None):
    """
    Wandelt einen Text in einen Wert für die Datenbank um.

    Anders als wert_aus_eingabe() beschwert sich diese Funktion nicht: Passt
    der Text nicht zum Feldtyp, kommt None zurück - das Feld bleibt dann leer.
    Gebraucht wird das an zwei Stellen, an denen ein einzelner unpassender
    Wert nicht alles abbrechen soll: beim Einlesen einer Datei und beim
    Umstellen eines Feldes auf eine andere Art.
    """
    # Windows schreibt Zeilenumbrüche als zwei Zeichen. In der Datenbank soll
    # überall dasselbe stehen, sonst entstehen beim Anzeigen doppelte Umbrüche.
    text = str(text).replace("\r\n", "\n").replace("\r", "\n")
    if typ not in ("text", "langtext"):
        text = text.strip()
    if text == "":
        return None

    if typ == "janein":
        wert = text.casefold()
        if wert in ("yes", "y", "ja", "j", "1", "true", "wahr", "x"):
            return 1
        if wert in ("no", "n", "nein", "0", "false", "falsch"):
            return 0
        return None

    try:
        return wert_aus_eingabe(typ, text, optionen)
    except ValueError:
        return None      # unpassender Wert - das Feld bleibt leer


def text_fuer_anzeige(typ, wert):
    """Macht aus dem gespeicherten Wert einen Text für Tabelle und Formular."""
    if wert is None:
        return ""

    if typ == "janein":
        if wert:
            return ja_text()
        return nein_text()

    if typ == "zahl":
        # 5.0 soll als "5" erscheinen, 5.5 bleibt "5.5"
        zahl = float(wert)
        if not math.isfinite(zahl):
            return str(wert)
        if zahl == int(zahl):
            return str(int(zahl))
        return str(zahl)

    return str(wert)


# ---------------------------------------------------------------------------
# Datensätze
# ---------------------------------------------------------------------------

def such_ausdruck(feld):
    """
    Der Text, in dem die Suche eines Feldes sucht.

    Zahlen liegen als Kommazahl in der Datenbank: aus 5 wird 5.0. Ein
    schlichtes CAST würde also "5.0" durchsuchen, während in der Tabelle "5"
    steht - eine Suche nach "0" fände dann jede ganze Zahl. Deshalb wird hier
    derselbe Text gebildet, den auch text_fuer_anzeige() erzeugt.
    """
    spalte = '"' + feld["spalte"] + '"'

    if feld["typ"] != "zahl":
        return "CAST(" + spalte + " AS TEXT)"

    return ("CASE WHEN " + spalte + " IS NULL THEN NULL"
            " WHEN " + spalte + " = CAST(" + spalte + " AS INTEGER)"
            " THEN CAST(CAST(" + spalte + " AS INTEGER) AS TEXT)"
            " ELSE CAST(" + spalte + " AS TEXT) END")


def bedingung_bauen(felder, suchbegriff, filter_feld, filter_wert):
    """
    Baut den WHERE-Teil für Suche und Filter.

    Zurück kommen der SQL-Text (mit Fragezeichen) und die Liste der Werte.
    Die Spaltennamen stammen aus der Tabelle "felder", also aus geprüften Daten.
    """
    bedingungen = []
    werte = []

    if suchbegriff:
        # In LIKE haben % und _ eine Sonderbedeutung: % steht für beliebigen Text,
        # _ für ein beliebiges Zeichen. Wer nach "50%" sucht, meint aber wirklich
        # das Prozentzeichen. Deshalb setzen wir einen Backslash davor und sagen
        # SQLite mit ESCAPE, dass dieser die Sonderbedeutung aufhebt.
        gesucht = suchbegriff.replace("\\", "\\\\")
        gesucht = gesucht.replace("%", "\\%")
        gesucht = gesucht.replace("_", "\\_")
        muster = "%" + gesucht + "%"

        teile = []
        for feld in felder:
            # such_ausdruck macht auch aus Zahlen und Daten einen Text,
            # damit über alle Felder hinweg gesucht werden kann.
            teile.append(such_ausdruck(feld) + " LIKE ? ESCAPE '\\'")
            werte.append(muster)
        if teile:
            bedingungen.append("(" + " OR ".join(teile) + ")")

    if filter_feld is not None and filter_wert != "":
        if filter_feld["typ"] == "janein":
            bedingungen.append('"' + filter_feld["spalte"] + '" = ?')
            if filter_wert == ja_text():
                werte.append(1)
            else:
                werte.append(0)
        else:
            bedingungen.append('"' + filter_feld["spalte"] + '" = ?')
            werte.append(filter_wert)

    if bedingungen:
        return " WHERE " + " AND ".join(bedingungen), werte
    return "", werte


def spaltenliste(felder):
    """
    Die Spalten, die eine Abfrage holt: die laufende Nummer und alle Felder.
    Die Namen kommen aus der Tabelle "felder", sind also geprüft.
    """
    spalten = ["id"]
    for feld in felder:
        spalten.append('"' + feld["spalte"] + '"')
    return ", ".join(spalten)


def datensaetze_suchen(datenbank_id, suchbegriff="", filter_feld=None, filter_wert="",
                       sortier_feld=None, absteigend=False, limit=100, offset=0,
                       eintrag=None, felder=None):
    """
    Holt eine Seite von Datensätzen.

    limit und offset sorgen dafür, dass immer nur eine Seite geladen wird.
    Es liegen also nie mehr als eine Seite Datensätze gleichzeitig im
    Speicher, auch wenn die Datenbank 10.000 Einträge hat.

    eintrag und felder darf man mitgeben, wenn man sie ohnehin schon geholt
    hat - dann spart sich diese Funktion die beiden Abfragen dafür.
    """
    if eintrag is None:
        eintrag = datenbank_holen(datenbank_id)
    if eintrag is None:
        return []

    if felder is None:
        felder = felder_liste(datenbank_id)
    if not felder:
        return []

    where_teil, werte = bedingung_bauen(felder, suchbegriff, filter_feld, filter_wert)

    # Sortiert wird nach einem Feld aus der Tabelle "felder" - niemals nach
    # einem Text, den der Nutzer eingegeben hat.
    if sortier_feld is None:
        sortierung = "id"
    else:
        sortierung = '"' + sortier_feld["spalte"] + '"'

    if absteigend:
        richtung = "DESC"
    else:
        richtung = "ASC"

    sql = ("SELECT " + spaltenliste(felder) + ' FROM "' + eintrag["tabelle"] + '"'
           + where_teil + " ORDER BY " + sortierung + " " + richtung + " LIMIT ? OFFSET ?")

    werte.append(limit)
    werte.append(offset)

    verbindung = verbindung_holen()
    cursor = verbindung.execute(sql, werte)
    zeilen = cursor.fetchall()
    cursor.close()
    return zeilen


def anzahl_datensaetze(datenbank_id, suchbegriff="", filter_feld=None, filter_wert="",
                       eintrag=None, felder=None):
    """
    Zählt, wie viele Datensätze zur Suche passen.
    eintrag und felder darf man wie oben mitgeben, wenn sie schon vorliegen.
    """
    if eintrag is None:
        eintrag = datenbank_holen(datenbank_id)
    if eintrag is None:
        return 0

    if felder is None:
        felder = felder_liste(datenbank_id)
    where_teil, werte = bedingung_bauen(felder, suchbegriff, filter_feld, filter_wert)

    verbindung = verbindung_holen()
    cursor = verbindung.execute(
        'SELECT COUNT(*) FROM "' + eintrag["tabelle"] + '"' + where_teil, werte
    )
    anzahl = cursor.fetchone()[0]
    cursor.close()
    return anzahl


def datensatz_holen(datenbank_id, datensatz_id):
    """Holt einen einzelnen Datensatz (oder None)."""
    eintrag = datenbank_holen(datenbank_id)
    if eintrag is None:
        return None

    felder = felder_liste(datenbank_id)

    verbindung = verbindung_holen()
    cursor = verbindung.execute(
        "SELECT " + spaltenliste(felder) + ' FROM "' + eintrag["tabelle"] + '" WHERE id = ?',
        (datensatz_id,)
    )
    zeile = cursor.fetchone()
    cursor.close()
    return zeile


def datensatz_hinzufuegen(datenbank_id, werte_je_feld):
    """
    Legt einen neuen Datensatz an und gibt seine id zurück.

    werte_je_feld ist ein Wörterbuch: {feld_id: wert}
    """
    eintrag = datenbank_holen(datenbank_id)
    felder = felder_liste(datenbank_id)

    spalten = []
    platzhalter = []
    werte = []
    for feld in felder:
        if feld["id"] in werte_je_feld:
            spalten.append('"' + feld["spalte"] + '"')
            platzhalter.append("?")
            werte.append(werte_je_feld[feld["id"]])

    if not spalten:
        raise ValueError(sprache.text("nichts_eingegeben"))

    sql = ('INSERT INTO "' + eintrag["tabelle"] + '" (' + ", ".join(spalten) + ")"
           " VALUES (" + ", ".join(platzhalter) + ")")

    verbindung = verbindung_holen()
    with verbindung:
        cursor = verbindung.execute(sql, werte)
        neue_id = cursor.lastrowid
        cursor.close()
    return neue_id


def viele_datensaetze_hinzufuegen(datenbank_id, liste_von_werten, erwartete_felder=None):
    """
    Legt viele Datensätze auf einmal an - dafür braucht es nur einen
    Schreibvorgang statt tausender einzelner. Wird von testdaten.py benutzt.

    liste_von_werten ist eine Liste von Wörterbüchern {feld_id: wert}.
    """
    if not liste_von_werten:
        return

    verbindung = verbindung_holen()
    with verbindung:
        verbindung.execute("BEGIN IMMEDIATE")
        eintrag = datenbank_holen(datenbank_id)
        felder = felder_liste(datenbank_id)
        if eintrag is None or not felder:
            if erwartete_felder is not None:
                raise ValueError(sprache.text("import_schema_geaendert"))
            return
        _import_felder_pruefen(felder, erwartete_felder)
        _viele_datensaetze_einfuegen(verbindung, eintrag, felder, liste_von_werten)


def import_schema_pruefen(datenbank_id, erwartete_felder, zusaetzliche_felder=False):
    """Prüft nach einem Dialog, ob die zuvor angezeigte Feldstruktur noch gilt."""
    if datenbank_holen(datenbank_id) is None:
        raise ValueError(sprache.text("import_schema_geaendert"))
    aktuelle_felder = felder_liste(datenbank_id)
    _import_felder_pruefen(aktuelle_felder, erwartete_felder, zusaetzliche_felder)


def _import_felder_pruefen(aktuelle_felder, erwartete_felder, zusaetzliche_felder=False):
    """Bricht ab, wenn sich das Schema seit dem Zuordnen der Importdatei änderte."""
    if erwartete_felder is None:
        return

    schluessel = ("anzeigename", "spalte", "typ", "optionen")
    aktuell = {
        feld["id"]: tuple(feld[name] for name in schluessel)
        for feld in aktuelle_felder
    }
    erwartet = {
        feld["id"]: tuple(feld[name] for name in schluessel)
        for feld in erwartete_felder
    }
    unveraendert = all(aktuell.get(feld_id) == signatur
                       for feld_id, signatur in erwartet.items())
    if not unveraendert or (not zusaetzliche_felder and aktuell != erwartet):
        raise ValueError(sprache.text("import_schema_geaendert"))


def csv_datensaetze_uebernehmen(datenbank_id, ueberschriften, zeilen,
                                neue_felder_anlegen, unbekannt,
                                schluessel_feld_id, erwartete_felder):
    """Legt Importfelder und Datensätze gemeinsam oder gar nicht an."""
    if not zeilen:
        return 0, 0

    verbindung = verbindung_holen()
    with verbindung:
        verbindung.execute("BEGIN IMMEDIATE")
        eintrag = datenbank_holen(datenbank_id)
        felder = felder_liste(datenbank_id)
        if eintrag is None:
            raise ValueError(sprache.text("import_schema_geaendert"))
        _import_felder_pruefen(felder, erwartete_felder)

        if neue_felder_anlegen:
            felder = _import_felder_in_transaktion(
                verbindung, eintrag, felder, unbekannt, datenbank_id)

        positionen = {}
        for nummer, ueberschrift in enumerate(ueberschriften):
            schluessel = text_vergleichsschluessel(ueberschrift)
            if not schluessel:
                continue
            if schluessel in positionen:
                raise ValueError(sprache.text("csv_doppelte_ueberschriften") % ueberschrift)
            positionen[schluessel] = nummer

        zuordnung = []
        treffer = {}
        for feld in felder:
            schluessel = text_vergleichsschluessel(feld["anzeigename"])
            if schluessel not in positionen:
                continue
            if schluessel in treffer:
                raise ValueError(sprache.text("csv_feld_uneindeutig")
                                 % feld["anzeigename"])
            treffer[schluessel] = feld
            zuordnung.append((positionen[schluessel], feld))

        if not zuordnung:
            raise ValueError(sprache.text("keine_spalte_passt"))

        datensaetze = []
        for zeile in zeilen:
            werte = {}
            for nummer, feld in zuordnung:
                if nummer < len(zeile):
                    werte[feld["id"]] = wert_aus_text(
                        feld["typ"], zeile[nummer], feld["optionen"])
            datensaetze.append(werte)

        if schluessel_feld_id is None:
            _viele_datensaetze_einfuegen(verbindung, eintrag, felder, datensaetze)
            return len(datensaetze), 0

        schluessel_feld = next(
            (feld for feld in felder if feld["id"] == schluessel_feld_id), None
        )
        if schluessel_feld is None or schluessel_feld_id not in {
                feld["id"] for _, feld in zuordnung}:
            raise ValueError(sprache.text("import_schema_geaendert"))
        return _datensaetze_abgleichen_in_transaktion(
            verbindung, eintrag, felder, datenbank_id, datensaetze, schluessel_feld)


def _viele_datensaetze_einfuegen(verbindung, eintrag, felder, liste_von_werten):
    """Schreibt Datensätze mit der bereits offenen Transaktion."""
    if not liste_von_werten:
        return

    spalten = ['"' + feld["spalte"] + '"' for feld in felder]
    platzhalter = ["?"] * len(felder)
    sql = ('INSERT INTO "' + eintrag["tabelle"] + '" (' + ", ".join(spalten) + ")"
           " VALUES (" + ", ".join(platzhalter) + ")")
    zeilen = [[werte.get(feld["id"]) for feld in felder]
              for werte in liste_von_werten]
    verbindung.executemany(sql, zeilen)


def datensaetze_abgleichen_pruefen(datenbank_id, liste_von_werten, schluessel_feld):
    """Prüft, dass das Schlüsselfeld im Bestand und in der Datei eindeutig ist."""
    eintrag = datenbank_holen(datenbank_id)
    felder = felder_liste(datenbank_id)
    if eintrag is None or not felder or not liste_von_werten:
        return
    if not any(feld["id"] == schluessel_feld["id"] for feld in felder):
        raise ValueError(sprache.text("feld_gibt_es_nicht"))

    spalte = '"' + schluessel_feld["spalte"] + '"'
    verbindung = verbindung_holen()
    cursor = verbindung.execute(
        "SELECT " + spalte + " AS schluessel FROM \"" + eintrag["tabelle"] + "\""
        " WHERE " + spalte + " IS NOT NULL"
    )
    bekannt = set()
    for zeile in cursor.fetchall():
        merkmal = text_fuer_anzeige(schluessel_feld["typ"], zeile["schluessel"])
        if merkmal == "":
            continue
        if merkmal in bekannt:
            cursor.close()
            raise ValueError(sprache.text("abgleichen_doppelte_bestand")
                             % schluessel_feld["anzeigename"])
        bekannt.add(merkmal)
    cursor.close()

    aus_datei = set()
    for werte in liste_von_werten:
        merkmal = text_fuer_anzeige(
            schluessel_feld["typ"], werte.get(schluessel_feld["id"])
        )
        if merkmal == "":
            continue
        if merkmal in aus_datei:
            raise ValueError(sprache.text("abgleichen_doppelte_datei") % merkmal)
        aus_datei.add(merkmal)


def datensaetze_abgleichen(datenbank_id, liste_von_werten, schluessel_feld,
                           erwartete_felder=None):
    """
    Hängt Datensätze an - oder überschreibt vorhandene, wenn sie sich am
    Schlüsselfeld wiedererkennen lassen. Zurück kommt (angelegt, geaendert).

    Die vorhandenen Schlüsselwerte werden einmal am Anfang eingelesen. Sonst
    bräuchte jede Zeile der Datei eine eigene Abfrage - bei 10.000 Zeilen
    wären das 10.000 Abfragen statt einer.
    """
    if not liste_von_werten:
        return 0, 0

    verbindung = verbindung_holen()
    # Acquire the write reservation before reading metadata or checking keys.
    # This keeps a second app process from changing the schema or importing
    # the same previously unused key between validation and writing.
    with verbindung:
        verbindung.execute("BEGIN IMMEDIATE")
        eintrag = datenbank_holen(datenbank_id)
        felder = felder_liste(datenbank_id)
        if eintrag is None or not felder:
            if erwartete_felder is not None:
                raise ValueError(sprache.text("import_schema_geaendert"))
            return 0, 0
        _import_felder_pruefen(felder, erwartete_felder)
        schluessel_feld = next(
            (feld for feld in felder if feld["id"] == schluessel_feld["id"]), None
        )
        if schluessel_feld is None:
            raise ValueError(sprache.text("feld_gibt_es_nicht"))
        return _datensaetze_abgleichen_in_transaktion(
            verbindung, eintrag, felder, datenbank_id, liste_von_werten, schluessel_feld
        )


def _datensaetze_abgleichen_in_transaktion(
        verbindung, eintrag, felder, datenbank_id, liste_von_werten, schluessel_feld):
    """Prüft und schreibt einen Abgleich innerhalb derselben Transaktion."""
    datensaetze_abgleichen_pruefen(datenbank_id, liste_von_werten, schluessel_feld)

    schluessel_spalte = '"' + schluessel_feld["spalte"] + '"'

    cursor = verbindung.execute(
        "SELECT id, " + schluessel_spalte + " AS schluessel FROM \"" + eintrag["tabelle"] + "\""
        " WHERE " + schluessel_spalte + " IS NOT NULL"
    )
    bekannt = {}
    for zeile in cursor.fetchall():
        merkmal = text_fuer_anzeige(schluessel_feld["typ"], zeile["schluessel"])
        # Duplikate wurden oben bereits abgewiesen; ein Wert darf nur einmal
        # auf einen vorhandenen Datensatz zeigen.
        if merkmal not in bekannt:
            bekannt[merkmal] = zeile["id"]
    cursor.close()

    neue = []
    aenderungen = []
    for werte in liste_von_werten:
        merkmal = text_fuer_anzeige(schluessel_feld["typ"], werte.get(schluessel_feld["id"]))
        if merkmal != "" and merkmal in bekannt:
            aenderungen.append((bekannt[merkmal], werte))
        else:
            neue.append(werte)

    if aenderungen:
        # Alle Zeilen einer Datei haben dieselben Spalten, deshalb genügt ein
        # einziger Befehl für alle Änderungen.
        betroffene = []
        for feld in felder:
            if feld["id"] in aenderungen[0][1]:
                betroffene.append(feld)

        zuweisungen = []
        for feld in betroffene:
            zuweisungen.append('"' + feld["spalte"] + '" = ?')

        sql = ('UPDATE "' + eintrag["tabelle"] + '" SET ' + ", ".join(zuweisungen)
               + " WHERE id = ?")

        zeilen = []
        for datensatz_id, werte in aenderungen:
            eine_zeile = []
            for feld in betroffene:
                eine_zeile.append(werte.get(feld["id"]))
            eine_zeile.append(datensatz_id)
            zeilen.append(eine_zeile)

    else:
        zeilen = []
        sql = None

    # Neue und geänderte Datensätze gehören zu einem Import. Ein Fehler in
    # einem Teil rollt dadurch den ganzen Import zurück.
    if neue:
        _viele_datensaetze_einfuegen(verbindung, eintrag, felder, neue)
    if aenderungen:
        verbindung.executemany(sql, zeilen)

    return len(neue), len(aenderungen)


def datensatz_aendern(datenbank_id, datensatz_id, werte_je_feld):
    """Überschreibt einen vorhandenen Datensatz."""
    eintrag = datenbank_holen(datenbank_id)
    felder = felder_liste(datenbank_id)

    zuweisungen = []
    werte = []
    for feld in felder:
        if feld["id"] in werte_je_feld:
            zuweisungen.append('"' + feld["spalte"] + '" = ?')
            werte.append(werte_je_feld[feld["id"]])

    if not zuweisungen:
        return

    werte.append(datensatz_id)
    sql = ('UPDATE "' + eintrag["tabelle"] + '" SET ' + ", ".join(zuweisungen) + " WHERE id = ?")

    verbindung = verbindung_holen()
    with verbindung:
        cursor = verbindung.execute(sql, werte)
        cursor.close()


def datensatz_loeschen(datenbank_id, datensatz_id):
    """Löscht einen Datensatz."""
    eintrag = datenbank_holen(datenbank_id)
    if eintrag is None:
        return

    verbindung = verbindung_holen()
    with verbindung:
        cursor = verbindung.execute(
            'DELETE FROM "' + eintrag["tabelle"] + '" WHERE id = ?', (datensatz_id,)
        )
        cursor.close()


# So viele verschiedene Werte nimmt die Filterliste höchstens auf.
# Eine Klappliste mit tausenden Einträgen wäre nicht mehr zu bedienen.
FILTERWERTE_HOECHSTENS = 200


def werte_einer_spalte(datenbank_id, feld):
    """
    Gibt die unterschiedlichen Werte eines Feldes für die Filterliste zurück.

    Zurück kommt (werte, gesamt). Gibt es mehr Werte als FILTERWERTE_HOECHSTENS,
    enthält die Liste nur den Anfang - gesamt sagt dann, wie viele es wirklich
    sind, damit die Oberfläche darauf hinweisen kann. Früher wurde stillschweigend
    abgeschnitten, und niemand konnte sehen, dass Werte fehlten.
    """
    if feld["typ"] == "janein":
        werte = [ja_text(), nein_text()]
        return werte, len(werte)

    if feld["typ"] == "auswahl":
        werte = optionen_liste(feld)
        return werte, len(werte)

    eintrag = datenbank_holen(datenbank_id)
    if eintrag is None:
        return [], 0

    spalte = '"' + feld["spalte"] + '"'
    tabelle = '"' + eintrag["tabelle"] + '"'
    nur_gefuellte = " WHERE " + spalte + " IS NOT NULL AND " + spalte + " <> ''"

    verbindung = verbindung_holen()

    cursor = verbindung.execute(
        "SELECT COUNT(DISTINCT " + spalte + ") FROM " + tabelle + nur_gefuellte
    )
    gesamt = cursor.fetchone()[0]
    cursor.close()

    cursor = verbindung.execute(
        "SELECT DISTINCT " + spalte + " AS wert FROM " + tabelle + nur_gefuellte
        + " ORDER BY 1 LIMIT " + str(FILTERWERTE_HOECHSTENS)
    )
    zeilen = cursor.fetchall()
    cursor.close()

    werte = []
    for zeile in zeilen:
        werte.append(text_fuer_anzeige(feld["typ"], zeile["wert"]))
    return werte, gesamt


# ---------------------------------------------------------------------------
# Die Datei selbst: sichern und aufräumen
# ---------------------------------------------------------------------------

def ist_dieselbe_datei(ein_pfad, anderer_pfad):
    """
    Sagt, ob zwei Pfade auf dieselbe Datei zeigen.

    Ein Vergleich der Texte genügt nicht: Es kann derselbe Ort mit anderer
    Schreibweise gemeint sein. Gibt es die Datei schon, fragt samefile das
    Betriebssystem - das ist die verlässliche Auskunft.
    """
    ein_pfad = os.path.realpath(ein_pfad)
    anderer_pfad = os.path.realpath(anderer_pfad)

    if ein_pfad == anderer_pfad:
        return True
    if os.path.exists(ein_pfad) and os.path.exists(anderer_pfad):
        return os.path.samefile(ein_pfad, anderer_pfad)
    return False


def sicherung_schreiben(zielpfad):
    """
    Schreibt eine vollständige Kopie der Datenbankdatei.

    sqlite3 bringt das selbst mit: backup() überträgt die geöffnete Datenbank
    Seite für Seite in eine zweite Datei. Das ist sicherer, als die Datei zu
    kopieren - dabei könnte man einen halb geschriebenen Stand erwischen.

    Auf die geöffnete Datenbank selbst darf dabei nicht geschrieben werden:
    SQLite wartet sonst endlos darauf, dass die Sperre fällt, die die eigene
    Verbindung hält - das Programm bliebe stehen, ohne Meldung, ohne Ausweg.
    Deshalb wird das hier abgefangen, bevor irgendetwas geschrieben wird.
    """
    if ist_dieselbe_datei(zielpfad, DATENBANK_DATEI):
        raise ValueError(sprache.text("sicherung_auf_sich_selbst"))

    ziel = sqlite3.connect(zielpfad)
    try:
        verbindung_holen().backup(ziel)
    finally:
        ziel.close()


def aufraeumen():
    """
    Gibt den Platz frei, den gelöschte Daten in der Datei noch belegen.
    Zurück kommt die Größe vorher und nachher (in Bytes).

    SQLite behält gelöschte Seiten für neue Daten zurück; die Datei wird von
    allein also nie kleiner. VACUUM baut sie neu auf. Das geht nur außerhalb
    einer Transaktion, deshalb wird vorher alles festgeschrieben.
    """
    verbindung = verbindung_holen()
    verbindung.commit()

    vorher = os.path.getsize(DATENBANK_DATEI)
    cursor = verbindung.execute("VACUUM")
    cursor.close()
    nachher = os.path.getsize(DATENBANK_DATEI)

    return vorher, nachher
