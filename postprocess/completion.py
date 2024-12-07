import os
import json
import sys
import random
import concurrent.futures
from datetime import datetime
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor
from prompt import *
from utils import *

client = OpenAI()
model = "gpt-4o"

CONCURRENT_NUM = 80
RE_GENERATE = False
MAX_CONTEXT_ENTRIES = 10
DETAILED_OUTPUT = False


def call_openai(query, base64_image=None):
    messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    } if base64_image else None,
                    {
                        "type": "text",
                        "text": query
                    },
                ],
            },
        ]

    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=1000
    )

    reply = completion.choices[0].message.content
    return reply


def process_concurrently(data_dir, function):
    tasks = []
    
    for item in os.listdir(data_dir):
        item_path = os.path.join(data_dir, item)
        directory_name = "events_"

        if os.path.isdir(item_path) and item.startswith(directory_name):
            print(f'Processing directory: {item_path}')
            for filename in os.listdir(item_path):
                if filename.endswith('.jsonl') and 'task' in filename:
                    file_path = os.path.join(item_path, filename)   
                    md_path = os.path.join(item_path, filename.replace('.jsonl', '.md'))
                    try:
                        with open(md_path, 'r', encoding='utf-8') as file:
                            lines = file.readlines()
                        task_description = lines[1].replace('**Description:** ', '').strip()
                        tasks.append((file_path, task_description))
                    except Exception as e:
                        print(f"error: failed to extract task description from {md_path}: {e}")

    random.shuffle(tasks)
    with ThreadPoolExecutor(max_workers=CONCURRENT_NUM) as executor:
        futures = [executor.submit(function, file_path, task_description) 
                  for file_path, task_description in tasks]
        concurrent.futures.wait(futures)


def get_action_description(action, element_name, marked_screenshot_path=None, marked_screenshot_data=None):
    """
    Generate action description for click-related actions.
    """
    if marked_screenshot_path:
        base64_image = encode_image(marked_screenshot_path)
    elif marked_screenshot_data:
        base64_image = marked_screenshot_data
    else:
        base64_image = None
        
    click_action, _ = parse_click_action(action)
    if click_action: 
        # Is a click-related action, generate action description
        query = CLICK_ACTION_DESCRIPTION_PROMPT \
        + f"The name of the clicked target for reference: {element_name}\n\n"

        reply = call_openai(query, base64_image)
        description = f"{click_action} <\{reply}>"
        
    else:
        # Not a click-related action, return the original action as description
        description = action
        
    return description


def get_action_description_check(action, element_name, action_description, marked_screenshot_path=None, marked_screenshot_data=None):
    """
    Check the action description for click-related actions.
    """
    if marked_screenshot_path:
        base64_image = encode_image(marked_screenshot_path)
    elif marked_screenshot_data:
        base64_image = marked_screenshot_data
    else:
        base64_image = None
        
    click_action, coordinates = parse_click_action(action)
    if click_action: 
        # Is a click-related action, check the action description
        x, y = coordinates
        clicked_element_description = action_description.split('<\\')[1].split('>')[0]
        
        query = CLICK_ACTION_DESCRIPTION_CHECK_PROMPT \
        + f"The exact coordinates of the mouse click: ({x}, {y})\n" \
        + f"The element name from the accessibility tree: {element_name}\n" \
        + f"The pre-generated description of the click location: {clicked_element_description}\n"
        
        try_time = 0   

        while True:
            try_time += 1

            reply = call_openai(query, base64_image)

            if "Answer:" in reply:
                check_result = reply.split("Answer:")[1].strip().strip('*')        
                break

            if try_time > 3:
                check_result = None
                print(f"action description check failed after 3 times in {marked_screenshot_path}")
                break
                    
    else:
        # Not a click-related action, return None
        check_result = None
        
    if check_result and check_result.strip().startswith("Wrong"):
        modifyed_description = check_result.split("Wrong. Correct Description:")[1].strip()
        final_answer = f"{click_action} <\{modifyed_description}>"
    else:
            final_answer = None
        
    return check_result, final_answer


def get_thought(task_description, action, history, following_actions, marked_screenshot_path=None, marked_screenshot_data=None):
    """
    Generate thought for the action.
    """
    if marked_screenshot_path:
        base64_image = encode_image(marked_screenshot_path)
    elif marked_screenshot_data:
        base64_image = marked_screenshot_data
    else:
        base64_image = None
        
    query = THOUGHT_PROMPT \
        + f"The task you are attempting to complete: {task_description}\n\n" \
        + f"Your performing history:\n{history}\n\n" \
        + f"Your subsequent actions:\n{following_actions}\n\n" \
        + f"The specific action you chose to perform: {action}\n\n"

    thought = call_openai(query, base64_image)
    
    if "Action:" in thought:
        print(f"warning: found 'Action:' in thought generation, deleting it")
        thought = thought.split("Action:")[0].strip()
    if "*Action*:" in thought:
        print(f"warning: found '*Action*:' in thought generation, deleting it")
        thought = thought.split("*Action*:")[0].strip()
    
    return thought


def add_field_for_file(file_path, field, task_description):
    print(f"begin adding {field} for {file_path}")
    entries = []

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            entries = [json.loads(line) for line in file]
    except Exception as e:
        print(f"error: failed to read file {file_path}: {e}")
        return
    
    if field == 'thought':
        all_actions = [entry['action_description'] for entry in entries]
    
    try:
        for id, entry in enumerate(entries):
            if field in entry and entry[field] and content_is_rational(entry[field]):
                if not RE_GENERATE:
                    continue
            
            if 'marked_screenshot' not in entry:
                print(f"error: marked_screenshot field not found: {file_path}")
                continue
            
            marked_screenshot_path = os.path.join(os.path.dirname(file_path), entry['marked_screenshot'])
            if not os.path.isfile(marked_screenshot_path):
                print(f"error: screenshot file not found: {marked_screenshot_path}")
                continue
            
            try:
                if field == 'action_description':
                    action_description = get_action_description(entry['action'], entry['element'], marked_screenshot_path=marked_screenshot_path)
                    
                    entry['action_description'] = action_description
                    
                    if DETAILED_OUTPUT:
                        print(f"generated action_description: {action_description}")
                elif field == 'action_description_checked':
                    action_description_checked, modified_action_description = get_action_description_check(
                    entry['action'], entry['element'], entry['action_description'], 
                    marked_screenshot_path=marked_screenshot_path)
                    
                    entry['action_description_checked'] = action_description_checked
                    
                    if modified_action_description:
                        entry['action_description'] = modified_action_description
                    
                    if DETAILED_OUTPUT and action_description_checked:
                        print(f"generated action_description_checked: {action_description_checked}")
                elif field == 'thought':
                    # build history steps
                    history_steps = []
                    start_idx = max(0, id - MAX_CONTEXT_ENTRIES)
                    for hist_id in range(start_idx, id):
                        hist_entry = entries[hist_id]
                        if 'thought' in hist_entry and hist_entry['thought'] and content_is_rational(hist_entry['thought']):
                            history_steps.append(f"{hist_id+1}:\nThought: {hist_entry['thought']}\nAction: {hist_entry['action_description']}")
                    # build subsequent steps
                    subsequent_actions = all_actions[id+1:id+1+MAX_CONTEXT_ENTRIES]
                    subsequent_actions_str = get_action_string(subsequent_actions)
                    thought = get_thought(
                        task_description, entry['action_description'], '\n'.join(history_steps), subsequent_actions_str, marked_screenshot_path=marked_screenshot_path)
                    
                    entry['thought'] = thought
                    
                    if DETAILED_OUTPUT:
                        print(f"generated thought: {thought}")
                else:
                    print(f"error: unknown field: {field}")
            except Exception as e:
                print(f"error: failed to get {field} for {marked_screenshot_path}: {e}")
                continue

        with open(file_path, 'w', encoding='utf-8') as file:
            for entry in entries:
                json.dump(entry, file, ensure_ascii=False)
                file.write('\n')

        rewrite_markdown_file_by_jsonl(file_path)
        print(f"finished adding {field} for {file_path}")

    except Exception as e:
        print(f"error: failed to process file {file_path}: {e}")
        if "Expecting" in str(e) or "Invalid control character" in str(e):
            print(f"file {file_path} is corrupted, deleting...")
            try:
                os.remove(file_path)
                print(f"deleted corrupted file: {file_path}")
            except OSError as delete_error:
                print(f"error: failed to delete corrupted file: {delete_error}")


def action_semantic_completion(file_path, task_description):
    """
    Adds the field 'action_description' to the jsonl file as action semantics.

    Parameters:
    file_path (str): The path to the jsonl file to be processed.
    """
    # add action description
    add_field_for_file(file_path, 'action_description', task_description)
    # add action description check
    add_field_for_file(file_path, 'action_description_checked', task_description)
    # add thought
    add_field_for_file(file_path, 'thought', task_description)



if __name__ == "__main__":
    start_time = datetime.now()
    print(f"start time: {start_time}")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) > 1:
        data_dir = os.path.join(current_dir, sys.argv[1])
    else:
        data_dir = os.path.join(current_dir, 'data') # write the data directory here
    if not os.path.exists(data_dir):
        print(f"error: {data_dir} directory does not exist")
        exit()
    
    process_concurrently(data_dir, action_semantic_completion)

    end_time = datetime.now()
    print(f"end time: {end_time}")
    print(f"Total time: {end_time - start_time}")
