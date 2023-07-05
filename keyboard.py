
import asyncio
import keypad
from chords import nasa_en as chord_map


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
        self.mode = "<NORM>"

    pressed = []
    last_chorded = ''

    key_subs = []

    _mode = "typing"


    _state = "chord"
    def on_key(self, key_tuple):
        for sub in self.key_subs:
            sub.on_key(key_tuple)
        self.mode = key_tuple[1]
        self.last_chorded = key_tuple[0]

    def widget_sub(self, subscriber):
        if not callable(subscriber.on_key):
            raise Exception(f"{subscriber} Cant subscribe because on_key non-callable function")
        self.key_subs.append(subscriber)


    def t(self, text):
        print(text)

    def modifier(self, mod):
        print("modifier")

    def switches_to_key_tuple(self, switches):
        try:
            switches = tuple(sorted(switches))
            return chord_map[self.mode][switches]
        except Exception as err:
            raise KeyError(f"Keymap Error, mode: {self.mode}  switches: {switches}")

    def monitor_keys(self):
        with keypad.Keys(
                self.keys.keymap(),
                value_when_pressed=False,
                pull=True
        ) as keys:

            hot = False
            while True:
                key_event = keys.events.get()
                if key_event is not None:
                    if hot and key_event.released:
                        ## insert key action code here
                        try:
                            self.on_key(self.switches_to_key_tuple(self.pressed))
                        except KeyError as err:
                            self.last_chorded = "err"
                            print(KeyError, err)
                        self.pressed.remove(key_event.key_number)
                        hot = False
                    elif key_event.pressed:
                        self.pressed.append(key_event.key_number)
                        hot = True
                    elif key_event.released:
                        self.pressed.remove(key_event.key_number)
                    else:
                        print(f"unhandled key event")
                await asyncio.sleep(0)


