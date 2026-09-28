"""
dialoge.py
----------
Die beiden Fenster, mit denen der Nutzer die Struktur ändert:

  neue_datenbank(...)  legt eine neue Datenbank an
  neues_feld(...)      fügt einer Datenbank ein Feld hinzu

Beide Fenster prüfen nichts selbst. Sie geben die Eingabe an datenbank.py
weiter und zeigen die Meldung an, falls dort etwas beanstandet wird.
So gibt es nur eine Stelle, an der die Regeln stehen.
"""

import tkinter as tk
from tkinter import ttk

import datenbank
import design
import sprache


def dialog_oeffnen(eltern, titel):
    """
    Erzeugt ein kleines Fenster über dem Hauptfenster.

    Die Größe wird nicht fest vorgegeben, sondern von tkinter aus dem Inhalt
    berechnet (siehe dialog_zeigen). Dadurch passt der Dialog auch dann, wenn
    die Systemschrift größer ist - zum Beispiel unter Windows.
    """
    dialog = tk.Toplevel(eltern)
    dialog.title(titel)
    dialog.configure(background=design.FLAECHE)
    dialog.resizable(False, False)
    dialog.transient(eltern)
    # Erst einmal verstecken, damit man den Aufbau nicht flackern sieht.
    dialog.withdraw()
    return dialog


def dialog_zeigen(dialog, eltern):
    """
    Zeigt den fertig aufgebauten Dialog mittig über dem Hauptfenster.

    "Modal" bedeutet: Solange er offen ist, kann man das Hauptfenster nicht
    bedienen. Das verhindert, dass zwei Dinge gleichzeitig geändert werden.
    """
    dialog.update_idletasks()
    breite = dialog.winfo_reqwidth()
    hoehe = dialog.winfo_reqheight()

    x = eltern.winfo_rootx() + (eltern.winfo_width() - breite) // 2
    y = eltern.winfo_rooty() + (eltern.winfo_height() - hoehe) // 3
    dialog.geometry("%dx%d+%d+%d" % (breite, hoehe, max(x, 0), max(y, 0)))

    dialog.deiconify()
    dialog.grab_set()


def kopfzeile(dialog, titel, erklaerung):
    """Überschrift und ein erklärender Satz am oberen Rand des Dialogs."""
    rahmen = tk.Frame(dialog, background=design.FLAECHE)
    rahmen.pack(fill="x", padx=24, pady=(20, 0))

    tk.Label(rahmen, text=titel, font=design.SCHRIFT_UEBERSCHRIFT,
             background=design.FLAECHE, foreground=design.TEXT).pack(anchor="w")
    tk.Label(rahmen, text=erklaerung, font=design.SCHRIFT_KLEIN, justify="left",
             background=design.FLAECHE, foreground=design.TEXT_LEISE).pack(anchor="w", pady=(4, 0))
    return rahmen


def beschriftung(eltern, text):
    """Kleine Beschriftung über einem Eingabefeld."""
    return tk.Label(eltern, text=text, font=design.SCHRIFT_KLEIN,
                    background=design.FLAECHE, foreground=design.TEXT_LEISE)


# ---------------------------------------------------------------------------
# Neue Datenbank
# ---------------------------------------------------------------------------

def neue_datenbank(eltern):
    """
    Fragt nach einem Namen und legt die Datenbank an.
    Gibt die Nummer der neuen Datenbank zurück oder None bei Abbruch.
    """
    ergebnis = {"id": None}

    dialog = dialog_oeffnen(eltern, sprache.text("neue_datenbank_titel"))
    kopfzeile(dialog, sprache.text("neue_datenbank_titel"),
              sprache.text("neue_datenbank_erklaerung"))

    inhalt = tk.Frame(dialog, background=design.FLAECHE)
    inhalt.pack(fill="both", expand=True, padx=24, pady=(18, 0))

    beschriftung(inhalt, sprache.text("name_der_datenbank")).pack(anchor="w")
    eingabe = ttk.Entry(inhalt, font=design.SCHRIFT, width=34)
    eingabe.pack(fill="x", pady=(4, 0))
    eingabe.focus()

    tk.Label(inhalt,
             text=sprache.text("datenbank_startfeld"),
             font=design.SCHRIFT_KLEIN, background=design.FLAECHE,
             foreground=design.TEXT_LEISE).pack(anchor="w", pady=(8, 0))

    hinweis = tk.Label(inhalt, text="", font=design.SCHRIFT_KLEIN, justify="left",
                       background=design.FLAECHE, foreground=design.GEFAHR, wraplength=400)
    hinweis.pack(anchor="w", pady=(10, 0))

    def anlegen():
        try:
            # Die Prüfung passiert in datenbank.py - hier wird nur angezeigt.
            ergebnis["id"] = datenbank.datenbank_anlegen(
                eingabe.get(), [("Name", "text", None)]
            )
        except ValueError as fehler:
            hinweis.config(text=str(fehler))
            return
        dialog.destroy()

    knopfleiste(dialog, sprache.text("datenbank_anlegen_knopf"), anlegen)

    dialog.bind("<Return>", lambda ereignis: anlegen())
    dialog.bind("<Escape>", lambda ereignis: dialog.destroy())

    dialog_zeigen(dialog, eltern)
    eltern.wait_window(dialog)
    return ergebnis["id"]


# ---------------------------------------------------------------------------
# Neues Feld
# ---------------------------------------------------------------------------

def neues_feld(eltern, datenbank_id, datenbank_name):
    """
    Fragt Name und Typ eines neuen Feldes ab und legt es an.
    Gibt True zurück, wenn ein Feld angelegt wurde.
    """
    ergebnis = {"angelegt": False}

    dialog = dialog_oeffnen(eltern, sprache.text("feld_hinzufuegen_titel"))
    kopfzeile(dialog, sprache.text("feld_hinzufuegen_titel"),
              sprache.text("feld_hinzufuegen_erklaerung") % datenbank_name)

    inhalt = tk.Frame(dialog, background=design.FLAECHE)
    inhalt.pack(fill="both", expand=True, padx=24, pady=(18, 0))

    beschriftung(inhalt, sprache.text("name_des_feldes")).pack(anchor="w")
    eingabe_name = ttk.Entry(inhalt, font=design.SCHRIFT, width=34)
    eingabe_name.pack(fill="x", pady=(4, 14))
    eingabe_name.focus()

    beschriftung(inhalt, sprache.text("art_des_feldes")).pack(anchor="w")

    # Für die Auswahlliste brauchen wir die Texte, die der Nutzer sieht.
    typ_texte = []
    for schluessel in datenbank.FELDTYPEN:
        typ_texte.append(datenbank.typ_anzeigename(schluessel))

    auswahl_typ = ttk.Combobox(inhalt, values=typ_texte, state="readonly", font=design.SCHRIFT)
    auswahl_typ.set(datenbank.typ_anzeigename("text"))
    auswahl_typ.pack(fill="x", pady=(4, 6))

    erklaerung_typ = tk.Label(inhalt, text="", font=design.SCHRIFT_KLEIN, justify="left",
                              background=design.FLAECHE, foreground=design.TEXT_LEISE)
    erklaerung_typ.pack(anchor="w")

    # Bereich für die Möglichkeiten eines Auswahlfeldes.
    # Er wird nur angezeigt, wenn "Auswahl" gewählt ist.
    bereich_optionen = tk.Frame(inhalt, background=design.FLAECHE)
    beschriftung(bereich_optionen,
                 sprache.text("moegliche_werte")).pack(anchor="w", pady=(12, 4))
    eingabe_optionen = design.textfeld(bereich_optionen, hoehe=4)
    eingabe_optionen.pack(fill="x")

    def gewaehlter_typ():
        """Findet zum angezeigten Text den internen Namen des Feldtyps."""
        angezeigt = auswahl_typ.get()
        for schluessel in datenbank.FELDTYPEN:
            if datenbank.typ_anzeigename(schluessel) == angezeigt:
                return schluessel
        return "text"

    def typ_gewechselt(ereignis=None):
        typ = gewaehlter_typ()
        erklaerung_typ.config(text=sprache.text("erklaerung_" + typ))
        if typ == "auswahl":
            bereich_optionen.pack(fill="x", anchor="w")
        else:
            bereich_optionen.pack_forget()
        # Der Dialog wird höher oder niedriger - die Größe neu berechnen lassen.
        dialog.geometry("")

    auswahl_typ.bind("<<ComboboxSelected>>", typ_gewechselt)
    typ_gewechselt()

    hinweis = tk.Label(inhalt, text="", font=design.SCHRIFT_KLEIN, justify="left",
                       background=design.FLAECHE, foreground=design.GEFAHR, wraplength=420)
    hinweis.pack(anchor="w", pady=(12, 0))

    def anlegen():
        typ = gewaehlter_typ()
        optionen = eingabe_optionen.get("1.0", "end")
        try:
            datenbank.feld_hinzufuegen(datenbank_id, eingabe_name.get(), typ, optionen)
        except ValueError as fehler:
            hinweis.config(text=str(fehler))
            return
        ergebnis["angelegt"] = True
        dialog.destroy()

    knopfleiste(dialog, sprache.text("feld_hinzufuegen_titel"), anlegen)

    dialog.bind("<Escape>", lambda ereignis: dialog.destroy())

    dialog_zeigen(dialog, eltern)
    eltern.wait_window(dialog)
    return ergebnis["angelegt"]


# ---------------------------------------------------------------------------
# Umbenennen
# ---------------------------------------------------------------------------

def umbenennen(eltern, titel, erklaerung, alter_name, speichern):
    """
    Fragt nach einem neuen Namen. Für Datenbanken und für Felder derselbe
    Dialog - was danach passiert, steckt in der übergebenen Funktion.

    speichern  bekommt den eingetippten Namen und löst bei einem Problem
               einen ValueError aus. Der wird hier angezeigt, statt den
               Dialog zu schließen.

    Gibt True zurück, wenn umbenannt wurde.
    """
    ergebnis = {"geaendert": False}

    dialog = dialog_oeffnen(eltern, titel)
    kopfzeile(dialog, titel, erklaerung)

    inhalt = tk.Frame(dialog, background=design.FLAECHE)
    inhalt.pack(fill="both", expand=True, padx=24, pady=(18, 0))

    beschriftung(inhalt, sprache.text("neuer_name")).pack(anchor="w")
    eingabe = ttk.Entry(inhalt, font=design.SCHRIFT, width=34)
    eingabe.pack(fill="x", pady=(4, 0))
    eingabe.insert(0, alter_name)
    # Der alte Name steht schon drin und ist ausgewählt: Tippen ersetzt ihn,
    # eine kleine Änderung am Ende ist aber genauso möglich.
    eingabe.select_range(0, tk.END)
    eingabe.focus()

    hinweis = tk.Label(inhalt, text="", font=design.SCHRIFT_KLEIN, justify="left",
                       background=design.FLAECHE, foreground=design.GEFAHR, wraplength=400)
    hinweis.pack(anchor="w", pady=(10, 0))

    def uebernehmen():
        try:
            speichern(eingabe.get())
        except ValueError as fehler:
            hinweis.config(text=str(fehler))
            return
        ergebnis["geaendert"] = True
        dialog.destroy()

    knopfleiste(dialog, sprache.text("umbenennen"), uebernehmen)

    dialog.bind("<Return>", lambda ereignis: uebernehmen())
    dialog.bind("<Escape>", lambda ereignis: dialog.destroy())

    dialog_zeigen(dialog, eltern)
    eltern.wait_window(dialog)
    return ergebnis["geaendert"]


# ---------------------------------------------------------------------------
# Feldart ändern
# ---------------------------------------------------------------------------

def feld_art_aendern(eltern, feld, zaehlen, speichern):
    """
    Fragt nach einer neuen Art für ein Feld und zeigt vorher an, wie viele
    Werte die Umstellung nicht überstehen.

    zaehlen(neue_art)              gibt (gefuellt, verloren) zurück
    speichern(neue_art, optionen)  übernimmt die Änderung

    Gibt True zurück, wenn umgestellt wurde.
    """
    ergebnis = {"geaendert": False}

    dialog = dialog_oeffnen(eltern, sprache.text("art_aendern_titel"))
    kopfzeile(dialog, sprache.text("art_aendern_titel"),
              sprache.text("art_aendern_erklaerung")
              % (feld["anzeigename"], datenbank.typ_anzeigename(feld["typ"])))

    inhalt = tk.Frame(dialog, background=design.FLAECHE)
    inhalt.pack(fill="both", expand=True, padx=24, pady=(18, 0))

    beschriftung(inhalt, sprache.text("neue_art")).pack(anchor="w")

    typ_texte = []
    for schluessel in datenbank.FELDTYPEN:
        typ_texte.append(datenbank.typ_anzeigename(schluessel))

    auswahl_typ = ttk.Combobox(inhalt, values=typ_texte, state="readonly", font=design.SCHRIFT)
    auswahl_typ.set(datenbank.typ_anzeigename(feld["typ"]))
    auswahl_typ.pack(fill="x", pady=(4, 6))

    folgen = tk.Label(inhalt, text="", font=design.SCHRIFT_KLEIN, justify="left",
                      background=design.FLAECHE, foreground=design.TEXT_LEISE, wraplength=420)
    folgen.pack(anchor="w")

    # Die Möglichkeiten eines Auswahlfeldes - nur sichtbar, wenn nötig.
    bereich_optionen = tk.Frame(inhalt, background=design.FLAECHE)
    beschriftung(bereich_optionen,
                 sprache.text("moegliche_werte")).pack(anchor="w", pady=(12, 4))
    eingabe_optionen = design.textfeld(bereich_optionen, hoehe=4)
    eingabe_optionen.pack(fill="x")
    if feld["typ"] == "auswahl":
        eingabe_optionen.insert("1.0", "\n".join(datenbank.optionen_liste(feld)))

    def gewaehlte_art():
        """Findet zum angezeigten Text den internen Namen der Feldart."""
        angezeigt = auswahl_typ.get()
        for schluessel in datenbank.FELDTYPEN:
            if datenbank.typ_anzeigename(schluessel) == angezeigt:
                return schluessel
        return feld["typ"]

    def folgen_auffrischen():
        art = gewaehlte_art()
        if art == feld["typ"]:
            if art != "auswahl":
                folgen.config(text=sprache.text("art_unveraendert"))
                return

        optionen = eingabe_optionen.get("1.0", "end") if art == "auswahl" else None
        gefuellt, verloren = zaehlen(art, optionen)
        if gefuellt == 0:
            folgen.config(text=sprache.text("art_feld_leer"))
        elif verloren == 0:
            folgen.config(text=sprache.text("art_alle_bleiben") % gefuellt)
        else:
            folgen.config(text=sprache.text("art_werte_verloren") % (verloren, gefuellt))

    def art_gewechselt(ereignis=None):
        if gewaehlte_art() == "auswahl":
            bereich_optionen.pack(fill="x", anchor="w")
        else:
            bereich_optionen.pack_forget()

        folgen_auffrischen()

        # Der Dialog wird höher oder niedriger - die Größe neu berechnen lassen.
        dialog.geometry("")

    optionen_auftrag = {"id": None}

    def optionen_gewechselt(ereignis=None):
        if gewaehlte_art() == "auswahl":
            if optionen_auftrag["id"] is not None:
                dialog.after_cancel(optionen_auftrag["id"])

            def spaeter_auffrischen():
                optionen_auftrag["id"] = None
                folgen_auffrischen()

            optionen_auftrag["id"] = dialog.after(200, spaeter_auffrischen)

    auswahl_typ.bind("<<ComboboxSelected>>", art_gewechselt)
    for ereignis in ("<KeyRelease>", "<<Paste>>", "<<Cut>>"):
        eingabe_optionen.bind(ereignis, optionen_gewechselt, add="+")
    art_gewechselt()

    hinweis = tk.Label(inhalt, text="", font=design.SCHRIFT_KLEIN, justify="left",
                       background=design.FLAECHE, foreground=design.GEFAHR, wraplength=420)
    hinweis.pack(anchor="w", pady=(12, 0))

    def uebernehmen():
        try:
            speichern(gewaehlte_art(), eingabe_optionen.get("1.0", "end"))
        except ValueError as fehler:
            hinweis.config(text=str(fehler))
            return
        ergebnis["geaendert"] = True
        dialog.destroy()

    knopfleiste(dialog, sprache.text("art_aendern_knopf"), uebernehmen)
    dialog.bind("<Escape>", lambda ereignis: dialog.destroy())

    dialog_zeigen(dialog, eltern)
    eltern.wait_window(dialog)
    return ergebnis["geaendert"]


# ---------------------------------------------------------------------------
# Gemeinsame Knopfleiste am unteren Rand
# ---------------------------------------------------------------------------

def knopfleiste(dialog, text_hauptknopf, aktion):
    """Abbrechen links, die eigentliche Aktion rechts - in beiden Dialogen gleich."""
    leiste = tk.Frame(dialog, background=design.HINTERGRUND)
    leiste.pack(side="bottom", fill="x")
    design.trennlinie(leiste).pack(fill="x")

    inhalt = tk.Frame(leiste, background=design.HINTERGRUND)
    inhalt.pack(fill="x", padx=24, pady=14)

    ttk.Button(inhalt, text=text_hauptknopf, style="Akzent.TButton",
               command=aktion).pack(side="right")
    ttk.Button(inhalt, text=sprache.text("abbrechen"),
               command=dialog.destroy).pack(side="right", padx=(0, 8))
