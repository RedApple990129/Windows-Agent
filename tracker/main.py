import multiprocessing
from tracker import Tracker
from task import Task
import tkinter as tk
import tkinter.font as tkFont
import tkinter.ttk as ttk
from tkinter import messagebox  # Import messagebox


class TrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tracker")
        self.tracker = Tracker()

        # Set window size to screen size and maximize window
        self.root.geometry(
            f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}")
        self.root.state("zoomed")  # Maximize window

        self.root.configure(bg="#f0f0f0")  # Set background color
        self.root.resizable(True, True)
        self.root.resizable(False, False)  # Disable resizing the window

        # Font
        self.title_font = tkFont.Font(
            family="Helvetica", size=26, weight="bold")
        self.label_font = tkFont.Font(family="Helvetica", size=18)
        self.button_font = tkFont.Font(family="Arial", size=12)
        self.text_font = tkFont.Font(family="Helvetica", size=15)

        # Label
        self.title_label = tk.Label(
            root, text="", font=self.label_font,
            wraplength=400, bg="#f0f0f0", fg="#555555")
        self.title_label.pack(pady=(20, 40))

        # Intercept close button click event
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

        # Create initial interface
        self.initial_interface()

    def quit_app(self):
        self.tracker.stop()
        self.tracker.folder_reset.reset()  # reset folder
        self.tracker.update_tasks()
        self.root.destroy()

    """
    Interface Definitions
    """

    def initial_interface(self):
        self.clear_interface()
        self.title_label.config(text="Welcome to OS Tracker!")

        self.task_button = tk.Button(
            self.root, text="Task Oriented Mode", command=self.task_oriented_interface,
            width=25, height=2, font=self.button_font)
        self.task_button.pack(pady=10)
        ToolTip(self.task_button, "Tracking with a specific task")

        self.non_task_button = tk.Button(
            self.root, text="Non-Task Oriented Mode", command=self.non_task_oriented_interface,
            width=25, height=2, font=self.button_font)
        self.non_task_button.pack(pady=10)
        ToolTip(self.non_task_button,
                "Tracking while using computer freely")

    def task_oriented_interface(self):
        self.clear_interface()
        self.title_label.config(text="Task Oriented Mode")

        self.given_task_button = tk.Button(
            self.root, text="Given Task", command=self.next_given_task_interface,
            width=15, height=2, font=self.button_font)
        self.given_task_button.pack(pady=10)
        ToolTip(self.given_task_button, "Complete given task")

        self.free_task_button = tk.Button(
            self.root, text="Free Task", command=self.free_task_interface,
            width=15, height=2, font=self.button_font)
        self.free_task_button.pack(pady=10)
        ToolTip(self.free_task_button,
                "Freely use pc and summarize the tasks completed on your own.")

        self.back_button = tk.Button(
            self.root, text="Back", command=self.initial_interface,
            width=15, height=2, font=self.button_font)
        self.back_button.pack(pady=10)

    def non_task_oriented_interface(self):
        self.clear_interface()
        self.title_label.config(text="Non-Task Oriented Mode")

        self.start_button = tk.Button(
            self.root, text="Start", command=self.start_non_task_tracking,
            width=15, height=2, font=self.button_font)
        self.start_button.pack(pady=10)

        self.back_button = tk.Button(
            self.root, text="Back", command=self.initial_interface,
            width=15, height=2, font=self.button_font)
        self.back_button.pack(pady=10)

    def free_task_interface(self):
        self.clear_interface()
        self.title_label.config(text="Free Task Mode")

        self.subtitle_label = tk.Label(
            self.root, text="Freely use pc and summarize the tasks completed on your own.", font=("Arial", 15),
            wraplength=750)
        self.subtitle_label.pack(pady=(0, 30))

        self.start_button = tk.Button(
            self.root, text="Start", command=self.start_free_task_tracking,
            width=15, height=2, font=self.button_font)
        self.start_button.pack(pady=10)

        self.back_button = tk.Button(
            self.root, text="Back", command=self.task_oriented_interface,
            width=15, height=2, font=self.button_font)
        self.back_button.pack(pady=10)

        self.corner_label = tk.Label(self.root, text=f"You have finished {self.tracker.finished_free_cnt} free tasks.",
                                     font=("Arial", 14), bg="#f0f0f0")
        self.corner_label.pack(side="bottom", anchor="se", padx=30, pady=30)

    def next_given_task_interface(self):
        self.given_task_interface(offset=1)

    def current_given_task_interface(self):
        self.given_task_interface(offset=0)

    def previous_given_task_interface(self):
        self.given_task_interface(offset=-1)

    def given_task_interface(self, offset):
        if self.tracker.finish_all():
            messagebox.showinfo(
                "Task Completed", "All tasks have been finished!")
        else:
            self.clear_interface()
            self.title_label.config(text="Given Task Mode")

            self.tracker.get_given_task(offset)

            self.subtitle_label = tk.Label(
                self.root, text=f"Category: {self.tracker.task.category}", font=("Arial", 15), wraplength=750)
            self.subtitle_label.pack(pady=(0, 30))

            self.corner_label = tk.Label(self.root,
                                         text=f"You have finished {self.tracker.finished_given_cnt} given tasks.",
                                         font=("Arial", 14), bg="#f0f0f0")
            self.corner_label.pack(side="bottom", anchor="se", padx=30, pady=30)

            # Create a Canvas widget for the rounded rectangle
            canvas = tk.Canvas(self.root, width=1500,
                               height=510, bg="#f0f0f0", highlightthickness=0)
            canvas.pack(pady=5, padx=30, anchor="center")

            # Draw a rounded rectangle
            create_roundrectangle(
                canvas, 20, 0, 1480, 500, radius=30, fill="#ffffff", outline="#cccccc")

            # Add task description text to the canvas
            canvas.create_text(30, 10, text=self.tracker.task.description, font=self.text_font,
                               width=1450, anchor="nw")

            # Create a frame to hold the buttons
            button_frame = tk.Frame(self.root, bg="#f0f0f0")
            button_frame.pack(pady=20)

            # left column
            self.previous_button = tk.Button(button_frame, text="Previous Task",
                                             command=self.previous_given_task_interface,
                                             width=15, height=2, font=self.button_font)
            self.previous_button.grid(row=0, column=0, padx=20, pady=10)

            self.next_button = tk.Button(button_frame, text="Next Task", command=self.next_given_task_interface,
                                         width=15, height=2, font=self.button_font)
            self.next_button.grid(row=1, column=0, padx=20, pady=10)

            # right column
            self.start_button = tk.Button(button_frame, text="Start", command=self.start_given_task_tracking,
                                          width=15, height=2, font=self.button_font)
            self.start_button.grid(row=0, column=1, padx=20, pady=10)
            ToolTip(self.start_button, "Start tracking with this task")

            self.bad_task_button = tk.Button(button_frame, text="Bad Task", command=self.mark_bad_task,
                                             width=15, height=2, font=self.button_font)
            self.bad_task_button.grid(row=1, column=1, padx=20, pady=10)

            # back button centered below the other buttons with the same size
            self.back_button = tk.Button(button_frame, text="Back", command=self.task_oriented_interface,
                                         width=15, height=2, font=self.button_font)
            self.back_button.grid(
                row=2, column=0, columnspan=2, padx=20, pady=20)

    def modify_description_interface(self):
        self.clear_interface()
        self.title_label.config(text="Modify Task Description")

        # Add multi-line input text box and set initial content to task description
        self.entry = tk.Text(self.root, font=self.text_font,
                             width=120, height=20)  # Adjust width and height
        # Set initial content, "1.0" represents the first character position of the first line
        self.entry.insert("1.0", self.tracker.task.description)
        self.entry.pack(pady=(10, 10))  # Leave 25 pixels at top, 10 pixels at bottom

        self.save_button = tk.Button(
            self.root, text="Save", command=self.save_modified_description,
            width=15, height=2, font=self.button_font)
        self.save_button.pack(pady=10)

        self.cancel_button = tk.Button(
            self.root, text="Cancel", command=self.cancel_modify_description,
            width=15, height=2, font=self.button_font)
        self.cancel_button.pack(pady=10)

    def clear_interface(self):
        for widget in self.root.winfo_children():
            if widget != self.title_label:
                widget.destroy()

    """
    Given Task Mode Functions
    """

    def start_given_task_tracking(self):
        self.clear_interface()
        self.tracker.start(True)

        self.title_label.config(text="Tracking...")
        self.title_label.pack(pady=(30, 10))

        canvas_width = 1500  # Adjusted for padding
        canvas_height = 680
        text_front = ("Helvetica", 15)

        # Create a Canvas widget for the rounded rectangle
        canvas = tk.Canvas(self.root, width=canvas_width,
                           height=canvas_height, bg="#f0f0f0", highlightthickness=0)
        canvas.pack(pady=5, padx=30, anchor="center")

        # Draw a rounded rectangle
        create_roundrectangle(
            canvas, 20, 0, 1480, 650, radius=30, fill="#ffffff", outline="#cccccc")

        # Add task description text to the canvas
        canvas.create_text(30, 10, text=self.tracker.task.description, font=text_front,
                           width=1450, anchor="nw")

        self.finish_button = tk.Button(
            self.root, text="Finish", command=self.finish_given_task,
            width=15, height=2, font=self.button_font)
        self.finish_button.pack(pady=10)
        ToolTip(self.finish_button, "Task finished")

        self.fail_button = tk.Button(
            self.root, text="Fail", command=self.fail_given_task,
            width=15, height=2, font=self.button_font)
        self.fail_button.pack(pady=10)
        ToolTip(self.fail_button, "Task failed")

        print("Task oriented tracking started...")

        self.root.iconify()  # Minimize window

    def finish_given_task(self):
        self.tracker.stop_without_task()
        if messagebox.askyesno("Modify description", "Do you want to modify the description?"):
            self.modify_description_interface()
        else:
            self.after_finish_given_task()

    def after_finish_given_task(self):
        self.tracker.finish()
        if self.tracker.finish_all():
            messagebox.showinfo(
                "Task Completed", "All tasks have been finished!")
            self.initial_interface()
        else:
            self.next_given_task_interface()  # back to initial interface

    def fail_given_task(self):
        self.tracker.fail()
        print("Task failed.")

        if messagebox.askyesno("Confirm Task Failure", "Do you want to discard the record?"):
            self.tracker.discard()

        self.current_given_task_interface()  # back to initial interface

    def mark_bad_task(self):
        # Show a confirmation dialog
        confirm = messagebox.askyesno(
            "Confirm Bad Task",
            "Mark the current task as bad?\nThe task you marked as a bad task will be permanently discarded."
        )

        if confirm:
            # Mark the task as not feasible if the user confirms
            self.tracker.task.is_feasible = False
            self.next_given_task_interface()

    def save_modified_description(self):
        entry_text = self.entry.get("1.0", "end-1c")
        if not entry_text:
            messagebox.showwarning(
                "Input Error", "Please enter your task description")
            return

        self.tracker.task.description = entry_text
        self.after_finish_given_task()

    def cancel_modify_description(self):
        if messagebox.askyesno("Confirm Cancel Meaning", "Do you want to discard the record?"):
            self.tracker.discard()
            self.current_given_task_interface()  # back to initial interface
        else:
            self.after_finish_given_task()

    """
    Free Task Mode Functions
    """

    def start_free_task_tracking(self):
        self.clear_interface()
        self.tracker.get_free_task()
        self.tracker.start()

        self.title_label.config(text="Tracking...")
        self.title_label.pack(pady=(30, 10))

        self.stop_button = tk.Button(
            self.root, text="Stop", command=self.stop_free_task_tracking,
            width=15, height=2, font=self.button_font)
        self.stop_button.pack(pady=10)

        self.root.iconify()  # Minimize window

    def stop_free_task_tracking(self):
        self.tracker.stop_without_task()
        self.clear_interface()
        self.title_label.config(text="")

        # Create info label
        self.description_label = tk.Label(
            self.root, text="Please enter task description:", font=("Helvetica", 15), bg="#f0f0f0")
        self.description_label.pack(pady=(10, 5))

        # Add input text box
        self.entry = tk.Text(self.root, font=("Arial", 14),
                             width=120, height=20)  # Adjust width and height
        self.entry.pack(pady=(10, 10))  # Leave 25 pixels at top, 10 pixels at bottom

        # Level dropdown box
        self.level_var = tk.StringVar(value="easy")  # Default select "easy"
        self.level_label = tk.Label(
            self.root, text="Please select task level:", font=("Helvetica", 15), bg="#f0f0f0")
        self.level_label.pack(pady=(10, 5))

        # Create and configure style
        style = ttk.Style()
        style.configure('TMenubutton', font=('Helvetica', 14))

        self.level_menu = ttk.OptionMenu(
            self.root, self.level_var, "easy", "medium", "hard", style='TMenubutton')
        self.level_menu.config(width=15)  # Increase width
        self.level_menu.pack(pady=(5, 20))

        # Set larger font for dropdown menu options
        menu = self.level_menu["menu"]
        for index in range(menu.index("end") + 1):
            menu.entryconfig(index, font=tkFont.Font(
                family="Helvetica", size=14))

        # Save button
        self.save_button = tk.Button(self.root, text="Save", command=self.save_free_task,
                                     width=15, height=2, font=self.button_font)
        self.save_button.pack(pady=(10, 20))

        # Discard button
        self.discard_button = tk.Button(
            self.root, text="Discard", command=self.discard_free_task,
            width=15, height=2, font=self.button_font)
        self.discard_button.pack(pady=(10, 20))

    def save_free_task(self):  # Save user-defined task
        entry_text = self.entry.get("1.0", "end-1c")
        selected_level = self.level_var.get()

        if not entry_text:
            messagebox.showwarning(
                "Input Error", "Please enter your task description")
            return

        task = Task(entry_text, 0, selected_level)
        self.tracker.save_free_task(task)
        self.free_task_interface()

    def discard_free_task(self):  # Discard user-defined task record
        self.tracker.discard()
        self.free_task_interface()

    def discard_non_task(self):  # Discard non-task oriented mode record
        self.tracker.discard()
        self.non_task_oriented_interface()

    """
    Non Task-Oriented Mode Functions
    """

    def start_non_task_tracking(self):
        self.clear_interface()
        self.tracker.start()

        self.title_label.config(text="Tracking...")
        self.title_label.pack(pady=30)

        self.stop_button = tk.Button(
            self.root, text="Stop", command=self.stop_non_task_tracking,
            width=15, height=2, font=self.button_font)
        self.stop_button.pack(pady=30)

        print("Non-task oriented tracking started...")

        self.root.iconify()  # Minimize window

    def stop_non_task_tracking(self):
        self.tracker.stop()
        self.clear_interface()

        self.save_button = tk.Button(
            self.root, text="Save", command=self.non_task_oriented_interface,
            width=15, height=2, font=self.button_font)
        self.save_button.pack(pady=30)

        self.discard_button = tk.Button(
            self.root, text="Discard", command=self.discard_non_task,
            width=15, height=2, font=self.button_font)
        self.discard_button.pack(pady=30)

        print("Non-task oriented tracking stopped.")


"""
Tools
"""


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 55
        y += self.widget.winfo_rooty() + 55
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip, text=self.text,
                         background="#f7f7f7", relief="solid", borderwidth=1)
        label.pack()

    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


def create_roundrectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
    points = [x1 + radius, y1,
              x1 + radius, y1,
              x2 - radius, y1,
              x2 - radius, y1,
              x2, y1,
              x2, y1 + radius,
              x2, y1 + radius,
              x2, y2 - radius,
              x2, y2 - radius,
              x2, y2,
              x2 - radius, y2,
              x2 - radius, y2,
              x1 + radius, y2,
              x1 + radius, y2,
              x1, y2,
              x1, y2 - radius,
              x1, y2 - radius,
              x1, y1 + radius,
              x1, y1 + radius,
              x1, y1]

    return canvas.create_polygon(points, **kwargs, smooth=True)


def main():
    root = tk.Tk()
    TrackerApp(root)
    root.mainloop()


if __name__ == "__main__":
    multiprocessing.freeze_support()  # important for pyinstaller
    main()
