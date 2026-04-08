import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import pendulum
from core.logger import logger
from core.bot_config import config
from fnmatch import fnmatch

class ActivityTracker(FileSystemEventHandler):
    def __init__(self, root_dir=None):
        self.root_dir = root_dir or os.getcwd()
        self.max_activities = 100
        self.activities = []
        self.config = config.activity_tracker

    def _is_ignored(self, path):
        """Checks if a path should be ignored based on glob patterns."""
        ignored_patterns = self.config.IGNORED_PATHS
        relative_path = os.path.relpath(path, self.root_dir).replace("\\", "/")
        
        for pattern in ignored_patterns:
            if fnmatch(relative_path, pattern) or any(fnmatch(p, pattern) for p in relative_path.split("/")):
                return True
        return False

    def on_modified(self, event):
        if not event.is_directory and not self._is_ignored(event.src_path):
            self._add_activity("change", event.src_path, "File modified")

    def on_created(self, event):
        if not self._is_ignored(event.src_path):
            type_str = "directory" if event.is_directory else "file"
            self._add_activity("add", event.src_path, f"{type_str.capitalize()} created")

    def on_deleted(self, event):
        if not self._is_ignored(event.src_path):
            type_str = "directory" if event.is_directory else "file"
            self._add_activity("delete", event.src_path, f"{type_str.capitalize()} deleted")

    def on_moved(self, event):
        if not self._is_ignored(event.dest_path):
            self._add_activity("rename", event.dest_path, f"Moved from {os.path.basename(event.src_path)}")

    def _add_activity(self, type_str, file_path, details=""):
        timestamp = pendulum.now().format('HH:mm:ss')
        relative_path = os.path.relpath(file_path, self.root_dir)
        
        activity = {
            "type": type_str,
            "path": relative_path,
            "details": details,
            "timestamp": timestamp
        }
        
        self.activities.insert(0, activity)
        if len(self.activities) > self.max_activities:
            self.activities = self.activities[:self.max_activities]
            
        # Log to console using the standard logger logic
        icons = {"add": "✚", "change": "✎", "delete": "✖", "rename": "↪"}
        icon = icons.get(type_str, "•")
        
        # Color mapping would happen in logger, but for activity tracker we keep it simple
        logger.system(f"{icon} {type_str.upper()} │ {relative_path} {details}")

def init_activity_tracker(root_dir=None):
    """
    Initializes the activity tracker with a watchdog observer.
    """
    tracker = ActivityTracker(root_dir)
    
    if not tracker.config.ENABLED:
        logger.warning("Activity tracker is disabled in config.")
        return None

    observer = Observer()
    observer.schedule(tracker, tracker.root_dir, recursive=True)
    observer.start()
    
    logger.success("Activity tracker initialized (Watchdog).")
    return observer
