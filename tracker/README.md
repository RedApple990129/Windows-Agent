# PC Tracker User Manual

\[ English | [中文](README_zh.md) \]

- Version: 1.0
- Last updated: 2024-12-25

## 1. Introduction

PC Tracker is a lightweight infrastructure for efficiently collecting large-scale human-computer interaction trajectories. The program runs seamlessly in the background, automatically capturing screenshots and keyboard & mouse activities. 

Below is an example of the collected human-computer interaction trajectories:

![raw_trajectory_example](../assets/raw_trajectory_example.png)

## 2. Installation

- Ensure your operating system is Windows.
- Extract our software package to a location with sufficient disk space (recommended to have more than 3GB of available space for storing recorded data).

## 3. Quick Start

- [Optional] Set screen resolution to 16:9 (recommended 1920 x 1080).
- Open the extracted folder and launch `main.exe`.

## 4. Instructions

After starting the software, you can choose between **Task Oriented Mode** or **Non-Task Oriented Mode** for recording.

### Task Oriented Mode

This mode is divided into two sub-modes: **Given Task** and **Free Task**.

#### Given Task

In this mode, you will be assigned an uncompleted task each time.

- **Next Task**: Click `Next Task` to get the next task.
- **Previous Task**: Click `Previous Task` to return to the next task.
- **Bad Task Feedback**: If you think the current task is difficult to complete, click `Bad Task` to discard it permanently. Alternatively, you can start the task and modify its description after completion based on your actual execution.
- **Start Recording**: Click `Start`, and the tracker window will automatically minimize while recording begins.
- **End Task**: After completing the task, click `Finish` to save the record. Or if the task execution fails or you don’t want to record it, click `Fail`.
- **Modify Task Description**: After finishing the task, you can modify the task description based on your actual execution.

#### Free Task

In this mode, you can freely use the computer and summarize the task description and difficulty yourself.

- **Start Recording**: Click `Start`, and the tracker window will automatically minimize while recording begins.
- **Save and Summarize This Record**: Fill in the task description, select difficulty (easy/medium/hard), and click `Save` to save the record.
- **Discard This Record**: Click `Discard` to discard the record.

### Non-Task Oriented Mode

In this mode, you can freely use the computer, with similar methods to start and stop recording as described above.

## 5. Usage Notes

- **Does not currently support using extended screens**.
- **Does not currently support using Chinese input methods**.
- **Does not currently support using touchpads**.
- **The tracker window is fixed in fullscreen.** To support the filtering of tracker-related actions (such as clicking the Start button) in post-processing, the tracker window is fixed in fullscreen. You can reopen the tracker window by clicking to view the task description, then minimize it again, but please do not drag it to display in a non-fullscreen state.

## 6. Data Privacy

- After starting recording, your screenshots and keyboard & mouse operations will be automatically recorded. PC Tracker does not record any information from unopened software. If you believe the recording may infringe on your privacy, you can choose to discard the record.
- Collected data will be saved in the `./events` folder (hidden by default). Each trajectory comes with a Markdown file for easy visualization.

## 7. FAQ

**1. Does the software have networking capabilities?**

PC Tracker is completely local, does not support networking, and will not upload your data.

**2. What if my computer screen resolution is not 16:9?**

If your screen resolution is not 16:9, it will affect the subsequent unified processing of data. We recommend adjusting your screen resolution to 16:9.

**3. How much space will the collected data approximately occupy?**

The specific data size varies. Generally, even with intensive recording operations for 1 hour, it will not generate more than 1GB of data.

**4. What should I do if the interface doesn't display properly after launching the tracker?**

If some interface elements (such as buttons) appear incomplete after launching the software, this may be caused by your computer's display scaling settings. You can try adjusting the display scaling in Settings -> System -> Display, and then restart the software.

## 8. Contact

If you have any questions, please contact us at henryhe_sjtu@sjtu.edu.cn or zizi0123@sjtu.edu.cn.
