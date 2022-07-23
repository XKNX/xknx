import logging
from threading import Thread, Event

logger = logging.getLogger("xknx.log")


class BaseThread(Thread):
    """ Base class that can be used by threads that overwrite run and need a way to stop the thread """

    def __init__(self, name: str = ""):
        """ initialize an event and set the event, which equals _is_active==True """
        super().__init__(name=name)
        self._name = name
        self._is_active = Event()
        self._is_active.set()

    def stop(self):
        """ clears the `_is_active` flag which is equivalent to _is_active==False """
        if self._name:
            logger.debug(f"stopping thread {self._name}")
        self._is_active.clear()
