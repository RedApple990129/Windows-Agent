from datetime import datetime
from pywinauto import Desktop


def get_current_time():
    return datetime.now().strftime('%Y-%m-%d_%H:%M:%S')


desktop = Desktop(backend="uia")


def get_element_info_at_position(x, y):
    """
    Get UI element info at specified coordinates
    """
    try:
        element = desktop.from_point(x, y)
        # Get element's rectangle coordinates
        rect = element.rectangle()

        return {
            "name": element.element_info.name,
            "coordinates": {
                "left": rect.left,
                "top": rect.top,
                "right": rect.right,
                "bottom": rect.bottom
            }
        }
    except Exception as e:
        print(f"Error occurs when get element from position: {e}")
        return None


def print_debug(string):
    import sys
    sys.stderr.write(string + "\n")


# Return 1 if the caps lock key is on; return 0 if it is off
def get_capslock_state():
    import ctypes
    hllDll = ctypes.WinDLL("User32.dll")
    VK_CAPITAL = 0x14
    return hllDll.GetKeyState(VK_CAPITAL)
