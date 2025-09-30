class Observer:
    def update(self, value):
        self.value = value

class Subject:
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        self._observers.append(observer)

    def notify(self, value):
        for observer in self._observers:
            observer.update(value)
