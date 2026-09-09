from collections import deque

class JobQueue:
    def __init__(self):
        self._q=deque()
        self._ids=set()

    def enqueue(self,j):
        if j["job_id"] in self._ids:
            raise ValueError("DUPLICATE_JOB")
        self._q.append(j)
        self._ids.add(j["job_id"])

    def dequeue(self):
        return self._q.popleft() if self._q else None

    def __len__(self):
        return len(self._q)
