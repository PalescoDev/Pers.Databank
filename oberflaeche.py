"""
oberflaeche.py
--------------
Das Hauptfenster.

Aufbau:

  +--------------+--------------------------------------+---------------+
  | Seitenleiste |  Kopfzeile: Name + Aktionen          |  Detail-      |
  |              |  Werkzeugleiste: Suche + Filter      |  ansicht des  |
  |  Kunden      |  Tabelle mit den Datensätzen         |  gewählten    |
  |  Produkte    |                                      |  Datensatzes  |
  |  Aufgaben    |  Fußzeile: Blättern + Anzahl         |               |
  +--------------+--------------------------------------+---------------+

Diese Datei enthält kein SQL. Alle Zugriffe auf die Daten laufen über
datenbank.py, das Aussehen kommt aus design.py, die beiden Dialoge zum
Anlegen von Datenbanken und Feldern stehen in dialoge.py.
"""

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

import austausch
import datenbank
import design
import dialoge
import einstellungen
import sprache

# So lange wartet das Programm nach dem letzten Tastendruck, bevor es sucht.
# Dadurch wird beim Tippen nicht nach jedem Buchstaben die Datenbank befragt.
SUCH_VERZOEGERUNG = 300   # Millisekunden

def filter_alle():
    """
    Der Eintrag "Alle" in den beiden Filterlisten.

    Bewusst eine Funktion und keine feste Zeichenkette: Ein Wert, der beim
    Laden der Datei festgelegt wird, bliebe nach einem Sprachwechsel auf dem
    alten Text stehen - und der Vergleich mit dem Auswahlfeld ginge schief.
    """
    return sprache.text("filter_alle")


# ---------------------------------------------------------------------------
# Zustand: was ist gerade ausgewählt?
# ---------------------------------------------------------------------------

aktuelle_datenbank = None     # Zeile aus der Tabelle "datenbanken"
felder = []                   # die Felder der aktuellen Datenbank
aktuelle_seite = 0
letzte_seite = 0
sortier_feld = None           # nach welchem Feld sortiert wird (None = nach Nummer)
sortierung_absteigend = False
filter_feld = None            # nach welchem Feld gefiltert wird
detail_id = None              # angezeigter Datensatz; None = neuer Datensatz
detail_eingaben = {}          # feld_id -> Eingabefeld in der Detailansicht
seitenleisten_knoepfe = {}    # datenbank_id -> Eintrag in der Seitenleiste
# Worauf sich der Eintrag im Rechtsklick-Menü gerade bezieht
kontext_ziel = {"art": None, "feld": None, "datensatz": None}
such_auftrag = None           # laufender Warte-Auftrag der Suche
aktuelle_ansicht = "datensaetze"   # "datensaetze" oder "einstellungen"

# Widgets, die an mehreren Stellen gebraucht werden
fenster = None
datensatz_ansicht = None      # Tabelle und Detailbereich
einstellungen_ansicht = None  # die Einstellungsseite
einstellungen_knopf = None    # der Eintrag dafür in der Seitenleiste
seitenleiste_liste = None
titel_label = None
anzahl_label = None
eingabe_suche = None
auswahl_filter_feld = None
auswahl_filter_wert = None
tabelle = None
kontextmenue_spalte = None    # Rechtsklick auf eine Spaltenüberschrift
kontextmenue_zeile = None     # Rechtsklick auf eine Zeile
filter_hinweis = None
leer_hinweis = None
detail_inhalt = None
detail_leinwand = None        # die Leinwand, in der das Formular rollt
einstellungen_leinwand = None  # die Leinwand der Einstellungsseite
detail_titel = None
detail_leer = None
detail_knoepfe = None
status_label = None
knopf_zurueck = None
knopf_vor = None
knopf_feld = None
knopf_datensatz = None


# ---------------------------------------------------------------------------
# Umschalten zwischen Datensätzen und Einstellungen
# ---------------------------------------------------------------------------

def ansicht_wechseln(name):
    """
    Zeigt entweder die Datensätze oder die Einstellungen.

    Beide Seiten liegen fertig aufgebaut im Arbeitsbereich; es wird immer
    nur eine davon eingeblendet. Deshalb geht das Umschalten ohne Verzögerung
    und ohne dass beim Zurückwechseln etwas neu aufgebaut werden muss.
    """
    global aktuelle_ansicht

    if name == aktuelle_ansicht:
        return
    aktuelle_ansicht = name

    if name == "einstellungen":
        datensatz_ansicht.pack_forget()
        einstellungen_ansicht.pack(fill="both", expand=True)
        einstellungen.bestand_auffrischen()
    else:
        einstellungen_ansicht.pack_forget()
        datensatz_ansicht.pack(fill="both", expand=True)

    seitenleiste_markieren()


def datensaetze_pro_seite():
    """
    Wie viele Datensätze eine Seite der Tabelle zeigt.

    Es wird immer nur diese eine Seite geladen - deshalb bleibt die Anzeige
    auch bei 10.000 Datensätzen schnell. Die Zahl kommt aus den Einstellungen;
    steht dort etwas Unbrauchbares, wird der übliche Wert genommen.
    """
    anzahl = einstellungen.zahl("datensaetze_pro_seite")
    if anzahl < 1:
        anzahl = int(einstellungen.STANDARD["datensaetze_pro_seite"])
    return anzahl


# ---------------------------------------------------------------------------
# Seitenleiste
# ---------------------------------------------------------------------------

def ist_geoeffnet(datenbank_id):
    """Sagt, ob diese Datenbank gerade angezeigt wird."""
    return aktuelle_datenbank is not None and aktuelle_datenbank["id"] == datenbank_id


def seitenleiste_fuellen():
    """
    Baut die Liste der Datenbanken in der linken Spalte neu auf.
    Nötig, wenn eine Datenbank dazukommt oder wegfällt - nicht beim Wechseln.
    """
    global seitenleisten_knoepfe

    for widget in seitenleiste_liste.winfo_children():
        widget.destroy()
    seitenleisten_knoepfe = {}

    for eintrag in datenbank.datenbanken_liste():
        knopf = tk.Label(seitenleiste_liste, text=eintrag["name"], anchor="w",
                         background=design.SEITENLEISTE, padx=12, pady=7, cursor="hand2")
        knopf.pack(fill="x", padx=8, pady=1)

        # Jeder Eintrag merkt sich seine eigene Nummer.
        # Das "nummer=..." sorgt dafür, dass jeder Eintrag die richtige behält.
        nummer = eintrag["id"]
        knopf.bind("<Button-1>", lambda ereignis, n=nummer: datenbank_waehlen(n))
        knopf.bind("<Enter>", lambda ereignis, k=knopf, n=nummer: zeige_hover(k, n, True))
        knopf.bind("<Leave>", lambda ereignis, k=knopf, n=nummer: zeige_hover(k, n, False))

        seitenleisten_knoepfe[nummer] = knopf

    seitenleiste_markieren()


def zeige_hover(knopf, datenbank_id, darueber):
    """Hebt einen Eintrag leicht hervor, wenn die Maus darüber ist."""
    if ist_geoeffnet(datenbank_id) and aktuelle_ansicht == "datensaetze":
        return   # der geöffnete Eintrag ist ohnehin schon hervorgehoben
    if darueber:
        knopf.config(background=design.RAHMEN)
    else:
        knopf.config(background=design.SEITENLEISTE)


def einstellungen_hover(darueber):
    """Dasselbe für den Eintrag "Settings" ganz unten."""
    if aktuelle_ansicht == "einstellungen":
        return
    if darueber:
        einstellungen_knopf.config(background=design.RAHMEN)
    else:
        einstellungen_knopf.config(background=design.SEITENLEISTE)


def seitenleiste_markieren():
    """
    Hebt den Eintrag hervor, der gerade angezeigt wird - eine Datenbank
    oder die Einstellungen.
    Dafür werden nur die Farben geändert - die Einträge bleiben bestehen.
    """
    for datenbank_id in seitenleisten_knoepfe:
        knopf = seitenleisten_knoepfe[datenbank_id]
        if ist_geoeffnet(datenbank_id) and aktuelle_ansicht == "datensaetze":
            knopf.config(background=design.AKZENT_HELL, foreground=design.AKZENT,
                         font=design.SCHRIFT_FETT)
        else:
            knopf.config(background=design.SEITENLEISTE, foreground=design.TEXT,
                         font=design.SCHRIFT)

    if aktuelle_ansicht == "einstellungen":
        einstellungen_knopf.config(background=design.AKZENT_HELL, foreground=design.AKZENT,
                                   font=design.SCHRIFT_FETT)
    else:
        einstellungen_knopf.config(background=design.SEITENLEISTE, foreground=design.TEXT,
                                   font=design.SCHRIFT)


def datenbank_waehlen(datenbank_id):
    """Wechselt zu einer anderen Datenbank."""
    global aktuelle_datenbank, felder, aktuelle_seite, sortier_feld
    global sortierung_absteigend, filter_feld

    # Ein Klick auf eine Datenbank führt immer zurück zu den Datensätzen -
    # auch dann, wenn gerade die Einstellungen zu sehen sind.
    ansicht_wechseln("datensaetze")

    # Ist diese Datenbank schon offen, gibt es nichts weiter zu tun.
    # Sonst würde ein Klick auf den bereits gewählten Eintrag alles neu aufbauen.
    if ist_geoeffnet(datenbank_id):
        return

    aktuelle_datenbank = datenbank.datenbank_holen(datenbank_id)
    if aktuelle_datenbank is None:
        return

    # Merken, welche Datenbank zuletzt offen war - beim nächsten Start kann
    # das Programm sie wieder öffnen (siehe Einstellungen).
    einstellungen.setzen("zuletzt_geoeffnet", datenbank_id)

    felder = datenbank.felder_liste(datenbank_id)
    aktuelle_seite = 0
    sortier_feld = None
    sortierung_absteigend = False
    filter_feld = None

    eingabe_suche.delete(0, tk.END)
    titel_label.config(text=aktuelle_datenbank["name"])

    seitenleiste_markieren()
    filter_auswahl_fuellen()
    tabelle_spalten_aufbauen()
    detail_formular_aufbauen()
    detail_leeren()
    liste_laden()


# ---------------------------------------------------------------------------
# Tabelle
# ---------------------------------------------------------------------------

def tabelle_spalten_aufbauen():
    """
    Baut die Spalten der Tabelle neu auf.
    Wird beim Wechsel der Datenbank und nach dem Anlegen eines Feldes gebraucht.
    """
    spalten_namen = []
    for feld in felder:
        spalten_namen.append("f" + str(feld["id"]))

    tabelle.configure(columns=spalten_namen)

    for feld in felder:
        spalte = "f" + str(feld["id"])
        # Das Sortieren hängt nicht an der einzelnen Überschrift, sondern an
        # einer einzigen Klick-Behandlung für die ganze Tabelle (kopf_geklickt).
        # Sonst würde bei jedem Datenbankwechsel eine neue Rückruffunktion
        # angelegt, ohne dass die alte je verschwindet.
        tabelle.heading(spalte, text=feld["anzeigename"], anchor="w")

        if feld["typ"] == "janein":
            breite = 90
        elif feld["typ"] == "zahl":
            breite = 110
        elif feld["typ"] == "datum":
            breite = 120
        elif feld["typ"] == "langtext":
            breite = 260
        else:
            breite = 170

        # Die Spalten haben feste Breiten, damit bei vielen Feldern waagerecht
        # gescrollt werden kann. Nur die letzte Spalte darf mitwachsen, damit
        # bei wenigen Feldern kein leerer Streifen rechts stehen bleibt.
        ist_letzte = feld["id"] == felder[-1]["id"]
        tabelle.column(spalte, width=breite, minwidth=60, stretch=ist_letzte, anchor="w")

    ueberschriften_auffrischen()


def ueberschriften_auffrischen():
    """Setzt einen kleinen Pfeil an die Überschrift, nach der sortiert wird."""
    for feld in felder:
        spalte = "f" + str(feld["id"])
        text = feld["anzeigename"]
        if sortier_feld is not None and feld["id"] == sortier_feld["id"]:
            if sortierung_absteigend:
                text = text + "  ↓"
            else:
                text = text + "  ↑"
        tabelle.heading(spalte, text=text)


def zeile_als_werte(zeile):
    """Macht aus einem Datensatz die Liste der Texte für eine Tabellenzeile."""
    werte = []
    for feld in felder:
        text = datenbank.text_fuer_anzeige(feld["typ"], zeile[feld["spalte"]])
        # In der Tabelle steht jeder Datensatz in einer Zeile,
        # deshalb werden Zeilenumbrüche durch Leerzeichen ersetzt.
        werte.append(text.replace("\n", " "))
    return werte


def liste_laden():
    """
    Holt die aktuelle Seite aus der Datenbank und zeigt sie an.
    Wird nach jeder Änderung aufgerufen, die die Reihenfolge betreffen kann.
    """
    global aktuelle_seite, letzte_seite

    if aktuelle_datenbank is None:
        return

    suchbegriff = eingabe_suche.get().strip()
    filter_wert = ""
    if filter_feld is not None and auswahl_filter_wert.get() != filter_alle():
        filter_wert = auswahl_filter_wert.get()

    # aktuelle_datenbank und felder liegen hier schon vor. Werden sie
    # mitgegeben, muss die Datenbankschicht sie nicht noch einmal nachschlagen -
    # ein Seitenaufbau kostet dadurch zwei Abfragen statt sechs.
    gesamt = datenbank.anzahl_datensaetze(
        aktuelle_datenbank["id"], suchbegriff, filter_feld, filter_wert,
        eintrag=aktuelle_datenbank, felder=felder
    )

    pro_seite = datensaetze_pro_seite()

    # Nummer der letzten Seite ausrechnen (250 Datensätze = Seiten 0, 1, 2).
    if gesamt > 0:
        letzte_seite = (gesamt - 1) // pro_seite
    else:
        letzte_seite = 0
    if aktuelle_seite > letzte_seite:
        aktuelle_seite = letzte_seite

    ueberspringen = aktuelle_seite * pro_seite

    zeilen = datenbank.datensaetze_suchen(
        aktuelle_datenbank["id"],
        suchbegriff=suchbegriff,
        filter_feld=filter_feld,
        filter_wert=filter_wert,
        sortier_feld=sortier_feld,
        absteigend=sortierung_absteigend,
        limit=pro_seite,
        offset=ueberspringen,
        eintrag=aktuelle_datenbank,
        felder=felder
    )

    # Alte Zeilen auf einmal entfernen - das ist schneller als einzeln.
    alte = tabelle.get_children()
    if alte:
        tabelle.delete(*alte)

    # Sind die abwechselnden Zeilen abgeschaltet, bekommen alle Zeilen
    # dieselbe Kennzeichnung und damit dieselbe Farbe.
    abwechselnd = einstellungen.ja("zeilen_abwechselnd")

    nummer = 0
    for zeile in zeilen:
        if nummer % 2 == 0 or not abwechselnd:
            streifen = "gerade"
        else:
            streifen = "ungerade"
        tabelle.insert("", tk.END, iid=str(zeile["id"]),
                       values=zeile_als_werte(zeile), tags=(streifen,))
        nummer = nummer + 1

    leere_anzeige_pruefen(gesamt, suchbegriff)
    status_auffrischen(gesamt, ueberspringen, len(zeilen))


def leere_anzeige_pruefen(gesamt, suchbegriff):
    """Zeigt statt einer leeren Tabelle einen erklärenden Hinweis."""
    if gesamt > 0:
        leer_hinweis.place_forget()
        return

    if suchbegriff or (filter_feld is not None and auswahl_filter_wert.get() != filter_alle()):
        text = sprache.text("keine_treffer")
        unterzeile = sprache.text("keine_treffer_hinweis")
    else:
        text = sprache.text("noch_keine_datensaetze")
        unterzeile = sprache.text("noch_keine_datensaetze_hinweis")

    leer_hinweis.kopf.config(text=text)
    leer_hinweis.text.config(text=unterzeile)
    # Der Hinweis wird mittig über die leere Tabelle gelegt.
    leer_hinweis.place(relx=0.5, rely=0.45, anchor="center")


def status_auffrischen(gesamt, ueberspringen, sichtbar):
    """Schreibt "1-100 von 10000" in die Fußzeile und schaltet die Pfeile."""
    if gesamt == 0:
        status_label.config(text=sprache.text("keine_datensaetze"))
    else:
        von = ueberspringen + 1
        bis = ueberspringen + sichtbar
        status_label.config(text=sprache.text("bereich") % (von, bis, gesamt))

    if gesamt == 1:
        anzahl_label.config(text=sprache.text("ein_datensatz"))
    else:
        anzahl_label.config(text=sprache.text("n_datensaetze") % gesamt)

    if aktuelle_seite > 0:
        knopf_zurueck.state(["!disabled"])
    else:
        knopf_zurueck.state(["disabled"])

    if aktuelle_seite < letzte_seite:
        knopf_vor.state(["!disabled"])
    else:
        knopf_vor.state(["disabled"])


def zeile_auffrischen(datensatz_id):
    """
    Aktualisiert eine einzelne Tabellenzeile.
    Nach dem Bearbeiten muss dadurch nicht die ganze Liste neu geladen werden.
    """
    schluessel = str(datensatz_id)
    if schluessel not in tabelle.get_children():
        return
    zeile = datenbank.datensatz_holen(aktuelle_datenbank["id"], datensatz_id)
    if zeile is not None:
        tabelle.item(schluessel, values=zeile_als_werte(zeile))


# ---------------------------------------------------------------------------
# Suchen, Filtern, Sortieren, Blättern
# ---------------------------------------------------------------------------

def suche_geplant(ereignis=None):
    """
    Wird bei jedem Tastendruck im Suchfeld aufgerufen.

    Statt sofort zu suchen, wird ein kurzer Moment gewartet. Tippt der Nutzer
    weiter, wird der vorherige Auftrag verworfen. So entsteht pro Suchbegriff
    nur eine Abfrage statt einer pro Buchstabe.
    """
    global such_auftrag

    if such_auftrag is not None:
        fenster.after_cancel(such_auftrag)
    such_auftrag = fenster.after(SUCH_VERZOEGERUNG, suche_ausfuehren)


def suche_ausfuehren():
    """Führt die Suche aus - immer beginnend auf der ersten Seite."""
    global aktuelle_seite, such_auftrag
    such_auftrag = None
    aktuelle_seite = 0
    liste_laden()


def filter_auswahl_fuellen():
    """Füllt die Auswahlliste mit den Feldern, nach denen man filtern kann."""
    namen = [filter_alle()]
    for feld in felder:
        if feld["typ"] in datenbank.FILTERBARE_TYPEN:
            namen.append(feld["anzeigename"])

    auswahl_filter_feld["values"] = namen
    auswahl_filter_feld.set(filter_alle())
    auswahl_filter_wert["values"] = [filter_alle()]
    auswahl_filter_wert.set(filter_alle())
    auswahl_filter_wert.state(["disabled"])
    filter_hinweis.config(text="")


def filter_feld_gewechselt(ereignis=None):
    """Der Nutzer hat ausgewählt, nach welchem Feld gefiltert wird."""
    global filter_feld, aktuelle_seite

    name = auswahl_filter_feld.get()
    filter_feld = None
    for feld in felder:
        if feld["anzeigename"] == name:
            filter_feld = feld

    if filter_feld is None:
        auswahl_filter_wert["values"] = [filter_alle()]
        auswahl_filter_wert.set(filter_alle())
        auswahl_filter_wert.state(["disabled"])
        filter_hinweis.config(text="")
    else:
        gefunden, gesamt = datenbank.werte_einer_spalte(aktuelle_datenbank["id"], filter_feld)
        werte = [filter_alle()]
        for wert in gefunden:
            werte.append(wert)
        auswahl_filter_wert["values"] = werte
        auswahl_filter_wert.set(filter_alle())
        auswahl_filter_wert.state(["!disabled", "readonly"])

        # Die Liste zeigt höchstens 200 Werte. Gibt es mehr, muss man das
        # sehen können - sonst hält man die Liste für vollständig.
        if len(gefunden) < gesamt:
            filter_hinweis.config(text=sprache.text("filter_gekuerzt") % (len(gefunden), gesamt))
        else:
            filter_hinweis.config(text="")

    aktuelle_seite = 0
    liste_laden()


def filter_wert_gewechselt(ereignis=None):
    """Der Nutzer hat einen Wert für den Filter ausgewählt."""
    global aktuelle_seite
    aktuelle_seite = 0
    liste_laden()


def alles_zuruecksetzen():
    """Leert Suche und Filter und zeigt wieder alle Datensätze."""
    global aktuelle_seite, filter_feld, sortier_feld, sortierung_absteigend

    eingabe_suche.delete(0, tk.END)
    filter_feld = None
    sortier_feld = None
    sortierung_absteigend = False
    aktuelle_seite = 0

    auswahl_filter_feld.set(filter_alle())
    auswahl_filter_wert["values"] = [filter_alle()]
    auswahl_filter_wert.set(filter_alle())
    auswahl_filter_wert.state(["disabled"])
    filter_hinweis.config(text="")

    ueberschriften_auffrischen()
    liste_laden()


def kopf_geklickt(ereignis):
    """
    Wird bei jedem Klick in die Tabelle aufgerufen und prüft, ob eine
    Spaltenüberschrift getroffen wurde. Wenn ja, wird danach sortiert.
    """
    if tabelle.identify_region(ereignis.x, ereignis.y) != "heading":
        return

    # identify_column liefert "#1" für die erste Spalte, "#2" für die zweite ...
    kennung = tabelle.identify_column(ereignis.x)
    nummer = int(kennung.replace("#", "")) - 1

    if 0 <= nummer < len(felder):
        sortieren(felder[nummer])


def sortieren(feld):
    """
    Sortiert nach einem Feld.
    Ein zweiter Klick auf dieselbe Überschrift dreht die Reihenfolge um.
    """
    global sortier_feld, sortierung_absteigend, aktuelle_seite

    if sortier_feld is not None and sortier_feld["id"] == feld["id"]:
        sortierung_absteigend = not sortierung_absteigend
    else:
        sortier_feld = feld
        sortierung_absteigend = False

    aktuelle_seite = 0
    ueberschriften_auffrischen()
    liste_laden()


def seite_vor():
    """Blättert eine Seite weiter (am Ende passiert nichts)."""
    global aktuelle_seite
    if aktuelle_seite < letzte_seite:
        aktuelle_seite = aktuelle_seite + 1
        liste_laden()


def seite_zurueck():
    """Blättert eine Seite zurück."""
    global aktuelle_seite
    if aktuelle_seite > 0:
        aktuelle_seite = aktuelle_seite - 1
        liste_laden()


# ---------------------------------------------------------------------------
# Detailansicht rechts
# ---------------------------------------------------------------------------

def detail_formular_aufbauen():
    """
    Baut die Eingabefelder der Detailansicht neu auf - für jedes Feld der
    Datenbank eines. Wird beim Wechsel der Datenbank und nach dem Anlegen
    eines neuen Feldes aufgerufen.
    """
    global detail_eingaben

    for widget in detail_inhalt.winfo_children():
        widget.destroy()
    detail_eingaben = {}

    for feld in felder:
        block = tk.Frame(detail_inhalt, background=design.FLAECHE)
        block.pack(fill="x", pady=(0, 14))

        tk.Label(block, text=feld["anzeigename"], anchor="w", font=design.SCHRIFT_KLEIN,
                 background=design.FLAECHE, foreground=design.TEXT_LEISE).pack(fill="x")

        typ = feld["typ"]

        if typ == "janein":
            zustand = tk.BooleanVar()
            widget = ttk.Checkbutton(block, text=sprache.text("ja"), variable=zustand)
            widget.pack(anchor="w", pady=(4, 0))
            widget.zustand = zustand          # Wert merken, um ihn später zu lesen

        elif typ == "auswahl":
            # width=1: Das Feld soll nicht selbst Platz fordern, sondern sich
            # durch fill="x" auf die Breite der Detailspalte ziehen lassen.
            widget = ttk.Combobox(block, values=[""] + datenbank.optionen_liste(feld),
                                  state="readonly", font=design.SCHRIFT, width=1)
            widget.pack(fill="x", pady=(4, 0))

        elif typ == "langtext":
            widget = design.textfeld(block, hoehe=4)
            widget.pack(fill="x", pady=(4, 0))

        else:
            widget = ttk.Entry(block, font=design.SCHRIFT, width=1)
            widget.pack(fill="x", pady=(4, 0))
            if typ == "datum":
                tk.Label(block, text=sprache.text("datumsformat"), font=design.SCHRIFT_KLEIN,
                         background=design.FLAECHE, foreground=design.TEXT_LEISE).pack(anchor="w")

        detail_eingaben[feld["id"]] = widget


def mit_rad_scrollen(ereignis):
    """
    Rollt mit dem Mausrad - je nachdem, was gerade zu sehen ist, das Formular
    in der Detailansicht oder die Einstellungsseite.

    Die Bindung dafür gilt fürs ganze Fenster (bind_all), weil das Rad sonst
    nur über der Leinwand selbst wirken würde, nicht über den Feldern darin.
    Genau deshalb steht diese Funktion hier oben und nicht im Aufbau des
    Fensters: Eine solche Bindung wird beim Zerstören eines Bedienelements
    nicht mit aufgeräumt. Sie wird einmal beim Start gesetzt und arbeitet
    seitdem mit der Leinwand, die gerade aktuell ist. Eine zweite Bindung für
    die Einstellungen würde diese hier verdrängen - deshalb entscheidet die
    Funktion selbst, welche Leinwand gemeint ist.
    """
    if aktuelle_ansicht == "einstellungen":
        leinwand = einstellungen_leinwand
    else:
        leinwand = detail_leinwand

    if leinwand is None:
        return
    # Windows und macOS melden das Mausrad über <MouseWheel>, Linux über
    # Button-4/5. Alle drei werden gebunden, ganz ohne Abfrage des Systems.
    if ereignis.num == 4:
        leinwand.yview_scroll(-1, "units")
    elif ereignis.num == 5:
        leinwand.yview_scroll(1, "units")
    elif ereignis.delta > 0:
        leinwand.yview_scroll(-1, "units")
    else:
        leinwand.yview_scroll(1, "units")


def detail_leeren():
    """Bereitet die Detailansicht für einen neuen Datensatz vor."""
    global detail_id
    detail_id = None

    for feld in felder:
        widget = detail_eingaben.get(feld["id"])
        if widget is None:
            continue
        if feld["typ"] == "janein":
            widget.zustand.set(False)
        elif feld["typ"] == "langtext":
            widget.delete("1.0", tk.END)
        elif feld["typ"] == "auswahl":
            widget.set("")
        else:
            widget.delete(0, tk.END)

    detail_titel.config(text=sprache.text("neuer_datensatz"))
    detail_bereich_zeigen(len(felder) > 0)


def detail_fuellen(datensatz_id):
    """Zeigt einen vorhandenen Datensatz in der Detailansicht."""
    global detail_id

    zeile = datenbank.datensatz_holen(aktuelle_datenbank["id"], datensatz_id)
    if zeile is None:
        detail_leeren()
        return

    detail_id = datensatz_id

    for feld in felder:
        widget = detail_eingaben.get(feld["id"])
        if widget is None:
            continue
        wert = zeile[feld["spalte"]]
        if feld["typ"] == "janein":
            widget.zustand.set(bool(wert))
        elif feld["typ"] == "langtext":
            widget.delete("1.0", tk.END)
            if wert is not None:
                widget.insert("1.0", str(wert))
        elif feld["typ"] == "auswahl":
            widget.set(datenbank.text_fuer_anzeige(feld["typ"], wert))
        else:
            widget.delete(0, tk.END)
            widget.insert(0, datenbank.text_fuer_anzeige(feld["typ"], wert))

    # Als Überschrift den Inhalt des ersten Feldes zeigen - das sagt mehr
    # als eine laufende Nummer. Ist es leer, nehmen wir die Nummer.
    ueberschrift = datenbank.text_fuer_anzeige(felder[0]["typ"], zeile[felder[0]["spalte"]]).strip()
    if ueberschrift == "":
        ueberschrift = sprache.text("datensatz_nummer") % datensatz_id
    detail_titel.config(text=ueberschrift[:28])
    detail_bereich_zeigen(True)


def detail_bereich_zeigen(zeigen):
    """
    Schaltet zwischen Formular und dem Hinweis "kein Datensatz gewählt" um.

    Wichtig: detail_inhalt darf hier nicht mit pack() ein- oder ausgeblendet
    werden. Es sitzt bereits als Element in der Leinwand (create_window).
    Zwei Anordnungsarten für dasselbe Feld bringen tkinter dazu, die Größen
    endlos neu zu berechnen - das Fenster hängt dann bei voller Rechenlast.
    Der Hinweis wird deshalb einfach darübergelegt.
    """
    if zeigen:
        detail_leer.place_forget()
        detail_knoepfe.pack(side="bottom", fill="x")
    else:
        detail_knoepfe.pack_forget()
        detail_leer.place(relx=0.5, rely=0.4, anchor="center")


def detail_werte_lesen():
    """
    Liest alle Eingabefelder aus und wandelt sie in Werte für die Datenbank um.
    Passt eine Eingabe nicht zum Feldtyp, gibt es einen ValueError.
    """
    werte = {}
    bestand = None
    if detail_id is not None and aktuelle_datenbank is not None:
        bestand = datenbank.datensatz_holen(aktuelle_datenbank["id"], detail_id)

    for feld in felder:
        widget = detail_eingaben.get(feld["id"])
        if widget is None:
            continue

        if feld["typ"] == "janein":
            eingabe = widget.zustand.get()
        elif feld["typ"] == "langtext":
            # end-1c excludes Tk's automatic final newline while preserving
            # any spaces or blank lines the user actually typed.
            eingabe = widget.get("1.0", "end-1c")
        else:
            eingabe = widget.get()

        # Older imports could store a choice outside its configured options.
        # Keep that legacy value when untouched so editing another field stays
        # possible; choosing a new value still goes through normal validation.
        if feld["typ"] == "auswahl" and bestand is not None:
            bisher = bestand[feld["spalte"]]
            if (bisher is not None and eingabe == str(bisher)
                    and eingabe not in datenbank.optionen_liste(feld)):
                werte[feld["id"]] = bisher
                continue

        try:
            werte[feld["id"]] = datenbank.wert_aus_eingabe(
                feld["typ"], eingabe, feld["optionen"]
            )
        except ValueError as fehler:
            raise ValueError(sprache.text("feld_mit_fehler") % feld["anzeigename"]
                             + str(fehler))

    return werte


def datensatz_speichern():
    """Legt einen neuen Datensatz an oder speichert die Änderung."""
    global detail_id

    if aktuelle_datenbank is None or not felder:
        return

    try:
        werte = detail_werte_lesen()
    except ValueError as fehler:
        messagebox.showwarning(sprache.text("eingabe_pruefen"), str(fehler))
        return

    if detail_id is None:
        neue_id = datenbank.datensatz_hinzufuegen(aktuelle_datenbank["id"], werte)
        detail_id = neue_id
        # Ein neuer Datensatz kann irgendwo einsortiert werden,
        # deshalb wird die Liste hier neu geladen.
        liste_laden()
        if str(neue_id) in tabelle.get_children():
            tabelle.selection_set(str(neue_id))
            tabelle.see(str(neue_id))
        detail_fuellen(neue_id)
    else:
        gespeicherte_id = detail_id
        datenbank.datensatz_aendern(aktuelle_datenbank["id"], gespeicherte_id, werte)
        # Änderungen können Suche, Filter, Sortierung und Seitenzahl verändern.
        liste_laden()
        if str(gespeicherte_id) in tabelle.get_children():
            tabelle.selection_set(str(gespeicherte_id))
            tabelle.see(str(gespeicherte_id))
        detail_fuellen(gespeicherte_id)


def datensatz_loeschen(datensatz_id=None):
    """
    Löscht einen Datensatz nach einer Rückfrage.

    Ohne Angabe wird der gerade angezeigte gelöscht (Knopf in der
    Detailansicht). Das Kontextmenü übergibt stattdessen die Nummer der
    angeklickten Zeile.
    """
    global detail_id

    if datensatz_id is None:
        datensatz_id = detail_id
    if datensatz_id is None:
        return

    # Die Rückfrage lässt sich in den Einstellungen abschalten. Für Felder und
    # ganze Datenbanken gilt das ausdrücklich nicht - dort hängt zu viel dran.
    if einstellungen.ja("loeschen_nachfragen"):
        if not messagebox.askyesno(sprache.text("loeschen_bestaetigen"),
                                   sprache.text("datensatz_wirklich_loeschen")):
            return

    datenbank.datensatz_loeschen(aktuelle_datenbank["id"], datensatz_id)
    if detail_id == datensatz_id:
        detail_leeren()
    liste_laden()


def neuer_datensatz():
    """Leert die Detailansicht, damit ein neuer Datensatz eingegeben werden kann."""
    tabelle.selection_remove(tabelle.selection())
    detail_leeren()

    # Den Blinkbalken gleich ins erste Feld setzen
    if felder:
        erstes = detail_eingaben.get(felder[0]["id"])
        if erstes is not None:
            erstes.focus()


def zeile_angeklickt(ereignis=None):
    """Wird aufgerufen, wenn in der Tabelle eine Zeile markiert wird."""
    markierung = tabelle.selection()
    if markierung:
        detail_fuellen(int(markierung[0]))


# ---------------------------------------------------------------------------
# Struktur ändern: neue Datenbank, neues Feld
# ---------------------------------------------------------------------------

def neue_datenbank_anlegen():
    """Öffnet den Dialog für eine neue Datenbank."""
    neue_id = dialoge.neue_datenbank(fenster)
    if neue_id is not None:
        # Es gibt jetzt einen Eintrag mehr, deshalb wird die Liste neu aufgebaut.
        seitenleiste_fuellen()
        datenbank_waehlen(neue_id)


def struktur_hat_sich_geaendert():
    """
    Übernimmt eine Änderung an den Feldern in die ganze Anzeige: Tabelle,
    Formular und Filter. Die markierte Zeile bleibt markiert.

    Gebraucht wird das nach jedem Eingriff in die Struktur - ein neues Feld,
    ein umbenanntes, eine andere Feldart, eine andere Reihenfolge.
    """
    global felder, sortier_feld, filter_feld, sortierung_absteigend

    sortier_id = sortier_feld["id"] if sortier_feld is not None else None
    filter_id = filter_feld["id"] if filter_feld is not None else None
    felder = datenbank.felder_liste(aktuelle_datenbank["id"])
    sortier_feld = next((feld for feld in felder if feld["id"] == sortier_id), None)
    if sortier_feld is None:
        sortierung_absteigend = False
    filter_feld = next(
        (feld for feld in felder
         if feld["id"] == filter_id and feld["typ"] in datenbank.FILTERBARE_TYPEN),
        None
    )
    gemerkte_auswahl = tabelle.selection()

    tabelle_spalten_aufbauen()
    detail_formular_aufbauen()
    filter_auswahl_fuellen()
    if filter_feld is None:
        liste_laden()
    else:
        auswahl_filter_feld.set(filter_feld["anzeigename"])
        filter_feld_gewechselt()

    if gemerkte_auswahl and gemerkte_auswahl[0] in tabelle.get_children():
        tabelle.selection_set(gemerkte_auswahl[0])
        detail_fuellen(int(gemerkte_auswahl[0]))
    else:
        detail_leeren()


def neues_feld_anlegen():
    """Öffnet den Dialog für ein neues Feld der aktuellen Datenbank."""
    if aktuelle_datenbank is None:
        return

    if dialoge.neues_feld(fenster, aktuelle_datenbank["id"], aktuelle_datenbank["name"]):
        struktur_hat_sich_geaendert()


def daten_exportieren():
    """Schreibt alle Datensätze der offenen Datenbank in eine Datei."""
    if aktuelle_datenbank is None:
        return

    anzahl = austausch.exportieren(fenster, aktuelle_datenbank["id"],
                                   aktuelle_datenbank["name"])
    if anzahl is not None:
        messagebox.showinfo(sprache.text("gespeichert"),
                            sprache.text("datensaetze_geschrieben") % anzahl)


def daten_importieren():
    """
    Liest Datensätze aus einer Datei ein.

    Danach kann die Datenbank neue Felder haben (wenn die Datei Spalten
    enthielt, die es noch nicht gab), deshalb wird die Anzeige neu aufgebaut.
    """
    if aktuelle_datenbank is None:
        return

    ergebnis = austausch.importieren(fenster, aktuelle_datenbank["id"],
                                     aktuelle_datenbank["name"])
    if ergebnis is None:
        return

    angelegt, geaendert = ergebnis
    struktur_hat_sich_geaendert()

    if geaendert == 0:
        messagebox.showinfo(sprache.text("importiert"),
                            sprache.text("datensaetze_angehaengt") % angelegt)
    else:
        messagebox.showinfo(sprache.text("importiert"),
                            sprache.text("import_ergebnis") % (angelegt, geaendert))


def feld_umbenennen(feld):
    """
    Fragt nach einer neuen Überschrift für ein Feld.

    Das ist der schonende Weg für einen Vertipper: Früher blieb nur, das Feld
    zu löschen und neu anzulegen - und dabei gingen alle Werte darin verloren.
    """
    if aktuelle_datenbank is None:
        return

    def speichern(neuer_name):
        # Geprüft wird in datenbank.py; ein Problem meldet der Dialog.
        datenbank.feld_umbenennen(aktuelle_datenbank["id"], feld["id"], neuer_name)

    if dialoge.umbenennen(fenster,
                          sprache.text("feld_umbenennen_titel"),
                          sprache.text("feld_umbenennen_erklaerung"),
                          feld["anzeigename"], speichern):
        struktur_hat_sich_geaendert()


def feld_art_aendern(feld):
    """
    Stellt ein Feld auf eine andere Art um, zum Beispiel von Text auf Zahl.
    Der Dialog sagt vorher, wie viele Werte das nicht überstehen.
    """
    if aktuelle_datenbank is None:
        return

    def zaehlen(neue_art, optionen=None):
        return datenbank.typ_umstellung_zaehlen(
            aktuelle_datenbank["id"], feld["id"], neue_art, optionen
        )

    def speichern(neue_art, optionen):
        datenbank.feld_typ_aendern(aktuelle_datenbank["id"], feld["id"], neue_art, optionen)

    if dialoge.feld_art_aendern(fenster, feld, zaehlen, speichern):
        struktur_hat_sich_geaendert()


def feld_verschieben(feld, um):
    """Schiebt eine Spalte nach links (um = -1) oder nach rechts (+1)."""
    if aktuelle_datenbank is None:
        return

    if datenbank.feld_verschieben(aktuelle_datenbank["id"], feld["id"], um):
        struktur_hat_sich_geaendert()


def datenbank_umbenennen():
    """Fragt nach einem neuen Namen für die offene Datenbank."""
    global aktuelle_datenbank

    if aktuelle_datenbank is None:
        return

    def speichern(neuer_name):
        datenbank.datenbank_umbenennen(aktuelle_datenbank["id"], neuer_name)

    if not dialoge.umbenennen(fenster,
                              sprache.text("datenbank_umbenennen_titel"),
                              sprache.text("datenbank_umbenennen_erklaerung"),
                              aktuelle_datenbank["name"], speichern):
        return

    # Der Name steckt in zwei Anzeigen: Überschrift und Seitenleiste.
    # Die Seitenleiste wird neu aufgebaut, weil sie alphabetisch sortiert ist.
    aktuelle_datenbank = datenbank.datenbank_holen(aktuelle_datenbank["id"])
    titel_label.config(text=aktuelle_datenbank["name"])
    seitenleiste_fuellen()


def feld_entfernen(feld):
    """Löscht ein Feld samt seiner Werte nach einer deutlichen Rückfrage."""
    anzahl = datenbank.anzahl_datensaetze(aktuelle_datenbank["id"])
    if not messagebox.askyesno(
            sprache.text("feld_loeschen_titel"),
            sprache.text("feld_loeschen_frage") % (feld["anzeigename"], anzahl)):
        return

    try:
        datenbank.feld_loeschen(aktuelle_datenbank["id"], feld["id"])
    except ValueError as fehler:
        messagebox.showwarning(sprache.text("feld_nicht_geloescht"), str(fehler))
        return

    # Die Anzeige muss die Spalte überall verlieren.
    struktur_hat_sich_geaendert()


# Die Funktionen hinter den Menüeinträgen. Worauf sie sich beziehen, steht in
# kontext_ziel - der Eintrag im Menü wird nur umbeschriftet. Das ist Absicht:
# Würde bei jedem Rechtsklick ein Eintrag neu angelegt, sammelten sich die
# zugehörigen Rückruffunktionen an, ohne je wieder zu verschwinden.

# Die Nummern der Einträge im Menü einer Spaltenüberschrift.
# Die Trennlinien zählen dabei mit.
MENUE_UMBENENNEN = 0
MENUE_ART = 1
MENUE_LINKS = 3
MENUE_RECHTS = 4
MENUE_LOESCHEN = 6


def kontext_feld_umbenennen():
    """Menüeintrag "Feld umbenennen"."""
    if kontext_ziel["feld"] is not None:
        feld_umbenennen(kontext_ziel["feld"])


def kontext_feld_art():
    """Menüeintrag "Art ändern"."""
    if kontext_ziel["feld"] is not None:
        feld_art_aendern(kontext_ziel["feld"])


def kontext_nach_links():
    """Menüeintrag "Nach links"."""
    if kontext_ziel["feld"] is not None:
        feld_verschieben(kontext_ziel["feld"], -1)


def kontext_nach_rechts():
    """Menüeintrag "Nach rechts"."""
    if kontext_ziel["feld"] is not None:
        feld_verschieben(kontext_ziel["feld"], 1)


def kontext_feld_loeschen():
    """Menüeintrag "Feld löschen"."""
    if kontext_ziel["feld"] is not None:
        feld_entfernen(kontext_ziel["feld"])


def kontext_datensatz_loeschen():
    """Menüeintrag "Datensatz löschen"."""
    if kontext_ziel["datensatz"] is not None:
        datensatz_loeschen(kontext_ziel["datensatz"])


def menue_erzeugen():
    """Ein leeres Menü im Stil des Programms - für die beiden Rechtsklick-Menüs."""
    return tk.Menu(fenster, tearoff=0,
                   background=design.FLAECHE, foreground=design.TEXT,
                   activebackground=design.AKZENT, activeforeground=design.TEXT_HELL,
                   font=design.SCHRIFT, borderwidth=1, relief="solid")


def kontextmenue_zeigen(ereignis):
    """
    Rechtsklick in der Tabelle: zeigt ein kleines Menü an.

    Was darin steht, hängt davon ab, wohin geklickt wurde:
      auf eine Spaltenüberschrift -> das ganze Feld löschen
      auf eine Zeile              -> diesen einen Datensatz löschen
    """
    if aktuelle_datenbank is None or not felder:
        return

    bereich = tabelle.identify_region(ereignis.x, ereignis.y)

    if bereich == "heading":
        # identify_column liefert "#1" für die erste Spalte, "#2" für die zweite ...
        nummer = int(tabelle.identify_column(ereignis.x).replace("#", "")) - 1
        if nummer < 0 or nummer >= len(felder):
            return
        kontext_ziel["art"] = "feld"
        kontext_ziel["feld"] = felder[nummer]
        name = felder[nummer]["anzeigename"]

        kontextmenue_spalte.entryconfigure(
            MENUE_UMBENENNEN, label=sprache.text("kontext_feld_umbenennen") % name)
        kontextmenue_spalte.entryconfigure(
            MENUE_ART, label=sprache.text("kontext_feld_art") % name)
        kontextmenue_spalte.entryconfigure(
            MENUE_LOESCHEN, label=sprache.text("kontext_feld_loeschen") % name)

        # Ganz außen geht es in die jeweilige Richtung nicht weiter.
        if nummer == 0:
            kontextmenue_spalte.entryconfigure(MENUE_LINKS, state="disabled")
        else:
            kontextmenue_spalte.entryconfigure(MENUE_LINKS, state="normal")

        if nummer == len(felder) - 1:
            kontextmenue_spalte.entryconfigure(MENUE_RECHTS, state="disabled")
        else:
            kontextmenue_spalte.entryconfigure(MENUE_RECHTS, state="normal")

        menue = kontextmenue_spalte

    else:
        zeile = tabelle.identify_row(ereignis.y)
        if not zeile:
            return
        # Die angeklickte Zeile auswählen und gleich anzeigen, damit man sieht,
        # worum es geht. Die Nummer wird zusätzlich gemerkt, damit das Löschen
        # auch dann den richtigen Datensatz trifft, wenn die Auswahl noch nicht
        # verarbeitet wurde.
        tabelle.selection_set(zeile)
        detail_fuellen(int(zeile))
        kontext_ziel["art"] = "datensatz"
        kontext_ziel["datensatz"] = int(zeile)
        menue = kontextmenue_zeile

    # tk_popup zeigt das Menü an der Mausposition.
    # grab_release gibt die Maus danach wieder frei.
    try:
        menue.tk_popup(ereignis.x_root, ereignis.y_root)
    finally:
        menue.grab_release()


def datenbank_entfernen():
    """Löscht die aktuelle Datenbank samt Inhalt nach einer deutlichen Rückfrage."""
    global aktuelle_datenbank

    if aktuelle_datenbank is None:
        return

    anzahl = datenbank.anzahl_datensaetze(aktuelle_datenbank["id"])
    if not messagebox.askyesno(
            sprache.text("datenbank_loeschen_titel"),
            sprache.text("datenbank_loeschen_frage") % (aktuelle_datenbank["name"], anzahl)):
        return

    datenbank.datenbank_loeschen(aktuelle_datenbank["id"])
    aktuelle_datenbank = None
    seitenleiste_fuellen()

    uebrig = datenbank.datenbanken_liste()
    if uebrig:
        datenbank_waehlen(uebrig[0]["id"])
    else:
        leeren_zustand_zeigen()


def leeren_zustand_zeigen():
    """Zeigt das Fenster ohne ausgewählte Datenbank."""
    global felder
    felder = []
    detail_formular_aufbauen()   # entfernt die Eingabefelder der alten Datenbank
    titel_label.config(text=sprache.text("keine_datenbank"))
    anzahl_label.config(text="")
    tabelle.configure(columns=())
    tabelle.delete(*tabelle.get_children())
    leer_hinweis.kopf.config(text=sprache.text("noch_keine_datenbank"))
    leer_hinweis.text.config(text=sprache.text("noch_keine_datenbank_hinweis"))
    leer_hinweis.place(relx=0.5, rely=0.45, anchor="center")
    detail_bereich_zeigen(False)
    status_label.config(text="")
    seitenleiste_fuellen()


# ---------------------------------------------------------------------------
# Fehler und Beenden
# ---------------------------------------------------------------------------

def fehler_anzeigen(fehlerart, fehler, spur):
    """
    Wird von tkinter aufgerufen, wenn bei einer Aktion ein Fehler auftritt -
    zum Beispiel, wenn die Datenbankdatei von einem anderen Programm gesperrt ist.

    Ohne diese Funktion landet der Fehler nur unsichtbar auf der Konsole.
    """
    messagebox.showerror(
        sprache.text("fehler_titel"),
        sprache.text("fehler_text") % str(fehler)
    )


def programm_beenden():
    """Wird beim Schließen des Fensters aufgerufen."""
    # Einen noch wartenden Suchauftrag abbrechen, damit nichts nachläuft.
    if such_auftrag is not None:
        fenster.after_cancel(such_auftrag)
    datenbank.datenbank_schliessen()
    fenster.destroy()


# ---------------------------------------------------------------------------
# Fenster aufbauen
# ---------------------------------------------------------------------------

def fenster_starten():
    """Baut das Fenster auf und startet das Programm."""
    global fenster

    fenster = tk.Tk()
    fenster.title("Pers.Databank")
    fenster.geometry("1240x740")
    fenster.minsize(940, 580)

    # Erst die Einstellungen holen, dann Farben, Schrift und Sprache danach
    # ausrichten - Bedienelemente merken sich beides schon beim Erzeugen.
    einstellungen.laden()
    darstellung_uebernehmen()

    fenster.report_callback_exception = fehler_anzeigen
    fenster.protocol("WM_DELETE_WINDOW", programm_beenden)

    # Das Mausrad wird genau einmal gebunden - diese Bindung überlebt einen
    # Neuaufbau der Bedienelemente und darf deshalb nicht in inhalt_aufbauen()
    # stehen. Dort würde bei jedem Farbwechsel eine weitere dazukommen.
    for ereignisname in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
        fenster.bind_all(ereignisname, mit_rad_scrollen)

    inhalt_aufbauen()
    startzustand_herstellen()

    fenster.mainloop()

    # Falls das Fenster auf anderem Weg geschlossen wurde
    datenbank.datenbank_schliessen()


def darstellung_uebernehmen():
    """
    Setzt Farben, Schriftgröße und Sprache so, wie es in den Einstellungen
    steht. Muss vor dem Aufbau der Bedienelemente laufen.
    """
    sprache.sprache_setzen(einstellungen.text("sprache"))
    design.farben_setzen(einstellungen.text("farbmodus"))
    design.stile_einrichten(fenster, einstellungen.zahl("schriftgroesse"))
    fenster.configure(background=design.HINTERGRUND)


def oberflaeche_neu_aufbauen():
    """
    Baut alle Bedienelemente neu auf - nötig nach einem Wechsel von Farbe,
    Schriftgröße oder Sprache.

    Ein Bedienelement bekommt Farbe und Aufschrift beim Erzeugen mit;
    nachträglich ließen sie sich nur ändern, indem man jedes einzelne Element
    anfasst. Einmal alles neu aufzubauen ist kürzer und lässt nichts aus.
    Der Zustand, den der Nutzer sieht - welche Datenbank offen ist und welche
    Seite gerade angezeigt wird -, wird vorher gemerkt und danach wieder
    hergestellt.
    """
    global aktuelle_datenbank, such_auftrag

    gemerkte_datenbank = None
    if aktuelle_datenbank is not None:
        gemerkte_datenbank = aktuelle_datenbank["id"]
    gemerkte_ansicht = aktuelle_ansicht

    # Einen noch wartenden Suchauftrag abbrechen: Er würde sonst gleich auf
    # Bedienelemente zugreifen, die es dann nicht mehr gibt.
    if such_auftrag is not None:
        fenster.after_cancel(such_auftrag)
        such_auftrag = None

    for widget in fenster.winfo_children():
        widget.destroy()

    # Ohne das hielte datenbank_waehlen die Datenbank für bereits geöffnet
    # und würde die neue Tabelle gar nicht erst füllen.
    aktuelle_datenbank = None

    darstellung_uebernehmen()
    inhalt_aufbauen()
    startzustand_herstellen(gemerkte_datenbank)

    if gemerkte_ansicht == "einstellungen":
        ansicht_wechseln("einstellungen")


def startzustand_herstellen(gewuenschte_datenbank=None):
    """
    Füllt die Seitenleiste und öffnet eine Datenbank.

    Ohne Vorgabe entscheiden die Einstellungen: entweder die zuletzt benutzte
    Datenbank oder die erste in der Liste. Gibt es die gemerkte nicht mehr
    (sie wurde gelöscht), wird ebenfalls die erste genommen.
    """
    seitenleiste_fuellen()

    vorhandene = datenbank.datenbanken_liste()
    if not vorhandene:
        leeren_zustand_zeigen()
        return

    if gewuenschte_datenbank is None and einstellungen.ja("letzte_datenbank_merken"):
        gewuenschte_datenbank = einstellungen.zahl("zuletzt_geoeffnet")

    for eintrag in vorhandene:
        if eintrag["id"] == gewuenschte_datenbank:
            datenbank_waehlen(gewuenschte_datenbank)
            return

    datenbank_waehlen(vorhandene[0]["id"])


def einstellung_wirkt_auf_darstellung():
    """
    Farbe, Schriftgröße oder Sprache wurden geändert.

    Neu aufgebaut wird erst, wenn der Klick fertig verarbeitet ist
    (after_idle): Sonst würde sich der gerade angeklickte Auswahlknopf
    mitten in seiner eigenen Rückmeldung selbst löschen.
    """
    fenster.after_idle(oberflaeche_neu_aufbauen)


def einstellung_wirkt_auf_liste():
    """Eine Einstellung der Tabelle wurde geändert: Liste neu laden."""
    global aktuelle_seite
    aktuelle_seite = 0
    liste_laden()


def inhalt_aufbauen():
    """Erzeugt alle Bedienelemente des Fensters."""
    global seitenleiste_liste, titel_label, anzahl_label, eingabe_suche
    global auswahl_filter_feld, auswahl_filter_wert, tabelle, leer_hinweis
    global kontextmenue_spalte, kontextmenue_zeile, filter_hinweis
    global detail_inhalt, detail_leinwand, detail_titel, detail_leer, detail_knoepfe
    global einstellungen_leinwand
    global status_label, knopf_zurueck, knopf_vor, knopf_feld, knopf_datensatz
    global datensatz_ansicht, einstellungen_ansicht, einstellungen_knopf
    global aktuelle_ansicht

    aktuelle_ansicht = "datensaetze"

    # ===== Linke Seitenleiste ============================================
    seitenleiste = tk.Frame(fenster, background=design.SEITENLEISTE, width=220)
    seitenleiste.pack(side="left", fill="y")
    seitenleiste.pack_propagate(False)

    tk.Label(seitenleiste, text="Pers.Databank", font=design.SCHRIFT_UEBERSCHRIFT,
             background=design.SEITENLEISTE, foreground=design.TEXT,
             anchor="w", padx=20, pady=18).pack(fill="x")

    tk.Label(seitenleiste, text=sprache.text("datenbanken_ueberschrift"),
             font=design.SCHRIFT_KLEIN,
             background=design.SEITENLEISTE, foreground=design.TEXT_LEISE,
             anchor="w", padx=20).pack(fill="x", pady=(0, 6))

    seitenleiste_liste = tk.Frame(seitenleiste, background=design.SEITENLEISTE)
    seitenleiste_liste.pack(fill="both", expand=True)

    # Herkunftshinweis, dezent am unteren Rand der Seitenleiste.
    # Er wird zuerst unten angeheftet und sitzt dadurch unter den Knöpfen.
    tk.Label(seitenleiste, text="GitHub-PalescoDev", font=design.SCHRIFT_KLEIN,
             background=design.SEITENLEISTE, foreground=design.TEXT_LEISE,
             anchor="w", padx=20).pack(side="bottom", fill="x", pady=(0, 12))

    fuss_leiste = tk.Frame(seitenleiste, background=design.SEITENLEISTE)
    fuss_leiste.pack(fill="x", side="bottom", pady=(14, 8), padx=14)
    ttk.Button(fuss_leiste, text=sprache.text("neue_datenbank_knopf"),
               command=neue_datenbank_anlegen).pack(fill="x")
    ttk.Button(fuss_leiste, text=sprache.text("datenbank_umbenennen_knopf"),
               command=datenbank_umbenennen).pack(fill="x", pady=(6, 0))
    ttk.Button(fuss_leiste, text=sprache.text("datenbank_loeschen_knopf"),
               style="Gefahr.TButton",
               command=datenbank_entfernen).pack(fill="x", pady=(6, 0))

    # Der Eintrag für die Einstellungen sieht aus wie eine Datenbank in der
    # Liste darüber und verhält sich auch so - er schaltet nur eben auf eine
    # andere Seite um statt auf andere Daten.
    einstellungen_knopf = tk.Label(seitenleiste, text=sprache.text("einstellungen_eintrag"),
                                   anchor="w",
                                   background=design.SEITENLEISTE, foreground=design.TEXT,
                                   font=design.SCHRIFT, padx=12, pady=7, cursor="hand2")
    einstellungen_knopf.pack(side="bottom", fill="x", padx=8)
    einstellungen_knopf.bind("<Button-1>",
                             lambda ereignis: ansicht_wechseln("einstellungen"))
    einstellungen_knopf.bind("<Enter>", lambda ereignis: einstellungen_hover(True))
    einstellungen_knopf.bind("<Leave>", lambda ereignis: einstellungen_hover(False))

    design.trennlinie(seitenleiste).pack(side="bottom", fill="x", padx=8, pady=(8, 6))

    design.senkrechte_linie(fenster).pack(side="left", fill="y")

    # ===== Arbeitsbereich neben der Seitenleiste =========================
    # Darin liegen zwei Seiten: die Datensätze und die Einstellungen. Beide
    # werden hier fertig aufgebaut, sichtbar ist immer nur eine davon.
    arbeitsbereich = tk.Frame(fenster, background=design.HINTERGRUND)
    arbeitsbereich.pack(side="left", fill="both", expand=True)

    datensatz_ansicht = tk.Frame(arbeitsbereich, background=design.HINTERGRUND)
    datensatz_ansicht.pack(fill="both", expand=True)

    einstellungen_ansicht = tk.Frame(arbeitsbereich, background=design.HINTERGRUND)
    einstellungen_leinwand = einstellungen.seite_fuellen(
        einstellungen_ansicht,
        einstellung_wirkt_auf_darstellung,
        einstellung_wirkt_auf_liste
    )

    # ===== Rechter Detailbereich =========================================
    detail = tk.Frame(datensatz_ansicht, background=design.FLAECHE, width=310)
    detail.pack(side="right", fill="y")
    detail.pack_propagate(False)
    design.senkrechte_linie(datensatz_ansicht).pack(side="right", fill="y")

    detail_kopf = tk.Frame(detail, background=design.FLAECHE)
    detail_kopf.pack(fill="x", padx=20, pady=(18, 12))
    tk.Label(detail_kopf, text=sprache.text("details"), font=design.SCHRIFT_KLEIN,
             background=design.FLAECHE, foreground=design.TEXT_LEISE, anchor="w").pack(fill="x")
    detail_titel = tk.Label(detail_kopf, text=sprache.text("neuer_datensatz"),
                            font=design.SCHRIFT_UEBERSCHRIFT,
                            background=design.FLAECHE, foreground=design.TEXT, anchor="w")
    detail_titel.pack(fill="x", pady=(2, 0))

    design.trennlinie(detail).pack(fill="x")

    # Knopfleiste unten im Detailbereich
    detail_knoepfe = tk.Frame(detail, background=design.FLAECHE)
    design.trennlinie(detail_knoepfe).pack(fill="x")
    knopf_rahmen = tk.Frame(detail_knoepfe, background=design.FLAECHE)
    knopf_rahmen.pack(fill="x", padx=20, pady=14)
    ttk.Button(knopf_rahmen, text=sprache.text("speichern"), style="Akzent.TButton",
               command=datensatz_speichern).pack(side="left")
    ttk.Button(knopf_rahmen, text=sprache.text("loeschen"), style="Gefahr.TButton",
               command=datensatz_loeschen).pack(side="right")

    # Der scrollbare Bereich mit den Eingabefeldern.
    # Eine Leinwand (Canvas) mit einem Rahmen darin ist der übliche Weg,
    # in tkinter etwas scrollbar zu machen.
    detail_mitte = tk.Frame(detail, background=design.FLAECHE)
    detail_mitte.pack(fill="both", expand=True)

    leinwand = tk.Canvas(detail_mitte, background=design.FLAECHE, highlightthickness=0)
    rollbalken = ttk.Scrollbar(detail_mitte, orient="vertical",
                               style="Modern.Vertical.TScrollbar", command=leinwand.yview)
    leinwand.configure(yscrollcommand=rollbalken.set)
    rollbalken.pack(side="right", fill="y")
    leinwand.pack(side="left", fill="both", expand=True)

    detail_inhalt = tk.Frame(leinwand, background=design.FLAECHE)
    # 20 Pixel Abstand nach links; die Breite lässt rechts denselben Abstand frei.
    inhalt_fenster = leinwand.create_window((20, 16), window=detail_inhalt, anchor="nw")

    # Achtung: Diese beiden Funktionen müssen getrennt bleiben.
    # Würde bei einer Größenänderung des Inhalts auch die Breite neu gesetzt,
    # löste das wieder eine Größenänderung aus - die beiden würden sich
    # endlos gegenseitig aufrufen und das Programm auf 100 % Rechenlast bringen.

    def inhalt_hat_sich_geaendert(ereignis=None):
        """Der Inhalt ist höher oder niedriger geworden: nur den Rollbereich anpassen."""
        leinwand.configure(scrollregion=leinwand.bbox("all"))

    def leinwand_wurde_groesser(ereignis=None):
        """Das Fenster wurde in der Breite verändert: Inhalt mitziehen."""
        leinwand.itemconfigure(inhalt_fenster, width=max(ereignis.width - 40, 100))

    detail_inhalt.bind("<Configure>", inhalt_hat_sich_geaendert)
    leinwand.bind("<Configure>", leinwand_wurde_groesser)

    # Das Mausrad arbeitet mit dieser Leinwand (siehe mit_rad_scrollen).
    detail_leinwand = leinwand

    detail_leer = tk.Label(detail_mitte, background=design.FLAECHE, foreground=design.TEXT_LEISE,
                           font=design.SCHRIFT, wraplength=250, justify="center",
                           text=sprache.text("kein_datensatz_gewaehlt"))

    # ===== Hauptbereich in der Mitte =====================================
    haupt = tk.Frame(datensatz_ansicht, background=design.HINTERGRUND)
    haupt.pack(side="left", fill="both", expand=True)

    # --- Kopfzeile ---
    kopf = tk.Frame(haupt, background=design.HINTERGRUND)
    kopf.pack(fill="x", padx=24, pady=(18, 12))

    kopf_links = tk.Frame(kopf, background=design.HINTERGRUND)
    kopf_links.pack(side="left")
    titel_label = tk.Label(kopf_links, text="", font=design.SCHRIFT_TITEL,
                           background=design.HINTERGRUND, foreground=design.TEXT, anchor="w")
    titel_label.pack(anchor="w")
    anzahl_label = tk.Label(kopf_links, text="", font=design.SCHRIFT_KLEIN,
                            background=design.HINTERGRUND, foreground=design.TEXT_LEISE, anchor="w")
    anzahl_label.pack(anchor="w")

    knopf_datensatz = ttk.Button(kopf, text=sprache.text("neuer_datensatz_knopf"),
                                 style="Akzent.TButton", command=neuer_datensatz)
    knopf_datensatz.pack(side="right")
    knopf_feld = ttk.Button(kopf, text=sprache.text("feld_hinzufuegen_knopf"),
                            command=neues_feld_anlegen)
    knopf_feld.pack(side="right", padx=(0, 8))

    # Import und Export sind seltener nötig und deshalb dezenter gestaltet.
    ttk.Button(kopf, text=sprache.text("exportieren"), style="Flach.TButton",
               command=daten_exportieren).pack(side="right", padx=(0, 8))
    ttk.Button(kopf, text=sprache.text("importieren"), style="Flach.TButton",
               command=daten_importieren).pack(side="right", padx=(0, 4))

    # --- Werkzeugleiste mit Suche und Filter ---
    werkzeuge = tk.Frame(haupt, background=design.HINTERGRUND)
    werkzeuge.pack(fill="x", padx=24, pady=(0, 12))

    tk.Label(werkzeuge, text=sprache.text("suche"), font=design.SCHRIFT_KLEIN,
             background=design.HINTERGRUND, foreground=design.TEXT_LEISE).pack(side="left", padx=(0, 8))

    eingabe_suche = ttk.Entry(werkzeuge, font=design.SCHRIFT, width=26)
    eingabe_suche.pack(side="left")
    eingabe_suche.bind("<KeyRelease>", suche_geplant)
    eingabe_suche.bind("<Return>", lambda ereignis: suche_ausfuehren())

    tk.Label(werkzeuge, text=sprache.text("filter"), font=design.SCHRIFT_KLEIN,
             background=design.HINTERGRUND, foreground=design.TEXT_LEISE).pack(side="left", padx=(20, 8))

    auswahl_filter_feld = ttk.Combobox(werkzeuge, state="readonly", width=14, font=design.SCHRIFT)
    auswahl_filter_feld.pack(side="left")
    auswahl_filter_feld.bind("<<ComboboxSelected>>", filter_feld_gewechselt)

    auswahl_filter_wert = ttk.Combobox(werkzeuge, state="disabled", width=14, font=design.SCHRIFT)
    auswahl_filter_wert.pack(side="left", padx=(6, 0))
    auswahl_filter_wert.bind("<<ComboboxSelected>>", filter_wert_gewechselt)

    ttk.Button(werkzeuge, text=sprache.text("zuruecksetzen"), style="Flach.TButton",
               command=alles_zuruecksetzen).pack(side="left", padx=(12, 0))

    # Sagt, wenn die Filterliste nicht alle Werte zeigen kann.
    filter_hinweis = tk.Label(werkzeuge, text="", font=design.SCHRIFT_KLEIN,
                              background=design.HINTERGRUND, foreground=design.TEXT_LEISE)
    filter_hinweis.pack(side="left", padx=(12, 0))

    # --- Tabelle ---
    tabellen_karte = tk.Frame(haupt, background=design.RAHMEN)
    tabellen_karte.pack(fill="both", expand=True, padx=24)

    tabellen_innen = tk.Frame(tabellen_karte, background=design.FLAECHE)
    tabellen_innen.pack(fill="both", expand=True, padx=1, pady=1)

    tabelle = ttk.Treeview(tabellen_innen, columns=(), show="headings", selectmode="browse")
    tabelle.tag_configure("gerade", background=design.FLAECHE)
    tabelle.tag_configure("ungerade", background=design.ZEILE_WECHSEL)

    waagerecht = ttk.Scrollbar(tabellen_innen, orient="horizontal",
                               style="Modern.Horizontal.TScrollbar", command=tabelle.xview)
    senkrecht = ttk.Scrollbar(tabellen_innen, orient="vertical",
                              style="Modern.Vertical.TScrollbar", command=tabelle.yview)
    tabelle.configure(yscrollcommand=senkrecht.set, xscrollcommand=waagerecht.set)

    waagerecht.pack(side="bottom", fill="x")
    senkrecht.pack(side="right", fill="y")
    tabelle.pack(side="left", fill="both", expand=True)

    tabelle.bind("<<TreeviewSelect>>", zeile_angeklickt)
    # Eine einzige Bindung für alle Spaltenüberschriften (siehe kopf_geklickt)
    tabelle.bind("<Button-1>", kopf_geklickt)

    # Die beiden Menüs für den Rechtsklick werden einmal erzeugt und später
    # nur noch umbeschriftet. Ein neues Menü pro Klick würde sich ansammeln.
    # Es sind zwei, weil auf einer Spaltenüberschrift zwei Dinge möglich sind
    # (umbenennen, löschen) und auf einer Zeile nur eines.
    kontextmenue_spalte = menue_erzeugen()
    kontextmenue_spalte.add_command(label="", command=kontext_feld_umbenennen)
    kontextmenue_spalte.add_command(label="", command=kontext_feld_art)
    kontextmenue_spalte.add_separator()
    kontextmenue_spalte.add_command(label=sprache.text("kontext_nach_links"),
                                    command=kontext_nach_links)
    kontextmenue_spalte.add_command(label=sprache.text("kontext_nach_rechts"),
                                    command=kontext_nach_rechts)
    kontextmenue_spalte.add_separator()
    kontextmenue_spalte.add_command(label="", command=kontext_feld_loeschen)

    kontextmenue_zeile = menue_erzeugen()
    kontextmenue_zeile.add_command(label=sprache.text("kontext_datensatz_loeschen"),
                                   command=kontext_datensatz_loeschen)

    # Welche Taste der Rechtsklick ist, meldet jedes System anders.
    # Alle drei üblichen Varianten werden gebunden, ganz ohne Abfrage.
    for ereignisname in ("<Button-3>", "<Button-2>", "<Control-Button-1>"):
        tabelle.bind(ereignisname, kontextmenue_zeigen)

    # Hinweis, der bei leerer Tabelle angezeigt wird
    leer_hinweis = tk.Frame(tabellen_innen, background=design.FLAECHE)
    leer_hinweis.kopf = tk.Label(leer_hinweis, text="", font=design.SCHRIFT_UEBERSCHRIFT,
                                 background=design.FLAECHE, foreground=design.TEXT)
    leer_hinweis.kopf.pack(pady=(90, 6))
    leer_hinweis.text = tk.Label(leer_hinweis, text="", font=design.SCHRIFT,
                                 background=design.FLAECHE, foreground=design.TEXT_LEISE)
    leer_hinweis.text.pack()

    # --- Fußzeile ---
    fuss = tk.Frame(haupt, background=design.HINTERGRUND)
    fuss.pack(fill="x", padx=24, pady=12)

    knopf_zurueck = ttk.Button(fuss, text="‹", width=3, style="Flach.TButton", command=seite_zurueck)
    knopf_zurueck.pack(side="left")
    knopf_vor = ttk.Button(fuss, text="›", width=3, style="Flach.TButton", command=seite_vor)
    knopf_vor.pack(side="left", padx=(4, 12))

    status_label = tk.Label(fuss, text="", font=design.SCHRIFT_KLEIN,
                            background=design.HINTERGRUND, foreground=design.TEXT_LEISE)
    status_label.pack(side="left")
