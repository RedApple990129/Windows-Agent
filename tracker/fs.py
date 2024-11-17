import os
import shutil
import ctypes
import subprocess
import time


def ensure_folder(folder_path):
    # Ensure the folder exists, create if it doesn't
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def hide_folder(folder_path):
    # Set folder attribute to hidden
    FILE_ATTRIBUTE_HIDDEN = 0x02
    ctypes.windll.kernel32.SetFileAttributesW(folder_path, FILE_ATTRIBUTE_HIDDEN)


def set_hidden_file(file_path, hide=True):
    # Set or remove hidden attribute
    if hide:
        os.system(f'attrib +h "{file_path}"')
    else:
        os.system(f'attrib -h "{file_path}"')


class FolderReset:
    def __init__(self, folder_path="./files", backup_path="./__files__"):
        self.folder_path = folder_path  # Visible folder
        self.backup_path = backup_path  # Backup hidden folder
        if self.backup_path and not os.path.exists(backup_path):
            self.backup_path = None  # No backup path
        self.reset()

    def reset(self):
        if self.backup_path:
            # Ensure the folder exists
            ensure_folder(self.folder_path)

            # Attempt to clear the original folder
            MAX_RETRIES = 2
            for attempt in range(MAX_RETRIES):
                try:
                    # On Windows, use system command to delete
                    subprocess.call(f'rd /s /q "{self.folder_path}"', shell=True)
                    break  # Exit loop if successfully deleted
                except PermissionError as e:
                    print(f"Except error in folder reset: {e}. Retrying ({attempt + 1}/{MAX_RETRIES})...")
                    time.sleep(3)
            else:
                print("WARNING: Failed to clear folder after multiple attempts.")
                return  # Exit method, do not proceed

            # Restore backup content, make folder writable
            shutil.copytree(self.backup_path, self.folder_path)

        # else: No backup path, no reset needed


def delete_file(file_path):
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            print(f"Failed to delete {file_path}: {e}")


def delete_folder(folder_path):
    try:
        if os.name == 'nt':
            # On Windows, use system command to delete
            subprocess.call(f'rd /s /q "{folder_path}"', shell=True)
        else:
            # On other systems, use shutil to delete
            shutil.rmtree(folder_path)
    except OSError as e:
        print(f"Failed to delete {folder_path}: {e}")
