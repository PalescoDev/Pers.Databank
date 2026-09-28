"""Regression tests for import validation and database edge cases."""

import os
import sqlite3
import tempfile
import unittest
from unittest import mock

import austausch
import datenbank
import sprache


class DatabaseRegressionTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        datenbank.datenbank_schliessen()
        self.alter_pfad = datenbank.DATENBANK_DATEI
        datenbank.DATENBANK_DATEI = os.path.join(self.folder.name, "test.db")
        datenbank.datenbank_vorbereiten()
        self.datenbank_id = datenbank.datenbank_anlegen("Test", [
            ("Äpfel", "text", None),
            ("Status", "auswahl", "Neu\nErledigt"),
            ("Aktiv", "janein", None),
            ("Wert", "zahl", None),
        ])
        self.felder = datenbank.felder_liste(self.datenbank_id)

    def tearDown(self):
        datenbank.datenbank_schliessen()
        datenbank.DATENBANK_DATEI = self.alter_pfad
        self.folder.cleanup()

    def test_case_insensitive_field_name_and_unicode_database_name(self):
        with self.assertRaises(ValueError):
            datenbank.feld_hinzufuegen(self.datenbank_id, "äPFEL", "text")
        with self.assertRaises(ValueError):
            datenbank.datenbank_anlegen("tEST", [("Name", "text", None)])

    def test_unicode_names_are_compared_in_canonical_form(self):
        datenbank.feld_hinzufuegen(self.datenbank_id, "Café", "text")
        with self.assertRaises(ValueError):
            datenbank.feld_hinzufuegen(self.datenbank_id, "Cafe\u0301", "text")
        datenbank.datenbank_anlegen("Café", [("Name", "text", None)])
        with self.assertRaises(ValueError):
            datenbank.datenbank_anlegen("Cafe\u0301", [("Name", "text", None)])

    def test_nfd_csv_heading_updates_nfc_field(self):
        datenbank.feld_hinzufuegen(self.datenbank_id, "Café", "text")
        cafe = next(feld for feld in datenbank.felder_liste(self.datenbank_id)
                    if feld["anzeigename"] == "Café")
        datenbank.datensatz_hinzufuegen(self.datenbank_id, {cafe["id"]: "Ada"})
        felder = datenbank.felder_liste(self.datenbank_id)
        result = datenbank.csv_datensaetze_uebernehmen(
            self.datenbank_id, ["Cafe\u0301"], [["Ada"]], False, [],
            cafe["id"], felder)
        self.assertEqual(result, (0, 1))

    def test_ambiguous_legacy_unicode_fields_are_rejected(self):
        datenbank.feld_hinzufuegen(self.datenbank_id, "Café", "text")
        datenbank.feld_hinzufuegen(self.datenbank_id, "Sonstiges", "text")
        other = next(feld for feld in datenbank.felder_liste(self.datenbank_id)
                     if feld["anzeigename"] == "Sonstiges")
        with datenbank.verbindung_holen():
            datenbank.verbindung_holen().execute(
                "UPDATE felder SET anzeigename = ? WHERE id = ?",
                ("Cafe\u0301", other["id"]),
            )
        felder = datenbank.felder_liste(self.datenbank_id)
        with self.assertRaises(ValueError):
            datenbank.csv_datensaetze_uebernehmen(
                self.datenbank_id, ["Café"], [["Ada"]], False, [], None, felder)
        self.assertEqual(datenbank.anzahl_datensaetze(self.datenbank_id), 0)

    def test_non_finite_numbers_and_unknown_yes_no_values(self):
        for value in ("nan", "inf", "-inf", "1e999"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    datenbank.wert_aus_eingabe("zahl", value)
        self.assertIsNone(datenbank.wert_aus_text("janein", "maybe"))
        self.assertEqual(datenbank.wert_aus_text("janein", "Nein"), 0)
        self.assertEqual(datenbank.wert_aus_text("janein", "yes"), 1)
        self.assertEqual(datenbank.text_fuer_anzeige("zahl", float("inf")), "inf")

    def test_free_text_preserves_edge_spaces_and_blank_lines(self):
        text = "\n  Name with spaces  \n"
        self.assertEqual(datenbank.wert_aus_eingabe("text", text), text)
        self.assertEqual(datenbank.wert_aus_eingabe("langtext", text), text)
        self.assertEqual(datenbank.wert_aus_text("text", text.replace("\n", "\r\n")), text)
        self.assertEqual(datenbank.wert_aus_text("langtext", "  only spaces  "),
                         "  only spaces  ")
        self.assertIsNone(datenbank.wert_aus_eingabe("text", ""))

    def test_schema_check_allows_only_additions_when_requested(self):
        expected = list(self.felder)
        datenbank.feld_hinzufuegen(self.datenbank_id, "Extra", "text")
        datenbank.import_schema_pruefen(
            self.datenbank_id, expected, zusaetzliche_felder=True)
        feld_id = self.felder[0]["id"]
        original_name = self.felder[0]["anzeigename"]
        datenbank.feld_umbenennen(self.datenbank_id, feld_id, "Anderer Name")
        with self.assertRaises(ValueError):
            datenbank.import_schema_pruefen(
                self.datenbank_id, expected, zusaetzliche_felder=True)
        datenbank.feld_umbenennen(self.datenbank_id, feld_id, original_name)
        datenbank.feld_typ_aendern(self.datenbank_id, self.felder[0]["id"], "zahl")
        with self.assertRaises(ValueError):
            datenbank.import_schema_pruefen(
                self.datenbank_id, expected, zusaetzliche_felder=True)

    def test_invalid_import_field_name_does_not_leave_partial_schema(self):
        expected_names = [feld["anzeigename"] for feld in self.felder]
        with self.assertRaises(ValueError):
            datenbank.import_felder_anlegen(
                self.datenbank_id, ["Gültig", "x" * 41], self.felder)
        self.assertEqual(
            [feld["anzeigename"] for feld in datenbank.felder_liste(self.datenbank_id)],
            expected_names,
        )

    def test_duplicate_key_rolls_back_new_fields_and_rows_together(self):
        fields = list(self.felder)
        with self.assertRaises(ValueError):
            datenbank.csv_datensaetze_uebernehmen(
                self.datenbank_id,
                ["Äpfel", "Neue Notiz"],
                [["doppelt", "eins"], ["doppelt", "zwei"]],
                True,
                ["Neue Notiz"],
                fields[0]["id"],
                fields,
            )
        self.assertEqual(
            [feld["anzeigename"] for feld in datenbank.felder_liste(self.datenbank_id)],
            [feld["anzeigename"] for feld in fields],
        )
        self.assertEqual(datenbank.anzahl_datensaetze(self.datenbank_id), 0)

    def test_csv_import_creates_field_and_record_together(self):
        expected = list(self.felder)
        result = datenbank.csv_datensaetze_uebernehmen(
            self.datenbank_id,
            ["Äpfel", "Notiz"],
            [[" Ada ", "  behalten  "]],
            True,
            ["Notiz"],
            None,
            expected,
        )
        self.assertEqual(result, (1, 0))
        fields = datenbank.felder_liste(self.datenbank_id)
        note = next(feld for feld in fields if feld["anzeigename"] == "Notiz")
        record = datenbank.datensatz_holen(self.datenbank_id, 1)
        self.assertEqual(record[self.felder[0]["spalte"]], " Ada ")
        self.assertEqual(record[note["spalte"]], "  behalten  ")

    def test_invalid_csv_field_rolls_back_the_full_import(self):
        fields = list(self.felder)
        with self.assertRaises(ValueError):
            datenbank.csv_datensaetze_uebernehmen(
                self.datenbank_id,
                ["Äpfel", "Gültig", "x" * 41],
                [["Ada", "ok", "zu lang"]],
                True,
                ["Gültig", "x" * 41],
                None,
                fields,
            )
        self.assertEqual(
            [feld["anzeigename"] for feld in datenbank.felder_liste(self.datenbank_id)],
            [feld["anzeigename"] for feld in fields],
        )
        self.assertEqual(datenbank.anzahl_datensaetze(self.datenbank_id), 0)

    def test_choice_values_are_checked_for_manual_and_imported_data(self):
        status = self.felder[1]
        with self.assertRaises(ValueError):
            datenbank.wert_aus_eingabe("auswahl", "Unbekannt", status["optionen"])
        self.assertIsNone(datenbank.wert_aus_text("auswahl", "Unbekannt", status["optionen"]))
        self.assertEqual(datenbank.wert_aus_text("auswahl", "Neu", status["optionen"]), "Neu")

    def test_type_change_preview_counts_whitespace_as_lost_free_text(self):
        text_field = self.felder[0]
        record_id = datenbank.datensatz_hinzufuegen(
            self.datenbank_id, {text_field["id"]: "   "})
        self.assertEqual(
            datenbank.typ_umstellung_zaehlen(self.datenbank_id, text_field["id"], "zahl"),
            (1, 1),
        )
        datenbank.feld_typ_aendern(self.datenbank_id, text_field["id"], "zahl")
        updated_field = datenbank.feld_holen(self.datenbank_id, text_field["id"])
        record = datenbank.datensatz_holen(self.datenbank_id, record_id)
        self.assertIsNone(record[updated_field["spalte"]])

    def test_real_export_round_trips_through_the_csv_reader(self):
        werte = {
            self.felder[0]["id"]: "\n  Ada; Lovelace  \n",
            self.felder[1]["id"]: "Neu",
            self.felder[2]["id"]: 0,
            self.felder[3]["id"]: 3.5,
        }
        datenbank.datensatz_hinzufuegen(self.datenbank_id, werte)
        pfad = os.path.join(self.folder.name, "export.csv")

        self.assertEqual(austausch.datei_schreiben(pfad, self.datenbank_id), 1)
        ueberschriften, zeilen = austausch.datei_einlesen(pfad)
        self.assertEqual(ueberschriften, [feld["anzeigename"] for feld in self.felder])
        self.assertEqual(zeilen, [["\n  Ada; Lovelace  \n", "Neu", "No", "3.5"]])

    def test_choice_option_update_clears_values_that_are_removed(self):
        status = self.felder[1]
        datenbank.datensatz_hinzufuegen(self.datenbank_id, {status["id"]: "Neu"})
        datenbank.datensatz_hinzufuegen(self.datenbank_id, {status["id"]: "Erledigt"})
        self.assertEqual(
            datenbank.typ_umstellung_zaehlen(
                self.datenbank_id, status["id"], "auswahl", "Neu\nIn Arbeit"
            ),
            (2, 1),
        )

        datenbank.feld_typ_aendern(self.datenbank_id, status["id"], "auswahl", "Neu\nIn Arbeit")
        zeilen = datenbank.verbindung_holen().execute(
            'SELECT "' + status["spalte"] + '" FROM "'
            + datenbank.datenbank_holen(self.datenbank_id)["tabelle"] + '" ORDER BY id'
        ).fetchall()
        self.assertEqual([zeile[0] for zeile in zeilen], ["Neu", None])

    def test_duplicate_match_keys_are_rejected_before_any_write(self):
        name = self.felder[0]
        datenbank.datensatz_hinzufuegen(self.datenbank_id, {name["id"]: "eins"})
        with self.assertRaises(ValueError):
            datenbank.datensaetze_abgleichen(self.datenbank_id, [
                {name["id"]: "neu"}, {name["id"]: "neu"},
            ], name)
        self.assertEqual(datenbank.anzahl_datensaetze(self.datenbank_id), 1)

        datenbank.datensatz_hinzufuegen(self.datenbank_id, {name["id"]: "eins"})
        with self.assertRaises(ValueError):
            datenbank.datensaetze_abgleichen(self.datenbank_id, [{name["id"]: "neu"}], name)
        self.assertEqual(datenbank.anzahl_datensaetze(self.datenbank_id), 2)

    def test_import_aborts_if_field_schema_changed_after_mapping(self):
        erwartete_felder = list(self.felder)
        name, status = self.felder[0], self.felder[1]

        # The import dialog mapped a text field, then another app changed it.
        datenbank.feld_typ_aendern(self.datenbank_id, name["id"], "zahl")
        with self.assertRaises(ValueError):
            datenbank.datensaetze_abgleichen(
                self.datenbank_id, [{name["id"]: "keine Zahl"}], name,
                erwartete_felder=erwartete_felder)
        self.assertEqual(datenbank.anzahl_datensaetze(self.datenbank_id), 0)

        # The append path must make the same check under its write lock.
        datenbank.feld_typ_aendern(self.datenbank_id, status["id"], "text")
        with self.assertRaises(ValueError):
            datenbank.viele_datensaetze_hinzufuegen(
                self.datenbank_id, [{status["id"]: "Neu"}],
                erwartete_felder=erwartete_felder)
        self.assertEqual(datenbank.anzahl_datensaetze(self.datenbank_id), 0)

    def test_reconcile_rolls_back_all_rows_if_one_write_fails(self):
        name = self.felder[0]
        tabelle = datenbank.datenbank_holen(self.datenbank_id)["tabelle"]
        verbindung = datenbank.verbindung_holen()
        with verbindung:
            verbindung.execute(
                'CREATE TRIGGER test_import_fehler BEFORE INSERT ON "' + tabelle + '" '
                'WHEN NEW."' + name["spalte"] + '" = \'Fehler\' '
                'BEGIN SELECT RAISE(ABORT, \'Testfehler\'); END'
            )

        with self.assertRaises(sqlite3.IntegrityError):
            datenbank.datensaetze_abgleichen(self.datenbank_id, [
                {name["id"]: "Neu"}, {name["id"]: "Fehler"},
            ], name)
        self.assertEqual(datenbank.anzahl_datensaetze(self.datenbank_id), 0)

    def test_old_sqlite_column_rebuild_keeps_values_and_autoincrement_sequence(self):
        for nummer in range(3):
            datenbank.datensatz_hinzufuegen(self.datenbank_id, {
                self.felder[0]["id"]: "Eintrag " + str(nummer),
                self.felder[1]["id"]: "Neu",
            })
        tabelle = datenbank.datenbank_holen(self.datenbank_id)["tabelle"]
        verbindung = datenbank.verbindung_holen()
        with verbindung:
            verbindung.execute('DELETE FROM "' + tabelle + '" WHERE id = 3')

        with mock.patch.object(datenbank.sqlite3, "sqlite_version_info", (3, 34, 0)):
            datenbank.feld_loeschen(self.datenbank_id, self.felder[2]["id"])

        geblieben = datenbank.felder_liste(self.datenbank_id)
        self.assertEqual(len(geblieben), 3)
        datensatz_id = datenbank.datensatz_hinzufuegen(
            self.datenbank_id, {geblieben[0]["id"]: "Danach"}
        )
        self.assertEqual(datensatz_id, 4)
        werte = verbindung.execute(
            'SELECT "' + geblieben[0]["spalte"] + '" FROM "' + tabelle + '" ORDER BY id'
        ).fetchall()
        self.assertEqual([zeile[0] for zeile in werte], ["Eintrag 0", "Eintrag 1", "Danach"])


class CsvRegressionTests(unittest.TestCase):
    def lese_text(self, text):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False) as datei:
            datei.write(text)
            pfad = datei.name
        try:
            return austausch.datei_einlesen(pfad)
        finally:
            os.unlink(pfad)

    def test_delimiter_detection_ignores_quoted_separator_in_heading(self):
        headings, rows = self.lese_text('"Name; kurz";Ort\n"Ada; A.";Berlin\n')
        self.assertEqual(headings, ["Name; kurz", "Ort"])
        self.assertEqual(rows, [["Ada; A.", "Berlin"]])

    def test_duplicate_headings_are_rejected_case_insensitively(self):
        with self.assertRaises(ValueError):
            self.lese_text("Name;name\nAda;Lovelace\n")

    def test_duplicate_headings_are_rejected_across_unicode_forms(self):
        with self.assertRaises(ValueError):
            self.lese_text("Café;Cafe\u0301\neins;zwei\n")

    def test_ragged_rows_and_malformed_csv_are_rejected(self):
        with self.assertRaises(ValueError):
            self.lese_text("Name;Ort\nAda\n")
        with self.assertRaises(ValueError):
            self.lese_text('Name;Ort\nAda;"London\n')
        with self.assertRaises(ValueError):
            self.lese_text("Name;\nAda;London\n")

    def test_matching_key_can_have_the_same_name_as_the_no_match_option(self):
        name = sprache.text("abgleichen_keins")
        bekannt = [(name, {"id": 12, "anzeigename": name})]
        anzeigenamen = austausch.schluessel_optionen_erstellen(bekannt)
        self.assertNotEqual(anzeigenamen[0], anzeigenamen[1])
        self.assertEqual(austausch.schluessel_auswahl_aufloesen(0, bekannt), "")
        self.assertEqual(austausch.schluessel_auswahl_aufloesen(1, bekannt), name)


if __name__ == "__main__":
    unittest.main()
