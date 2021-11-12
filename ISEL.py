import serial
import time
import numpy


class ISEL:
    COM = '/dev/ttyUSB0' # this is used for linux - RevPi
    baud = 19200
    data_bits = 8
    timeout = 1
    steps_per_rev = [800, 800, 800, 800]  #[X, Y, Z, A] Axis
    steigung = [5, 5, 5, 5]
    factor = [0, 0, 0, 0]
    fast_feed = 30000
    measure_feed = 8000
    bauteil_hoehe = 0
    soft_x = [0, 110]
    soft_y = [-10000, 10000]
    soft_z = [0, 180]
    soft_a = [-10000, 10000]
    user_output_channels = [0, 0, 0, 0, 0, 0, 0, 0]
    user_input_channels  = [0, 0, 0, 0, 0, 0, 0, 0]
    type = 'x,y'
    num_of_axis = 0
    cur_pos = [0, 0, 0, 0]

    def __init__(self):
        self.factor[0] = self.steigung[0] / self.steps_per_rev[0]
        self.factor[1] = self.steigung[1] / self.steps_per_rev[1]
        self.factor[2] = self.steigung[2] / self.steps_per_rev[2]
        self.factor[3] = self.steigung[3] / self.steps_per_rev[3]

    def factor_update(self):
        self.factor[0] = self.steigung[0] / self.steps_per_rev[0]
        self.factor[1] = self.steigung[1] / self.steps_per_rev[1]
        self.factor[2] = self.steigung[2] / self.steps_per_rev[2]
        self.factor[3] = self.steigung[3] / self.steps_per_rev[3]

    def open(self):
        self.serial_cnc = serial.Serial(self.COM, self.baud, self.data_bits, parity='N', stopbits=1, timeout=self.timeout)
        print('ISEL communication started: ', self.serial_cnc.is_open)

    def close(self):
        self.serial_cnc.close()

    def start(self):
        self.serial_cnc.reset_input_buffer()
        self.factor_update()
        self.init_axis_type(self.type)
        # self.set_ref_speed(1000, 1000)
        self.referenzfahrt(self.type)  # starts to reference the axis
        # self.interpolate3d(0) # nicht mit dem 1-Achs-Controller verwendbar

    def axis_type(self, axis_type):
        switcher = {
            'x':     1,
            'y':     2,
            'x,y':   3,
            'z':     4,
            'x,z':   5,
            'y,z':   6,
            'x,y,z': 7,
            'a':     8
        }
        return str(switcher.get(axis_type))

    def init_axis_type(self, axis_type):
        self.num_of_axis = self.axis_type(axis_type)
        self.send_command('@0'+str(self.num_of_axis))

    def set_ref_speed(self, x_ref_speed, y_ref_speed=0, z_ref_speed=0, a_ref_speed=0):
        command = '@0d'
        if self.type == 'x':
            command = command +str(x_ref_speed)
        elif self.type == 'x,y':
            command = command + str(x_ref_speed) + ',' + str(y_ref_speed)
        elif self.type == 'x,y,z':
            command = command + str(x_ref_speed) + ',' + str(y_ref_speed) + ',' + str(z_ref_speed)
        self.send_command(command)

    def referenzfahrt(self, tmp_type):
        command = '@0R' + self.axis_type(tmp_type)
        self.send_command(command)
        self.cur_pos = [0, 0, 0, 0]

    def interpolate3d(self, activation): # de-/aktiviert die Interpolation von 3 Achsen
        if activation == 1:
            self.send_command('@0z1')
        else:
            self.send_command('@0z0')

    def check_working_area(self, x, y, z, a):
        ret = 1
        if x < self.soft_x[0] or x > self.soft_x[1]:
            ax_code = 'x'
            ret = 0
        elif y < self.soft_y[0] or y > self.soft_y[1]:
            ax_code = 'y'
            ret = 0
        elif z < self.soft_z[0] or z > self.soft_z[1]:
            ax_code = 'z'
            ret = 0
        elif a < self.soft_a[0] or a > self.soft_a[1]:
            ax_code = 'a'
            ret = 0
        if ret == 0:
            print('unzulässige Achsposition - ' + ax_code + '-Achse ist außerhalb der Software-Endschalter')
            if ax_code == 'x':
                print('Softwareschalter' + str(self.soft_x) + '; Eingabe: ' + str(x))
            elif ax_code == 'y':
                print('Softwareschalter' + str(self.soft_y) + '; Eingabe: ' + str(y))
            elif ax_code == 'z':
                print('Softwareschalter' + str(self.soft_z) + '; Eingabe: ' + str(z))
            elif ax_code == 'a':
                print('Softwareschalter' + str(self.soft_a) + '; Eingabe: ' + str(a))
        return ret

    def calc_steps(self, x_pos, y_pos, z_pos, a_pos):
        steps = [0, 0, 0, 0]
        steps[0] = x_pos / self.factor[0]
        steps[1] = y_pos / self.factor[1]
        steps[2] = z_pos / self.factor[2]
        steps[3] = a_pos / self.factor[3]
        return steps

    def init_param(self, code='D', value=3):
        self.send_command('@0I' + str(code) + str(value))

# ***************************** Bewegungsteuerung *************************************

    def move_abs_x(self, x_pos, feed=fast_feed):
        self.move_abs_xyza(x_pos, feed, self.cur_pos[1], feed, self.cur_pos[2], feed, self.cur_pos[3], feed)

    def move_abs_y(self, y_pos, feed=fast_feed):
        self.move_abs_xyza(self.cur_pos[0], feed, y_pos, feed, self.cur_pos[2], feed, self.cur_pos[3], feed)

    def move_abs_z(self, z_pos, feed=fast_feed):
        self.move_abs_xyza(self.cur_pos[0], feed, self.cur_pos[1], feed, z_pos, feed, self.cur_pos[3], feed)

    def move_abs_a(self, a_pos, feed=fast_feed):
        self.move_abs_xyza(self.cur_pos[0], feed, self.cur_pos[1], feed, self.cur_pos[2], feed, a_pos, feed)

    def move_abs_xy(self, x_pos, x_feed, y_pos, y_feed):
        self.move_abs_xyza(x_pos, x_feed, y_pos, y_feed, self.cur_pos[2], x_feed, self.cur_pos[3], x_feed)

    def move_abs_xz(self, x_pos, x_feed, z_pos, z_feed):
        self.move_abs_xyza(x_pos, x_feed, self.cur_pos[1], x_feed, z_pos, z_feed, self.cur_pos[3], x_feed)

    def move_abs_xa(self, x_pos, x_feed, a_pos, a_feed):
        self.move_abs_xyza(x_pos, x_feed, self.cur_pos[1], x_feed, self.cur_pos[2], x_feed, a_pos, a_feed)

    def move_abs_yz(self, y_pos, y_feed, z_pos, z_feed):
        self.move_abs_xyza(self.cur_pos[0], y_feed, y_pos, y_feed, z_pos, z_feed, self.cur_pos[3], z_feed)

    def move_abs_ya(self, y_pos, y_feed, a_pos, a_feed):
        self.move_abs_xyza(self.cur_pos[0], y_feed, y_pos, y_feed, self.cur_pos[2], y_feed, a_pos, a_feed)

    def move_abs_za(self, z_pos, z_feed, a_pos, a_feed):
        self.move_abs_xyza(self.cur_pos[0], z_feed, self.cur_pos[1], z_feed, z_pos, z_feed, a_pos, a_feed)

    def move_abs_xyza(self, x_pos, x_feed, y_pos, y_feed, z_pos, z_feed, a_pos, a_feed):
        if self.cur_pos[0] != x_pos or self.cur_pos[1] != y_pos or self.cur_pos[2] != z_pos or self.cur_pos[3] != a_pos:  # at least one Position must be different
            if self.check_working_area(x_pos, y_pos, z_pos, a_pos):
                steps = self.calc_steps(x_pos, y_pos, z_pos, a_pos)
                command = '@0M ' + str(steps[0]) + ',' + str(x_feed)
                if self.type == 'x,y':
                    command = command + ',' + str(steps[1]) + ',' + str(y_feed)
                elif self.type == 'x,y,z':
                    command = command + ',' + str(steps[1]) + ',' + str(y_feed) + ',' + str(steps[2]) + ',' + str(z_feed) + ',' + str(0) + ',' + str(x_feed)
                elif self.type == 'x,y,z,a':
                    command = command + ',' + str(steps[1]) + ',' + str(y_feed) + ',' + str(steps[2]) + ',' + str(z_feed) + ',' + str(steps[3]) + ',' + str(a_feed)
                self.send_command(command)
                self.cur_pos = [x_pos, y_pos, z_pos, a_pos]  # new Position

# ******************************** Nullpunkt neu setzen ************************************

    def set_zero_point(self,axis=type):
        ax_code = self.axis_type(axis)
        if axis == 'x':
            self.soft_x = [self.soft_x[0]-self.cur_pos[0], self.soft_x[1]-self.cur_pos[0]]
            self.cur_pos[0] = 0
        elif axis == 'y':
            self.soft_y = [self.soft_y[0]-self.cur_pos[1], self.soft_y[1]-self.cur_pos[1]]
            self.cur_pos[1] = 0
        elif axis == 'x,y':
            self.set_zero_point('x')
            self.set_zero_point('y')
        elif axis == 'z':
            self.soft_z = [self.soft_z[0]-self.cur_pos[2], self.soft_z[1]-self.cur_pos[2]]
            self.cur_pos[2] = 0
        elif axis == 'x,z':
            self.set_zero_point('x')
            self.set_zero_point('z')
        elif axis == 'y,z':
            self.set_zero_point('y')
            self.set_zero_point('z')
        elif axis == 'x,y,z':
            self.set_zero_point('x')
            self.set_zero_point('y')
            self.set_zero_point('z')
        elif axis == 'a':
            self.soft_a = [self.soft_a[0]-self.cur_pos[3], self.soft_a[1]-self.cur_pos[3]]
            self.cur_pos[3] = 0
        command = '@0n'+str(ax_code)
        # print(command)  # use for debugging
        self.send_command(command)

# ******************************** Ausgänge schalten ***************************************

    def write_port(self, port_nr=0, value=0):
        command = '@0B' + str(port_nr) + ',' + str(value)
        # print(command)  # use for debugging
        self.send_command(command)

    def write_user_port(self, output, value):
        if 0 <= output <= 7:
            if value == 0 or value == 1:
                self.user_output_channels[output] = value
                user = numpy.array(self.user_output_channels[:])
                bits = numpy.array([1, 2, 4, 8, 16, 32, 64, 128])
                tmp = user*bits
                output_value = tmp[0] + tmp[1] + tmp[2] + tmp[3] + tmp[4] + tmp[5] + tmp[6] + tmp[7]
                self.write_port(0, output_value)
                # print(output_value)  # use for debugging

# ******************************** Eingänge abfragen ****************************************

    def read_port(self, port_nr=0):
        command = '@0b' + str(port_nr)
        tmp = int(self.send_command(command), 16)  # Rückgabewert ist im HexCode gewandelt in Integer
        tmp2 = '{0:08b}'.format(tmp)
        # print(tmp2)  # use for debugging
        for i in range(0, 7):
            self.user_input_channels[7-i] = int(tmp2[i])
        print(self.user_input_channels)

# ******************************** CNC Datenfeld abspeichern ********************************
    # die Speicherung des Datenfeldes ist noch nicht implementiert - Zeitaufwand ca. 8h

# ******************************* Ausgabe über die serielle Schnittstelle *******************

    def send_command(self, command):
        self.serial_cnc.flushInput()  # clear input
        self.serial_cnc.write(bytes(command, 'utf8')+b'\r')  # Change command to byte and add the Carriage Return Character
        while self.serial_cnc.in_waiting == 0:  # wait for the response of the controller
            time.sleep(0.01)
            # just wait
        ret_com = self.serial_cnc.readline()
        # print(ret_com)  # use for debugging
        if bytes(ret_com[0:1]) != b'0':  # check controller response
            self.error_check(ret_com)
        return ret_com[1:]

    def error_check(self, error_code):
        # print(command)  # for progamming necessary
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
        print(switcher.get(bytes(error_code)))

