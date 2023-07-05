"""
Chorded Keyboard in Circuit Python
"""
import asyncio
import digitalio
import keypad
import board
import terminalio
import displayio
from adafruit_display_text import bitmap_label, label
from adafruit_display_shapes.rect import Rect
import adafruit_logging as logging
import neopixel
from chords import nasa_en as chord_map
from widgets import WidgetBase, SpiffChorderUIWidget, DebugWidget, TypistGameWidget, NavigationWidget, PageBase, LastChordedWidget
from keyboard import ChordedKeyboard, Keys, Key


"""
Display all things on display module
"""


async def display_ui(main_group, current_page, k0, k12):

    while True:
        await asyncio.sleep(0.1)
        print("lets go into")
        current_page.into(main_group)
        while True:

            k12_event = k12.events.get()
            if k12_event is not None:
                if k12_event.pressed:
                    if k12_event.key_number == 0:
                        if isinstance(current_page.onD1, PageBase):
                            current_page = current_page.onD1
                            break
                        elif callable(current_page.onD1):
                            current_page.onD1()
                            break

                    elif k12_event.key_number == 1:
                        if isinstance(current_page.onD2, PageBase):
                            current_page = current_page.onD2
                            break
                        elif callable(current_page.onD2):
                            current_page.onD2()
                            break

            k0_event = k0.events.get()
            if k0_event is not None:
                if k0_event.pressed:
                    if isinstance(current_page.onD0, PageBase):
                        current_page = current_page.onD0
                        break
                    elif callable(current_page.onD0):
                        current_page.onD0()
                        break

            current_page.update()
            # Update this to change the text displayed.
            board.DISPLAY.show(main_group)

            await asyncio.sleep(0.1)



def set_low(pin_name):
    pin = digitalio.DigitalInOut(pin_name)
    pin.direction = digitalio.Direction.OUTPUT
    pin.value = False
    return pin


async def main():

    kb_keys = Keys()
    kb_keys.add_key(Key(board.A1, "N", "Near"))
    kb_keys.add_key(Key(board.A2, "C", "Center"))
    kb_keys.add_key(Key(board.A3, "F", "Far"))
    kb_keys.add_key(Key(board.D11, "I", "Index"))
    kb_keys.add_key(Key(board.D10, "M", "Middle"))
    kb_keys.add_key(Key(board.D9, "R", "Ring"))
    kb_keys.add_key(Key(board.D6, "P", "Pinky"))

    # Set up keyboard
    kb = ChordedKeyboard(kb_keys)



    # Set up debug widget.  Will be used to debug
    debug_widget = DebugWidget()
    logger = logging.Logger("main")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(debug_widget.handler)

    # Set up keyboard on-screen representation
    key_reps = SpiffChorderUIWidget(kb, logger=logger)

    # Set up typing game
    game_widget = TypistGameWidget(kb)

    # Set up navigation
    nav_widget = NavigationWidget()

    # Set up "last chorded" widget
    last_chorded_widget = LastChordedWidget(kb)

    # Set up main page
    start_page = PageBase("Home", "This is a page where you start")
    # start_page.add_widget(debug_widget)
    start_page.add_widget(key_reps)
    start_page.add_widget(nav_widget)
    start_page.add_widget(last_chorded_widget)

    game_page = PageBase("Game", "A practice game to up the WPM\'s")
    game_page.add_widget(key_reps)
    game_page.add_widget(game_widget)
    game_page.add_widget(nav_widget)

    start_page.onD2 = game_page
    game_page.onD0 = start_page

    thumb_common = set_low(board.A0)
    imrp_common = set_low(board.D12)

    # pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
    # pixel.brightness = 1

    ## Making the only group that can display widgets.
    # Apparently there's some "feature" that only allows a group to be added to one group.
    # You can't add the same group to multiple other groups.  So we'll just add all of them to main_group
    main_group = displayio.Group()

    # set up the front keys to pass into the display_ui
    k0 = keypad.Keys(
        (board.D0,),
        value_when_pressed=False,
        pull=True
    )
    k12 = keypad.Keys(
            (board.D1, board.D2),
            value_when_pressed=True,
            pull=True
    )

    keys_task = asyncio.create_task(kb.monitor_keys())
    ui_task = asyncio.create_task(display_ui(main_group, start_page, k0, k12))
    await asyncio.gather(keys_task, ui_task)

asyncio.run(main())

