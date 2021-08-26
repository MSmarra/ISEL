import serial
import time


class ISEL:
    COM = '/dev/ttyUSB0'
    baud = 19200
    dataBits = 8
    timeout = 1
    stepsPerRevX = 800
    stepsPerRevY = 800
    steigungX = 5
    steigungY = 5

    def __init__(self):
        self.serialCNC = serial.Serial(self.COM, self.baud, self.dataBits, parity='N', stopbits=1, timeout=self.timeout)
        self.factorX = self.steigungX / self.stepsPerRevX
        self.factorY = self.steigungY / self.stepsPerRevY

    def open(self):
        print('ISEL communication started: ', self.serialCNC.is_open)

    def start(self):
        self.serialCNC.reset_input_buffer()

        self.sendCommand('@03')  # Define number of axis the controller is using: here 2 (x,y)
        self.sendCommand('@0d1000,1000')  # Reference speed in impulses per second
        self.referenzfahrt()  # starts to reference the axis
        #self.serialCNC.write(b'@0R3\r')  # Referenzfahrt für zwei Achsen

    def referenzfahrt(self):
        command = '@0R3'
        self.sendCommand(command)

    def sendCommand(self, command):
        self.serialCNC.flushInput()  # clear input
        self.serialCNC.write(bytes(command, 'utf8')+b'\r')  # Change command to byte and add the Carriage Return Character
        while self.serialCNC.in_waiting == 0:  # wait for the response of the controller
            time.sleep(0.1)
            # just wait
        retCom = self.serialCNC.readline()
        if bytes(retCom) != b'0':  # check controller response
            self.errorCheck(retCom)

    def errorCheck(self, command):
        #print(command)  # for progamming necessary
        switcher = {
            #b'0': 'OK',
            b'1': 'Fehler in übergener Zahl\n-Die Steuerung hat eine Zahlenangabe empfangen, die nicht korrekt interpretiert werden konnte.\n-Der übergebene Zahlenwert ist außerhalb des zulässigen Bereichs oder der übergebene Zahlenwert enthält unzulässige Zeichen.',
            b'2': 'Endschalterfehler',
            b'3': 'unzulässige Achsangabe',
            b'4': 'keine Achse definiert',
            b'5': 'Syntax-Fehler',
            b'6': 'Speicherende',
            b'7': 'unzulässige Parameterzahl',
            b'8': 'zu speichernder Befehl inkorrekt',
            b'9': 'Anlagenfehelr',
            b'A': 'von dieser Steuerung nicht benutzt',
            b'B': 'von dieser Steuerung nicht benutzt',
            b'C': 'von dieser Steuerung nicht benutzt',
            b'D': 'unzulässige Geschwindigkeit',
            b'E': 'von dieser Steuerung nicht benutzt',
            b'F': 'Benutzerstop\n-Der Benutzer hat die Halttaste an der Steuerung betätigt, die aktuelle Bewegung wurde angehalten. Die Befehlsausführung kann mit der Starttaste oder dem Startbefehl @0S wieder aufgenommen werden',
            b'G': 'ungültiges Datenfeld',
            b'H': 'Haubenfehler'
        # to be filled up with the complete error description
        }
        print(switcher.get(bytes(command)))

