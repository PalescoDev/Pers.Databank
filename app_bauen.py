"""
app_bauen.py
------------
Macht aus dem Programm eine fertige Anwendung zum Doppelklicken:

    Windows   ->  Pers.Databank.exe   (eine einzige Datei)
    macOS     ->  Pers.Databank.app
    Linux     ->  Pers.Databank       (ausführbare Datei)

Das Hilfsprogramm PyInstaller wird automatisch nachinstalliert, falls es
fehlt. Die fertige Anwendung braucht danach kein Python mehr - Python und
die Oberfläche stecken mit drin.

Starten mit:
    Windows:        python app_bauen.py
    macOS / Linux:  python3 app_bauen.py

Diese Datei wird nur zum Bauen gebraucht. Das Programm selbst
(start.py und die anderen Dateien) kommt ohne sie aus.
"""

import os
import shutil
import struct
import subprocess
import sys
import zlib

NAME = "Pers.Databank"
ORDNER = os.path.dirname(os.path.abspath(__file__))
BAU_ORDNER = os.path.join(ORDNER, "bau_dateien")


# ---------------------------------------------------------------------------
# 1. Fehlende Hilfsprogramme nachinstallieren
# ---------------------------------------------------------------------------

def pyinstaller_sicherstellen():
    """
    Prüft, ob PyInstaller vorhanden ist, und installiert es sonst.
    Die Installation läuft ohne Rückfragen im Hintergrund.
    """
    try:
        import PyInstaller           # noqa: F401  (nur zum Prüfen importiert)
        print("PyInstaller is available.")
        return True
    except ImportError:
        pass

    print("PyInstaller is missing - installing it now ...")
    grundbefehl = [sys.executable, "-m", "pip", "install", "--quiet",
                   "--disable-pip-version-check", "pyinstaller"]

    # Erst normal versuchen, sonst in den Benutzerordner installieren.
    for zusatz in ([], ["--user"]):
        ergebnis = subprocess.run(grundbefehl + zusatz)
        if ergebnis.returncode == 0:
            print("PyInstaller has been installed.")
            return True

    print("\nThe installation did not work.")
    print("Please run this once by hand:")
    print("    " + sys.executable + " -m pip install pyinstaller")
    return False


# ---------------------------------------------------------------------------
# 2. Programmsymbol zeichnen
# ---------------------------------------------------------------------------

def in_ellipse(x, y, mx, my, rx, ry):
    """Liegt der Punkt innerhalb einer Ellipse?"""
    dx = (x - mx) / rx
    dy = (y - my) / ry
    return dx * dx + dy * dy <= 1.0


def farbe_an(x, y, groesse):
    """
    Bestimmt die Farbe eines Bildpunktes des Symbols:
    ein blaues Feld mit abgerundeten Ecken und einem weißen Datenspeicher.
    """
    blau = (47, 111, 235)      # dieselbe Farbe wie die Knöpfe im Programm
    weiss = (255, 255, 255)

    # Alle Maße beziehen sich auf ein Bild von 1024 Punkten Kantenlänge
    # und werden auf die gewünschte Größe umgerechnet.
    f = groesse / 1024.0
    px, py = x / f, y / f

    rand, radius = 40, 210
    links, oben, rechts, unten = rand, rand, 1024 - rand, 1024 - rand

    if px < links or px > rechts or py < oben or py > unten:
        return (0, 0, 0, 0)     # außerhalb: durchsichtig

    # Ecken abrunden
    in_ecke_x = px < links + radius or px > rechts - radius
    in_ecke_y = py < oben + radius or py > unten - radius
    if in_ecke_x and in_ecke_y:
        mx = links + radius if px < links + radius else rechts - radius
        my = oben + radius if py < oben + radius else unten - radius
        if (px - mx) ** 2 + (py - my) ** 2 > radius * radius:
            return (0, 0, 0, 0)

    # Der Datenspeicher: ein Zylinder aus drei Scheiben
    mitte_x = 512
    deckel_y, boden_y = 350, 660
    rx, ry = 250, 88

    im_koerper = abs(px - mitte_x) <= rx and deckel_y <= py <= boden_y
    if im_koerper or in_ellipse(px, py, mitte_x, deckel_y, rx, ry) \
            or in_ellipse(px, py, mitte_x, boden_y, rx, ry):
        # zwei Trennlinien zwischen den Scheiben
        for linie_y in (453, 556):
            if py >= linie_y:
                aussen = in_ellipse(px, py, mitte_x, linie_y, rx, ry)
                innen = in_ellipse(px, py, mitte_x, linie_y, rx - 16, ry - 16)
                if aussen and not innen:
                    return blau + (255,)
        return weiss + (255,)

    return blau + (255,)


def png_erzeugen(groesse):
    """Zeichnet das Symbol in der gewünschten Größe und gibt die PNG-Daten zurück."""
    zeilen = bytearray()
    for y in range(groesse):
        zeilen.append(0)                 # Filtertyp 0 = keiner
        for x in range(groesse):
            zeilen.extend(farbe_an(x, y, groesse))

    def block(typ, daten):
        return (struct.pack(">I", len(daten)) + typ + daten
                + struct.pack(">I", zlib.crc32(typ + daten) & 0xffffffff))

    kopf = struct.pack(">IIBBBBB", groesse, groesse, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + block(b"IHDR", kopf)
            + block(b"IDAT", zlib.compress(bytes(zeilen), 9))
            + block(b"IEND", b""))


def symbol_fuer_windows(zielordner):
    """Baut eine .ico-Datei. Sie enthält mehrere Größen als PNG."""
    groessen = [16, 32, 48, 64, 128, 256]
    bilder = []
    for groesse in groessen:
        bilder.append((groesse, png_erzeugen(groesse)))

    kopf = struct.pack("<HHH", 0, 1, len(bilder))
    eintraege = b""
    daten = b""
    versatz = 6 + 16 * len(bilder)
    for groesse, png in bilder:
        # 256 wird in der Dateistruktur als 0 geschrieben
        kante = 0 if groesse >= 256 else groesse
        eintraege += struct.pack("<BBBBHHII", kante, kante, 0, 0, 1, 32, len(png), versatz)
        daten += png
        versatz += len(png)

    pfad = os.path.join(zielordner, "symbol.ico")
    with open(pfad, "wb") as datei:
        datei.write(kopf + eintraege + daten)
    return pfad


def symbol_fuer_macos(zielordner):
    """Baut eine .icns-Datei mit dem macOS-Bordmittel iconutil."""
    iconset = os.path.join(zielordner, "symbol.iconset")
    os.makedirs(iconset, exist_ok=True)

    # Namen und Größen, die macOS erwartet
    teile = [(16, "icon_16x16.png"), (32, "icon_16x16@2x.png"),
             (32, "icon_32x32.png"), (64, "icon_32x32@2x.png"),
             (128, "icon_128x128.png"), (256, "icon_128x128@2x.png"),
             (256, "icon_256x256.png"), (512, "icon_256x256@2x.png")]

    gezeichnet = {}
    for groesse, dateiname in teile:
        if groesse not in gezeichnet:
            gezeichnet[groesse] = png_erzeugen(groesse)
        with open(os.path.join(iconset, dateiname), "wb") as datei:
            datei.write(gezeichnet[groesse])

    pfad = os.path.join(zielordner, "symbol.icns")
    ergebnis = subprocess.run(["iconutil", "-c", "icns", iconset, "-o", pfad],
                              capture_output=True)
    if ergebnis.returncode != 0:
        return None
    return pfad


def symbol_erzeugen():
    """Erzeugt das Symbol im Format des jeweiligen Systems."""
    os.makedirs(BAU_ORDNER, exist_ok=True)
    print("Drawing the application icon ...")

    if sys.platform.startswith("win"):
        return symbol_fuer_windows(BAU_ORDNER)
    if sys.platform == "darwin":
        return symbol_fuer_macos(BAU_ORDNER)
    return None      # unter Linux vergibt die Arbeitsumgebung das Symbol


# ---------------------------------------------------------------------------
# 3. Anwendung bauen
# ---------------------------------------------------------------------------

def bauen(symbol):
    """Ruft PyInstaller auf und legt das Ergebnis in den Projektordner."""
    # Erst alle Einstellungen für PyInstaller sammeln ...
    optionen = ["--noconfirm",
                "--windowed",               # kein schwarzes Konsolenfenster
                "--name", NAME,
                "--distpath", ORDNER,
                "--workpath", os.path.join(BAU_ORDNER, "arbeit"),
                "--specpath", BAU_ORDNER]

    # Unter Windows und Linux soll eine einzige Datei entstehen.
    # Unter macOS ist die .app bereits ein fertiges Paket.
    if sys.platform != "darwin":
        optionen.append("--onefile")

    if symbol:
        optionen += ["--icon", symbol]

    # ... und dann den vollständigen Aufruf zusammensetzen.
    # Die Einstellungen müssen hinter "-m PyInstaller" stehen, sonst hält
    # Python sie für seine eigenen und bricht mit "unknown option" ab.
    befehl = [sys.executable, "-m", "PyInstaller"] + optionen + [os.path.join(ORDNER, "start.py")]

    print("Building the application - this takes a moment ...\n")
    ergebnis = subprocess.run(befehl)
    return ergebnis.returncode == 0


def aufraeumen():
    """Entfernt die Zwischendateien, die beim Bauen entstanden sind."""
    shutil.rmtree(BAU_ORDNER, ignore_errors=True)

    # Unter macOS legt PyInstaller neben der .app noch einen gleichnamigen
    # Ordner ab. Er wird nicht gebraucht.
    beiwerk = os.path.join(ORDNER, NAME)
    if sys.platform == "darwin" and os.path.isdir(beiwerk):
        shutil.rmtree(beiwerk, ignore_errors=True)


def ergebnis_melden():
    """Sagt, wo die fertige Anwendung liegt."""
    if sys.platform == "darwin":
        fertig = os.path.join(ORDNER, NAME + ".app")
    elif sys.platform.startswith("win"):
        fertig = os.path.join(ORDNER, NAME + ".exe")
    else:
        fertig = os.path.join(ORDNER, NAME)

    print()
    if os.path.exists(fertig):
        print("Done! The application is here:")
        print("    " + fertig)
        print()
        print("It starts with a double click and needs no Python.")
        print("The data is stored in the folder \"Pers.Databank\" in your home")
        print("directory (" + os.path.join(os.path.expanduser("~"), "Pers.Databank") + ").")
    else:
        print("The application was not found. Please check the messages above.")


if __name__ == "__main__":
    if not pyinstaller_sicherstellen():
        raise SystemExit(1)

    symbol = symbol_erzeugen()
    erfolgreich = bauen(symbol)
    aufraeumen()

    if not erfolgreich:
        print("\nThe build failed. Please check the messages above.")
        raise SystemExit(1)

    ergebnis_melden()
