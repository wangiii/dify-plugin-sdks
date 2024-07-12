from abc import ABC, abstractmethod
import asyncio
import collections
from concurrent.futures import ThreadPoolExecutor
import signal
import time
from dify_plugin.config.config import DifyPluginEnv
from dify_plugin.core.runtime.entities.io import PluginInStream
from dify_plugin.utils.io_reader import PluginInputStream
from dify_plugin.utils.io_writer import PluginOutputStream

class PeekableQueue[T](asyncio.Queue):
    _queue: collections.deque[T]

    def peek(self):
        if not self._queue:
            return None
        return self._queue[0]
    
    def get_nowait(self) -> T:
        return super().get_nowait()
    
    def remove(self, item: T):
        self._queue.remove(item)

class TaskEntity:
    def __init__(self, task: asyncio.Task, expired_at: float):
        self.task = task
        self.expired_at = expired_at

class IOServer(ABC):
    listener_task: asyncio.Task
    eventloop_task: asyncio.Task
    gc_task: asyncio.Task
    task_queue: PeekableQueue[TaskEntity]

    def __init__(self, config: DifyPluginEnv) -> None:
        self.config = config
        self.executer = ThreadPoolExecutor(max_workers=self.config.MAX_WORKER)
        self.task_queue = PeekableQueue()

    gc_task: asyncio.Task
    task_queue: PeekableQueue[TaskEntity]

    def close(self, *args):
        self.listener_task.cancel()
        self.eventloop_task.cancel()
        self.gc_task.cancel()

        self._remove_all_tasks()

    def _setup_signal_handler(self):
        signal.signal(signal.SIGINT, self.close)
    
    @abstractmethod
    async def _execute_request(self, session_id: str, data: dict):
        pass

    async def _setup_instruction_listener(self):
        def filter(data: PluginInStream) -> bool:
            if data.event == PluginInStream.Event.Request:
                return True
            return False
        
        async for data in (await PluginInputStream.read(filter)).read():
            asyncio.create_task(self._execute_request_thread(data.session_id, data.data))

    async def _gc_io_tasks(self, interval=0.05):
        """
        all tasks that are in ordered so that the oldest task is always at the front
        just need to check the front task if it is expired, cancel and remove it,
        then move to the next one
        """
        while asyncio.get_event_loop().is_running():
            if self.task_queue.empty():
                try:
                    await asyncio.sleep(interval)
                except asyncio.CancelledError:
                    break
                continue

            task = self.task_queue.peek()
            if task is None:
                await asyncio.sleep(interval)
                continue
            
            if task.expired_at < time.time():
                # remove the task
                task = self.task_queue.get_nowait()
                if not task.task.done():
                    task.task.cancel()
                # move to the next task immediately

    def _remove_all_tasks(self):
        while not self.task_queue.empty():
            task = self.task_queue.get_nowait()
            if not task.task.done():
                task.task.cancel()

    async def _execute_request_thread(self, session_id: str, data: dict):
        task = asyncio.create_task(self._execute_request(session_id, data))
        # create a task that will expire in $MAX_REQUEST_TIMEOUT second
        task_wrapper = TaskEntity(task, time.time() + self.config.MAX_REQUEST_TIMEOUT)
        # add done callback
        task_wrapper.task.add_done_callback(lambda t: self._remove_task(task_wrapper))
        # put the task in the queue
        self.task_queue.put_nowait(task_wrapper)
        # wait for the task to finish
        try:
            await task
            # loop.run_until_complete(task)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            PluginOutputStream.error(session_id=session_id, data={'error': str(e)})

        PluginOutputStream.log(data={'message': 'Task finished', 'session_id': session_id})

    def _remove_task(self, task: TaskEntity):
        try:
            self.task_queue.remove(task)
        except ValueError:
            pass

    async def _run(self):
        self._setup_signal_handler()

        self.listener_task = asyncio.create_task(self._setup_instruction_listener())
        self.eventloop_task = asyncio.create_task(PluginInputStream.event_loop())
        self.gc_task = asyncio.create_task(self._gc_io_tasks())

        await asyncio.gather(self.listener_task, self.eventloop_task, self.gc_task)

    def run(self):
        asyncio.run(self._run())
