def hexdump(dat):
    out = ""
    for i in range(0, len(dat), 16):
        h = ' '.join(["%02X" % c for c in dat[i:i + 16]])
        a = ''.join(["%c" % c if 0x20 <= c <= 0x7e else '.' for c in dat[i:i + 16]])
        out += f"  {i:08X}  {h:<47s}  |{a}|\n"
    out += f"  {len(dat):08X}"
    return out


def strdump(dat, encoding):
    out = ""
    pos = 0
    while pos < len(dat):
        if dat[pos] >= 0x80:
            try:
                out += dat[pos:pos + 2].decode(encoding=encoding)
                pos += 2
                continue
            except Exception as ex:
                print(f"make_strdump: {dat[pos:pos + 2]} {ex}")

        out += chr(dat[pos]) if 0x20 <= dat[pos] <= 0x7e else '.'
        pos += 1
    return "|" + out + "|"


if __name__ == '__main__':
    print(hexdump(b'1234567890ABCDEF'))
    print(strdump(b'1234567890ABCDEF', encoding='euc-kr'))
