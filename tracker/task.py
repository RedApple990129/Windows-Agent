import json
import os
import time


def find_tasks_json():
    start_dir = os.path.abspath(".")
    for root, dirs, files in os.walk(start_dir):
        if 'tasks.json' in files:
            return os.path.join(root, 'tasks.json')
    return None


def find_task_cnt_json():
    start_dir = os.path.abspath(".")
    for root, dirs, files in os.walk(start_dir):
        if 'task_cnt.json' in files:
            return os.path.join(root, 'task_cnt.json')
    return None


tasks_path = find_tasks_json()
task_cnt_path = find_task_cnt_json()
task_cnt = 0


class Task:
    def __init__(self, description, id, level, file_input=None, category="other", finished=False, is_bad=False):
        self.description = description
        self.level = level
        self.id = id
        self.category = category
        self.file_input = file_input
        self.finished = finished
        self.is_bad = is_bad


def from_json(task, task_cnt) -> Task:
    return Task(task['task'], task_cnt, task['level'], task['file_input'], task['category'], task['finished'])


def free_task():
    return Task("free task", 0, "easy")


def load_task_cnt():
    with open(task_cnt_path, 'r') as file:
        data = json.load(file)
        return data['given_task'], data['free_task']


def load_given_tasks():
    tasks = []
    global task_cnt
    if tasks_path is None:
        return [free_task()]  # for robustness
    with open(tasks_path, 'r') as file:
        data = json.load(file)
        for task in data:
            task_cnt += 1
            tasks.append(from_json(task, task_cnt))
    return tasks


def update_given_tasks(given_tasks):
    if tasks_path is None:
        return
    try:
        # set_hidden_file(tasks_path, False)
        with open(tasks_path, 'w') as file:
            json.dump(
                [{'task': task.description,
                  'level': task.level,
                  'file_input': task.file_input,
                  'category': task.category,
                  'finished': task.finished}
                 for task in given_tasks if not task.is_bad],
                file,
                indent=2  # Set indentation to 2 spaces
            )
        # set_hidden_file(tasks_path, True)
    except Exception as e:
        print(e)
        # sleep for 10 seconds
        time.sleep(10)


def update_task_cnt(finished_given_cnt, finished_free_cnt):
    print(f"update task cnt: {finished_given_cnt}, {finished_free_cnt}")
    # set_hidden_file(task_cnt_path, False)
    with open(task_cnt_path, 'w') as file:
        json.dump({'given_task': finished_given_cnt, 'free_task': finished_free_cnt}, file, indent=2)
    # set_hidden_file(task_cnt_path, True)
