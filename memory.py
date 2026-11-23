
import json
import re
from datetime import datetime, timezone
from uuid import uuid4

from config import MEMORY_FILE


class Memory:
    def __init__(self):
        self.data = {
            "tasks": [],
            "experiences": []
        }
        self.load()

    def load(self):
        if not MEMORY_FILE.exists():
            return

        try:
            loaded = json.loads(
                MEMORY_FILE.read_text(encoding="utf-8")
            )

            if isinstance(loaded, dict):
                self.data = {
                    "tasks": loaded.get("tasks", []),
                    "experiences": loaded.get("experiences", [])
                }

        except (OSError, json.JSONDecodeError):
            self.data = {
                "tasks": [],
                "experiences": []
            }

    def save(self):
        temporary = MEMORY_FILE.with_suffix(".tmp")

        temporary.write_text(
            json.dumps(self.data, indent=2),
            encoding="utf-8"
        )

        temporary.replace(MEMORY_FILE)

    def add_task(self, task):
        task_id = str(uuid4())

        self.data["tasks"].append({
            "id": task_id,
            "task": task,
            "status": "running",
            "started": datetime.now(timezone.utc).isoformat(),
            "finished": None
        })

        self.save()
        return task_id

    def finish_task(self, task_id, status):
        for task in reversed(self.data["tasks"]):
            if task["id"] == task_id:
                task["status"] = status
                task["finished"] = datetime.now(
                    timezone.utc
                ).isoformat()
                break

        self.save()

    def add_action(
        self,
        task_id,
        action,
        result,
        before=None,
        after=None,
        status="executed"
    ):
        experience = {
            "id": str(uuid4()),
            "task_id": task_id,
            "time": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "result": str(result)[:1000],
            "before": before,
            "after": after,
            "status": status
        }

        self.data["experiences"].append(experience)
        self.data["experiences"] = self.data["experiences"][-500:]

        self.save()

    def retrieve(self, task, limit=5):
        words = set(re.findall(r"\w+", task.lower()))

        scored = []

        for item in self.data["tasks"]:
            previous = set(
                re.findall(r"\w+", item["task"].lower())
            )

            if not previous:
                continue

            score = len(words & previous) / len(words | previous)

            if score > 0.08:
                scored.append((score, item))

        scored.sort(key=lambda item: item[0], reverse=True)

        results = []

        for score, task_item in scored[:limit]:
            actions = [
                experience
                for experience in self.data["experiences"]
                if experience["task_id"] == task_item["id"]
            ]

            results.append({
                "task": task_item["task"],
                "outcome": task_item["status"],
                "similarity": round(score, 2),
                "actions": [
                    {
                        "action": item["action"],
                        "result": item["result"],
                        "status": item["status"]
                    }
                    for item in actions[-10:]
                ]
            })

        return results

    def recent_actions(self, limit=10):
        return [
            {
                "action": item["action"],
                "result": item["result"],
                "status": item["status"]
            }
            for item in self.data["experiences"][-limit:]
        ]
