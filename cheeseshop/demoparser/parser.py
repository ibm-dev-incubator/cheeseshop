from cheeseshop.demoparser.bitbuf import Bitbuffer
from collections import defaultdict
from collections import deque
from collections import OrderedDict
from enum import IntEnum
import math

from cheeseshop.demoparser import consts
from cheeseshop.demoparser.protobufs import netmessages_pb2
from cheeseshop.demoparser.demofile import DemoFile
from cheeseshop.demoparser.entities import EntityList
from cheeseshop.demoparser.props import Decoder
from cheeseshop.demoparser.props import PropFlags
from cheeseshop.demoparser.props import PropTypes
from cheeseshop.demoparser.structures import UserInfo

from cheeseshop.demoparser.util import parse_entity_update

class DemoCommand(IntEnum):
    SIGNON = 1
    PACKET = 2
    SYNCTICK = 3
    CONSOLECMD = 4
    USERCMD = 5
    DATATABLES = 6
    STOP = 7
    CUSTOMDATA = 8
    STRINGTABLES = 9


class DemoParser:

    def __init__(self, demofile):
        self.demofile = DemoFile(demofile)
        self.merged_enums = {
            v[1]: v[0] for v in netmessages_pb2.NET_Messages.items() +
            netmessages_pb2.SVC_Messages.items()
        }
        self.current_tick = 0
        self.data_tables = []
        self.string_tables = []
        self.server_classes = []
        self.game_events = OrderedDict()
        self.pending_baselines = OrderedDict()
        self.instance_baselines = OrderedDict()
        self.entities = EntityList(self)
        self.callbacks = defaultdict(list)
        self.callbacks['svc_GameEventList'] = [self._handle_game_event_list]
        self.callbacks['svc_GameEvent'] = [self._handle_game_event]
        self.callbacks['svc_CreateStringTable'] = [self._create_string_table]
        self.callbacks['svc_UpdateStringTable'] = [self._update_string_table]
        self.callbacks['svc_PacketEntities'] = [self._handle_packet_entities]
        self.callbacks['string_table_update'] = [self._table_updated]

    def _fire_event(self, event, *args):
        for func in self.callbacks.get(event, []):
            func(*args)

    def add_callback(self, event, func):
        self.callbacks[event].append(func)

    def parse(self):
        while True:
            header = self.demofile.read_command_header()
            if header.tick != self.current_tick:
                self._fire_event('tick_end', self.current_tick)
                self.current_tick = header.tick
                self._fire_event('tick_start', self.current_tick)

            if header.command in (DemoCommand.SIGNON, DemoCommand.PACKET):
                self._handle_demo_packet(header)
            elif header.command == DemoCommand.SYNCTICK:
                continue
            elif header.command == DemoCommand.CONSOLECMD:
                length, buf = self.demofile.read_raw_data()
            elif header.command == DemoCommand.USERCMD:
                self.demofile.read_user_command()
            elif header.command == DemoCommand.DATATABLES:
                self._handle_data_table(header)
            elif header.command == DemoCommand.CUSTOMDATA:
                pass
            elif header.command == DemoCommand.STRINGTABLES:
                self._handle_string_tables(header)
            elif header.command == DemoCommand.STOP:
                self._fire_event('tick_end', self.current_tick)
                self._fire_event('end')
                break
            else:
                raise Exception("Unrecognized command")

    def _handle_packet_entities(self, msg):
        buf = Bitbuffer(msg.entity_data)
        entity_idx = -1

        for i in range(msg.updated_entries):
            entity_idx += 1 + buf.read_var_int()

            if buf.read_bool():
                if buf.read_bool():
                    # Remove entity
                    self.entities[entity_idx] = None
            elif buf.read_bool():
                class_id = buf.read_int_bits(self.server_class_bits)
                serial = buf.read_int_bits(
                    consts.NUM_NETWORKED_EHANDLE_SERIAL_NUMBER_BITS
                )

                new_entity = self.entities.new_entity(
                    entity_idx, class_id, serial
                )
                self._read_new_entity(buf, new_entity)
            else:
                entity = self.entities[entity_idx]
                self._read_new_entity(buf, entity)

    def _read_new_entity(self, buf, entity):
        server_class = self.server_classes[entity.class_id]
        updates = parse_entity_update(buf, server_class)

        for update in updates:
            table_name = update['prop']['table'].net_table_name
            var_name = update['prop']['prop'].var_name

            self._fire_event(
                'change', entity, table_name, var_name, update['value']
            )
            entity.update_prop(table_name, var_name, update['value'])

    def _handle_demo_packet(self, cmd_header):

        self.demofile.read_command_data()
        self.demofile.read_sequence_data()

        for cmd, size, data in self.demofile.read_packet_data():
            cls = self._class_by_net_message_type(cmd)()
            cls.ParseFromString(data)
            self._fire_event(self.merged_enums[cmd], cls)

    def _handle_data_table(self, cmd_header):
        # Size of entire data table chunk
        self.demofile.data.read(4)
        table = self._class_by_message_name('svc_SendTable')

        while True:
            # Type of table, not needed for now
            self.demofile.read_varint()

            data = self.demofile.read_var_bytes()

            msg = table()
            msg.ParseFromString(data)
            if msg.is_end:
                break

            self.data_tables.append(msg)

        server_classes = self.demofile.read_short()
        self.server_class_bits = math.ceil(math.log2(server_classes))

        for i in range(server_classes):
            class_id = self.demofile.read_short()
            assert class_id == i

            name = self.demofile.read_string()
            table_name = self.demofile.read_string()

            dt = self._data_table_by_name(table_name)

            table = {
                'class_id': class_id,
                'name': name,
                'table_name': table_name,
                'props': self._flatten_data_table(dt)
            }
            self.server_classes.append(table)

            # Handle pending baselines
            pending_baseline = self.pending_baselines.get(class_id)
            if pending_baseline:
                self.instance_baselines[class_id] = \
                    self._parse_instance_baseline(
                        pending_baseline, class_id
                )
                self._fire_event(
                    'baseline_update',
                    class_id,
                    table,
                    self.instance_baselines[class_id]
                )
                del self.pending_baselines[class_id]

        self._fire_event('datatable_ready', table)

    def _update_string_table(self, msg):
        buf = Bitbuffer(msg.string_data)
        table = self.string_tables[msg.table_id]

        self._parse_string_table_update(
            buf, table, msg.num_changed_entries, len(table['entries']),
            0, False
        )

    def _create_string_table(self, msg):
        buf = Bitbuffer(msg.string_data)
        #print(msg.name)

        table = {
            'name': msg.name,
            'entries': [{'entry': None, 'user_data': None}] * msg.max_entries
        }
        self.string_tables.append(table)
        self._parse_string_table_update(
            buf, table, msg.num_entries, msg.max_entries,
            msg.user_data_size_bits, msg.user_data_fixed_size
        )

    def _parse_string_table_update(
            self, buf, table, num_entries, max_entries, user_data_bits,
            user_data_fixed_size):
        entry_bits = int(math.log2(max_entries))
        history = deque(maxlen=32)

        dict_encode = buf.read_bool()
        assert not dict_encode, 'Dictionary encoding not supported'

        for i in range(num_entries):
            index = i
            entry = None

            if not buf.read_bool():
                index = buf.read_int_bits(entry_bits)

            assert index >=0 and index <= max_entries

            # entry changed?
            changed = buf.read_bool()
            if changed:
                # substring check
                substr = buf.read_bool()
                if substr:
                    idx = buf.read_int_bits(5)
                    bytes_to_copy = buf.read_int_bits(consts.SUBSTRING_BITS)
                    substring = history[idx][:bytes_to_copy * 8]
                    suffix = buf.read_string()
                    entry = substring + suffix
                else:
                    entry = buf.read_string()

                table['entries'][index]['entry'] = entry

            # Deal with user data
            user_data = None
            if buf.read_bool():
                if user_data_fixed_size:
                    user_data = buf.read_bits(user_data_bits).tobytes()
                else:
                    size = buf.read_int_bits(consts.MAX_USERDATA_BITS)
                    user_data = buf.read_bits(size * 8).tobytes()

                table['entries'][index]['user_data'] = user_data

            history.append(entry)
            self._fire_event(
                'string_table_update', table, index, table['entries'][index]
            )

    def _handle_string_tables(self, cmd_header):
        buf = self.demofile.read_bitstream()
        num_tables = buf.read_uint8()

        for i in range(num_tables):
            table_name = buf.read_string()
            self._handle_string_table(table_name, buf)

    def _handle_string_table(self, table_name, buf):
        table = self._table_by_name(table_name)
        entries = buf.read_uint16()

        for entry_idx in range(entries):
            entry_name = buf.read_string()

            one_bit = buf.read_bool()
            user_data = None
            if one_bit:
                user_data_len = buf.read_uint16()
                user_data = buf.read_bits(user_data_len * 8).tobytes()
                if table_name == 'userinfo':
                    user_data = UserInfo.from_data(user_data)

            table['entries'][entry_idx] = {
                'entry': entry_name,
                'user_data': user_data
            }

            self._fire_event(
                'string_table_update', table, entry_idx,
                table['entries'][entry_idx]
            )

        # Client-side entries, maybe they don't exist? I've never seen them
        if buf.read_bool():
            num_strings = buf.read_uint16()

            for string in range(num_strings):
                # entry name
                buf.read_string()
                user_data = None

                if buf.read_bool():
                    user_data_len = buf.read_uint16()
                    user_data = buf.read_bits(user_data_len * 8).tobytes()

    def _handle_game_event_list(self, msg):
        for event in msg.descriptors:
            self.game_events.update({
                event.eventid: {
                    'name': event.name,
                    'event': event
                }
            })

    def _handle_game_event(self, msg):
        event = self.game_events[msg.eventid]
        self._fire_event(event['name'], event, msg)

    def _class_by_net_message_type(self, msg_type):
        cls = self.merged_enums[msg_type]

        if not cls:
            raise Exception(
                "Class for message type {} not found.".format(msg_type)
            )

        enum_type = cls[:3]
        enum_name = cls[4:]
        class_name = 'C{}Msg_{}'.format(enum_type.upper(), enum_name)

        return getattr(netmessages_pb2, class_name)

    def _class_by_message_name(self, name):
        enum_type = name[:3]
        enum_name = name[4:]
        class_name = 'C{}Msg_{}'.format(enum_type.upper(), enum_name)
        return getattr(netmessages_pb2, class_name)

    def _table_by_name(self, name):
        return [t for t in self.string_tables if t['name'] == name][0]

    def _data_table_by_name(self, name):
        return [t for t in self.data_tables if t.net_table_name == name][0]

    def _table_updated(self, table, index, entry):
        if table['name'] != 'instancebaseline' or not entry['user_data']:
            return

        class_id = int(entry['entry'])
        baseline_buf = Bitbuffer(entry['user_data'])

        try:
            self.server_classes[class_id]
        except IndexError:
            self.pending_baselines[class_id] = baseline_buf
            return

        self.instance_baselines[class_id] = self._parse_instance_baseline(
            baseline_buf, class_id
        )

    def _parse_instance_baseline(self, buf, class_id):
        class_baseline = OrderedDict()
        server_class = self.server_classes[class_id]

        for baseline in parse_entity_update(buf, server_class):
            table_name = baseline['prop']['table'].net_table_name
            var_name = baseline['prop']['prop'].var_name

            if table_name not in class_baseline:
                class_baseline[table_name] = OrderedDict()
            class_baseline[table_name][var_name] = baseline['value']

        return class_baseline

    def _flatten_data_table(self, table):
        flattened_props = self._collect_props(
            table, self._collect_exclusions(table)
        )

        priorities = set(p['prop'].priority for p in flattened_props)
        priorities.add(64)
        priorities = sorted(list(priorities))

        start = 0
        for prio in priorities:
            while True:
                current_prop = start
                while current_prop < len(flattened_props):
                    prop = flattened_props[current_prop]['prop']
                    if (prop.priority == prio or (prio == 64 and
                       (prop.flags & PropFlags.SPROP_CHANGES_OFTEN))):
                        if start != current_prop:
                            temp = flattened_props[start]
                            flattened_props[start] = \
                                flattened_props[current_prop]
                            flattened_props[current_prop] = temp
                        start += 1
                        break
                    current_prop += 1
                if current_prop == len(flattened_props):
                    break

        # Doesn't seem to work
        # props = sorted(flattened_props, key=lambda x: x['prop'].priority)
        return flattened_props

    def _is_prop_excluded(self, exclusions, table, prop):
        for exclusion in exclusions:
            if (table.net_table_name == exclusion.dt_name and
               prop.var_name == exclusion.var_name):
                return True

    def _collect_exclusions(self, table):
        exclusions = []

        for idx, prop in enumerate(table.props):
            if prop.flags & PropFlags.SPROP_EXCLUDE:
                exclusions.append(prop)

            if prop.type == PropTypes.DPT_DataTable:
                sub_table = self._data_table_by_name(prop.dt_name)
                exclusions.extend(self._collect_exclusions(sub_table))
        return exclusions

    def _collect_props(self, table, exclusions):
        flattened = []

        for idx, prop in enumerate(table.props):

            if (prop.flags & PropFlags.SPROP_INSIDEARRAY or
               prop.flags & PropFlags.SPROP_EXCLUDE or
               self._is_prop_excluded(exclusions, table, prop)):
                continue

            if prop.type == PropTypes.DPT_DataTable:
                sub_table = self._data_table_by_name(prop.dt_name)
                child_props = self._collect_props(sub_table, exclusions)

                if prop.flags & PropFlags.SPROP_COLLAPSIBLE == 0:
                    for cp in child_props:
                        cp['collapsible'] = False

                flattened.extend(child_props)
            elif prop.type == PropTypes.DPT_Array:
                flattened.append({
                    'prop': prop,
                    'array_element_prop': table.props[idx - 1],
                    'table': table
                })
            else:
                flattened.append({
                    'prop': prop,
                    'table': table
                })

        def _key_sort(item):
            if item.get('collapsible', True) is False:
                return 0
            return 1
        return sorted(flattened, key=_key_sort)
