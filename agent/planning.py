from prompt import PLANNING_AGENT_PROMPT
from util import *

class PlanningAgent:
    def __init__(self, plan_client):
        self.plan_client = plan_client
        self.plan_model = plan_client.models.list().data[0].id
        print(f"Planning model: {self.plan_model}")
        self.history = []
        self.HISTORY_CUT_OFF = 10
        
    def get_plan(self, screenshot, task_description, retry_click_elements=None):
        """
        get the next plan
        Args:
            screenshot: the screenshot
            task_description: task description
            retry_click_elements: the list of elements that failed to click before
        Returns:
            plan_str: plan description
            action_str: specific action
        """
        instruction = self.get_plan_instruction(task_description)
        
        if retry_click_elements:
            retry_elements_str = "> and <".join(retry_click_elements)
            instruction += f"\n\nNote: The element <{retry_elements_str}> you want to click before is not found, please try a new plan."
        
        base64_image = encode_image(screenshot)
        messages = get_mllm_messages(instruction, base64_image)
        completion = self.plan_client.chat.completions.create(
            model=self.plan_model,
            messages=messages,
            max_tokens=512,
            temperature=0.8
        )
        output_text = completion.choices[0].message.content
        return self.split_output(output_text)
    
    def add_to_history(self, output):
        """
        add the output to the history
        """
        self.history.append(output)
        
    def get_plan_instruction(self, task_description):
        """
        generate the planning instruction
        """
        prompt = PLANNING_AGENT_PROMPT + f"Your task is: {task_description}\n\n"
        
        if len(self.history) > self.HISTORY_CUT_OFF:
            history_str = "\n\n".join(f"[{i+1}] {item}" for i, item in enumerate(self.history[-self.HISTORY_CUT_OFF:]))
        else:
            history_str = "\n\n".join(f"[{i+1}] {item}" for i, item in enumerate(self.history))
            
        if history_str == '':
            history_str = "None"
            
        prompt += f"History of the previous actions and thoughts you have done to reach the current screen: {history_str}\n\n"
        prompt += "--------------------------------------------\n\n"
        prompt += f"Given the screenshot. What's the next step that you will do to help with the task?"
        return prompt
    
    def split_output(self, output):
        """
        split the output into plan and action
        """
        plan_str = output.split("Action:")[0].strip()
        action_str = output.split("Action:")[1].strip()
        return plan_str, action_str
