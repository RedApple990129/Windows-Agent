import threading
import time

import pyautogui
import win32con
import win32gui
import win32ui

screen_size = pyautogui.size()


class ScreenCapturer:
    def __init__(self):
        self.hwindow = win32gui.GetDesktopWindow()

    def capture(self):
        # dc: device context
        window_dc = win32gui.GetWindowDC(self.hwindow)
        img_dc = win32ui.CreateDCFromHandle(window_dc)
        mem_dc = img_dc.CreateCompatibleDC()
        # Create a bitmap object
        screenshot = win32ui.CreateBitmap()
        # Create a bitmap compatible with the device context and set its width and height
        screenshot.CreateCompatibleBitmap(img_dc, screen_size[0], screen_size[1])
        # Select the bitmap into the memory device context
        mem_dc.SelectObject(screenshot)
        # Perform a bit block transfer
        mem_dc.BitBlt((0, 0), screen_size, img_dc, (0, 0), win32con.SRCCOPY)
        # screenshot: bitmap byte stream
        bits = screenshot.GetBitmapBits(True)
        # Release resources
        mem_dc.DeleteDC()
        win32gui.ReleaseDC(self.hwindow, window_dc)
        win32gui.DeleteObject(screenshot.GetHandle())
        return bits


capturer = ScreenCapturer()


class RecentScreen:
    def __init__(self, capture_interval=0.1):
        self.screenshot = capturer.capture()
        self.capture_interval = capture_interval
        self.lock = threading.Lock()
        self.refresh_thread = threading.Thread(target=self.refreshing)
        self.refresh_thread.daemon = True
        self.refresh_thread.start()

    def refreshing(self):
        while True:
            screenshot = capturer.capture()
            with self.lock:
                self.screenshot = screenshot
            time.sleep(self.capture_interval)

    def get(self):
        with self.lock:
            return self.screenshot
