class Key(object):
    def __init__(self, pin, char_abbrev, description):
        self.pin = pin
        self.char_abbrev = char_abbrev
        self.description = description

class Keys(list):
    def __init__(self):
        super().__init__()

    def add_key(self, key: Key):
        self.append(key)

    def keymap(self) -> tuple:
        return tuple([k.pin for k in self])


class ChordedKeyboard(object):
    def __init__(self, keys: Keys):
        if isinstance(keys, Keys):
            self.keys = keys
        else:
            raise TypeError(f"keys should be of type Keys\n\ttype was {type(keys)}")

    pressed = []
    last_chorded = ''

    _mode = "typing"


    _state = "chord"
    def t(self, text):
        print(text)

    def modifier(self, mod):
        print("modifier")

