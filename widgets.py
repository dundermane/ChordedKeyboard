from __future__ import annotations
import asyncio
import displayio
import terminalio
import sys

import adafruit_logging as logging

from adafruit_display_text import bitmap_label, label
from adafruit_display_shapes.rect import Rect
from keyboard import Keys, Key, ChordedKeyboard

__old_stdout__ = sys.stdout


class WidgetBase(displayio.Group):
    def __init__(self):
        super().__init__()

    def update(self):
        """A function that gets called on every ui refresh (often)"""
        raise NotImplementedError(f"{type(self)} MUST override 'update'")

    def once(self, page: PageBase):
        """A function that gets called once at the entrance of the widget onto the dancefloor"""
        raise NotImplementedError(f"{type(self)} MUST override 'once'")



class PageBase(list):
    def __init__(self, page_name, page_description):
        super().__init__()
        self.page_name = page_name
        self.page_description = page_description
        self._widgets = []
        self._onD0 = None
        self._onD1 = None
        self._onD2 = None

    def update(self):
        for wid in self._widgets:
            wid.update()

    def add_widget(self, widget: WidgetBase):
        # add widget to the widgets (for updating)
        self._widgets.append(widget)
        # add widgets to the displayio Group
        self.append(widget)

    def into(self, group: displayio.Group):

        for w in range(len(group)):
            group.pop()
        for w in self:
            w.once(self)
            group.append(w)


    @property
    def onD0(self):
        return self._onD0

    @onD0.setter
    def onD0(self, page: PageBase):
        self._onD0 = page

    @property
    def onD1(self):
        return self._onD1

    @onD1.setter
    def onD1(self, page: PageBase):
        self._onD1 = page

    @property
    def onD2(self):
        return self._onD2

    @onD2.setter
    def onD2(self, page: PageBase):
        self._onD2 = page



class SpiffChorderUIWidget(WidgetBase):
    def __init__(self,
                 kb: ChordedKeyboard,
                 logger: logging.Logger = logging.Logger("default")):
        super().__init__()

        self._logger = logger

        self._kb = kb
        for i, key in enumerate([(self._kb.keys.index(kr), kr.char_abbrev) for kr in self._kb.keys[0:3]]):
            x = 15 + (i * 26)
            y = 20
            k = self.KeyRep(*key, x=x, y=y)
            self.append(k)

        for i, key in enumerate([(self._kb.keys.index(kr), kr.char_abbrev) for kr in self._kb.keys[3:7]]):
            x = 120 + (i * 26)
            y = 20
            k = self.KeyRep(*key, x=x, y=y)
            self.append(k)

    class KeyRep(displayio.Group):
        def __init__(self, n_key, label_text, *args, **kwargs):
            self.pressed = False
            self.n_key = n_key
            self._label_text = label_text

            self._rect = Rect(0, 0, 20, 20, stroke=3, fill=0x0000FF, outline=0x0000FF)
            self._label = bitmap_label.Label(terminalio.FONT, text=label_text, scale=2, color=0x000000, x=4, y=10)

            super().__init__(*args, **kwargs)

            self.append(self._rect)
            self.append(self._label)

        def set_pressed(self):
            self.pressed = True
            self._rect.outline = 0x00FF00

        def reset_pressed(self):
            self.pressed = False
            self._rect.outline = 0x0000FF

    def update(self):
        for ki, kr in enumerate(iter(self)):
            if ki in self._kb.pressed:
                kr.set_pressed()
            else:
                kr.reset_pressed()

    def once(self, page: PageBase):
        pass


class DebugWidget(WidgetBase):
    def __init__(self):
        super().__init__()
        self._dbg_area = bitmap_label.Label(terminalio.FONT, text="text", scale=1)
        self._dbg_area.x = 20
        self._dbg_area.y = 80
        self.append(self._dbg_area)
        self.handler = self.DebugHandler(self._dbg_area)

    class DebugHandler(logging.Handler):
        def __init__(self, debug_label: bitmap_label.Label):
            super().__init__()
            self._debug_label = debug_label

        def emit(self, record):
            self._debug_label.text = record.msg

    def update(self):
        pass

    def once(self, page: PageBase):
        pass


class TypistGameWidget(WidgetBase):
    def __init__(self):
        super().__init__()
        self._next_word = label.Label(terminalio.FONT,
                                      text="automobile",
                                      scale=2,
                                      anchor_point=(0.5, 0.0),
                                      anchored_position=(120, 45))
        self._next_letter_highlight = Rect(self._next_word[0][2].x,
                                           self._next_word[0][2].height + 4,
                                           self._next_word[0][2].width * 6,
                                           2,
                                           fill=0xFFFFFF)
        self._next_word[0].append(self._next_letter_highlight)

        self.append(self._next_word)

    def update(self):
        pass

    def once(self, page: PageBase):
        pass


class NavigationWidget(WidgetBase):
    def __init__(self):
        super().__init__()
        self._d0_label = label.Label(terminalio.FONT,
                                     text="D0",
                                     scale=1,
                                     anchor_point=(0.0, 0.5),
                                     label_direction="DWR",
                                     anchored_position=(0, 115))
        self._d1_label = label.Label(terminalio.FONT,
                                     text="D1",
                                     scale=1,
                                     anchor_point=(0.0, 0.5),
                                     label_direction="DWR",
                                     anchored_position=(0, 68))
        self._d2_label = label.Label(terminalio.FONT,
                                     text="D2",
                                     scale=1,
                                     anchor_point=(0.0, 0.5),
                                     label_direction="DWR",
                                     anchored_position=(0, 20))

        self.append(self._d0_label)
        self.append(self._d1_label)
        self.append(self._d2_label)


    def update(self):
        pass

    def once(self, page: PageBase):
        """do a update on the names of all the nav"""
        try:
            self._d0_label.text = page.onD0.page_name
        except Exception as err:
            print("no page name for D0 found")
            self._d0_label.text = ""
        try:
            self._d1_label.text = page.onD1.page_name
        except Exception as err:
            print("no page name for D0 found")
            self._d1_label.text = ""
        try:
            self._d2_label.text = page.onD2.page_name
        except Exception as err:
            print("no page name for D0 found")
            self._d2_label.text = ""
