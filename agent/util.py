import os
import time
import io
import base64
from PIL import ImageDraw, ImageGrab
from pywinauto import Desktop

desktop = Desktop(backend="uia")


def get_screenshot():
    screenshot = ImageGrab.grab()
    return screenshot


def encode_image(image):
    # encode image to base64 string
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


def save_screenshot(screenshot, path):
    screenshot.save(path, format="PNG")


def get_mllm_messages(instruction, base64_image):
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    },
                },
                {
                    "type": "text",
                    "text": instruction
                },
            ],
        },
    ]
    return messages


def get_element_info_from_position(x, y):
    # get the UI element info at the specified coordinates
    try:
        element = desktop.from_point(x, y)
        # get the rectangle coordinates of the element
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


def mark_screenshot(original_screenshot, coordinates, rect=None):
    screenshot = original_screenshot.copy()
    x, y = coordinates
    point = {"x": x, "y": y}

    if rect is not None:
        # create a drawable object
        draw = ImageDraw.Draw(screenshot)
        # draw the rectangle
        draw.rectangle(
            [(rect["left"], rect["top"]), (rect["right"], rect["bottom"])],
            outline="red",
            width=3  # line width
        )

    if point is not None:
        draw = ImageDraw.Draw(screenshot)

        # calculate the top-left and bottom-right coordinates of the solid circle
        radius = 3
        left = point["x"] - radius
        top = point["y"] - radius
        right = point["x"] + radius
        bottom = point["y"] + radius

        # draw the solid circle
        draw.ellipse(
            [(left, top), (right, bottom)],
            fill="red"
        )

        # add a larger hollow circle
        circle_radius = 18
        circle_left = point["x"] - circle_radius
        circle_top = point["y"] - circle_radius
        circle_right = point["x"] + circle_radius
        circle_bottom = point["y"] + circle_radius

        # draw the hollow circle
        draw.ellipse(
            [(circle_left, circle_top), (circle_right, circle_bottom)],
            outline="red",
            width=2
        )

    return screenshot


def record_in_md(directory_path, task_description, screenshot_path, output, external_reflection=None,
                 first_event=False):
    file_name = "inference_record.md"
    with open(os.path.join(directory_path, file_name), "a", encoding="utf-8") as file:
        if first_event:
            file.write(f"# Inference Task\n")
            file.write(f"**Description:** {task_description}\n\n")
        file.write(f"### {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        file.write(f"**Screenshot:**\n")
        file.write(f'<img src="{screenshot_path}" width="100%" height="100%">\n\n')
        file.write(f"**External Reflection:**\n{external_reflection}\n\n") if external_reflection else None
        file.write(f"**Output:**\n{output}\n\n")


def log(message, filename="agent.log"):
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    # open the file with UTF-8 encoding
    with open(filename, 'a', encoding='utf-8') as file:
        file.write(f"{current_time}\n{message}\n\n")


def print_in_green(message):
    print(f"\033[92m{message}\033[0m")
