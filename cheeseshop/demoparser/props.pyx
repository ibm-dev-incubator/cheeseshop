# cython: profile=True
from enum import IntEnum
import math
from libc.math cimport sqrt

from cheeseshop.demoparser import consts


cdef class Decoder:

    def __cinit__(self, object buf, dict prop):
        self.buf = buf
        self.fprop = prop
        self.prop = prop['prop']
        self.flags = self.prop.flags

    cdef public object decode(self):
        assert self.prop.type != PropTypes.DPT_DataTable

        if self.prop.type == PropTypes.DPT_Int:
            ret = self._decode_int()
        elif self.prop.type == PropTypes.DPT_Float:
            ret = self._decode_float()
        elif self.prop.type == PropTypes.DPT_Vector:
            ret = self._decode_vector()
        elif self.prop.type == PropTypes.DPT_VectorXY:
            ret = self._decode_vector_xy()
        elif self.prop.type == PropTypes.DPT_String:
            ret = self._decode_string()
        elif self.prop.type == PropTypes.DPT_Int64:
            ret = self._decode_int64()
        elif self.prop.type == PropTypes.DPT_Array:
            ret = self._decode_array()
        else:
            raise Exception("Unsupported prop type")

        return ret

    cdef long _decode_int(self):
        cdef long ret
        if self.flags & PropFlags.SPROP_UNSIGNED != 0:
            if self.prop.num_bits == 1:
                ret = self.buf.read_bool()
            else:
                ret = self.buf.read_int_bits(self.prop.num_bits)
        else:
            ret = self.buf.read_sint_bits(self.prop.num_bits)
        return ret

    cdef float _decode_float(self):
        cdef int interp
        cdef float val
        special = self._decode_special_float()

        if special is not None:
            return special

        interp = self.buf.read_int_bits(self.prop.num_bits)
        val = interp / ((1 << self.prop.num_bits) - 1)
        val = self.prop.low_value + \
            (self.prop.high_value - self.prop.low_value) * val

        return val

    cdef dict _decode_vector(self):
        cdef bint sign
        cdef float sum_sqr
        vector = {
            'x': self._decode_float(),
            'y': self._decode_float()
        }

        if (self.flags & PropFlags.SPROP_NORMAL) == 0:
            vector['z'] = self._decode_float()
        else:
            sign = self.buf.read_bool()
            sum_sqr = (vector['x'] ** 2) + (vector['y'] ** 2)
            if sum_sqr < 1.0:
                vector['z'] = sqrt(1.0 - sum_sqr)
            else:
                vector['z'] = 0.0

            if sign:
                vector['z'] *= -1.0

        return vector

    cdef dict _decode_vector_xy(self):
        cdef float x, y
        x = self._decode_float()
        y = self._decode_float()
        return {
            'x': x,
            'y': y,
            'z': 0.0
        }

    cdef bytes _decode_string(self):
        length = self.buf.read_int_bits(9)
        if not length:
            return b""
        string = self.buf.read_bits(length * 8).tobytes()
        return string

    def _decode_int64(self):
        assert False, 'int64'

    cdef list _decode_array(self):
        cdef int num_elements
        max_elements = self.prop.num_elements
        bits = math.ceil(math.log2(max_elements)) + 1
        num_elements = self.buf.read_int_bits(bits)

        elements = []
        for idx in range(num_elements):
            prop = {'prop': self.fprop['array_element_prop']}
            val = Decoder(self.buf, prop).decode()
            elements.append(val)

        return elements

    cdef _decode_special_float(self):
        val = None

        if self.flags & PropFlags.SPROP_COORD != 0:
            val = self.buf.read_bit_coord()
        elif self.flags & PropFlags.SPROP_COORD_MP != 0:
            val = self.buf.read_bit_coord_mp(consts.CW_None)
        elif self.flags & PropFlags.SPROP_COORD_MP_LOWPRECISION != 0:
            val = self.buf.read_bit_coord_mp(consts.CW_LowPrecision)
        elif self.flags & PropFlags.SPROP_COORD_MP_INTEGRAL != 0:
            val = self.buf.read_bit_coord_mp(consts.CW_Integral)
        elif self.flags & PropFlags.SPROP_NOSCALE != 0:
            val = self.buf.read_float()
        elif self.flags & PropFlags.SPROP_NORMAL != 0:
            val = self.buf.read_bit_normal()
        elif (self.flags & PropFlags.SPROP_CELL_COORD):
            val = self.buf.read_bit_cell_coord(
                self.prop.num_bits, consts.CW_None
            )
        elif self.flags & PropFlags.SPROP_CELL_COORD_LOWPRECISION != 0:
            val = self.buf.read_bit_cell_coord(
                self.prop.num_bits, consts.CW_LowPrecision
            )
        elif self.flags & PropFlags.SPROP_CELL_COORD_INTEGRAL != 0:
            val = self.buf.read_bit_cell_coord(
                self.prop.num_bits, consts.CW_Integral
            )

        return val
