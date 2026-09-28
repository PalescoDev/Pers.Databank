"""
einstellungen.py
----------------
Die Einstellungen des Programms: welche es gibt, wie sie gespeichert werden
und die Seite, auf der man sie ändert.

Gespeichert wird in daten.db - in einer kleinen Tabelle mit zwei Spalten
(Name der Einstellung, Wert). Geschrieben wird sie in datenbank.py, hier steht
nur, welche Einstellungen es gibt und was sie bedeuten.

Alle Werte sind Texte. Das klingt umständlich, macht das Speichern aber
denkbar einfach: Es gibt nur eine Art von Wert, und für Zahlen und Ja/Nein
stehen unten die drei kleinen Hilfsfunktionen zahl(), ja() und text().
"""

import datetime
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk

import datenbank
import design
import sprache

# Alle Einstellungen mit ihrem Wert, solange nichts anderes gespeichert ist.
# Steht ein Name hier nicht drin, wird er beim Laden nicht übernommen -
# so kann eine alte oder von Hand bearbeitete Datei nichts durcheinanderbringen.
STANDARD = {
    "sprache": "en",                     # "en" oder "de"
    "farbmodus": "hell",                 # "hell" oder "dunkel"
    "schriftgroesse": "0",               # -1 kleiner, 0 normal, 2 größer
    "datensaetze_pro_seite": "100",      # wie viele Zeilen eine Seite zeigt
    "zeilen_abwechselnd": "ja",          # jede zweite Zeile leicht abgesetzt
    "loeschen_nachfragen": "ja",         # vor dem Löschen eines Datensatzes fragen
    "letzte_datenbank_merken": "ja",     # beim Start die zuletzt benutzte öffnen
    "zuletzt_geoeffnet": "",             # deren Nummer (füllt das Programm selbst)
}

# Die Werte, die gerade gelten. Sie werden von laden() gefüllt.
WERTE = {}

# Die Auswahlfelder der Einstellungsseite brauchen je eine tkinter-Variable.
# Sie muss aufgehoben werden: Wirft Python sie weg, verliert das Bedienelement
# seinen Wert. Deshalb sammelt dieses Wörterbuch sie ein.
variablen = {}

# Ab dieser Breite werden erklärende Sätze umbrochen. Der Wert richtet sich
# nach der schmalsten Spalte, die im kleinsten erlaubten Fenster entsteht
# (940 Pixel breit, davon 220 für die Seitenleiste, der Rest halbiert).
TEXTBREITE = 250

# Die Zeile "3 databases with 42 records in total" auf der Seite.
# Sie wird jedes Mal aufgefrischt, wenn die Einstellungen aufgerufen werden.
bestand_label = None


# ---------------------------------------------------------------------------
# Laden, lesen, speichern
# ---------------------------------------------------------------------------

def laden():
    """
    Holt die gespeicherten Einstellungen aus der Datenbank.
    Alles, was dort fehlt, bekommt den Wert aus STANDARD.
    """
    global WERTE

    WERTE = {}
    for schluessel in STANDARD:
        WERTE[schluessel] = STANDARD[schluessel]

    gespeichert = datenbank.einstellungen_lesen()
    for schluessel in gespeichert:
        if schluessel in STANDARD:
            WERTE[schluessel] = gespeichert[schluessel]


def setzen(schluessel, wert):
    """Ändert eine Einstellung und schreibt sie sofort in die Datenbank."""
    WERTE[schluessel] = str(wert)
    datenbank.einstellung_speichern(schluessel, str(wert))


def text(schluessel):
    """Gibt eine Einstellung als Text zurück."""
    if schluessel in WERTE:
        return WERTE[schluessel]
    return STANDARD.get(schluessel, "")


def zahl(schluessel):
    """
    Gibt eine Einstellung als Zahl zurück.
    Steht dort keine Zahl (leeres Feld, von Hand bearbeitet), kommt 0 zurück.
    """
    try:
        return int(text(schluessel))
    except ValueError:
        return 0


def ja(schluessel):
    """Gibt eine Ja/Nein-Einstellung als True oder False zurück."""
    return text(schluessel) == "ja"


def zuruecksetzen():
    """Setzt alle Einstellungen auf ihren ursprünglichen Wert zurück."""
    for schluessel in STANDARD:
        # Welche Datenbank zuletzt offen war, ist keine Einstellung im
        # eigentlichen Sinn - die soll das Zurücksetzen nicht vergessen.
        if schluessel != "zuletzt_geoeffnet":
            setzen(schluessel, STANDARD[schluessel])


# ---------------------------------------------------------------------------
# Bausteine der Einstellungsseite
# ---------------------------------------------------------------------------

def abschnitt(eltern, ueberschrift):
    """Eine Überschrift und der Bereich darunter, in dem die Zeilen stehen."""
    tk.Label(eltern, text=ueberschrift, font=design.SCHRIFT_KLEIN, anchor="w",
             background=design.FLAECHE, foreground=design.TEXT_LEISE).pack(fill="x", pady=(0, 8))

    bereich = tk.Frame(eltern, background=design.FLAECHE)
    bereich.pack(fill="x", pady=(0, 18))
    return bereich


def beschriftung(eltern, titel, erklaerung=""):
    """Der Name einer Einstellung, darunter bei Bedarf ein erklärender Satz."""
    tk.Label(eltern, text=titel, font=design.SCHRIFT, anchor="w",
             background=design.FLAECHE, foreground=design.TEXT).pack(fill="x")
    if erklaerung != "":
        # wraplength ist die Breite, ab der umbrochen wird. Sie muss in die
        # schmalste Spalte passen, die im kleinsten erlaubten Fenster entsteht -
        # sonst steht Text über den Rand hinaus und ist nicht mehr zu lesen.
        tk.Label(eltern, text=erklaerung, font=design.SCHRIFT_KLEIN, anchor="w",
                 justify="left", wraplength=TEXTBREITE,
                 background=design.FLAECHE, foreground=design.TEXT_LEISE).pack(fill="x")


def auswahl_knoepfe(eltern, schluessel, moeglichkeiten, beim_aendern):
    """
    Eine Reihe von Auswahlknöpfen, von denen immer genau einer gilt.

    moeglichkeiten ist eine Liste aus (Wert, Beschriftung).
    """
    zustand = tk.StringVar(value=text(schluessel))
    variablen[schluessel] = zustand

    reihe = tk.Frame(eltern, background=design.FLAECHE)
    reihe.pack(fill="x", pady=(6, 0))

    def gewaehlt():
        setzen(schluessel, zustand.get())
        beim_aendern()

    for wert, aufschrift in moeglichkeiten:
        ttk.Radiobutton(reihe, text=aufschrift, value=wert, variable=zustand,
                        command=gewaehlt).pack(side="left", padx=(0, 18))


def ankreuzfeld(eltern, schluessel, aufschrift, beim_aendern):
    """Ein Kästchen zum Ein- und Ausschalten."""
    zustand = tk.BooleanVar(value=ja(schluessel))
    variablen[schluessel] = zustand

    def gewaehlt():
        if zustand.get():
            setzen(schluessel, "ja")
        else:
            setzen(schluessel, "nein")
        beim_aendern()

    ttk.Checkbutton(eltern, text=aufschrift, variable=zustand,
                    command=gewaehlt).pack(anchor="w", pady=(6, 0))


# ---------------------------------------------------------------------------
# Die Einstellungsseite
# ---------------------------------------------------------------------------

def seite_fuellen(rahmen, darstellung_geaendert, anzeige_geaendert):
    """
    Baut die Einstellungsseite in den übergebenen Rahmen.

    darstellung_geaendert  wird gerufen, wenn Farbe, Schriftgröße oder Sprache
                           wechseln. Dann muss das Fenster neu aufgebaut werden:
                           Bedienelemente merken sich Farbe und Aufschrift beim
                           Erzeugen, nachträglich ändert sich davon nichts mehr.
    anzeige_geaendert      wird gerufen, wenn die Tabelle neu geladen werden muss.

    Zurück kommt die Leinwand, in der die Seite sitzt - das Hauptfenster
    braucht sie, um das Mausrad darauf wirken zu lassen.
    """
    global bestand_label

    variablen.clear()

    # --- Rollbarer Bereich ------------------------------------------------
    # Die Seite kann höher werden als das Fenster - bei großer Schrift, in
    # einer wortreicheren Sprache oder wenn eine Einstellung dazukommt.
    # Eine Leinwand mit einem Rahmen darin ist der übliche Weg, in tkinter
    # etwas rollbar zu machen (genauso wie im Detailbereich).
    leinwand = tk.Canvas(rahmen, background=design.HINTERGRUND, highlightthickness=0)
    rollbalken = ttk.Scrollbar(rahmen, orient="vertical",
                               style="Modern.Vertical.TScrollbar", command=leinwand.yview)
    leinwand.configure(yscrollcommand=rollbalken.set)
    rollbalken.pack(side="right", fill="y")
    leinwand.pack(side="left", fill="both", expand=True)

    inhalt = tk.Frame(leinwand, background=design.HINTERGRUND)
    inhalt_fenster = leinwand.create_window((0, 0), window=inhalt, anchor="nw")

    # Diese beiden Funktionen müssen getrennt bleiben: Würde bei einer
    # Größenänderung des Inhalts auch die Breite neu gesetzt, löste das wieder
    # eine Größenänderung aus - beide riefen sich endlos gegenseitig auf.

    def inhalt_hat_sich_geaendert(ereignis=None):
        """Der Inhalt ist höher geworden: nur den Rollbereich anpassen."""
        leinwand.configure(scrollregion=leinwand.bbox("all"))

    def leinwand_wurde_breiter(ereignis=None):
        """Das Fenster wurde in der Breite verändert: Inhalt mitziehen."""
        leinwand.itemconfigure(inhalt_fenster, width=ereignis.width)

    inhalt.bind("<Configure>", inhalt_hat_sich_geaendert)
    leinwand.bind("<Configure>", leinwand_wurde_breiter)

    # --- Kopfzeile --------------------------------------------------------
    kopf = tk.Frame(inhalt, background=design.HINTERGRUND)
    kopf.pack(fill="x", padx=24, pady=(16, 10))

    tk.Label(kopf, text=sprache.text("einstellungen_titel"), font=design.SCHRIFT_TITEL,
             anchor="w",
             background=design.HINTERGRUND, foreground=design.TEXT).pack(anchor="w")
    tk.Label(kopf, text=sprache.text("einstellungen_untertitel"),
             font=design.SCHRIFT_KLEIN, anchor="w",
             background=design.HINTERGRUND, foreground=design.TEXT_LEISE).pack(anchor="w")

    # --- Karte mit den beiden Spalten ------------------------------------
    karte = tk.Frame(inhalt, background=design.RAHMEN)
    karte.pack(fill="x", padx=24, pady=(0, 24))

    innen = tk.Frame(karte, background=design.FLAECHE)
    innen.pack(fill="both", expand=True, padx=1, pady=1)

    # Die beiden Spalten werden hier ausnahmsweise mit grid angeordnet statt
    # mit pack. Grund: uniform sorgt dafür, dass beide immer gleich breit
    # sind. Mit pack bekäme die Spalte mit dem breiteren Inhalt mehr Platz -
    # in einem schmalen Fenster blieb für die andere so wenig übrig, dass
    # Beschriftungen abgeschnitten wurden.
    innen.columnconfigure(0, weight=1, uniform="spalten")
    innen.columnconfigure(2, weight=1, uniform="spalten")
    innen.rowconfigure(0, weight=1)

    links = tk.Frame(innen, background=design.FLAECHE)
    links.grid(row=0, column=0, sticky="nsew", padx=24, pady=16)

    design.senkrechte_linie(innen).grid(row=0, column=1, sticky="ns", pady=16)

    rechts = tk.Frame(innen, background=design.FLAECHE)
    rechts.grid(row=0, column=2, sticky="nsew", padx=24, pady=16)

    # --- Linke Spalte: Aussehen ------------------------------------------
    bereich = abschnitt(links, sprache.text("abschnitt_aussehen"))

    beschriftung(bereich, sprache.text("farbschema"))
    auswahl_knoepfe(bereich, "farbmodus",
                    [("hell", sprache.text("farbe_hell")),
                     ("dunkel", sprache.text("farbe_dunkel"))],
                    darstellung_geaendert)

    tk.Frame(bereich, background=design.FLAECHE, height=12).pack()

    beschriftung(bereich, sprache.text("textgroesse"))
    auswahl_knoepfe(bereich, "schriftgroesse",
                    [("-1", sprache.text("groesse_klein")),
                     ("0", sprache.text("groesse_normal")),
                     ("2", sprache.text("groesse_gross"))],
                    darstellung_geaendert)

    # --- Sprache ----------------------------------------------------------
    # Die beiden Namen stehen bewusst jeweils in ihrer eigenen Sprache und
    # werden nicht übersetzt - so findet sich auch jemand zurecht, der die
    # gerade eingestellte Sprache nicht versteht.
    bereich = abschnitt(links, sprache.text("abschnitt_sprache"))

    beschriftung(bereich, sprache.text("sprache_der_oberflaeche"),
                 sprache.text("sprache_hinweis"))
    auswahl_knoepfe(bereich, "sprache",
                    [("en", "English"), ("de", "Deutsch")],
                    darstellung_geaendert)

    bereich = abschnitt(rechts, sprache.text("abschnitt_tabelle"))

    beschriftung(bereich, sprache.text("datensaetze_pro_seite"),
                 sprache.text("nur_eine_seite"))

    zustand = tk.StringVar(value=text("datensaetze_pro_seite"))
    variablen["datensaetze_pro_seite"] = zustand

    def seitengroesse_gewechselt(ereignis=None):
        setzen("datensaetze_pro_seite", zustand.get())
        anzeige_geaendert()

    auswahl = ttk.Combobox(bereich, values=["25", "50", "100", "250", "500"],
                           textvariable=zustand, state="readonly",
                           font=design.SCHRIFT, width=8)
    auswahl.pack(anchor="w", pady=(6, 0))
    auswahl.bind("<<ComboboxSelected>>", seitengroesse_gewechselt)

    ankreuzfeld(bereich, "zeilen_abwechselnd", sprache.text("zeilen_schattieren"),
                anzeige_geaendert)

    # --- Rechte Spalte: Verhalten ----------------------------------------
    bereich = abschnitt(links, sprache.text("abschnitt_loeschen"))

    beschriftung(bereich, sprache.text("datensaetze"),
                 sprache.text("felder_immer_nachfragen"))
    ankreuzfeld(bereich, "loeschen_nachfragen", sprache.text("vor_loeschen_fragen"),
                nichts_tun)

    bereich = abschnitt(links, sprache.text("abschnitt_start"))

    beschriftung(bereich, sprache.text("welche_datenbank"),
                 sprache.text("sonst_die_erste"))
    ankreuzfeld(bereich, "letzte_datenbank_merken",
                sprache.text("zuletzt_benutzte_oeffnen"), nichts_tun)

    bereich = abschnitt(rechts, sprache.text("abschnitt_daten"))

    beschriftung(bereich, sprache.text("datenbankdatei"))
    tk.Label(bereich, text=datenbank.DATENBANK_DATEI, font=design.SCHRIFT_KLEIN,
             anchor="w", justify="left", wraplength=TEXTBREITE,
             background=design.FLAECHE, foreground=design.TEXT_LEISE).pack(fill="x")
    bestand_label = tk.Label(bereich, text=bestand_beschreiben(), font=design.SCHRIFT_KLEIN,
                             anchor="w", justify="left", wraplength=TEXTBREITE,
                             background=design.FLAECHE,
                             foreground=design.TEXT_LEISE)
    bestand_label.pack(fill="x", pady=(2, 0))

    hauptfenster = rahmen.winfo_toplevel()

    def sicherung_speichern():
        """Schreibt die ganze Datei ein zweites Mal - als Sicherheitskopie."""
        pfad = filedialog.asksaveasfilename(
            parent=hauptfenster,
            title=sprache.text("sicherung_titel"),
            defaultextension=".db",
            initialfile="Pers.Databank " + datetime.date.today().isoformat() + ".db",
            filetypes=[(sprache.text("sicherung_datei"), "*.db"),
                       (sprache.text("alle_dateien"), "*.*")]
        )
        if not pfad:
            return

        try:
            datenbank.sicherung_schreiben(pfad)
        except ValueError as fehler:
            # Der einzige Fall: Es wurde die Datei gewählt, mit der das
            # Programm gerade arbeitet.
            messagebox.showwarning(sprache.text("sicherung_geht_nicht"), str(fehler))
            return

        messagebox.showinfo(sprache.text("sicherung_fertig_titel"),
                            sprache.text("sicherung_fertig") % pfad)

    def datei_aufraeumen():
        """Gibt den Platz frei, den gelöschte Daten noch belegen."""
        vorher, nachher = datenbank.aufraeumen()
        bestand_auffrischen()

        if nachher >= vorher:
            messagebox.showinfo(sprache.text("aufraeumen_titel"),
                                sprache.text("aufraeumen_nichts"))
            return

        messagebox.showinfo(sprache.text("aufraeumen_titel"),
                            sprache.text("aufraeumen_fertig")
                            % (groesse_text(vorher), groesse_text(nachher)))

    def alles_zuruecksetzen():
        zuruecksetzen()
        darstellung_geaendert()

    knopfreihe = tk.Frame(bereich, background=design.FLAECHE)
    knopfreihe.pack(anchor="w", pady=(12, 0))
    ttk.Button(knopfreihe, text=sprache.text("sicherung_knopf"),
               command=sicherung_speichern).pack(side="left")
    ttk.Button(knopfreihe, text=sprache.text("aufraeumen_knopf"),
               command=datei_aufraeumen).pack(side="left", padx=(8, 0))

    ttk.Button(bereich, text=sprache.text("standard_wiederherstellen"),
               command=alles_zuruecksetzen).pack(anchor="w", pady=(8, 0))

    return leinwand


def nichts_tun():
    """
    Für Einstellungen, die sofort gelten, ohne dass etwas neu gezeichnet
    werden muss - der gespeicherte Wert wird beim nächsten Mal gelesen.
    """
    pass


def groesse_text(bytes_anzahl):
    """Eine Dateigröße als lesbarer Text: 345 KB oder 1,2 MB."""
    if bytes_anzahl >= 1000 * 1000:
        return sprache.text("megabyte") % sprache.kommazahl(bytes_anzahl / (1000.0 * 1000.0))
    return sprache.text("kilobyte") % round(bytes_anzahl / 1000.0)


def bestand_auffrischen():
    """
    Zählt die Datenbanken und Datensätze neu.
    Wird aufgerufen, wenn die Einstellungen aufgeschlagen werden - inzwischen
    können ja Datensätze dazugekommen oder weggefallen sein.
    """
    if bestand_label is not None:
        bestand_label.config(text=bestand_beschreiben())


def bestand_beschreiben():
    """Ein Satz darüber, wie viel gerade in der Datei steht."""
    datenbanken = datenbank.datenbanken_liste()

    gesamt = 0
    for eintrag in datenbanken:
        gesamt = gesamt + datenbank.anzahl_datensaetze(eintrag["id"])

    if len(datenbanken) == 1:
        anfang = sprache.text("eine_datenbank")
    else:
        anfang = sprache.text("n_datenbanken") % len(datenbanken)

    if gesamt == 1:
        return sprache.text("bestand_ein_datensatz") % anfang
    return sprache.text("bestand_datensaetze") % (anfang, gesamt)
