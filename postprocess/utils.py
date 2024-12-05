import os
import re
import json
import base64
import cv2
import numpy as np
from PIL import Image, ImageDraw

POINT_RADIUS = 3
CIRCLE_RADIUS = 18
CIRCLE_WIDTH = 3


def rewrite_markdown_file_by_jsonl(jsonl_path):
    """
    rewrite markdown file by jsonl file
    """
    with open(jsonl_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    entries = [json.loads(line) for line in lines]
    markdown_path = jsonl_path.replace('.jsonl', '.md')
    rewrite_markdown_file(markdown_path, entries)


def rewrite_markdown_file(markdown_path, entries):
    """
    rewrite markdown file by entries, use marked_screenshot if exists
    """
    prompt = '''Given the screenshot as below. What's the next step that you will do to help with the task?'''
    with open(markdown_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # keep the first 5 lines
    kept_lines = lines[:5]

    # add new lines after the kept lines
    for entry in entries:
        timestamp = entry['timestamp']
        action = get_full_action(entry)
        screenshot_path = entry['marked_screenshot'] if 'marked_screenshot' in entry else entry['screenshot']
        image_description = entry['image_description'] if 'image_description' in entry else None
        thought = entry['thought'] if 'thought' in entry else None
        action_description = entry['action_description'] if 'action_description' in entry else None
        action_description_checked = entry['action_description_checked'] if 'action_description_checked' in entry else None

        kept_lines.append(f'### {timestamp}\n')
        kept_lines.append(f'**Input:** \n\n{prompt}\n\n')
        kept_lines.append(
            f'<img src="{screenshot_path}" width="100%" height="100%">\n\n')
        # if image_description:
        #     kept_lines.append(f'**Image Description:** \n\n{image_description}\n\n')
        if action_description:
            kept_lines.append(
                f'**Action Description:** \n\n{action_description}\n\n')
        if thought:
            kept_lines.append(f'**Thought:** \n\n{thought}\n\n')
        if action_description_checked:
            kept_lines.append(
                f'**Action Description Checked:** \n\n{action_description_checked}\n\n')
        kept_lines.append(f'**Output:** \n\n{action}\n\n')

    # rewrite the file
    with open(markdown_path, 'w', encoding='utf-8') as file:
        file.writelines(kept_lines)


def remove_screenshot(screenshot_path):
    """
    remove the screenshot file and the possible _marked file
    """
    if os.path.exists(screenshot_path):
        os.remove(screenshot_path)

    # remove the possible _marked file
    marked_screenshot_path = screenshot_path.replace('.png', '_marked.png')
    if os.path.exists(marked_screenshot_path):
        os.remove(marked_screenshot_path)


def get_full_action(entry):
    """
    get the full action string from entry
    """
    action = entry['action']
    element = entry['element']
    if element:
        target = 'click'
        index = action.find(target)
        if index != -1:
            # find the end position of 'click'
            insert_position = index + len(target)
            # insert ':' after 'click'
            action = action[:insert_position] + \
                f' element {element} at' + action[insert_position:]
    return action


def encode_image(image_path):
    """
    encode image to base64
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def get_file_size_kb(file_path):
    file_size_bytes = os.path.getsize(file_path)
    file_size_kb = file_size_bytes / 1024  # convert to KB
    return round(file_size_kb, 1)  # keep 1 decimal place


def mark_image(is_click_action, image_path, rect, point1, point2=None):
    """
    mark the image and save as a new file, return the new file path
    """
    # open the image
    with Image.open(image_path) as image:
        if is_click_action:
            # create a drawable object
            draw = ImageDraw.Draw(image)

            # draw a rectangle
            draw.rectangle(
                [(rect["left"], rect["top"]), (rect["right"], rect["bottom"])],
                outline="red",
                width=3  # line width
            )

            # draw a point
            draw_point(point1["x"], point1["y"], draw)

            # draw a circle
            draw_circle(point1["x"], point1["y"], draw)

            # draw a short arrow
            draw_short_arrow(point1["x"], point1["y"], draw)

        else:
            draw = ImageDraw.Draw(image)

            # draw a point
            draw_point(point1["x"], point1["y"], draw)
            draw_point(point2["x"], point2["y"], draw)

            if (abs(point1["x"] - point2["x"]) + abs(point1["y"] - point2["y"])) > 15:
                # draw a circle
                draw_circle(point1["x"], point1["y"], draw)
                draw_circle(point2["x"], point2["y"], draw)
            else:
                print(f"the distance between point1 and point2 in image {image_path} is too small, skip drawing circles")
                
            # draw a long arrow
            draw_long_arrow(point1["x"], point1["y"], point2["x"], point2["y"], draw)

    # generate the output path, add "_marked" to the original file name
    base, ext = os.path.splitext(image_path)
    output_path = f"{base}_marked{ext}"

    # save the marked image
    image.save(output_path)
    # print(f"marked image saved to: {output_path}")
    return output_path


def resize_to_1080p(image_path):
    """
    check and resize the image to fixed 1920x1080 resolution, return whether success
    """
    try:
        with Image.open(image_path) as img:
            img.verify()  # verify the image integrity
    except:
        print(f"[ERROR] image corrupted: {image_path}")
        return False

    # open the image
    with Image.open(image_path) as img:
        # check if the image is already 1080p
        if img.size == (1920, 1080):
            print(f"image is already 1080p, no need to resize: {image_path}")
            return True

        # resize the image to fixed 1920x1080 resolution
        try:
            resized_img = img.resize((1920, 1080), Image.LANCZOS)
        except:
            print(f"[ERROR] cannot resize image: {image_path}")
            return False

        # save the resized image, overwrite the original file
        resized_img.save(image_path, optimize=True)
        print(f"image resized and saved: {image_path}")
        return True


def resize_action(action_str, scale_x, scale_y):
    """
    extract coordinates from the action string, scale them, and replace the coordinate part in the original string.

    :param action_str: action string, e.g. "double click (1415, 741)"
    :param scale_x: X axis scale factor
    :param scale_y: Y axis scale factor
    :return: the scaled action string
    """
    # use regex to match the coordinate part
    pattern = r'\((\d+),\s*(\d+)\)'
    match = re.search(pattern, action_str)

    if match:
        original_x = float(match.group(1))
        original_y = float(match.group(2))
        scaled_x = round(original_x * scale_x)
        scaled_y = round(original_y * scale_y)
        print(
            f"scale coordinates: ({original_x}, {original_y}) -> ({scaled_x}, {scaled_y})")

        # construct the new coordinate string
        new_coords = f"({scaled_x}, {scaled_y})"

        # replace the original coordinate string
        new_action_str = re.sub(pattern, new_coords, action_str)
        return new_action_str
    else:
        return action_str


def are_screenshots_identical(screenshot_path1, screenshot_path2):
    """
    check if two screenshots are identical
    """
    # read the images
    img1 = cv2.imread(screenshot_path1)
    img2 = cv2.imread(screenshot_path2)

    # check if the images are successfully read
    if img1 is None or img2 is None:
        print(f"cannot read image: {screenshot_path1} or {screenshot_path2}")
        return False

    # check if the images have the same size
    if img1.shape != img2.shape:
        return False

    # check if the images are identical
    difference = cv2.subtract(img1, img2)
    return not np.any(difference)


def parse_click_action(action):
    pattern = r'((?:double |right )?click)\s*\((\d+),\s*(\d+)\)'
    match = re.match(pattern, action)
    
    if match:
        action = match.group(1)  # extract the action name
        x = int(match.group(2))  # extract x coordinate and convert to integer
        y = int(match.group(3))  # extract y coordinate and convert to integer
        return action, (x, y)
    else:
        return None, None


def parse_drag_action(action):
    assert action.startswith('drag from'), f"error: action '{action}' is not a drag action"
    start1 = action.find('from (') + 6
    end1 = action.find(') to (')
    start2 = action.find('to (') + 4
    end2 = len(action) - 1
    
    # extract two sets of coordinates
    coord1 = action[start1:end1]
    coord2 = action[start2:end2]
    
    # split and convert to integers
    x1, y1 = map(int, coord1.split(', '))
    x2, y2 = map(int, coord2.split(', '))
    
    return (x1, y1), (x2, y2)


def extract_coordinates(text):
    pattern = r'(?:drag to|press) \((\d+), (\d+)\)'
    match = re.search(pattern, text)
    if match:
        x, y = map(int, match.groups())
        return x, y
    return None


def draw_point(x, y, draw):
    radius = POINT_RADIUS
    left = x - radius
    top = y - radius
    right = x + radius
    bottom = y + radius

    draw.ellipse(
        [(left, top), (right, bottom)],
        fill="red"
    )


def draw_circle(x, y, draw):
    radius = CIRCLE_RADIUS
    left = x - radius
    top = y - radius
    right = x + radius
    bottom = y + radius

    draw.ellipse(
        [(left, top), (right, bottom)],
        outline="red",
        width=CIRCLE_WIDTH
    )


def draw_short_arrow(x, y, draw):
    arrow_length = 50  # arrow length
    arrow_gap = CIRCLE_RADIUS + 2  # arrow gap
    arrow_width = 18   # arrow width
    angle = np.radians(30)  # arrow angle
    cos_angle = np.cos(angle)
    sin_angle = np.sin(angle)

    # draw the arrow body
    start_x = x - arrow_length * cos_angle
    start_y = y - arrow_length * sin_angle
    end_x = x - arrow_gap * cos_angle
    end_y = y - arrow_gap * sin_angle
    draw.line([(start_x, start_y), (end_x, end_y)],
              fill="red", width=3)

    # draw the arrow head
    arrow_point1 = (
        int(end_x - arrow_width),
        int(end_y)
    )
    arrow_point2 = (
        int(end_x - arrow_width * sin_angle),
        int(end_y - arrow_width * cos_angle)
    )

    draw.polygon([
        (end_x, end_y),
        arrow_point1,
        arrow_point2
    ], fill="red")


def draw_long_arrow(x1, y1, x2, y2, draw):
    head_length = 18  # arrow head length
    head_angle = np.radians(30)  # arrow head angle

    # calculate the midpoint of the line
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2

    # draw the arrow body
    draw.line([(x1, y1), (x2, y2)], fill="red", width=3)

    # arrow head direction vector
    vector_x = x2 - x1
    vector_y = y2 - y1
    length = np.hypot(vector_x, vector_y)
    unit_vector_x = vector_x / length
    unit_vector_y = vector_y / length

    # calculate the positions of the two points of the arrow head (now based on the midpoint)
    left_x = mid_x - head_length * \
        (unit_vector_x * np.cos(head_angle) +
         unit_vector_y * np.sin(head_angle))
    left_y = mid_y - head_length * \
        (unit_vector_y * np.cos(head_angle) -
         unit_vector_x * np.sin(head_angle))

    right_x = mid_x - head_length * \
        (unit_vector_x * np.cos(head_angle) -
         unit_vector_y * np.sin(head_angle))
    right_y = mid_y - head_length * \
        (unit_vector_y * np.cos(head_angle) +
         unit_vector_x * np.sin(head_angle))

    # use the midpoint as the vertex of the arrow head
    draw.polygon([(mid_x, mid_y), (left_x, left_y),
                  (right_x, right_y)], fill="red")
