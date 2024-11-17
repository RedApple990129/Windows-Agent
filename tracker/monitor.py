import threading
import time
from enum import Enum
from pynput import keyboard, mouse
from pynput.keyboard import Key
from recorder import Recorder
from utils import *

WAIT_INTERVAL = 6  # 6s per wait
DOUBLE_CLICK_INTERVAL = 0.5  # 0.5s for double click

HOT_KEY = [
    ["alt", "tab"],  # Switch between running program windows
    ["alt", "f4"],  # Close current window or program
    ["cmd", 'd'],  # Show desktop
    ["cmd", 'e'],  # Open file explorer
    ["cmd", 'l'],  # Lock computer
    ["cmd", 'r'],  # Open run dialog
    ["cmd", 't'],  # Cycle through taskbar programs
    ["cmd", 'x'],  # Open advanced user menu (Start button right-click menu)
    ["cmd", "space"],  # Switch input method
    ["cmd", 'i'],  # Open Windows settings
    ["cmd", 'a'],  # Open action center
    ["cmd", 's'],  # Open search
    ["cmd", 'u'],  # Open accessibility settings
    ["cmd", 'p'],  # Open projection settings
    ["cmd", 'v'],  # Open clipboard history
    ["cmd", "tab"],  # Open task view
    ["shift", "delete"]  # Permanently delete selected items (bypass recycle bin)
]


def switch_caption(char):
    if char.isalpha() and get_capslock_state() == 1:  # Caps lock is on
        if char.islower():
            return char.upper()
        else:
            return char.lower()
    else:
        return char


class ActionType(Enum):
    CLICK = "click"
    RIGHT_CLICK = "right click"
    DOUBLE_CLICK = "double click"
    MOUSE_DOWN = "press"
    DRAG = "drag to"
    SCROLL = "scroll"
    KEY_DOWN = "press key"
    HOTKEY = "hotkey"
    TYPE = "type text"
    WAIT = "wait"
    FINISH = "finish"
    FAIL = "fail"


class Action:
    def __init__(self, action_type: ActionType, **kwargs):
        self.action_type = action_type
        self.kwargs = kwargs

    def __str__(self):
        str = f"{self.action_type.value}"
        if self.action_type == ActionType.CLICK or self.action_type == ActionType.RIGHT_CLICK or self.action_type == ActionType.MOUSE_DOWN or self.action_type == ActionType.DOUBLE_CLICK:
            # str += f" element: {self.kwargs['name']} at ({self.kwargs['x']}, {self.kwargs['y']})"
            str += f" ({self.kwargs['x']}, {self.kwargs['y']})"
        if self.action_type == ActionType.DRAG:
            str += f" ({self.kwargs['x']}, {self.kwargs['y']})"
        if self.action_type == ActionType.SCROLL:
            str += f" ({self.kwargs['dx']}, {self.kwargs['dy']})"
        if self.action_type == ActionType.KEY_DOWN:
            str += f" {self.kwargs['key']}"
        if self.action_type == ActionType.HOTKEY:
            str += f" ({self.kwargs['key1']}, {self.kwargs['key2']})"
        if self.action_type == ActionType.TYPE:
            str += f": {self.kwargs['text']}"
        return str

    def get_element(self):
        ele = self.kwargs.get('name')
        return ele if ele != "" else "Unknown"


class Monitor:
    def __init__(self, task):
        self.recorder = Recorder(task)
        self.type_buffer = TypeBuffer(self.recorder)  # How many keyboard operations have been executed consecutively
        self.timer = Timer(self.recorder, self.type_buffer)
        self.scroll_buffer = ScrollBuffer(self.recorder)
        self.keyboard_monitor = KeyboardMonitor(
            self.recorder, self.type_buffer, self.timer, self.scroll_buffer)
        self.mouse_monitor = MouseMonitor(
            self.recorder, self.type_buffer, self.timer, self.scroll_buffer)

    def start(self):
        self.keyboard_monitor.start()
        self.mouse_monitor.start()
        self.type_buffer.reset()
        self.timer.reset()

    def stop_without_md(self):
        self.keyboard_monitor.stop()
        self.mouse_monitor.stop()
        self.timer.stop()
        self.recorder.wait()

    def generate_md(self, task=None):
        self.recorder.generate_md(task)

    def stop(self):
        self.stop_without_md()
        self.generate_md()

    def finish(self):
        self.recorder.record_action(Action(ActionType.FINISH))
        self.stop()

    def finish_without_md(self):
        self.recorder.record_action(Action(ActionType.FINISH))
        self.stop_without_md()

    def fail(self):
        self.recorder.record_action(Action(ActionType.FAIL))
        self.stop()

    def discard_record(self):
        self.recorder.discard()


class Timer:
    def __init__(self, recorder: Recorder, type_buffer):
        self.timer_inner = None
        self.recorder = recorder
        self.type_buffer = type_buffer
        self.reset()

    def reset(self):
        if self.timer_inner:
            self.timer_inner.cancel()
        self.timer_inner = threading.Timer(
            WAIT_INTERVAL, self.save_wait)  # Start timing, execute save_wait after interval seconds
        self.timer_inner.start()

    def stop(self):
        if self.timer_inner:
            self.timer_inner.cancel()

    def save_wait(self):
        if not self.type_buffer.last_action_is_typing:
            self.recorder.record_action(Action(ActionType.WAIT))
        self.reset()


class HotKeyBuffer:
    def __init__(self):
        self.buffer = []

    def add(self, key):
        self.buffer.append(key)

    def pop(self):
        if len(self.buffer) > 0:
            self.buffer.pop()

    def reset(self):
        self.buffer.clear()


class TypeBuffer:
    def __init__(self, recorder: Recorder):
        self.recorder = recorder
        self.type_action_cnt = 0
        self.text = ""
        self.is_typing = False
        self.last_action_is_typing = False  # Whether the last action could be typing
        self.last_action_is_shift = False
        self.pre_saved_type_event = None  # for TYPE action
        self.events_buffer = []  # Buffer keyboard events before confirming typing

    def pre_save_type_event(self):
        self.pre_saved_type_event = self.recorder.get_event()

    def reset(self):
        # save buffer
        if self.is_typing and not self.is_empty():
            # At this time, there should be a pre_saved_type_event
            assert self.pre_saved_type_event is not None
            type_action = Action(ActionType.TYPE, text=self.text)
            self.pre_saved_type_event['action'] = type_action
            self.recorder.record_event(self.pre_saved_type_event)
        elif not self.is_typing:
            # self.recorder.save_all()
            # Record all previous operations that were cached
            for event in self.events_buffer:
                self.recorder.record_event(event)

        # reset type buffer
        self.text = ""
        self.is_typing = False
        self.last_action_is_typing = False
        self.last_action_is_shift = False
        self.pre_saved_type_event = None
        self.events_buffer.clear()

    def append(self, char):
        self.text += char
        if not self.is_typing:
            press_action = Action(ActionType.KEY_DOWN, key=char)
            # self.recorder.record(press_action)
            press_event = self.recorder.get_event(press_action)
            self.events_buffer.append(press_event)

    def add_type_related_action(self):
        # The typing operation is about to be added
        if len(self.text) >= 2 and not self.is_typing:
            self.is_typing = True  # Enter typing state
            self.events_buffer.clear()  # The previous recorded keyboard operations will be merged into TYPE, no need to record separately

    def backspace(self):
        if len(self.text) > 0:
            self.text = self.text[:-1]
            if not self.is_typing:
                backspace_action = Action(ActionType.KEY_DOWN, key="backspace")
                # self.recorder.record(backspace_action)
                backspace_event = self.recorder.get_event(backspace_action)
                self.events_buffer.append(backspace_event)
        else:
            self.reset()
            backspace_action = Action(ActionType.KEY_DOWN, key="backspace")
            self.recorder.record_action(backspace_action)

    def set_last_action_is_typing(self):
        self.last_action_is_typing = True

    def reset_last_action_is_typing(self):
        self.last_action_is_typing = False

    def set_last_action_is_shift(self):
        self.last_action_is_shift = True

    def reset_last_action_is_shift(self):
        self.last_action_is_shift = False

    def set_typing(self):
        self.is_typing = True

    def is_empty(self) -> bool:
        return len(self.text) == 0


class ScrollBuffer:
    def __init__(self, recorder: Recorder):
        self.recorder = recorder
        self.dx = 0
        self.dy = 0
        self.pre_saved_scroll_event = None
        # self.empty = self.pre_saved_scroll_event is None

    def is_empty(self):
        return self.pre_saved_scroll_event is None

    def reset(self):
        if not self.is_empty() and (self.dx != 0 or self.dy != 0):
            scroll_action = Action(ActionType.SCROLL, dx=self.dx, dy=self.dy)
            self.pre_saved_scroll_event['action'] = scroll_action
            self.recorder.record_event(self.pre_saved_scroll_event)
        self.dx = 0
        self.dy = 0
        self.pre_saved_scroll_event = None

    def new(self, dx, dy):
        self.dx = dx
        self.dy = dy
        self.pre_saved_scroll_event = self.recorder.get_event()

    def add_delta(self, dx, dy):
        self.dx += dx
        self.dy += dy


class KeyboardMonitor:
    def __init__(self, recorder: Recorder, type_buffer: TypeBuffer, timer: Timer, scroll_buffer: ScrollBuffer):
        self.recorder = recorder
        self.listener = keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release)
        self.type_buffer = type_buffer
        self.timer = timer
        self.scroll_buffer = scroll_buffer
        self.hotkey_buffer = HotKeyBuffer()

    def start(self):
        self.listener.start()

    def stop(self):
        self.listener.stop()

    def on_press(self, key: Key):
        try:
            # Keyboard operation triggers timer and scroll buffer reset
            self.timer.reset()
            self.scroll_buffer.reset()

            # Record whether this operation is related to typing
            if is_related_to_type(key):
                self.type_buffer.set_last_action_is_typing()
                self.type_buffer.add_type_related_action()
            else:
                self.type_buffer.reset_last_action_is_typing()

            # Record whether the last key pressed was the shift key
            if key == Key.shift:
                self.type_buffer.set_last_action_is_shift()
            else:
                self.type_buffer.reset_last_action_is_shift()

            record_hotkey = False
            # Determine hotkey operation
            self.hotkey_buffer.add(get_key_str(key))
            if self.hotkey_buffer.buffer in HOT_KEY:
                record_hotkey = True  # Should be recorded as a hotkey operation

            # Handle record operation
            if not is_related_to_type(key):  # Keys that cannot appear in typing scenarios
                self.type_buffer.reset()  # Before entering typing state, all previous operations must have been recorded, just save the text in the buffer
                if self.type_buffer.last_action_is_shift:
                    shift_action = Action(ActionType.KEY_DOWN, key="shift")
                    self.recorder.record_action(shift_action)
                hotkey_2 = get_ctrl_hotkey(key)
                if hotkey_2 is not None:
                    last_action = self.recorder.get_last_action()
                    if last_action is not None and last_action.action_type == ActionType.KEY_DOWN and (
                            last_action.kwargs['key'] == 'ctrl_l' or last_action.kwargs['key'] == 'ctrl_r'):
                        ctrl_hotkey_action = Action(
                            ActionType.HOTKEY, key1='Ctrl', key2=hotkey_2)
                        self.recorder.change_last_action(ctrl_hotkey_action)
                    else:
                        ctrl_hotkey_action = Action(
                            ActionType.HOTKEY, key1='Ctrl', key2=hotkey_2)
                        self.recorder.record_action(ctrl_hotkey_action)
                elif not record_hotkey:
                    key_name = get_key_str(key)
                    key_press_action = Action(
                        ActionType.KEY_DOWN, key=key_name)
                    self.recorder.record_action(key_press_action)
            elif not record_hotkey:  # Keys that may appear in typing scenarios
                if self.type_buffer.is_empty():  # Only characters can be the first element of the buffer
                    if hasattr(key, 'char'):
                        switched_char = switch_caption(key.char)
                        self.type_buffer.append(switched_char)
                        self.type_buffer.pre_save_type_event()  # Save observation when entering typing state
                    else:
                        # At this time, the buffer is empty, directly record special keys
                        key_name = get_key_str(key)
                        key_press_action = Action(
                            ActionType.KEY_DOWN, key=key_name)
                        self.recorder.record_action(key_press_action)
                else:
                    # Just throw into the buffer
                    if key == Key.backspace:
                        self.type_buffer.backspace()
                    elif key == Key.space:
                        self.type_buffer.append(' ')
                    elif hasattr(key, 'char'):
                        switched_char = switch_caption(key.char)
                        self.type_buffer.append(switched_char)

            if record_hotkey:
                last_action = self.recorder.get_last_action()
                if last_action.action_type == ActionType.KEY_DOWN and last_action.kwargs['key'] == \
                        self.hotkey_buffer.buffer[0]:
                    ctrl_hotkey_action = Action(
                        ActionType.HOTKEY, key1=self.hotkey_buffer.buffer[0], key2=self.hotkey_buffer.buffer[1])
                    self.recorder.change_last_action(ctrl_hotkey_action)
                else:
                    ctrl_hotkey_action = Action(
                        ActionType.HOTKEY, key1=self.hotkey_buffer.buffer[0], key2=self.hotkey_buffer.buffer[1])
                    self.recorder.record_action(ctrl_hotkey_action)
        except AttributeError:
            print_debug("error!")

    def on_release(self, key: Key):
        self.hotkey_buffer.pop()


class LastClick:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.time = 0
        self.button = mouse.Button.left
        self.element_name = ""

    def update(self, x, y, button, element_name):
        self.x = x
        self.y = y
        self.time = time.time()
        self.button = button
        self.element_name = element_name


class MouseMonitor:
    def __init__(self, recorder: Recorder, type_buffer: TypeBuffer, timer: Timer, scroll_buffer: ScrollBuffer):
        self.recorder = recorder
        self.listener = mouse.Listener(
            on_click=self.on_click, on_scroll=self.on_scroll, on_move=self.on_move)
        self.type_buffer = type_buffer
        self.timer = timer
        self.scroll_buffer = scroll_buffer
        self.last_click = LastClick()
        self.pre_saved_drag_event = None

    def start(self):
        self.listener.start()

    def stop(self):
        self.listener.stop()

    def on_click(self, x, y, button, pressed):
        self.timer.reset()
        self.type_buffer.reset_last_action_is_typing()
        self.type_buffer.reset_last_action_is_shift()
        self.scroll_buffer.reset()
        if pressed:
            # Mouse click triggers information update
            element = get_element_info_at_position(x, y)  # Get UI element info at mouse click position
            self.type_buffer.reset()  # reset type buffer
            # Save observation when mouse is pressed, for possible drag operation
            self.pre_saved_drag_event = self.recorder.get_event()

            delta_time = time.time() - self.last_click.time
            if delta_time < DOUBLE_CLICK_INTERVAL and x == self.last_click.x and y == self.last_click.y:
                # Double click
                last_action = self.recorder.get_last_action()
                if last_action is not None and last_action.action_type == ActionType.CLICK:
                    double_click_action = Action(
                        ActionType.DOUBLE_CLICK, x=x, y=y, name=last_action.kwargs['name'])
                    self.recorder.change_last_action(double_click_action)
            else:
                # Click
                if button == mouse.Button.left:
                    click_action = Action(
                        ActionType.CLICK, x=x, y=y, name=element['name'])
                    self.recorder.record_action(
                        click_action, element['coordinates'])
                elif button == mouse.Button.right:
                    click_action = Action(
                        ActionType.RIGHT_CLICK, x=x, y=y, name=element['name'])
                    self.recorder.record_action(
                        click_action, element['coordinates'])
                else:
                    print_debug(f"Unknown button {button}")

            self.last_click.update(x, y, button, element['name'])

        else:  # released
            if x != self.last_click.x or y != self.last_click.y:  # Mouse dragged
                last_action = self.recorder.get_last_action()
                if last_action.action_type == ActionType.CLICK:  # Previous operation was a click operation
                    press_action = Action(ActionType.MOUSE_DOWN, x=self.last_click.x,
                                          y=self.last_click.y, name=self.last_click.element_name)
                    self.recorder.change_last_action(
                        press_action)  # Modify the previous click operation to press operation
                    # Record drag operation
                    drag_action = Action(ActionType.DRAG, x=x, y=y)
                    self.pre_saved_drag_event['action'] = drag_action
                    self.recorder.record_event(self.pre_saved_drag_event)
            else:  # Normal click
                pass

    def on_move(self, x, y):
        # print(f"Mouse moved to {(x, y)}")
        pass

    def on_scroll(self, x, y, dx, dy):
        self.timer.stop()  # Close timer during scrolling to avoid recording wait operations during scrolling
        self.type_buffer.reset_last_action_is_typing()
        self.type_buffer.reset_last_action_is_shift()
        self.type_buffer.reset()
        if self.scroll_buffer.is_empty():
            self.scroll_buffer.new(dx, dy)
        else:
            self.scroll_buffer.add_delta(dx, dy)


def is_related_to_type(key):
    if isinstance(key, Key):
        return key in [Key.shift, Key.space, Key.caps_lock, Key.backspace]
    elif isinstance(key, keyboard.KeyCode):
        return key.char is not None and ord(key.char) > 31
    return False


def get_ctrl_hotkey(key):
    if isinstance(key, keyboard.KeyCode) and key.char is not None and ord(key.char) <= 31:
        return chr(ord('@') + ord(key.char))
    return None


def get_key_str(key):
    if isinstance(key, Key):
        key_str = str(key)
        if "ctrl" in key_str:
            return "ctrl"
        if "shift" in key_str:
            return "shift"
        if "alt" in key_str:
            return "alt"
        if "cmd" in key_str:
            return "cmd"
        return key_str[4:]
    elif isinstance(key, keyboard.KeyCode):
        return key.char
