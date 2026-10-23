import json

class Data:
    def __init__(self):
        self.data = self._load() #A dictionary

    def _load(self) -> dict:
        """Load data from the file data.json"""
        try:
            with open("data.json", "r") as file:
                try:
                    data = json.load(file)
                except Exception as e:
                    print('Error when loading data:', e)
                    return {}
                return data
        except FileNotFoundError:
            return {}

    def _dump(self):
        """Save data to the file data.json"""
        with open("data.json", "w") as file:
            json.dump(self.data, file, indent=4)

    def save(self, key, data):
        """Save the data with the key, if key already exists, data is overwritten"""
        self.data[key] = data
        self._dump()

    def get(self, key, default = None):
        """Get data with the key, store default if key doesn't exist"""
        data = self.data.get(key)
        if data is None:
            data = default
            self.save(key, data)
        
        return data