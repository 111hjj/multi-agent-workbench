"""任务规划器 - 调用LLM将用户问题拆解为子任务列表"""
from typing import List, Dict, Any, Optional, AsyncGenerator
import json
import re
from agents.base.base_agent import BaseAgent
from utils.logger import logger

class PlannerAgent(BaseAgent):
    """任务规划器 - 分析用户请求并拆解为子任务"""
    
    def get_default_model(self) -> str:
        return "deepseek-r1:8b"
    
    def get_prompt(self) -> str:
        return """你是一个任务规划专家。将以下用户需求拆解为最多5个子任务。

每个子任务包含 type 和 params。

可选 type:
- retrieve: 从本地知识库检索信息
- crawl: 爬取指定URL的内容
- analyze: 分析给定文本（摘要、情感等）
- execute: 运行Python代码

输出格式：JSON数组，不要有其他文字。

示例：
[{"type": "retrieve", "params": {"query": "机器学习基础"}}, {"type": "analyze", "params": {"text": "检索结果"}}]
"""
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行规划任务"""
        try:
            yield {
                "type": "status",
                "agent_type": "planner",
                "status": "running",
                "current_step": "分析用户请求"
            }
            
            llm_response = ""
            async for chunk in self._call_llm(
                prompt=self._build_prompt(task, context),
                stream=stream
            ):
                llm_response += chunk
            
            subtasks = self._parse_subtasks(llm_response)
            
            yield {
                "type": "planning",
                "content": llm_response,
                "agent_type": "planner",
                "selected_agents": [s["type"] for s in subtasks],
                "agent_tasks": {s["type"]: s["params"] for s in subtasks},
                "subtasks": subtasks
            }
            
        except Exception as e:
            logger.error(f"PlannerAgent.execute 失败: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": f"规划失败: {str(e)}"
            }
    
    def _parse_subtasks(self, response: str) -> List[Dict[str, Any]]:
        """解析LLM的子任务结果"""
        try:
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
        except Exception as e:
            logger.warning(f"解析子任务失败: {e}")
        
        return self._fallback_planning(response)
    
    def _fallback_planning(self, query: str) -> List[Dict[str, Any]]:
        """后备规划逻辑"""
        query_lower = query.lower()
        subtasks = []
        
        has_url = bool(re.search(r'https?://[^\s]+', query))
        
        if has_url or any(kw in query_lower for kw in ["网页", "网站", "爬取", "抓取", "url"]):
            url_match = re.search(r'https?://[^\s]+', query)
            if url_match:
                url = url_match.group(0)
                subtasks.append({
                    "type": "crawl",
                    "params": {"url": url}
                })
        
        elif any(kw in query_lower for kw in ["分析", "总结", "摘要", "提取", "情感"]):
            subtasks.append({
                "type": "analyze",
                "params": {"text": query}
            })
        
        elif any(kw in query_lower for kw in ["代码", "运行", "执行", "计算", "python"]):
            subtasks.append({
                "type": "execute",
                "params": {"code": f"# 根据问题编写代码\n# {query}"}
            })
        
        else:
            subtasks.append({
                "type": "retrieve",
                "params": {"query": query}
            })
        
        return subtasks