# Importer les bibliothèques
print("Loading lib : BalatroFileObserver ... ", end='')

import os
import time
import queue
import threading

from collections import defaultdict

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

##########################################################################
# Constantes
##########################################################################
PATTERNS = ["*.jkr"]
IGNORE_PATTERNS = None
IGNORE_DIRECTORIES = True
CASE_SENSITIVE = True
GO_RECURSIVELY = False
POLLING_INTERVAL = 0.1
EVENT_DELAY = 0.05  # Délai en secondes

##########################################################################
# Classe balatroFileObserver gérant la surveillance
# des fichiers de config et sauvegarde de BAlatro
##########################################################################
class BalatroFileObserver(PatternMatchingEventHandler, threading.Thread):
	def __init__(self, dirPath):
		super().__init__(patterns=PATTERNS, ignore_patterns=IGNORE_PATTERNS,
						 ignore_directories=IGNORE_DIRECTORIES, case_sensitive=CASE_SENSITIVE)
		self.dirPath = dirPath
		self.queue = queue.Queue()
		self.event = threading.Event()
		self.last_event_time = defaultdict(float)
		self._initialize_observer()

	def _initialize_observer(self):
		self.observer = Observer()
		self.observer.schedule(self, self.dirPath, recursive=GO_RECURSIVELY)
	
	def run(self):
		self.observer.start()
	
	@staticmethod
	def _is_event_valid(last_time, current_time):
		return current_time - last_time > EVENT_DELAY
	
	def _handle_event(self, event):
		current_time = time.time()
		if self._is_event_valid(self.last_event_time[event.src_path], current_time):
			self.last_event_time[event.src_path] = current_time
			self.queue.put(event.src_path)
			self.event.set()
			print(f"Modifié : {current_time} - {event.src_path}")
	
	def on_deleted(self, event):
		self._handle_event(event)
	
	def on_modified(self, event):
		self._handle_event(event)
	
	def stop(self):
		self.observer.stop()
		self.observer.join()






print("OK")
if __name__ == "__main__":
	balatroSaveDir = os.path.join(os.getenv('APPDATA'), "Balatro", "1")
	# balatroSaveDir = os.path.join(os.getenv('APPDATA'), "Balatro", "3")
	
	balObs = BalatroFileObserver(balatroSaveDir)
	
	balObs.start()
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		balObs.stop()
		balObs.join()























