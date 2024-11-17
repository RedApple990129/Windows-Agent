import json
import multiprocessing

from PIL import Image, ImageDraw

from capturer import *
from fs import *
from utils import *

MARK_IMAGE = False


class Recorder:
    def __init__(self, task=None, buffer_len=1, directory="events"):
        self.pool = multiprocessing.Pool()
        self.task = task
        self.buffer_len = buffer_len
        self.directory = directory
        self.screenshot_dir = os.path.join(directory, "screenshot")
        self.buffer = []  # event buffer
        self.saved_cnt = 0
        self.timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Ensure directories exist
        ensure_folder(self.directory)
        ensure_folder(self.screenshot_dir)
        # Hide directory
        hide_folder(self.directory)
        # Generate filename prefix
        if self.task is not None:
            index = self.task.id
            prefix = f"task{index}" if index != 0 else "free_task"
        else:
            prefix = "events"
        # Generate filename
        self.event_filename = os.path.join(
            self.directory, f"{prefix}_{self.timestamp_str}.jsonl")
        self.md_filename = os.path.join(
            self.directory, f"{prefix}_{self.timestamp_str}.md")

        self.recent_screen = RecentScreen()

        self.screenshot_f_list = []

    def get_event(self, action=None):
        timestamp = get_current_time()
        screenshot = self.recent_screen.get()
        event = {
            'timestamp': timestamp,
            'action': action,
            'screenshot': screenshot,
        }
        return event

    def record_event(self, event, rect=None):
        self.buffer.append((event, rect))
        if len(self.buffer) > self.buffer_len:
            ev, rec = self.buffer.pop(0)
            self.save(ev, rec)

    def record_action(self, action, rect=None):
        event = self.get_event(action)
        self.record_event(event, rect)

    def get_last_action(self):
        if self.buffer and len(self.buffer) > 0:
            event, _ = self.buffer[-1]
            return event['action']
        else:
            return None

    def change_last_action(self, action):
        if self.buffer:
            event, rect = self.buffer.pop()
            event['action'] = action
            self.buffer.append((event, rect))
        else:
            print("WARNING: No record to change in the buffer!")

    def save(self, event, rect):
        self.saved_cnt += 1
        timestamp = event['timestamp'].replace(':', '').replace('-', '')
        action = event['action']
        screenshot_filename = os.path.join(
            self.screenshot_dir, f"{timestamp}_{self.saved_cnt}.png")

        point = {"x": action.kwargs.get('x'), "y": action.kwargs.get('y')}
        if None in point.values():
            point = None

        # Async save screenshot
        self.pool.apply_async(
            save_screenshot, (screenshot_filename, event['screenshot'], rect, point))

        event['screenshot'] = screenshot_filename
        event['action'] = str(action)
        event['element'] = action.get_element()
        event['rect'] = rect
        with open(self.event_filename, 'a', encoding='utf-8') as f:
            json.dump(event, f, ensure_ascii=False)
            f.write('\n')

        self.screenshot_f_list.append(screenshot_filename)

    def wait(self):
        # Save all buffered events
        for event, rect in self.buffer:
            self.save(event, rect)
        # Close process pool
        self.pool.close()
        self.pool.join()

    def generate_md(self, task=None):
        if task is not None:
            self.task = task  # Reset task

        prompt = '''Given the screenshot as below. What's the next step that you will do to help with the task?'''

        with open(self.event_filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        markdown_content = []
        if self.task is not None:
            index = self.task.id
            description = self.task.description
            level = self.task.level

            if index == 0:
                markdown_content.append(f'# Free Task\n')
            else:
                markdown_content.append(f'# Task {index}\n')

            markdown_content.append(f'**Description:** {description}\n\n')
            markdown_content.append(f'**Level:** {level}\n\n')
        else:
            markdown_content.append(f'# Non task-oriented events\n')

        for line in lines:
            event = json.loads(line.strip())
            timestamp = event.get('timestamp', '')
            action = event.get('action', '')
            screenshot_path = event.get('screenshot', '')
            screenshot_path = '\\'.join(screenshot_path.split(
                '\\')[1:])  # remove the first directory

            markdown_content.append(f'### {timestamp}\n')
            markdown_content.append(f'**Input:** \n\n{prompt}\n\n')
            markdown_content.append(
                f'<img src="{screenshot_path}" width="50%" height="50%">\n\n')
            markdown_content.append(f'**Output:** \n\n{action}\n\n')

        # Write content to Markdown file
        with open(self.md_filename, 'w', encoding='utf-8') as md_file:
            md_file.writelines(markdown_content)

    def discard(self):
        # Delete all record files
        delete_file(self.event_filename)
        # markdown may not be recorded, but not a problem
        delete_file(self.md_filename)
        for f in self.screenshot_f_list:
            delete_file(f)


def save_screenshot(save_filename, screenshot, rect=None, point=None):
    # Create image from buffer
    image = Image.frombuffer(
        'RGB',
        screen_size,
        screenshot, 'raw', 'BGRX', 0, 1
    )

    if MARK_IMAGE:
        mark_image(image, rect, point)

    # Save image
    image.save(save_filename)


def mark_image(image, rect, point):
    if rect is not None:
        # Create a drawable object
        draw = ImageDraw.Draw(image)
        # Draw rectangle
        draw.rectangle(
            [(rect["left"], rect["top"]), (rect["right"], rect["bottom"])],
            outline="red",
            width=3  # line width
        )

    if point is not None:
        draw = ImageDraw.Draw(image)

        # Calculate circle's top-left and bottom-right coordinates
        radius = 6
        left = point["x"] - radius
        top = point["y"] - radius
        right = point["x"] + radius
        bottom = point["y"] + radius

        # Draw circle
        draw.ellipse(
            [(left, top), (right, bottom)],
            fill="red"
        )
