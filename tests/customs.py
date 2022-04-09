
class CustomEntity:
    def __init__(self):
        self.result_dict = dict()

    def set_custom_field(self, field_id, value):
        if 'custom_fields' not in self.result_dict:
            self.result_dict['custom_fields'] = list()
        self.result_dict['custom_fields'].append({'id': field_id, 'values': value})

    def set_field(self, fields_name, value):
        self.result_dict[fields_name] = value
