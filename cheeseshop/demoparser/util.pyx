# cython: profile=True
from cheeseshop.demoparser.props cimport Decoder
from cheeseshop.demoparser.props cimport PropFlags
from cheeseshop.demoparser.props cimport PropTypes

cdef int read_field_index(object buf, long last_index, bint new_way):
    cdef long ret = 0
    cdef long val = 0

    if new_way and buf.read_bool():
        return last_index + 1

    if new_way and buf.read_bool():
        ret = buf.read_int_bits(3)
    else:
        ret = buf.read_int_bits(7)
        val = ret & (32 | 64)

        if val == 32:
            ret = (ret & ~96) | (buf.read_int_bits(2) << 5)
            assert ret >= 32
        elif val == 64:
            ret = (ret & ~96) | (buf.read_int_bits(4) << 5)
            assert ret >= 128
        elif val == 96:
            ret = (ret & ~96) | (buf.read_int_bits(7) << 5)
            assert ret >= 512

    if ret == 0xfff:
        return -1

    return last_index + 1 + ret


cpdef list parse_entity_update(object buf, object server_class):
    cdef bint new_way
    cdef long val = -1

    updated_props = []
    field_indices = []

    new_way = buf.read_bool()

    while True:
        val = read_field_index(buf, val, new_way)

        if val == -1:
            break

        field_indices.append(val)

    for index in field_indices:
        flattened_prop = server_class['props'][index]

        decoder = Decoder(buf, flattened_prop)

        updated_props.append({
            'prop': flattened_prop,
            'value': decoder.decode()
        })

    return updated_props
