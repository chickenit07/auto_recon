import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def runHttpxCommand():
    # Your implementation for running Httpx command
    print("Running Httpx command.")

def monitor_file_creation(directory, filename):
    stop_flag = False

    def file_created_callback():
        nonlocal stop_flag
        # Run HttpxCommand when the file is created
        runHttpxCommand()
        # Set the stop flag to True to exit the loop
        stop_flag = True

    class FileCreationHandler(FileSystemEventHandler):
        def on_created(self, event):
            if not event.is_directory and event.src_path.endswith(filename):
                print(f"File '{filename}' has been created.")
                file_created_callback()

    event_handler = FileCreationHandler()
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=False)
    observer.start()

    try:
        while not stop_flag:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

if __name__ == "__main__":
    # Replace '/path/to/directory' with the directory you want to monitor
    directory_to_watch = '/tmp'
    
    # Replace 'your_file.txt' with the pre-defined filename you want to monitor
    filename_to_watch = 'test.txt'

    monitor_file_creation(directory_to_watch, filename_to_watch)
