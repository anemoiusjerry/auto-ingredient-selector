import json

class Configer:

    def read_config(self):
        # Load config
        with open("config.json") as json_file:
            config = json.load(json_file)
        return config

    def write_config(self):
        """ Ideally config should only be saved when:
            - closing window
            - run button pressed
        """
