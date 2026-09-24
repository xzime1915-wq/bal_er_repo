import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from agent.tools import web_tools
from agent.gemini_client import chat_simple

_sub_lock = asyncio.Lock()


@dataclass
class SubAgentJob:
    id: str
    label: str
    task: str
    status: str = "running"
    progress: str = ""
    result: str = ""
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


_jobs: dict[str, SubAgentJob] = {}


def list_jobs() -> list[dict]:
    return [
        {
            "id": j.id,
            "label": j.label,
            "task": j.task,
            "status": j.status,
            "progress": j.progress,
            "result": j.result[:500] if j.result else "",
            "started_at": j.started_at,
        }
        for j in _jobs.values()
    ]


async def _run_job(job: SubAgentJob) -> None:
    try:
        job.progress = "Searching web..."
        search = await web_tools.web_search(job.task, max_results=5)
        job.progress = "Summarizing..."
        try:
            summary = await asyncio.wait_for(
                chat_simple(
                    f"SENZ sub-agent. Task: {job.task}\nWeb:\n{search}\nReply 3-5 sentences."
                ),
                timeout=20,
            )
        except Exception:
            summary = f"Web results (AI quota off):\n{search[:1200]}"
        job.result = summary
        job.status = "done"
        job.progress = "Complete"
    except Exception as e:
        job.status = "error"
        job.result = str(e)
        job.progress = "Failed"


async def delegate_task(task: str, label: str = "Sub-agent") -> str:
    job_id = str(uuid.uuid4())[:8]
    job = SubAgentJob(id=job_id, label=label, task=task)
    async with _sub_lock:
        _jobs[job_id] = job
    asyncio.create_task(_run_job(job))
    return json_dumps({"delegated": True, "job_id": job_id, "label": label})


def json_dumps(obj: dict) -> str:
    import json

    return json.dumps(obj, ensure_ascii=False)
