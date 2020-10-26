import serial
import serial.tools.list_ports
import binascii

_STX = 0x02
_ETX = 0x03

_TIMEOUT = 1


class CommError(Exception):
    def __init__(self, msg, raw=None):
        super().__init__(msg)
        self.raw = raw


class CommTimeoutError(CommError):
    pass


class CommStartError(CommError):
    pass


class CommLengthError(CommError):
    pass


class CommDataError(CommError):
    pass


class Comm(object):
    @staticmethod
    def calc_lrc(dat, lrc=0):
        for c in dat:
            lrc ^= c
        return lrc

    @staticmethod
    def build(dat):
        dat_len = len(dat) + 1
        raw = b''
        raw += bytes([_STX])
        raw += bytes([dat_len >> 8, dat_len & 0xff])
        raw += dat
        raw += bytes([_ETX])
        raw += bytes([Comm.calc_lrc(raw, _STX)])
        return raw

    @staticmethod
    def parse(dat):
        return dat[3: -2]

    @staticmethod
    def scan_ports():
        out = []
        ports = serial.tools.list_ports.comports()
        for dev, desc, hwid in sorted(ports):
            out.append(dev)
        return out

    def __init__(self, port, speed=38400):
        self.ser = serial.Serial()
        self.ser.port = port
        self.ser.baudrate = speed
        self.ser.timeout = _TIMEOUT
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.stopbits = serial.STOPBITS_TWO
        self.ser.parity = serial.PARITY_NONE
        self.ser.xonxoff = False
        self.ser.rtscts = False
        self.ser.dsrdtr = False

    def __del__(self):
        self.close()

    def open(self):
        if not self.ser.is_open:
            self.ser.open()

    def close(self):
        if self.ser.is_open:
            self.ser.close()

    def write(self, raw):
        self.ser.write(raw)

    def read(self, timeout=_TIMEOUT, start_error=False):
        self.ser.timeout = timeout

        while True:
            raw = self.ser.read(1)
            if len(raw) != 1:
                raise CommTimeoutError("Timeout Error", None)

            if raw[0] == _STX:
                self.ser.timeout = 3

                raw += self.ser.read(3)
                if len(raw) != 4:
                    raise CommLengthError("Length Error", raw)

                dat_len  = raw[1] << 8
                dat_len += raw[2]
                raw += self.ser.read(dat_len)
                if len(raw) != 4 + dat_len:
                    raise CommLengthError("Length Error", raw)

                if self.calc_lrc(raw) != _STX:
                    raise CommDataError("Data Error", raw)

                return raw
            else:
                if start_error:
                    raise CommStartError("Start Error", raw)

    def send(self, dat):
        self.write(self.build(dat))

    def recv(self, timeout=_TIMEOUT):
        return self.parse(self.read(timeout))


if __name__ == '__main__':
    comm = Comm('/dev/pts/2', 38400)
    print(comm)
    try:
        comm.open()
        dat = comm.recv(3)
        print(binascii.hexlify(dat))
        comm.send(dat)
    except CommError as ex:
        print(str(ex))
        print(binascii.hexlify(ex.raw))
    finally:
        comm.close()
