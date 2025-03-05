

class BabelParam:
    def __init__(self, name, value, target=None):
        self.name = name
        self.value = value
        self.target = target



class BabelParams:
    def __init__(self):
        self._params = []
    def get_all(self):
        return self._params
    def set_param(self, name, value, target=None):
        for i in self._params:
            if i.name == name:
                i.value = value
                return
        self._params.append(BabelParam(name, value, target))

    def get_param(self, name):
        for i in self._params:
            if i.name == name:
                return i.value
        return None
    
    def get_target(self, name):
        for i in self._params:
            if i.name == name:
                return i.target
        return None
    