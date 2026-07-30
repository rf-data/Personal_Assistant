# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler
# # LoggingEventHandler
# import time
# import subprocess

# class DataDropHandler(FileSystemEventHandler):
#     def on_created(self, event):
#         if event.src_path.endswith('.csv'):
#             print(f"New file: {event.src_path}")
#             subprocess.run(["python", "process_data.py", event.src_path])

# observer = Observer()
# observer.schedule(DataDropHandler(), path="data/", recursive=False)
# observer.start()

# try:
#     # while True:
#     #     time.sleep(1)
#     while observer.isAlive():
#         observer.join(1)

# except KeyboardInterrupt:
#     observer.stop()

# observer.join()

# ##################

# def on_modified(self, event):
#     if "error" in event.src_path:
#         with open(event.src_path, 'r') as log_file:
#             lines = log_file.readlines()
#             if "Traceback" in lines[-1]:
#                 print("New error detected. Check logs.")
#                 # Optionally send an email or Slack alert


# ##############

# import time
# from watchdog.events import FileSystemEvent, FileSystemEventHandler
# from watchdog.observers import Observer

# class MyEventHandler(FileSystemEventHandler):
#     def on_modified(self, event):
#         print(f"File {event.src_path} was modified")

#     def on_created(self, event):
#         print(f"File {event.src_path} was created")

#     def on_deleted(self, event):
#         print(f"File {event.src_path} was deleted")

#     def on_moved(self, event):
#         print(f"File moved from {event.src_path} to {event.dest_path}")
# # Set up the observer
# event_handler = MyEventHandler()
# observer = Observer()
# observer.schedule(event_handler, path='./watched_directory', recursive=True)
# # Start monitoring
# observer.start()
# try:
#     while True:
#         time.sleep(1)
# except KeyboardInterrupt:
#     observer.stop()
# observer.join()


# ####################################
# # Automated File Processing Pipeline
# ####################################

# import os
# import shutil
# from watchdog.events import FileSystemEventHandler
# from watchdog.observers import Observer

# class FileProcessorHandler(FileSystemEventHandler):
#     def __init__(self, input_dir, output_dir, archive_dir):
#         self.input_dir = input_dir
#         self.output_dir = output_dir
#         self.archive_dir = archive_dir

#     def on_created(self, event):
#         if not event.is_directory and event.src_path.endswith('.txt'):
#             self.process_file(event.src_path)

#     def process_file(self, filepath):
#         filename = os.path.basename(filepath)

#         # Process the file (example: convert to uppercase)
#         with open(filepath, 'r') as f:
#             content = f.read().upper()

#         # Save processed file
#         output_path = os.path.join(self.output_dir, f"processed_{filename}")
#         with open(output_path, 'w') as f:
#             f.write(content)

#         # Archive original file
#         archive_path = os.path.join(self.archive_dir, filename)
#         shutil.move(filepath, archive_path)

#         print(f"Processed {filename} -> {output_path}")

# ####################################
# # Real-time Log Analysis
# ####################################

# import re
# from watchdog.events import FileSystemEventHandler

# class LogMonitorHandler(FileSystemEventHandler):
#     def __init__(self):
#         self.error_patterns = [
#             r'ERROR',
#             r'CRITICAL',
#             r'Exception',
#             r'Failed'
#         ]

#     def on_modified(self, event):
#         if event.src_path.endswith('.log'):
#             self.analyze_log_changes(event.src_path)

#     def analyze_log_changes(self, log_path):
#         try:
#             with open(log_path, 'r') as f:
#                 # Read the last few lines
#                 lines = f.readlines()[-10:]  # Last 10 lines

#             for line in lines:
#                 for pattern in self.error_patterns:
#                     if re.search(pattern, line, re.IGNORECASE):
#                         self.send_alert(log_path, line.strip())
#                         break
#         except Exception as e:
#             print(f"Error reading log file: {e}")

#     def send_alert(self, log_path, error_line):
#         # Send email, Slack notification, etc.
#         print(f"ALERT from {log_path}: {error_line}")

# ####################################
# # Development Environment Auto-Reloader
# ####################################
# import subprocess
# import os
# import signal
# from watchdog.events import FileSystemEventHandler

# class DevServerHandler(FileSystemEventHandler):
#     def __init__(self, command):
#         self.command = command
#         self.process = None
#         self.start_server()

#     def start_server(self):
#         if self.process:
#             self.process.terminate()
#             self.process.wait()

#         print("Starting development server...")
#         self.process = subprocess.Popen(self.command, shell=True)

#     def on_modified(self, event):
#         if (not event.is_directory and
#             (event.src_path.endswith('.py') or
#              event.src_path.endswith('.js') or
#              event.src_path.endswith('.css'))):
#             print(f"File changed: {event.src_path}")
#             self.start_server()

#     def cleanup(self):
#         if self.process:
#             self.process.terminate()
#             self.process.wait()

# ####################################
# # Automated Backup System
# ####################################
# import os
# import shutil
# import datetime
# from watchdog.events import FileSystemEventHandler

# class BackupHandler(FileSystemEventHandler):
#     def __init__(self, backup_dir, file_extensions=None):
#         self.backup_dir = backup_dir
#         self.file_extensions = file_extensions or ['.py', '.js', '.css', '.html']
#         os.makedirs(backup_dir, exist_ok=True)

#     def on_modified(self, event):
#         if not event.is_directory and self.should_backup(event.src_path):
#             self.create_backup(event.src_path)

#     def should_backup(self, filepath):
#         return any(filepath.endswith(ext) for ext in self.file_extensions)

#     def create_backup(self, filepath):
#         filename = os.path.basename(filepath)
#         timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
#         backup_filename = f"{timestamp}_{filename}"
#         backup_path = os.path.join(self.backup_dir, backup_filename)

#         try:
#             shutil.copy2(filepath, backup_path)
#             print(f"Backed up: {filepath} -> {backup_path}")
#         except Exception as e:
#             print(f"Backup failed for {filepath}: {e}")


# ####################################
# # Smart File Organizer
# ####################################


# import os
# import shutil
# from datetime import datetime
# from watchdog.events import FileSystemEventHandler

# class FileOrganizerHandler(FileSystemEventHandler):
#     def __init__(self, base_dir):
#         self.base_dir = base_dir
#         self.file_categories = {
#             'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'],
#             'documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
#             'videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv'],
#             'audio': ['.mp3', '.wav', '.flac', '.aac'],
#             'archives': ['.zip', '.rar', '.tar', '.gz', '.7z'],
#             'code': ['.py', '.js', '.html', '.css', '.java', '.cpp']
#         }

#     def on_created(self, event):
#         if not event.is_directory:
#             self.organize_file(event.src_path)

#     def organize_file(self, filepath):
#         filename = os.path.basename(filepath)
#         file_ext = os.path.splitext(filename)[1].lower()

#         # Determine category
#         category = 'misc'  # default
#         for cat, extensions in self.file_categories.items():
#             if file_ext in extensions:
#                 category = cat
#                 break

#         # Create category directory
#         category_dir = os.path.join(self.base_dir, category)
#         os.makedirs(category_dir, exist_ok=True)

#         # Create date subdirectory
#         date_dir = os.path.join(category_dir, datetime.now().strftime("%Y-%m"))
#         os.makedirs(date_dir, exist_ok=True)

#         # Move file
#         destination = os.path.join(date_dir, filename)
#         try:
#             shutil.move(filepath, destination)
#             print(f"Organized: {filename} -> {destination}")
#         except Exception as e:
#             print(f"Failed to organize {filename}: {e}")


# Event Filtering
# from watchdog.events import PatternMatchingEventHandler

# # Only watch for Python files
# class PythonFileHandler(PatternMatchingEventHandler):
#     def __init__(self):
#         super().__init__(patterns=['*.py'], ignore_directories=True)

#     def on_modified(self, event):
#         print(f"Python file modified: {event.src_path}")


# Recursive vs Non-Recursive Monitoring
# # Watch subdirectories recursively
# observer.schedule(handler, path='./project', recursive=True)

# # Watch only the specified directory
# observer.schedule(handler, path='./project', recursive=False)


# Multiple Path Monitoring
# # Monitor multiple directories with the same handler
# paths_to_watch = ['./src', './tests', './docs']
# for path in paths_to_watch:
#     observer.schedule(handler, path, recursive=True)


# Debouncing Multiple Events
# import threading
# from collections import defaultdict

# class DebouncedHandler(FileSystemEventHandler):
#     def __init__(self, delay=1.0):
#         self.delay = delay
#         self.timers = defaultdict(lambda: None)

#     def on_modified(self, event):
#         filepath = event.src_path

#         # Cancel previous timer
#         if self.timers[filepath]:
#             self.timers[filepath].cancel()

#         # Set new timer
#         self.timers[filepath] = threading.Timer(
#             self.delay,
#             self._process_file,
#             [filepath]
#         )
#         self.timers[filepath].start()

#     def _process_file(self, filepath):
#         print(f"Processing (debounced): {filepath}")
#         # Your actual processing logic here
#         del self.timers[filepath]
