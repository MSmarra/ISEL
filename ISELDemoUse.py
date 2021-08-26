from ISELAchssteuerung.ISEL import ISEL
import time

# Klasse erzeugen
cnc = ISEL()
cnc.COM = 'COM4'

# Einstellungen für die Dreh-Kipp Achse
cnc.type = 'x,y'                # definiert die Anzahl der Achsen - Dreh-Kippeinheit wird als x,y angesehen

cnc.steigung[0] = 360           # erste Achse (0), bspw. Strecke 0-360° für Drehachse
cnc.steps_per_rev[0] = 800*30   # Anhand des Handbuchs - bzw. Achs- und Steuerungsabhängig: 800 Schritte im Controller und 30 Übersetzung des Motors
cnc.soft_x = [0, 260]           # Software Endschalter - prüft vor der Bewegung, ob diese zulässig ist - mechanisch begranzt auf 0-260°

cnc.steigung[1] = 360           # zweite Achse (1)
cnc.steps_per_rev[1] = 800*20   # Übersetzung des Motors 20

cnc.open()                      # für die Schnittstelle relevant
cnc.start()                     # s.o.

# Beispiel für Bewegungen
cnc.move_abs_x(90, 1000)                # Absolute Bewegung der x-Achse auf 90° mit 1000 Impulsen pro Sekunde (Geschwindigkeit)

cnc.fast_feed = 20000                   # Setzt die default-Geschwindigkeit (Maximum 30000) - gilt für alle Achsen
cnc.move_abs_x(130)                     # Absolute Bewegung auf 130 mit default-Geschwindigkeit

cnc.set_zero_point('x')                 # an der aktuellen Position der x-Achse den Nullpunkt setzen. Der Software-Enschalter ändert sich entsprechend auf [-120 140]°
cnc.move_abs_x(15)                      # fährt x-Achse noch 15° weiter - aufgrund des neuen Nullpunkts

cnc.move_abs_xy(0, 1000, -15, 1000)     # Absolute Bewegung der x und y-Achse auf x: 0° mit 1000 Impulsen pro Sekunde und y: auf -15° mit 1000 Impulsen pro Sekunde
cnc.set_zero_point('x,y')               # Setzt aktuelle Position als Nullpunkt für x und y-Achse

# Beispiel für Outputkanäle
# cnc.write_user_port(2, 1)     # am Controller befinden sich Ausgänge, die hier EIN geschaltet werden: hier Ausgang 2 (Beschriftung am Controller gilt)
# time.sleep(2)                 # Wartet zwei Sekunden - kein Bestandteil der Klasse
# cnc.write_user_port(2, 0)     # Ausgang ausgeschaltet

# Beispiel für das Lesen des Eingangs
cnc.read_port(0)                # Eingänge lesen - Bsp. Kabel hängt an Port 2
print('Zustand: ' + cnc.user_input_channels[1])   # digitale Beschriftung: Eingang 2 --> Variablenwert [1]

#cnc.move_abs_xy(100,1000,10,1000)
#cnc.move_abs_xy(1,1000,1,1000)
