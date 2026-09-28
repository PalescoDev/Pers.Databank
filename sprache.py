"""
sprache.py
----------
Alle Texte, die der Nutzer zu sehen bekommt - auf Englisch und auf Deutsch.

Wer einen Text ändern oder eine Sprache ergänzen möchte, ändert nur diese
Datei. Im übrigen Programm steht an keiner Stelle mehr ein fertiger Satz,
sondern immer nur sein Name:

    sprache.text("speichern")   ->  "Save"  oder  "Speichern"

Texte mit einer Lücke darin benutzen dieselben Platzhalter wie sonst auch
(%s für einen Text, %d für eine Zahl):

    sprache.text("bereich") % (1, 100, 4711)   ->  "1-100 von 4711"

Die Platzhalter müssen in beiden Sprachen dieselben sein - in derselben
Reihenfolge, sonst passt der eingesetzte Wert nicht mehr zum Satz.
"""

# Welche Sprache gerade gilt: "en" oder "de".
AKTUELL = "en"


def sprache_setzen(code):
    """
    Legt die Sprache fest. Bei einem unbekannten Kürzel bleibt es bei Englisch.

    Wichtig: Texte werden beim Erzeugen eines Bedienelements gesetzt. Nach
    einem Wechsel muss die Oberfläche also neu aufgebaut werden - genau wie
    bei den Farben.
    """
    global AKTUELL
    if code in ("en", "de"):
        AKTUELL = code
    else:
        AKTUELL = "en"


def kommazahl(wert):
    """
    Eine Zahl mit einer Nachkommastelle in der Schreibweise der Sprache:
    im Englischen 1.2, im Deutschen 1,2.
    """
    geschrieben = "%.1f" % wert
    if AKTUELL == "de":
        geschrieben = geschrieben.replace(".", ",")
    return geschrieben


def text(schluessel):
    """
    Gibt einen Text in der eingestellten Sprache zurück.

    Fehlt der Name in der Liste unten, kommt er selbst zurück. Dann steht
    zwar etwas Unschönes auf dem Bildschirm, aber das Programm läuft weiter -
    besser als ein Absturz wegen eines vergessenen Textes.
    """
    if schluessel not in TEXTE:
        return schluessel
    return TEXTE[schluessel][AKTUELL]


# ---------------------------------------------------------------------------
# Die Texte
# ---------------------------------------------------------------------------

TEXTE = {

    # --- immer wieder gebrauchte Knöpfe -----------------------------------
    "abbrechen": {"en": "Cancel", "de": "Abbrechen"},
    "speichern": {"en": "Save", "de": "Speichern"},
    "loeschen": {"en": "Delete", "de": "Löschen"},
    "importieren": {"en": "Import", "de": "Importieren"},
    "exportieren": {"en": "Export", "de": "Exportieren"},
    "zuruecksetzen": {"en": "Reset", "de": "Zurücksetzen"},
    "ja": {"en": "Yes", "de": "Ja"},
    "nein": {"en": "No", "de": "Nein"},
    "keine": {"en": "none", "de": "keine"},

    # --- Seitenleiste ------------------------------------------------------
    "datenbanken_ueberschrift": {"en": "DATABASES", "de": "DATENBANKEN"},
    "neue_datenbank_knopf": {"en": "+   New database", "de": "+   Neue Datenbank"},
    "datenbank_loeschen_knopf": {"en": "Delete this database",
                                 "de": "Diese Datenbank löschen"},
    "einstellungen_eintrag": {"en": "⚙   Settings", "de": "⚙   Einstellungen"},

    # --- Kopfzeile und Werkzeugleiste --------------------------------------
    "neuer_datensatz_knopf": {"en": "+   New record", "de": "+   Neuer Datensatz"},
    "feld_hinzufuegen_knopf": {"en": "+   Add field", "de": "+   Feld hinzufügen"},
    "suche": {"en": "Search", "de": "Suche"},
    "filter": {"en": "Filter", "de": "Filter"},
    "filter_alle": {"en": "All", "de": "Alle"},

    # --- Tabelle und Fußzeile ----------------------------------------------
    "keine_datensaetze": {"en": "No records", "de": "Keine Datensätze"},
    "ein_datensatz": {"en": "1 record", "de": "1 Datensatz"},
    "n_datensaetze": {"en": "%d records", "de": "%d Datensätze"},
    "bereich": {"en": "%d–%d of %d", "de": "%d–%d von %d"},

    "keine_treffer": {"en": "No matches", "de": "Keine Treffer"},
    "keine_treffer_hinweis": {
        "en": "Change the search term or reset the filter.",
        "de": "Ändere den Suchbegriff oder setze den Filter zurück.",
    },
    "noch_keine_datensaetze": {"en": "No records yet", "de": "Noch keine Datensätze"},
    "noch_keine_datensaetze_hinweis": {
        "en": "Create the first one with \"+  New record\" at the top right.",
        "de": "Lege den ersten mit „+  Neuer Datensatz“ rechts oben an.",
    },
    "keine_datenbank": {"en": "No database", "de": "Keine Datenbank"},
    "noch_keine_datenbank": {"en": "No database yet", "de": "Noch keine Datenbank"},
    "noch_keine_datenbank_hinweis": {
        "en": "Create the first one with \"+  New database\" at the bottom left.",
        "de": "Lege die erste mit „+  Neue Datenbank“ links unten an.",
    },

    # --- Detailansicht ------------------------------------------------------
    "details": {"en": "DETAILS", "de": "DETAILS"},
    "neuer_datensatz": {"en": "New record", "de": "Neuer Datensatz"},
    "datensatz_nummer": {"en": "Record %d", "de": "Datensatz %d"},
    "kein_datensatz_gewaehlt": {
        "en": "No record selected.\n\nPick a row on the left\nor create a new one.",
        "de": "Kein Datensatz gewählt.\n\nWähle links eine Zeile\noder lege einen neuen an.",
    },
    "datumsformat": {"en": "Format: YYYY-MM-DD", "de": "Format: JJJJ-MM-TT"},

    # --- Meldungen im Hauptfenster -----------------------------------------
    "eingabe_pruefen": {"en": "Check your input", "de": "Eingabe prüfen"},
    "feld_mit_fehler": {"en": "Field \"%s\":\n", "de": "Feld „%s“:\n"},

    "loeschen_bestaetigen": {"en": "Confirm deletion", "de": "Löschen bestätigen"},
    "datensatz_wirklich_loeschen": {"en": "Really delete this record?",
                                    "de": "Diesen Datensatz wirklich löschen?"},

    "gespeichert": {"en": "Saved", "de": "Gespeichert"},
    "datensaetze_geschrieben": {
        "en": "%d records were written to the file.",
        "de": "%d Datensätze wurden in die Datei geschrieben.",
    },
    "importiert": {"en": "Imported", "de": "Importiert"},
    "datensaetze_angehaengt": {"en": "%d records were added.",
                               "de": "%d Datensätze wurden angehängt."},

    "feld_loeschen_titel": {"en": "Delete field", "de": "Feld löschen"},
    "feld_loeschen_frage": {
        "en": "Really delete the field \"%s\"?\n\n"
              "Its content will be removed from all %d records.\n"
              "The other fields stay untouched.\n\n"
              "This cannot be undone.",
        "de": "Das Feld „%s“ wirklich löschen?\n\n"
              "Sein Inhalt verschwindet aus allen %d Datensätzen.\n"
              "Die anderen Felder bleiben unberührt.\n\n"
              "Das lässt sich nicht rückgängig machen.",
    },
    "feld_nicht_geloescht": {"en": "Field not deleted", "de": "Feld nicht gelöscht"},
    "kontext_feld_loeschen": {"en": "Delete field \"%s\"", "de": "Feld „%s“ löschen"},
    "kontext_datensatz_loeschen": {"en": "Delete record", "de": "Datensatz löschen"},
    "kontext_feld_art": {"en": "Change type of \"%s\"…", "de": "Art von „%s“ ändern …"},
    "kontext_nach_links": {"en": "Move left", "de": "Nach links"},
    "kontext_nach_rechts": {"en": "Move right", "de": "Nach rechts"},

    # --- Feldart ändern -----------------------------------------------------
    "art_aendern_titel": {"en": "Change field type", "de": "Feldart ändern"},
    "art_aendern_erklaerung": {
        "en": "\"%s\" is a %s field at the moment.\n"
              "Values that do not fit the new type are emptied.",
        "de": "„%s“ ist zurzeit ein Feld der Art %s.\n"
              "Werte, die nicht zur neuen Art passen, werden geleert.",
    },
    "neue_art": {"en": "New type", "de": "Neue Art"},
    "art_aendern_knopf": {"en": "Change type", "de": "Art ändern"},
    "art_feld_leer": {"en": "The field holds no values, so nothing can be lost.",
                      "de": "Das Feld enthält keine Werte, es kann nichts verlorengehen."},
    "art_alle_bleiben": {"en": "All %d values can be kept.",
                         "de": "Alle %d Werte bleiben erhalten."},
    "art_werte_verloren": {
        "en": "%d of %d values do not fit and will be emptied.",
        "de": "%d von %d Werten passen nicht und werden geleert.",
    },
    "art_unveraendert": {
        "en": "The field already has this type.",
        "de": "Diese Art hat das Feld bereits.",
    },
    "art_nur_moeglichkeiten": {
        "en": "The field already has this type - only the options are updated.",
        "de": "Diese Art hat das Feld bereits - es werden nur die Möglichkeiten übernommen.",
    },

    # --- Abgleich beim Einlesen ---------------------------------------------
    "abgleichen_feld": {"en": "Recognise existing records by",
                        "de": "Vorhandene erkennen an"},
    "abgleichen_keins": {"en": "nothing – always append",
                         "de": "nichts – immer anhängen"},
    "abgleichen_erklaerung": {
        "en": "A row whose value matches an existing record overwrites it\n"
              "instead of being added a second time.",
        "de": "Eine Zeile mit gleichem Wert überschreibt den vorhandenen\n"
              "Datensatz, statt ihn ein zweites Mal anzulegen.",
    },
    "abgleichen_doppelte_bestand": {
        "en": "The field \"%s\" has duplicate values in existing records.\n"
              "Choose a field whose values are unique.",
        "de": "Das Feld „%s“ hat doppelte Werte in vorhandenen Datensätzen.\n"
              "Wähle ein Feld mit eindeutigen Werten.",
    },
    "abgleichen_doppelte_datei": {
        "en": "The file contains the matching value \"%s\" more than once.\n"
              "No records were imported.",
        "de": "Die Datei enthält den Abgleichwert „%s“ mehrfach.\n"
              "Es wurden keine Datensätze importiert.",
    },
    "import_ergebnis": {
        "en": "%d records added, %d updated.",
        "de": "%d Datensätze angehängt, %d geändert.",
    },

    "datenbank_loeschen_titel": {"en": "Delete database", "de": "Datenbank löschen"},
    "datenbank_loeschen_frage": {
        "en": "Really delete the database \"%s\" with %d records?\n\n"
              "This cannot be undone.",
        "de": "Die Datenbank „%s“ mit %d Datensätzen wirklich löschen?\n\n"
              "Das lässt sich nicht rückgängig machen.",
    },

    "fehler_titel": {"en": "Error", "de": "Fehler"},
    "fehler_text": {
        "en": "The action could not be completed:\n\n%s\n\nThe program keeps running.",
        "de": "Die Aktion konnte nicht ausgeführt werden:\n\n%s\n\n"
              "Das Programm läuft weiter.",
    },

    # --- Dialog: neue Datenbank --------------------------------------------
    "neue_datenbank_titel": {"en": "New database", "de": "Neue Datenbank"},
    "neue_datenbank_erklaerung": {
        "en": "For example Customers, Products or Projects.\n"
              "You can add more fields at any time afterwards.",
        "de": "Zum Beispiel Kunden, Produkte oder Projekte.\n"
              "Weitere Felder lassen sich jederzeit ergänzen.",
    },
    "name_der_datenbank": {"en": "Name of the database", "de": "Name der Datenbank"},
    "datenbank_startfeld": {
        "en": "The database starts with a single field called \"Name\".",
        "de": "Die Datenbank beginnt mit einem einzigen Feld namens „Name“.",
    },
    "datenbank_anlegen_knopf": {"en": "Create database", "de": "Datenbank anlegen"},

    # --- Dialog: neues Feld -------------------------------------------------
    "feld_hinzufuegen_titel": {"en": "Add field", "de": "Feld hinzufügen"},
    "feld_hinzufuegen_erklaerung": {
        "en": "The new field then appears in the table and in every record\n"
              "of \"%s\". Existing data is kept.",
        "de": "Das neue Feld erscheint danach in der Tabelle und in jedem\n"
              "Datensatz von „%s“. Vorhandene Daten bleiben erhalten.",
    },
    "name_des_feldes": {"en": "Name of the field", "de": "Name des Feldes"},
    "art_des_feldes": {"en": "Type of field", "de": "Art des Feldes"},
    "moegliche_werte": {"en": "Possible values (one per line)",
                        "de": "Mögliche Werte (einer pro Zeile)"},

    # Die Feldarten, wie sie in der Auswahlliste stehen
    "typ_text": {"en": "Text", "de": "Text"},
    "typ_zahl": {"en": "Number", "de": "Zahl"},
    "typ_janein": {"en": "Yes/No", "de": "Ja/Nein"},
    "typ_datum": {"en": "Date", "de": "Datum"},
    "typ_auswahl": {"en": "Choice", "de": "Auswahl"},
    "typ_langtext": {"en": "Long text", "de": "Langer Text"},

    "erklaerung_text": {
        "en": "A single line of text, for example a name or a city.",
        "de": "Eine einzelne Zeile Text, zum Beispiel ein Name oder eine Stadt.",
    },
    "erklaerung_zahl": {
        "en": "Numbers only, for example a price or a quantity.",
        "de": "Nur Zahlen, zum Beispiel ein Preis oder eine Menge.",
    },
    "erklaerung_janein": {
        "en": "A checkbox to tick on and off.",
        "de": "Ein Kästchen zum An- und Abhaken.",
    },
    "erklaerung_datum": {
        "en": "A date in the form YYYY-MM-DD, for example 2026-08-11.",
        "de": "Ein Datum in der Form JJJJ-MM-TT, zum Beispiel 2026-08-11.",
    },
    "erklaerung_auswahl": {
        "en": "Fixed options to choose from.",
        "de": "Feste Möglichkeiten zum Auswählen.",
    },
    "erklaerung_langtext": {
        "en": "Several lines of text, for example a description.",
        "de": "Mehrere Zeilen Text, zum Beispiel eine Beschreibung.",
    },

    # --- Import und Export --------------------------------------------------
    "nichts_zu_speichern": {"en": "Nothing to save", "de": "Nichts zu speichern"},
    "datenbank_ohne_felder": {"en": "This database has no fields yet.",
                              "de": "Diese Datenbank hat noch keine Felder."},
    "datei_speichern_titel": {"en": "Save records", "de": "Datensätze speichern"},
    "datei_waehlen_titel": {"en": "Choose a file to import",
                            "de": "Datei zum Einlesen wählen"},
    "csv_datei": {"en": "CSV file", "de": "CSV-Datei"},
    "textdatei": {"en": "Text file", "de": "Textdatei"},
    "alle_dateien": {"en": "All files", "de": "Alle Dateien"},

    "datei_nicht_lesbar": {"en": "File not readable", "de": "Datei nicht lesbar"},
    "datei_konnte_nicht_gelesen_werden": {"en": "The file could not be read.",
                                          "de": "Die Datei konnte nicht gelesen werden."},
    "datei_ist_leer": {"en": "The file is empty.", "de": "Die Datei ist leer."},
    "datei_ohne_zeilen": {"en": "The file contains no rows.",
                          "de": "Die Datei enthält keine Zeilen."},
    "datei_csv_fehler": {
        "en": "The CSV file is malformed. Check its quotes and separators.",
        "de": "Die CSV-Datei ist fehlerhaft. Bitte prüfe Anführungszeichen und Trennzeichen.",
    },
    "csv_doppelte_ueberschriften": {
        "en": "The file contains a duplicate column heading: \"%s\".\n"
              "Please make every heading unique and try again.",
        "de": "Die Datei enthält eine doppelte Spaltenüberschrift: „%s“.\n"
              "Bitte mache alle Überschriften eindeutig und versuche es erneut.",
    },
    "csv_feld_uneindeutig": {
        "en": "More than one database field matches the CSV heading \"%s\". Rename the fields before importing.",
        "de": "Mehrere Datenbankfelder passen zur CSV-Überschrift „%s“. Bitte benenne die Felder vor dem Import um.",
    },
    "csv_leere_ueberschrift": {
        "en": "Column %d contains data but has no heading.\n"
              "Please name the column and try again.",
        "de": "Spalte %d enthält Daten, aber keine Überschrift.\n"
              "Bitte gib der Spalte einen Namen und versuche es erneut.",
    },
    "csv_zeilenbreite": {
        "en": "Row %d has %d cells, but the heading row has %d columns.\n"
              "No data was imported. Please correct the file and try again.",
        "de": "Zeile %d hat %d Zellen, die Kopfzeile aber %d Spalten.\n"
              "Es wurden keine Daten importiert. Bitte korrigiere die Datei und versuche es erneut.",
    },
    "nichts_gefunden": {"en": "Nothing found", "de": "Nichts gefunden"},
    "datei_ohne_datensaetze": {"en": "The file contains no records.",
                               "de": "Die Datei enthält keine Datensätze."},
    "keine_spalten_erkannt": {"en": "No columns detected",
                              "de": "Keine Spalten erkannt"},
    "erste_zeile_ohne_ueberschriften": {
        "en": "The first row of the file has no headings.",
        "de": "Die erste Zeile der Datei enthält keine Überschriften.",
    },
    "nichts_importiert": {"en": "Nothing imported", "de": "Nichts importiert"},
    "keine_spalte_passt": {
        "en": "No column in the file matches a field of this database.",
        "de": "Keine Spalte der Datei passt zu einem Feld dieser Datenbank.",
    },
    "import_schema_geaendert": {
        "en": "The database fields changed while the import was open. Please start the import again.",
        "de": "Die Datenbankfelder wurden während des Imports geändert. Bitte starte den Import erneut.",
    },

    "import_titel": {"en": "Import data", "de": "Daten einlesen"},
    "import_erklaerung": {
        "en": "From the file \"%s\"\ninto the database \"%s\".",
        "de": "Aus der Datei „%s“\nin die Datenbank „%s“.",
    },
    "werden_angehaengt": {"en": "%d records will be appended.",
                          "de": "%d Datensätze werden angehängt."},
    "bestehende_bleiben": {"en": "Existing records stay untouched.",
                           "de": "Vorhandene Datensätze bleiben unberührt."},
    "diese_spalten_kommen": {"en": "These columns will be imported",
                             "de": "Diese Spalten werden übernommen"},
    "diese_spalten_fehlen": {"en": "These columns do not exist yet",
                             "de": "Diese Spalten gibt es noch nicht"},
    "als_textfelder_anlegen": {"en": "Create them as new text fields",
                               "de": "Als neue Textfelder anlegen"},

    # --- Meldungen aus der Datenbank ----------------------------------------
    "feldname_fehlt": {"en": "Please enter a name for the field.",
                       "de": "Bitte gib dem Feld einen Namen."},
    "feldname_zu_lang": {"en": "The field name may be at most 40 characters long.",
                         "de": "Der Feldname darf höchstens 40 Zeichen lang sein."},
    "feldname_vergeben": {"en": "A field named \"%s\" already exists.",
                          "de": "Ein Feld namens „%s“ gibt es schon."},
    "datenbankname_fehlt": {"en": "Please enter a name for the database.",
                            "de": "Bitte gib der Datenbank einen Namen."},
    "datenbankname_zu_lang": {"en": "The name may be at most 40 characters long.",
                              "de": "Der Name darf höchstens 40 Zeichen lang sein."},
    "datenbankname_vergeben": {"en": "A database named \"%s\" already exists.",
                               "de": "Eine Datenbank namens „%s“ gibt es schon."},
    "unbekannte_feldart": {"en": "Unknown field type: %s",
                           "de": "Unbekannte Feldart: %s"},
    "datenbank_braucht_feld": {"en": "A database needs at least one field.",
                               "de": "Eine Datenbank braucht mindestens ein Feld."},
    "auswahl_braucht_werte": {
        "en": "A choice field needs at least two options\n(one per line).",
        "de": "Ein Auswahlfeld braucht mindestens zwei Möglichkeiten\n(eine pro Zeile).",
    },
    "datenbank_gibt_es_nicht": {"en": "This database no longer exists.",
                                "de": "Diese Datenbank gibt es nicht mehr."},
    "feld_gibt_es_nicht": {"en": "This field no longer exists.",
                           "de": "Dieses Feld gibt es nicht mehr."},
    "letztes_feld": {
        "en": "A database needs at least one field.\n"
              "This is the last one, so it cannot be removed.",
        "de": "Eine Datenbank braucht mindestens ein Feld.\n"
              "Dies ist das letzte, es lässt sich nicht entfernen.",
    },
    "keine_zahl": {"en": "\"%s\" is not a valid number.",
                   "de": "„%s“ ist keine gültige Zahl."},
    "keine_auswahl": {
        "en": "\"%s\" is not one of this field's possible values.",
        "de": "„%s“ ist keine der möglichen Antworten für dieses Feld.",
    },
    "kein_datum": {
        "en": "\"%s\" is not a valid date.\n"
              "Please use the form YYYY-MM-DD, for example 2026-08-11.",
        "de": "„%s“ ist kein gültiges Datum.\n"
              "Bitte in der Form JJJJ-MM-TT, zum Beispiel 2026-08-11.",
    },
    "nichts_eingegeben": {"en": "Nothing was entered.", "de": "Es wurde nichts eingegeben."},

    # --- Einstellungen ------------------------------------------------------
    "einstellungen_titel": {"en": "Settings", "de": "Einstellungen"},
    "einstellungen_untertitel": {
        "en": "Saved right away, and still in place the next time you start.",
        "de": "Wird sofort gespeichert und gilt auch beim nächsten Start.",
    },

    "abschnitt_aussehen": {"en": "APPEARANCE", "de": "AUSSEHEN"},
    "farbschema": {"en": "Colour scheme", "de": "Farben"},
    "farbe_hell": {"en": "Light", "de": "Hell"},
    "farbe_dunkel": {"en": "Dark", "de": "Dunkel"},
    "textgroesse": {"en": "Text size", "de": "Schriftgröße"},
    "groesse_klein": {"en": "Small", "de": "Klein"},
    "groesse_normal": {"en": "Normal", "de": "Normal"},
    "groesse_gross": {"en": "Large", "de": "Groß"},

    "abschnitt_sprache": {"en": "LANGUAGE", "de": "SPRACHE"},
    "sprache_der_oberflaeche": {"en": "Language of the interface",
                                "de": "Sprache der Oberfläche"},
    "sprache_hinweis": {
        "en": "Your data keeps the names you gave it.",
        "de": "Deine Daten behalten die Namen, die du vergeben hast.",
    },

    "abschnitt_tabelle": {"en": "TABLE", "de": "TABELLE"},
    "datensaetze_pro_seite": {"en": "Records per page", "de": "Datensätze pro Seite"},
    "nur_eine_seite": {
        "en": "Only one page is ever loaded - that is what keeps it fast.",
        "de": "Es wird immer nur eine Seite geladen - das hält es schnell.",
    },
    "zeilen_schattieren": {"en": "Shade every second row",
                           "de": "Jede zweite Zeile absetzen"},

    "abschnitt_loeschen": {"en": "DELETING", "de": "LÖSCHEN"},
    "datensaetze": {"en": "Records", "de": "Datensätze"},
    "felder_immer_nachfragen": {
        "en": "Fields and whole databases are always confirmed first.",
        "de": "Bei Feldern und ganzen Datenbanken wird immer nachgefragt.",
    },
    "vor_loeschen_fragen": {"en": "Ask before deleting a record",
                            "de": "Vor dem Löschen eines Datensatzes fragen"},

    "abschnitt_start": {"en": "AT START", "de": "BEIM START"},
    "welche_datenbank": {"en": "Which database opens", "de": "Welche Datenbank aufgeht"},
    "sonst_die_erste": {"en": "Otherwise the first one in the sidebar is opened.",
                        "de": "Sonst wird die erste in der Seitenleiste geöffnet."},
    "zuletzt_benutzte_oeffnen": {"en": "Open the one used last",
                                 "de": "Die zuletzt benutzte öffnen"},

    "abschnitt_daten": {"en": "DATA", "de": "DATEN"},
    "datenbankdatei": {"en": "Database file", "de": "Datenbankdatei"},
    "eine_datenbank": {"en": "1 database", "de": "1 Datenbank"},
    "n_datenbanken": {"en": "%d databases", "de": "%d Datenbanken"},
    "bestand_ein_datensatz": {"en": "%s with 1 record in total",
                              "de": "%s mit insgesamt 1 Datensatz"},
    "bestand_datensaetze": {"en": "%s with %d records in total",
                            "de": "%s mit insgesamt %d Datensätzen"},
    "standard_wiederherstellen": {"en": "Restore default settings",
                                  "de": "Ursprüngliche Einstellungen"},

    # --- Umbenennen ---------------------------------------------------------
    "umbenennen": {"en": "Rename", "de": "Umbenennen"},
    "neuer_name": {"en": "New name", "de": "Neuer Name"},
    "datenbank_umbenennen_knopf": {"en": "Rename this database",
                                   "de": "Diese Datenbank umbenennen"},
    "datenbank_umbenennen_titel": {"en": "Rename database", "de": "Datenbank umbenennen"},
    "datenbank_umbenennen_erklaerung": {
        "en": "Only the name in the sidebar changes.\nRecords and fields stay exactly as they are.",
        "de": "Es ändert sich nur der Name in der Seitenleiste.\n"
              "Datensätze und Felder bleiben unverändert.",
    },
    "feld_umbenennen_titel": {"en": "Rename field", "de": "Feld umbenennen"},
    "feld_umbenennen_erklaerung": {
        "en": "Only the heading changes.\nEvery value in the field is kept.",
        "de": "Es ändert sich nur die Überschrift.\nAlle Werte im Feld bleiben erhalten.",
    },
    "kontext_feld_umbenennen": {"en": "Rename field \"%s\"", "de": "Feld „%s“ umbenennen"},

    # --- Filter ---------------------------------------------------------------
    "filter_gekuerzt": {"en": "first %d of %d", "de": "erste %d von %d"},

    # --- Sichern und Aufräumen ------------------------------------------------
    "sicherung_knopf": {"en": "Save a copy…", "de": "Kopie speichern …"},
    "sicherung_titel": {"en": "Save a copy of the database",
                        "de": "Kopie der Datenbank speichern"},
    "sicherung_datei": {"en": "Database file", "de": "Datenbankdatei"},
    "sicherung_fertig_titel": {"en": "Copy saved", "de": "Kopie gespeichert"},
    "sicherung_geht_nicht": {"en": "Copy not saved", "de": "Kopie nicht gespeichert"},
    "sicherung_auf_sich_selbst": {
        "en": "That is the database this program is working with.\n\n"
              "Please choose a different name for the copy.",
        "de": "Das ist die Datenbank, mit der dieses Programm gerade arbeitet.\n\n"
              "Bitte wähle einen anderen Namen für die Kopie.",
    },
    "sicherung_fertig": {
        "en": "Everything was written to:\n%s\n\n"
              "The copy holds all databases, records and settings.",
        "de": "Alles wurde geschrieben nach:\n%s\n\n"
              "Die Kopie enthält alle Datenbanken, Datensätze und Einstellungen.",
    },
    "aufraeumen_knopf": {"en": "Compact the file", "de": "Datei aufräumen"},
    "aufraeumen_titel": {"en": "File compacted", "de": "Datei aufgeräumt"},
    "aufraeumen_fertig": {
        "en": "The file went from %s to %s.",
        "de": "Die Datei ist von %s auf %s geschrumpft.",
    },
    "aufraeumen_nichts": {"en": "There was nothing left to free up.",
                          "de": "Es gab nichts freizugeben."},
    "megabyte": {"en": "%s MB", "de": "%s MB"},
    "kilobyte": {"en": "%d KB", "de": "%d KB"},
}
