from __future__ import annotations
import asyncio
import displayio
import terminalio
import sys
import random

from words import __word_list__

import adafruit_logging as logging

from adafruit_display_text import bitmap_label, label
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.polygon import Polygon

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
    def onD0(self, cb):
        self._onD0 = cb

    @property
    def onD1(self):
        return self._onD1

    @onD1.setter
    def onD1(self, cb):
        self._onD1 = cb

    @property
    def onD2(self):
        return self._onD2

    @onD2.setter
    def onD2(self, cb):
        self._onD2 = cb


class SpiffChorderUIWidget(WidgetBase):
    def __init__(self,
                 kb: ChordedKeyboard,
                 logger: logging.Logger = logging.Logger("default")):
        super().__init__()

        self._logger = logger

        self._kb = kb
        for i, key in enumerate([(self._kb.keys.index(kr), kr.char_abbrev) for kr in self._kb.keys[0:3]]):
            x = 20 + (i * 26)
            y = 15
            k = self.KeyRep(*key, x=x, y=y)
            self.append(k)

        for i, key in enumerate([(self._kb.keys.index(kr), kr.char_abbrev) for kr in self._kb.keys[3:7]]):
            x = 125 + (i * 26)
            y = 15
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


def splash_frame(n):
    return Rect(15, 10, 210, 115, fill=0x00AAAA)


class TypistGameWidget(WidgetBase):
    def __init__(self, kb: ChordedKeyboard):
        super().__init__()
        self._kb = kb
        self._intro_splash = displayio.Group()
        self._intro_splash.append(splash_frame(1))
        splash_label = bitmap_label.Label(terminalio.FONT,
                                          text="Get ready for a cool game!\n\nTry to type the word! thats IT!",
                                          scale=1,
                                          x=30,
                                          y=40,
                                          color=0x000000)
        self._intro_splash.append(splash_label)

        self._word_group = displayio.Group()
        self._word_label = label.Label(terminalio.FONT,
                                       text="",
                                       scale=2,
                                       anchor_point=(0.5, 0.0),
                                       anchored_position=(120, 45))

        self.level = 0
        self.current_letter = 0
        self._new_word()

        self._highlighter = Rect(self._word_label.x + self._word_label[0][0].x,
                                 self._word_label.y + self._word_label[0][0].height + 10,
                                 self._word_label[0][0].width * 10,
                                 2,
                                 fill=0xFFFFFF)

        for letter in self._word_label[0]:
            print(f"label x: {letter.x * self._word_label.scale}")
        self._highlighter.hidden = False

        self._word_group.append(self._word_label)
        self._word_group.append(self._highlighter)
        # self._new_word()

        self.append(self._word_group)
        self._word_label.hidden = True

        self.append(self._intro_splash)

        self._sequential = self._close_splash
        self._next_sequence_name = "Ok"

        kb.widget_sub(self)


    def _highlight(self, n):
        try:
            self._highlighter.x = self._word_label.x + (self._word_label[0][n].x * self._word_label.scale)
            self._highlighter.y = self._word_label.y + self._word_label[0][n].height + 10
            self._highlighter.hidden = False

        except IndexError as err:
            print(f"ERROR\nindex: {n}\nword length: {len(self._word_label[0])}")
            raise err

    def _hide_highlight(self):
        self._highlighter.hidden = True

    def _new_word(self):
        wl = __word_list__[self.level]
        word = wl[random.randrange(0, len(wl))]
        self._word_label.text = word
        return word

    def _close_splash(self, page=None):

        self._intro_splash.hidden = True
        self._word_label.hidden = False
        self._next_sequence_name = "next"
        self._sequential = self._next_word

    def _next_word(self, page=None):
        self._word_label.hidden = False
        self.current_letter = 0
        self._new_word()

    def update(self):
        pass

    def on_key(self, char_tuple):
        print(f"char: {char_tuple[0]}")
        if char_tuple[0] == self._word_label.text[self.current_letter]:
            self.current_letter += 1
            if self.current_letter >= len(self._word_label.text):
                self.current_letter = 0
                self._new_word()
        self._highlight(self.current_letter)

    def once(self, page: PageBase):
        nav = list(filter(lambda w: isinstance(w, NavigationWidget), page))
        nav[0]._d2_label.text = self._next_sequence_name
        page.onD2 = lambda: self._sequential(page=page)


class NavigationWidget(WidgetBase):
    def __init__(self):
        super().__init__()

        self._d0_label = label.Label(terminalio.FONT,
                                     text="",
                                     scale=1,
                                     anchor_point=(0.0, 0.5),
                                     label_direction="DWR",
                                     anchored_position=(0, 20))
        self._d1_label = label.Label(terminalio.FONT,
                                     text="",
                                     scale=1,
                                     anchor_point=(0.0, 0.5),
                                     label_direction="DWR",
                                     anchored_position=(0, 68))
        self._d2_label = label.Label(terminalio.FONT,
                                     text="",
                                     scale=1,
                                     anchor_point=(0.0, 0.5),
                                     label_direction="DWR",
                                     anchored_position=(0, 115))

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
            # self._d0_label.text = ""
        try:
            self._d1_label.text = page.onD1.page_name
        except Exception as err:
            print("no page name for D1 found")
            # self._d1_label.text = ""
        try:
            self._d2_label.text = page.onD2.page_name
        except Exception as err:
            print("no page name for D2 found")
            # self._d2_label.text = ""


class LastChordedWidget(WidgetBase):
    def __init__(self, kb):
        super().__init__()

        char_group = displayio.Group(x=180, y=55)
        self._char_frame = Rect(-30, -5, 65, 70, outline=0xFF0000)
        self._char_label = bitmap_label.Label(terminalio.FONT,
                                              text="",
                                              scale=5,
                                              anchor_point=(0.0, 0.0),
                                              anchored_position=(0, 0),
                                              color=0xFFFFFF)
        last_keyed_label = bitmap_label.Label(terminalio.FONT,
                                                    text="last key",
                                                    scale=1,
                                                    label_direction="DWR",
                                                    anchor_point=(0.0, 0.0),
                                                    anchored_position=(-25, 10),
                                                    color=0xFFFFFF)
        char_group.append(self._char_frame)
        char_group.append(last_keyed_label)
        char_group.append(self._char_label)
        self.append(char_group)
        kb.widget_sub(self)

        self._anim_on_key = 0x0

    def update(self):

        if self._anim_on_key > 0:
            self._char_frame.outline = self._anim_on_key
            self._anim_on_key -= 0x4000
            print(f"anim: {self._anim_on_key}")

        else:
            self._char_frame.outline = 0xFF0000


    def once(self, page: PageBase):
        pass

    def on_key(self, char):
        self._char_label.text = char[0]
        self._anim_on_key = 0xF000
        print(f"char label h: {self._char_label.height} w: {self._char_label.width}")
