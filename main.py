"""FastAPI应用入口 - 多智能体协同知识工作台"""
import warnings
warnings.filterwarnings("ignore", message=".*pkg_resources is deprecated.*", category=UserWarning)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
from threading import Thread
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="多智能体协同知识工作台",
    description="支持任务拆解、多Agent协作、RAG检索、网页爬取的知识工作台",
    version="v1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tasks: Dict[str, Dict[str, Any]] = {}

class TaskRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None

class TaskResponse(BaseModel):
    task_id: str

class AgentStatus(BaseModel):
    agent_type: str
    status: str
    progress: Optional[int] = None
    current_step: Optional[str] = None

class StatusResponse(BaseModel):
    status: str
    progress: Optional[int] = None
    message: Optional[str] = None
    agent_statuses: Optional[List[AgentStatus]] = None

class ResultResponse(BaseModel):
    result: Optional[str] = None
    status: str
    error: Optional[str] = None

def run_agent_pipeline(task_id: str, query: str, context: Optional[Dict[str, Any]] = None):
    try:
        tasks[task_id]["status"] = "running"
        tasks[task_id]["progress"] = 0
        tasks[task_id]["message"] = "正在初始化..."
        tasks[task_id]["agent_statuses"] = [
            {"agent_type": "planner", "status": "pending", "progress": 0, "current_step": "等待中"},
            {"agent_type": "coordinator", "status": "pending", "progress": 0, "current_step": "等待中"},
            {"agent_type": "specialists", "status": "pending", "progress": 0, "current_step": "等待中"},
            {"agent_type": "summary", "status": "pending", "progress": 0, "current_step": "等待中"}
        ]
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_execute_workflow(query, context, task_id))
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["result"] = result
            tasks[task_id]["progress"] = 100
            tasks[task_id]["message"] = "任务完成"
            update_agent_status(task_id, "summary", "completed", 100, "汇总完成")
        finally:
            loop.close()
            
    except Exception as e:
        print(f"任务执行失败 {task_id}: {e}")
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        tasks[task_id]["message"] = f"任务失败: {str(e)}"

def update_agent_status(task_id: str, agent_type: str, status: str, progress: int, current_step: str):
    if task_id in tasks and "agent_statuses" in tasks[task_id]:
        for agent in tasks[task_id]["agent_statuses"]:
            if agent["agent_type"] == agent_type:
                agent["status"] = status
                agent["progress"] = progress
                agent["current_step"] = current_step
                break

async def _execute_workflow(query: str, context: Optional[Dict[str, Any]], task_id: str) -> str:
    from agents.workflow.agent_workflow import AgentWorkflow
    
    workflow = AgentWorkflow()
    
    results = []
    async for result in workflow.execute_workflow(query, context, stream=False):
        if result.get("type") == "planning":
            update_agent_status(task_id, "planner", "completed", 100, "规划完成")
            update_agent_status(task_id, "coordinator", "running", 0, "调度任务")
        elif result.get("type") == "agent_status":
            agent_type = result.get("agent_type")
            status = result.get("status")
            progress = result.get("progress", 0)
            current_step = result.get("current_step", "")
            
            if agent_type in ["document_retrieval", "crawl", "analyze", "execute", "retrieve", "concept_explanation", "code"]:
                update_agent_status(task_id, "specialists", status, progress, current_step)
        elif result.get("type") == "agent_result":
            results.append({"content": result.get("content", ""), "error": result.get("error", False)})
        elif result.get("type") == "complete":
            agent_results = result.get("agent_results", [])
            if not isinstance(agent_results, list):
                agent_results = []
            for agent_result in agent_results:
                results.append({
                    "content": agent_result.get("content", ""),
                    "error": agent_result.get("error", False)
                })
            update_agent_status(task_id, "summary", "completed", 100, "汇总完成")
    
    success_results = [r for r in results if not r.get("error")]
    
    if success_results:
        from agents.summary.summary import Summary
        summary = Summary()
        subtask_results = [{"subtask": {"type": "expert"}, "result": r} for r in success_results]
        return await summary.summarize(query, subtask_results)
    elif results:
        error_messages = [r.get("content", "") for r in results if r.get("error")]
        return "⚠️ 任务执行失败\n\n" + "\n\n".join(error_messages)
    
    return "任务执行完成"

@app.post("/task", response_model=TaskResponse)
async def create_task(req: TaskRequest):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "status": "pending",
        "result": None,
        "progress": 0,
        "message": "任务已创建",
        "error": None
    }
    
    thread = Thread(
        target=run_agent_pipeline,
        args=(task_id, req.query, req.context)
    )
    thread.start()
    
    print(f"创建任务: {task_id} - {req.query[:50]}...")
    
    return TaskResponse(task_id=task_id)

@app.get("/status/{task_id}", response_model=StatusResponse)
async def get_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks[task_id]
    return StatusResponse(
        status=task["status"],
        progress=task.get("progress"),
        message=task.get("message"),
        agent_statuses=task.get("agent_statuses")
    )

@app.get("/result/{task_id}", response_model=ResultResponse)
async def get_result(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks[task_id]
    return ResultResponse(
        result=task.get("result"),
        status=task["status"],
        error=task.get("error")
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/")
async def root():
    return {"message": "多智能体协同知识工作台 API", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)