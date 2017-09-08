# flake8: noqa
import sys

from cheeseshop.demoparser.parser import DemoParser

if __name__ == "__main__":
    def death(event, msg):
        for idx, key in enumerate(event['event'].keys):
            if key.name == 'attacker':
                user_id = msg.keys[idx].val_short
                attacker = d.entities.get_by_user_id(user_id)
            elif key.name == 'userid':
                user_id = msg.keys[idx].val_short
                victim = d.entities.get_by_user_id(user_id)
            elif key.name == 'weapon':
                weapon = msg.keys[idx].val_string
            elif key.name == 'headshot':
                headshot = msg.keys[idx].val_bool

        if attacker and victim:
            print("\n --- Player Death at tick {}---".format(d.current_tick))
            print("{} killed by {} with {}. Headshot? {}.\n"
                  "Attacker: health = {} position = {}\n"
                  "Victim: position = {}".format(
                      victim.name.decode(),
                      attacker.name.decode(),
                      weapon,
                      'Yes' if headshot else 'No',
                      attacker.health,
                      attacker.position,
                      victim.position))
    d = DemoParser(sys.argv[1])

    def end():
        for idx, dt in enumerate(d.data_tables):
            print(idx, dt.net_table_name)

        print(d.data_tables[212])

    def change(entity, table, var_name, value):
        if var_name == 'm_vecOrigin':
            if type(entity).__name__ == 'Player':
                pass
                # print("Update position")
                # print(d.string_tables[0]['entries'])

    # d.add_callback('player_death', death)
    # f = open('./positions2', 'wb')
    # d.add_callback('change', change)
    # d.add_callback('end', end)
    #import cProfile
    #cProfile.run('d.parse()', 'cprof21')
    d.parse()
