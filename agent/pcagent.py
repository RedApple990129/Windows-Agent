from util import *
import pyautogui
import time
import re
import os

MAX_ACTION_CNT = 50
PLANNING_MAX_RETRY = 3

class PCAgent:
    def __init__(self, planner_agent, grounding_agent, task_description, output_queue=None):
        self.planner_agent = planner_agent
        self.grounding_agent = grounding_agent
        self.task_description = task_description
        self.output_queue = output_queue
        self.retry_click_elements = []
        self.step_cnt = 0
        
        # set record directory
        file_path = os.path.dirname(os.path.abspath(__file__))
        directory_name = f"inference_{time.strftime('%Y-%m-%d_%H-%M-%S')}"
        self.directory_path = os.path.join(file_path, 'record', directory_name)
        os.makedirs(self.directory_path, exist_ok=True)

    def run(self):
        try:
            while self.step_cnt < MAX_ACTION_CNT:
                time.sleep(2)
                screenshot = get_screenshot()
                output, screenshot = self.step(screenshot)
                self.record(output, screenshot)
            
            print("Agent meets max action count.")
            self.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            self.exit(1)

    def step(self, screenshot, retry_click=0):
        """
        one step of the agent
        """
        # deal with retry click
        if retry_click == 0:
            self.retry_click_elements.clear()
        elif retry_click > PLANNING_MAX_RETRY:
            print(f"Plan Model failed to make valid plan after {PLANNING_MAX_RETRY} retries")
            self.exit(1)
        else:
            print(f"Retry after click not found: {self.retry_click_elements[-1]}")
        # call planner agent to get plan
        plan, action = self.planner_agent.get_plan(screenshot, self.task_description, self.retry_click_elements)
        
        if "click element:" in action:
            # call grounding agent to find element
            element_description = action.split("click element:")[1].strip()
            x, y, there_are_none = self.grounding_agent.find_element(element_description, screenshot)
            
            if there_are_none:
                # if element not found, retry
                self.retry_click_elements.append(element_description)
                self.add_fail_block(plan)
                return self.step(screenshot, retry_click+1)
            else:
                # if element found, execute action
                element = get_element_info_from_position(x, y)
                marked_screenshot = mark_screenshot(screenshot, (x, y), element["coordinates"])
                action = self.get_click_action(action, x, y)  # rewrite click action
                self.add_success_block(plan, action)
                self.execute_click_action(action, x, y)
                output = f"{plan}\nAction: {action}"
                self.planner_agent.add_to_history(output)
                self.after_action(output)
                return output, marked_screenshot
        else:
            # non-click action
            self.add_success_block(plan, action)
            self.execute_non_click_action(action)
            output = f"{plan}\nAction: {action}"
            self.planner_agent.add_to_history(output)
            self.after_action(output)
            return output, screenshot

    def get_click_action(self, action, x, y):
        if action.startswith("click"):
            return f"click ({x}, {y})"
        elif action.startswith("right click"):
            return f"right click ({x}, {y})"
        elif action.startswith("double click"):
            return f"double click ({x}, {y})"

    def after_action(self, output):
        print_in_green(f"\nAgent Done:\n{output}")
        self.step_cnt += 1

    def execute_click_action(self, action, x, y):
        if action.startswith("click"):
            pyautogui.click(x, y)
        elif action.startswith("right click"):
            pyautogui.rightClick(x, y)
        elif action.startswith("double click"):
            pyautogui.doubleClick(x, y)

    def execute_non_click_action(self, action):
        # drag
        match = re.match(r"(drag from) \((-?\d+), (-?\d+)\) to \((-?\d+), (-?\d+)\)", action)
        if match:
            x1 = int(match.group(2))  # start x coordinate
            y1 = int(match.group(3))  # start y coordinate
            x2 = int(match.group(4))  # target x coordinate
            y2 = int(match.group(5))  # target y coordinate
            pyautogui.mouseDown(x1, y1)
            pyautogui.dragTo(x2, y2, duration=0.5)
            return

        # scroll
        match = re.match(r"scroll \((-?\d+), (-?\d+)\)", action)
        if match:
            x = int(match.group(1))  # horizontal scroll distance
            y = int(match.group(2))  # vertical scroll distance
            if x != 0:
                pyautogui.hscroll(x)  # horizontal scroll
            if y != 0:
                pyautogui.scroll(y)  # vertical scroll
            return

        # press key
        match = re.match(r"press key: (.+)", action)
        if match:
            key_content = match.group(1)
            pyautogui.press(key_content)
            return

        # hotkey
        match = re.match(r"hotkey \((.+), (.+)\)", action)
        if match:
            key1 = match.group(1).lower()
            key2 = match.group(2).lower()
            pyautogui.hotkey(key1, key2)
            return

        # type text
        match = re.match(r"type text: (.+)", action)
        if match:
            text_content = match.group(1)
            pyautogui.write(text_content)
            return

        # wait
        if action == "wait":
            time.sleep(3)
            
        # finish
        if action == "finish":
            self.exit(0)

        # fail
        if action == "fail":
            self.exit(1)

    def record(self, output, screenshot):
        # record in markdown
        first_event = self.step_cnt == 1
        record_in_md(self.directory_path, self.task_description, f"{self.step_cnt}.png", output, first_event=first_event)
        # save image
        screenshot_path = os.path.join(self.directory_path, f"{self.step_cnt}.png")
        save_screenshot(screenshot, screenshot_path)
    
    def add_success_block(self, plan, action):
        if self.output_queue is not None:
            self.output_queue.put(f"{plan}\n\nAction: {action}")
    
    def add_fail_block(self, plan):
        if self.output_queue is not None:
            self.output_queue.put(f"{plan}")
        
    def exit(self, exit_code):
        if exit_code == 0:
            print("Task is done!")
        
        exit(exit_code)
    