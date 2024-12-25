import random
from monitor import Monitor
from task import *


class Tracker:
    def __init__(self):
        self.monitor = None
        self.running = False
        self.given_tasks = load_given_tasks()
        self.finished_given_cnt, self.finished_free_cnt = load_task_cnt()
        self.bad_task_cnt = 0
        self.task_num = len(self.given_tasks)
        print(f"task num = {self.task_num}")
        self.task_id = random.randint(0, self.task_num - 1)
        self.task = None

    def get_given_task(self, offset):
        while True:
            self.task_id = (self.task_id + self.task_num + offset) % self.task_num
            task = self.given_tasks[self.task_id]
            if not task.finished and not task.is_bad:
                break
        self.task = self.given_tasks[self.task_id]

    def finish_all(self):
        return self.finished_given_cnt + self.bad_task_cnt == self.task_num

    def update_tasks(self):
        update_given_tasks(self.given_tasks)
        update_task_cnt(self.finished_given_cnt, self.finished_free_cnt)

    def get_free_task(self):
        self.task = free_task()

    def start(self):
        if not self.running:
            self.monitor = Monitor(self.task)
            self.monitor.start()
            self.running = True

    def stop(self):
        if self.running:
            self.monitor.stop()
            self.running = False

    def finish(self):
        if self.running:
            self.monitor.finish()
            self.running = False
            self.given_tasks[self.task_id].finished = True
            self.finished_given_cnt += 1
        else:
            self.monitor.generate_md()
            self.given_tasks[self.task_id].finished = True
            self.finished_given_cnt += 1

    def fail(self):
        if self.running:
            self.monitor.fail()
            self.running = False

    def stop_without_task(self):
        # stop without markdown (task unknown)
        if self.running:
            self.monitor.finish_without_md()
            self.running = False

    def save_free_task(self, task):
        # 在stop without task后调用，更新task后保存记录
        self.monitor.generate_md(task)
        self.finished_free_cnt += 1

    def discard(self):
        # 在stop/stop free task后调用，丢弃记录
        self.monitor.discard_record()
