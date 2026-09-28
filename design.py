"""
design.py
---------
Farben, Schriften und das Aussehen der Bedienelemente - alles an einer Stelle.

Wer die Optik ändern möchte, ändert nur diese Datei.

Es gibt zwei Farbsätze: einen hellen und einen dunklen. Welcher gilt, legt
farben_setzen() fest. Danach stehen die Farben unter denselben Namen bereit
(design.FLAECHE, design.TEXT, ...), sodass der Rest des Programms gar nicht
wissen muss, welcher Satz gerade gewählt ist.

Die Schrift wird nicht fest vorgegeben, sondern von der Standardschrift des
Systems abgeleitet. Dadurch sieht das Programm unter Windows und macOS jeweils
so aus, wie man es dort gewohnt ist.
"""

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

# --- Farben ---------------------------------------------------------------
# Beide Sätze haben genau dieselben Namen. Der helle ist zurückhaltend:
# viel Weiß, wenige Linien, ein Blau als Akzent. Der dunkle folgt demselben
# Aufbau, nur werden hell und dunkel getauscht - und das Blau wird etwas
# heller, weil ein dunkles Blau auf dunklem Grund kaum zu erkennen wäre.

HELLE_FARBEN = {
    "HINTERGRUND": "#f5f6f8",       # Fläche hinter allem
    "FLAECHE": "#ffffff",           # Tabelle, Formulare, Dialoge
    "SEITENLEISTE": "#f0f1f4",      # linke Spalte
    "RAHMEN": "#dcdfe4",            # dezente Trennlinien
    "RAHMEN_STARK": "#c3c7ce",      # Rahmen von Eingabefeldern

    "TEXT": "#1f2328",              # normale Schrift
    "TEXT_LEISE": "#6b7280",        # Beschriftungen, Hinweise
    "TEXT_HELL": "#ffffff",         # Schrift auf farbigem Grund
    "TEXT_AUS": "#a5a9b0",          # abgeschaltete Bedienelemente

    "AKZENT": "#2f6feb",            # Hauptaktionen
    "AKZENT_DUNKEL": "#2559c4",     # gedrückt
    "AKZENT_HELL": "#e8effd",       # ausgewählter Eintrag in der Seitenleiste

    "GEFAHR": "#c0392b",            # Löschen
    "GEFAHR_FLAECHE": "#fdeeec",    # Löschknopf, Maus darüber
    "GEFAHR_GEDRUECKT": "#f7dedb",  # Löschknopf, gedrückt

    "ZEILE_WECHSEL": "#fafbfc",     # jede zweite Tabellenzeile
}

DUNKLE_FARBEN = {
    "HINTERGRUND": "#1b1d21",
    "FLAECHE": "#232629",
    "SEITENLEISTE": "#1f2124",
    "RAHMEN": "#34383d",
    "RAHMEN_STARK": "#4a4f57",

    "TEXT": "#e6e8ea",
    "TEXT_LEISE": "#9aa1ab",
    "TEXT_HELL": "#ffffff",
    "TEXT_AUS": "#61666e",

    "AKZENT": "#4c8dff",
    "AKZENT_DUNKEL": "#3b76e0",
    "AKZENT_HELL": "#2b3b57",

    "GEFAHR": "#ff7b6e",
    "GEFAHR_FLAECHE": "#33262a",
    "GEFAHR_GEDRUECKT": "#422c30",

    "ZEILE_WECHSEL": "#282b2f",
}

# Diese Namen füllt farben_setzen(). Ganz unten in dieser Datei wird die
# Funktion einmal aufgerufen, damit sie von Anfang an einen Wert haben.
HINTERGRUND = None
FLAECHE = None
SEITENLEISTE = None
RAHMEN = None
RAHMEN_STARK = None
TEXT = None
TEXT_LEISE = None
TEXT_HELL = None
TEXT_AUS = None
AKZENT = None
AKZENT_DUNKEL = None
AKZENT_HELL = None
GEFAHR = None
GEFAHR_FLAECHE = None
GEFAHR_GEDRUECKT = None
ZEILE_WECHSEL = None

# Diese Variablen werden von stile_einrichten() gefüllt.
SCHRIFT = None
SCHRIFT_FETT = None
SCHRIFT_KLEIN = None
SCHRIFT_TITEL = None
SCHRIFT_UEBERSCHRIFT = None


def farben_setzen(modus):
    """
    Wählt den hellen oder den dunklen Farbsatz aus.

    modus  "dunkel" für den dunklen Satz, alles andere für den hellen.

    Wichtig: Bedienelemente merken sich ihre Farbe beim Erzeugen. Diese
    Funktion muss also aufgerufen werden, bevor das Fenster aufgebaut wird.
    Wer die Farben später wechselt, muss die Bedienelemente neu aufbauen.
    """
    global HINTERGRUND, FLAECHE, SEITENLEISTE, RAHMEN, RAHMEN_STARK
    global TEXT, TEXT_LEISE, TEXT_HELL, TEXT_AUS
    global AKZENT, AKZENT_DUNKEL, AKZENT_HELL
    global GEFAHR, GEFAHR_FLAECHE, GEFAHR_GEDRUECKT, ZEILE_WECHSEL

    if modus == "dunkel":
        farben = DUNKLE_FARBEN
    else:
        farben = HELLE_FARBEN

    HINTERGRUND = farben["HINTERGRUND"]
    FLAECHE = farben["FLAECHE"]
    SEITENLEISTE = farben["SEITENLEISTE"]
    RAHMEN = farben["RAHMEN"]
    RAHMEN_STARK = farben["RAHMEN_STARK"]

    TEXT = farben["TEXT"]
    TEXT_LEISE = farben["TEXT_LEISE"]
    TEXT_HELL = farben["TEXT_HELL"]
    TEXT_AUS = farben["TEXT_AUS"]

    AKZENT = farben["AKZENT"]
    AKZENT_DUNKEL = farben["AKZENT_DUNKEL"]
    AKZENT_HELL = farben["AKZENT_HELL"]

    GEFAHR = farben["GEFAHR"]
    GEFAHR_FLAECHE = farben["GEFAHR_FLAECHE"]
    GEFAHR_GEDRUECKT = farben["GEFAHR_GEDRUECKT"]

    ZEILE_WECHSEL = farben["ZEILE_WECHSEL"]


def stile_einrichten(fenster, schrift_aenderung=0):
    """
    Legt Schriften und das Aussehen aller ttk-Bedienelemente fest.
    Wird beim Start aufgerufen - und noch einmal, wenn sich Farbe oder
    Schriftgröße ändern.

    schrift_aenderung  verschiebt alle Schriftgrößen (-1 kleiner, +2 größer).
    """
    global SCHRIFT, SCHRIFT_FETT, SCHRIFT_KLEIN, SCHRIFT_TITEL, SCHRIFT_UEBERSCHRIFT

    # Standardschrift des Systems als Grundlage nehmen
    standard = tkfont.nametofont("TkDefaultFont")
    familie = standard.actual("family")
    groesse = abs(standard.actual("size")) + schrift_aenderung
    if groesse < 9:
        groesse = 9

    SCHRIFT = (familie, groesse)
    SCHRIFT_FETT = (familie, groesse, "bold")
    SCHRIFT_KLEIN = (familie, groesse - 1)
    SCHRIFT_TITEL = (familie, groesse + 6, "bold")
    SCHRIFT_UEBERSCHRIFT = (familie, groesse + 1, "bold")

    stil = ttk.Style(fenster)
    # "clam" lässt sich auf allen Betriebssystemen gleich einfärben.
    # Die Voreinstellung von macOS ignoriert eigene Farben weitgehend.
    stil.theme_use("clam")

    # --- Tabelle ----------------------------------------------------------
    stil.configure("Treeview",
                   background=FLAECHE,
                   fieldbackground=FLAECHE,
                   foreground=TEXT,
                   font=SCHRIFT,
                   rowheight=groesse * 2 + 12,
                   borderwidth=0,
                   relief="flat")
    stil.map("Treeview",
             background=[("selected", AKZENT_HELL)],
             foreground=[("selected", TEXT)])

    stil.configure("Treeview.Heading",
                   background=HINTERGRUND,
                   foreground=TEXT_LEISE,
                   font=SCHRIFT_KLEIN,
                   relief="flat",
                   padding=(10, 8))
    stil.map("Treeview.Heading",
             background=[("active", RAHMEN)],
             foreground=[("active", TEXT)])

    # --- Buttons ----------------------------------------------------------
    # Normaler Button: hell mit dünnem Rahmen
    stil.configure("TButton",
                   background=FLAECHE,
                   foreground=TEXT,
                   font=SCHRIFT,
                   borderwidth=1,
                   focusthickness=0,
                   relief="solid",
                   padding=(12, 6))
    stil.map("TButton",
             background=[("pressed", RAHMEN), ("active", HINTERGRUND)],
             bordercolor=[("!disabled", RAHMEN_STARK)])

    # Hauptaktion: blau gefüllt
    stil.configure("Akzent.TButton",
                   background=AKZENT,
                   foreground=TEXT_HELL,
                   font=SCHRIFT_FETT,
                   borderwidth=0,
                   relief="flat",
                   padding=(14, 7))
    stil.map("Akzent.TButton",
             background=[("pressed", AKZENT_DUNKEL), ("active", AKZENT_DUNKEL)],
             foreground=[("disabled", TEXT_AUS)])

    # Löschen: roter Text, heller Hintergrund
    stil.configure("Gefahr.TButton",
                   background=FLAECHE,
                   foreground=GEFAHR,
                   font=SCHRIFT,
                   borderwidth=1,
                   relief="solid",
                   padding=(12, 6))
    stil.map("Gefahr.TButton",
             background=[("pressed", GEFAHR_GEDRUECKT), ("active", GEFAHR_FLAECHE)],
             bordercolor=[("!disabled", RAHMEN_STARK)])

    # Flacher Button ohne Rahmen (z.B. zum Blättern)
    stil.configure("Flach.TButton",
                   background=HINTERGRUND,
                   foreground=TEXT_LEISE,
                   font=SCHRIFT,
                   borderwidth=0,
                   relief="flat",
                   padding=(8, 4))
    stil.map("Flach.TButton",
             background=[("pressed", RAHMEN), ("active", RAHMEN)],
             foreground=[("active", TEXT), ("disabled", TEXT_AUS)])

    # Wie "Flach", aber auf weißer Fläche - für die Einstellungsseite
    stil.configure("FlachHell.TButton",
                   background=FLAECHE,
                   foreground=TEXT_LEISE,
                   font=SCHRIFT,
                   borderwidth=0,
                   relief="flat",
                   padding=(8, 4))
    stil.map("FlachHell.TButton",
             background=[("pressed", RAHMEN), ("active", HINTERGRUND)],
             foreground=[("active", TEXT), ("disabled", TEXT_AUS)])

    # --- Eingabefelder ----------------------------------------------------
    stil.configure("TEntry",
                   fieldbackground=FLAECHE,
                   foreground=TEXT,
                   insertcolor=TEXT,
                   bordercolor=RAHMEN_STARK,
                   lightcolor=RAHMEN_STARK,
                   darkcolor=RAHMEN_STARK,
                   borderwidth=1,
                   relief="solid",
                   padding=6)
    stil.map("TEntry",
             bordercolor=[("focus", AKZENT)],
             lightcolor=[("focus", AKZENT)],
             darkcolor=[("focus", AKZENT)])

    stil.configure("TCombobox",
                   fieldbackground=FLAECHE,
                   background=FLAECHE,
                   foreground=TEXT,
                   bordercolor=RAHMEN_STARK,
                   lightcolor=RAHMEN_STARK,
                   darkcolor=RAHMEN_STARK,
                   arrowcolor=TEXT_LEISE,
                   borderwidth=1,
                   padding=5)
    stil.map("TCombobox",
             bordercolor=[("focus", AKZENT)],
             fieldbackground=[("disabled", HINTERGRUND), ("readonly", FLAECHE)],
             foreground=[("disabled", TEXT_AUS)],
             arrowcolor=[("disabled", TEXT_AUS)])
    # Die aufgeklappte Liste wird nicht über ttk, sondern über Tk eingestellt.
    fenster.option_add("*TCombobox*Listbox.background", FLAECHE)
    fenster.option_add("*TCombobox*Listbox.foreground", TEXT)
    fenster.option_add("*TCombobox*Listbox.selectBackground", AKZENT)
    fenster.option_add("*TCombobox*Listbox.selectForeground", TEXT_HELL)
    fenster.option_add("*TCombobox*Listbox.font", SCHRIFT)

    # --- Sonstiges --------------------------------------------------------
    # indicatorcolor ist die Fläche im Kästchen bzw. im Kreis. Im dunklen
    # Modus muss sie ebenfalls dunkel sein, sonst leuchtet sie weiß heraus.
    stil.configure("TCheckbutton",
                   background=FLAECHE,
                   foreground=TEXT,
                   font=SCHRIFT,
                   focuscolor=FLAECHE,
                   indicatorcolor=FLAECHE,
                   bordercolor=RAHMEN_STARK)
    stil.map("TCheckbutton",
             background=[("active", FLAECHE)],
             indicatorcolor=[("selected", AKZENT), ("!selected", FLAECHE)])

    stil.configure("TRadiobutton",
                   background=FLAECHE,
                   foreground=TEXT,
                   font=SCHRIFT,
                   focuscolor=FLAECHE,
                   indicatorcolor=FLAECHE,
                   bordercolor=RAHMEN_STARK)
    stil.map("TRadiobutton",
             background=[("active", FLAECHE)],
             indicatorcolor=[("selected", AKZENT), ("!selected", FLAECHE)])

    # Rollbalken ohne die kleinen Pfeile an den Enden - das wirkt deutlich
    # ruhiger. Dafür wird der Aufbau des Balkens auf den reinen Schieber gekürzt.
    stil.layout("Modern.Vertical.TScrollbar", [
        ("Vertical.Scrollbar.trough", {
            "sticky": "ns",
            "children": [("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]
        })
    ])
    stil.layout("Modern.Horizontal.TScrollbar", [
        ("Horizontal.Scrollbar.trough", {
            "sticky": "we",
            "children": [("Horizontal.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]
        })
    ])
    for name in ("Modern.Vertical.TScrollbar", "Modern.Horizontal.TScrollbar"):
        stil.configure(name,
                       background=RAHMEN,
                       troughcolor=FLAECHE,
                       bordercolor=FLAECHE,
                       lightcolor=RAHMEN,
                       darkcolor=RAHMEN,
                       borderwidth=0,
                       width=10,
                       arrowsize=0)
        stil.map(name, background=[("active", RAHMEN_STARK)])

    stil.configure("TSeparator", background=RAHMEN)


def textfeld(eltern, hoehe=4):
    """
    Ein mehrzeiliges Textfeld im gleichen Stil wie die einzeiligen Felder.
    tk.Text kennt keine Rahmenfarbe, deshalb wird dafür der Fokusrahmen benutzt.

    width=1 ist Absicht: Ohne Angabe möchte ein Textfeld 80 Zeichen breit sein.
    In einem schmalen Bereich bekäme es diesen Platz nie - tkinter würde die
    Größen dann dauernd neu berechnen und im Leerlauf Rechenzeit verbrauchen.
    Die tatsächliche Breite ergibt sich aus fill="x" beim Einfügen.
    """
    return tk.Text(eltern, height=hoehe, width=1, font=SCHRIFT, wrap="word",
                   background=FLAECHE, foreground=TEXT,
                   relief="flat", borderwidth=0,
                   highlightthickness=1,
                   highlightbackground=RAHMEN_STARK,
                   highlightcolor=AKZENT,
                   padx=8, pady=6,
                   insertbackground=TEXT)


def trennlinie(eltern, farbe=None):
    """
    Eine dünne waagerechte Linie - für klare Abschnitte ohne schwere Rahmen.

    Die Farbe steht nicht direkt in der Kopfzeile der Funktion: Ein solcher
    Vorgabewert würde nur ein einziges Mal beim Laden der Datei bestimmt und
    bliebe beim Wechsel des Farbsatzes auf dem alten Wert stehen.
    """
    if farbe is None:
        farbe = RAHMEN
    return tk.Frame(eltern, height=1, background=farbe)


def senkrechte_linie(eltern, farbe=None):
    """Eine dünne senkrechte Linie zwischen zwei Bereichen."""
    if farbe is None:
        farbe = RAHMEN
    return tk.Frame(eltern, width=1, background=farbe)


# Damit die Farbnamen von Anfang an einen Wert haben, auch wenn niemand
# farben_setzen() aufruft.
farben_setzen("hell")
