from util import *
from prompt import GROUNDING_AGENT_PROMPT
import re

class GroundingAgent:
    def __init__(self, grounding_client):
        self.grounding_client = grounding_client
        self.grounding_model = grounding_client.models.list().data[0].id
        print(f"Grounding model: {self.grounding_model}")
        screenshot = get_screenshot()
        self.window_width = screenshot.width
        self.window_height = screenshot.height
        
    def find_element(self, element_description, screenshot):
        """
        find the element and return the coordinates (with check),
        return x, y, there_are_none
        """
        cnt = 0
        retry_limit = 3
        
        while cnt < retry_limit:
            x, y, there_are_none = self.call_grounding(element_description, screenshot)
            if there_are_none:
                return None, None, True
            elif self.check_grounding(x, y, screenshot, element_description):
                return x, y, False
            cnt += 1

        return None, None, True

    def call_grounding(self, element_description, screenshot):
        """
        call the grounding model to locate the element,
        return x, y, there_are_none
        """
        base64_image = encode_image(screenshot)
        instruction = f"Point to {element_description}"
        messages = get_mllm_messages(instruction, base64_image)
        
        completion = self.grounding_client.chat.completions.create(
            model=self.grounding_model,
            messages=messages,
            max_tokens=512,
            temperature=0.8,
            n=3  # Request n completions in parallel
        )
        
        # Try each response until we find valid coordinates
        for choice in completion.choices:
            x, y = self.parse_coordinates(choice.message.content)
            if x is not None and y is not None:
                return x, y, False
        
        # If no valid coordinates found in any response
        return None, None, True

    def check_grounding(self, x, y, screenshot, target_description):
        """
        check if the grounding result is correct,
        return True if accept
        """
        element = get_element_info_from_position(x, y)
        element_name = element['name'] if element['name'] != '' else 'unknown'
        marked_screenshot = mark_screenshot(screenshot, (x, y), element["coordinates"])
        base64_marked_screenshot = encode_image(marked_screenshot)
        
        instruction = GROUNDING_AGENT_PROMPT + \
            f"The element name from the accessibility tree: {element_name}\n" + \
            f"Target Element Description: {target_description}\n"
            
        messages = get_mllm_messages(instruction, base64_marked_screenshot)
        completion = self.grounding_client.chat.completions.create(
            model=self.grounding_model,
            messages=messages,
            max_tokens=512,
        )
        output_text = completion.choices[0].message.content
        return "Result: Reject" not in output_text

    def parse_coordinates(self, output_text):
        """
        parse the coordinates from the model output
        """
        # match single point coordinates
        point_pattern = r'<point\s*x="([\d.]+)"\s*y="([\d.]+)"'
        point_match = re.search(point_pattern, output_text)
        if point_match:
            try:
                x_percent = float(point_match.group(1))
                y_percent = float(point_match.group(2))
                return int(x_percent * self.window_width / 100), int(y_percent * self.window_height / 100)
            except (ValueError, IndexError):
                return None, None
        
        # match multiple point coordinates
        points_pattern = r'<points\s+((?:x\d+="[\d.]+"\s*y\d+="[\d.]+"\s*)+)'
        points_match = re.search(points_pattern, output_text)
        if points_match:
            try:
                coord_pattern = r'x1="([\d.]+)"\s*y1="([\d.]+)"'
                coord_match = re.search(coord_pattern, points_match.group(1))
                if coord_match:
                    x_percent = float(coord_match.group(1))
                    y_percent = float(coord_match.group(2))
                    return int(x_percent * self.window_width / 100), int(y_percent * self.window_height / 100)
            except (ValueError, IndexError):
                return None, None
                
        return None, None
