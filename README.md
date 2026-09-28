# Pers.Databank

Pers.Databank ist eine einfache Desktop-Anwendung für eigene Datenbanken. Sie läuft unter Windows und macOS und speichert alle Daten lokal.

## Download

Die aktuelle Version mit fertigen Dateien findest du unter [Releases](https://github.com/PalescoDev/Pers.Databank/releases/latest).

| System | Datei | Start |
|---|---|---|
| Windows | `Pers.Databank-Windows.exe` | Herunterladen und doppelklicken. |
| macOS | `Pers.Databank-macOS.zip` | Entpacken und die App beim ersten Start mit Rechtsklick → **Öffnen** starten. |

Python muss nicht installiert sein. Windows SmartScreen oder macOS können beim ersten Start eine Sicherheitsmeldung anzeigen.

## Funktionen

- Eigene Datenbanken, Felder und Einträge anlegen und verwalten
- Felder suchen, filtern, sortieren und neu anordnen
- CSV-Dateien importieren und exportieren
- Datenbanken sichern und bei Bedarf kompakt speichern
- Oberfläche auf Deutsch oder Englisch sowie mit hellem oder dunklem Design nutzen

## Daten und Datenschutz

Die fertige Anwendung speichert Daten lokal in `~/Pers.Databank/daten.db`. Beim Start aus dem Quellcode liegt die Datei im Projektordner. Die Datenbank kann über die Einstellungen gesichert und auf einen anderen Rechner übertragen werden.

## Aus dem Quellcode starten

Benötigt werden Python 3 und Tkinter. SQLite ist in Python enthalten.

```bash
python3 start.py
```

Unter Windows:

```powershell
python start.py
```

Zum Erstellen einer fertigen Anwendung:

```bash
python app_bauen.py
```

Das Programm wird für das System gebaut, auf dem der Befehl ausgeführt wird. GitHub Actions erstellt die Windows- und macOS-Dateien für jeden Versions-Release.

## Lizenz

Pers.Databank steht unter der [MIT-Lizenz](LICENSE).

Erstellt von **PalescoDev**.
