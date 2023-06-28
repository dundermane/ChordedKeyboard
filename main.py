"""
Chorded Keyboard in Circuit Python
"""
import asyncio
import digitalio
import keypad
import board
import terminalio
from adafruit_display_text import bitmap_label
import neopixel
from chords import nasa_en as chord_map
"""
Monitor all keys using keypad module
"""
class ChordedKeyboard(object):
    def __init__(self, keys):
        if isinstance(keys, tuple):
            self.keys = keys
        else:
            raise TypeError("keys should be of type tuple")

    pressed = []
    last_chorded = ''

    _mode = "typing"


    _state = "chord"
    def key(self, text):
        print(text)

    def modifier(self, mod):
        print("modifier")


async def monitor_keys(keys, kb):
    with keypad.Keys(
            keys,
            value_when_pressed=False,
            pull=True
    ) as keys:

        hot = False
        while True:
            key_event = keys.events.get()
            if key_event is not None:
                if hot and key_event.released:
                    ## insert key action code here
                    print(f"keys that are pressed: {kb.pressed}")
                    try:
                        kb.last_chorded = chord_map[tuple(sorted(kb.pressed))]
                    except KeyError as err:
                        kb.last_chorded = "err"
                    kb.pressed.remove(key_event.key_number)
                    hot = False
                elif key_event.pressed:
                    kb.pressed.append(key_event.key_number)
                    hot = True
                elif key_event.released:
                    kb.pressed.remove(key_event.key_number)
                else:
                    print(f"unhandled key event")
            await asyncio.sleep(0)


"""
Display all things on display module
"""


async def display_ui(kb):

    while True:
        # Update this to change the text displayed.
        text = f"pressed: {str(kb.pressed)}\nlast:{kb.last_chorded}"
        # Update this to change the size of the text displayed. Must be a whole number.
        scale = 1

        text_area = bitmap_label.Label(terminalio.FONT, text=text, scale=scale)
        text_area.x = 20
        text_area.y = 80
        board.DISPLAY.show(text_area)
        await asyncio.sleep(0.2)



async def main():

    keymap = (
        board.A1,  # (N) Near
        board.A2,  # (C) Center
        board.A3,  # (F) Far
        board.D11,  # (I) Index
        board.D10,  # (M) Middle
        board.D9,  # (R) Ring
        board.D6  # (P) Pinky
    )

    thumb_common = digitalio.DigitalInOut(board.A0)
    thumb_common.direction = digitalio.Direction.OUTPUT
    thumb_common.value = False

    imrp_common = digitalio.DigitalInOut(board.D12)
    imrp_common.direction = digitalio.Direction.OUTPUT
    imrp_common.value = False

    kb = ChordedKeyboard(keymap)

    pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
    pixel.brightness = 1


    keys_task = asyncio.create_task(monitor_keys(keymap, kb))

    ui_task = asyncio.create_task(display_ui(kb))

    await asyncio.gather(keys_task, ui_task)


asyncio.run(main())

