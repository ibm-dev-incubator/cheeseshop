# cython: profile=True
import struct
from bitarray import bitarray
from cheeseshop.demoparser import consts

cdef class Bitbuffer:

    cdef unsigned long index
    cdef public object buf

    def __init__(self, data, endian='little'):
        self.buf = bitarray(endian=endian)
        self.buf.frombytes(data)
        self.index = 0

    def read_bits(self, bits):

        end = self.index + bits
        data = self.buf[self.index:end]
        self.index += bits

        return data

    def peek(self, bits):
        end = self.index + bits
        return self.buf[self.index:end]

    def _to_int(self, ba, sign=False):
        return int.from_bytes(
            ba.tobytes(),
            byteorder=ba.endian(),
            signed=sign
        )

    def read_var_int(self):
        num = self.read_int_bits(6)
        bits = num & (16 | 32)

        if bits == 16:
            num = (num & 15) | (self.read_int_bits(4) << 4)
            assert num >= 16
        elif bits == 32:
            num = (num & 15) | (self.read_int_bits(8) << 4)
            assert num >= 256
        elif bits == 48:
            num = (num & 15) | (self.read_int_bits(28) << 4)
            assert num >= 4096

        return num

    def read_int_bits(self, bits):
        return self._to_int(self.read_bits(bits))

    def read_sint_bits(self, bits):
        return self._to_int(self.read_bits(bits), sign=True)

    def read_uint8(self):
        return self._to_int(self.read_bits(8))

    def read_uint16(self):
        return self._to_int(self.read_bits(16))

    def read_string(self, length=None):
        output = []
        append = True
        index = 0
        while True:
            char = self.read_uint8()
            if char == 0:
                append = False
                if not length:
                    break

            if append:
                output.append(chr(char))
            else:
                if index == length:
                    break
            index += 1

        return ''.join(output)

    def read_bool(self):
        return self._to_int(self.read_bits(1))

    def read_float(self):
        data = self.read_bits(32)
        data = data.tobytes()
        return struct.unpack('<f', data)[0]

    def read_bit_normal(self):
        sign_bit = self.read_bool()
        fraction = self.read_int_bits(consts.NORMAL_FRACTIONAL_BITS)

        value = fraction * consts.NORMAL_RESOLUTION
        return -value if sign_bit else value

    def read_bit_coord(self):
        integer = self.read_bool()
        fraction = self.read_bool()

        if not integer and not fraction:
            return 0.0

        sign_bit = self.read_bool()

        if integer:
            integer = self.read_int_bits(consts.COORD_INTEGER_BITS) + 1

        if fraction:
            fraction = self.read_int_bits(consts.COORD_FRACTIONAL_BITS)

        value = integer + (fraction * consts.COORD_RESOLUTION)
        if sign_bit:
            value = -value

        return value

    def read_bit_cell_coord(self, bits, coord_type):
        low_precision = (coord_type == consts.CW_LowPrecision)
        value = 0.0

        if coord_type == consts.CW_Integral:
            value = self.read_int_bits(bits)
        else:
            if coord_type == consts.COORD_FRACTIONAL_BITS_MP_LOWPRECISION:
                frac_bits = low_precision
            else:
                frac_bits = consts.COORD_FRACTIONAL_BITS

            if low_precision:
                resolution = consts.COORD_RESOLUTION_LOWPRECISION
            else:
                resolution = consts.COORD_RESOLUTION

            integer = self.read_int_bits(bits)
            fraction = self.read_int_bits(frac_bits)

            value = integer + (fraction * resolution)

        return value
