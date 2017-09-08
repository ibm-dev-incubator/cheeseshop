class BaseEntity:

    def __init__(self, parser, index, class_id, serial, props):
        self.parser = parser
        self.index = index
        self.class_id = class_id
        self.serial = serial
        self.props = props

    def update_prop(self, table, key, value):
        self.props[table][key] = value

    def get_prop(self, table, var):
        return self.props[table][var]
