from multiprocessing import Manager

manager = Manager()
event_queue = manager.Queue()