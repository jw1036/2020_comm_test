import binascii


class PacketBuilder(object):
    def __init__(self, dat=b''):
        self.dat = dat

    def __str__(self):
        return binascii.hexlify(self.dat).decode()

    def __repr__(self):
        return binascii.hexlify(self.dat).decode()

    def build(self):
        return self.dat

    def append(self, value, key=None):
        if isinstance(value, int):
            self.append(bytes([value]), key)
        else:
            self.dat += value
        return self

    def decode(self, value, key=None):
        pos = 0
        while pos < len(value):
            try:
                if value[pos: pos + 2] == b'$$':
                    self.append(value[pos: pos + 1])
                    pos += 2
                elif value[pos: pos + 1] == b'$':
                    self.append(int(value[pos + 1: pos + 3], base=16))
                    pos += 3
                else:
                    self.append(value[pos: pos + 1])
                    pos += 1
            except Exception as ex:
                self.append(value[pos: pos + 1])
                pos += 1
        return self


class PacketParser(object):
    def __init__(self, dat, fs=[]):
        self.dat = dat
        self.pos = 0
        self.fs = fs

    def __str__(self):
        return binascii.hexlify(self.dat).decode()

    def __repr__(self):
        return binascii.hexlify(self.dat).decode()

    def parse(self, width, key=None, fs=True):
        if width > len(self.dat) - self.pos:
            width = len(self.dat) - self.pos

        pos = self.pos
        for i in range(width):
            if fs:
                if self.dat[self.pos] in self.fs:
                    break
            self.pos += 1

        return self.dat[pos: self.pos]

    def next(self, value, key=None):
        if value in self.fs:
            fs = self.fs[0: self.fs.index(value)]
        else:
            fs = []

        while self.pos < len(self.dat):
            if self.dat[self.pos] == value:
                self.pos += 1
                return

            if self.dat[self.pos] in fs:
                break
            self.pos += 1


if __name__ == '__main__':
    builder = PacketBuilder()
    builder.append(b'12345678', "ITEM1")
    builder.append(0x1c)
    builder.append(0x1d)
    builder.append(b'ABCDEFGH', "ITEM2")
    builder.decode(b'$1cabcdefgh', "ITEM3")
    print(builder.build() == b'12345678\x1c\x1dABCDEFGH\x1cabcdefgh')

    parser = PacketParser(b'12345678\x1c\x1dABCDEFGH\x1cabcdefgh', [0x1d, 0x1c])
    print(parser.parse(5, "ITEM1") == b'12345')
    parser.next(0x1d)
    print(parser.parse(9, "ITEM2", False) == b'ABCDEFGH\x1c')
    print(parser.parse(10, "ITEM3") == b'abcdefgh')
