"""任务协调器 - 调度专家智能体执行子任务"""
from typing import Dict, Any, Optional, AsyncGenerator, List
from agents.base.base_agent import BaseAgent
from utils.logger import logger

class CoordinatorAgent(BaseAgent):
    """任务协调器 - 调度和执行子任务"""
    
    def get_default_model(self) -> str:
        return "deepseek-r1:8b"
    
    def get_prompt(self) -> str:
        return """你是一个任务协调专家。
分析用户的问题，确定需要哪些专家Agent来完成任务。

可用的专家Agent类型：
- document_retrieval: 从本地知识库检索相关文档
- crawl: 爬取指定网页内容
- analyze: 分析文本内容（摘要、情感分析等）
- code: 生成Python代码（编写函数、类等）
- execute: 执行已有的Python代码
- summary: 汇总多个结果

请根据用户需求，选择最合适的专家Agent组合。

输出格式：JSON格式，包含 selected_agents（Agent类型列表）和 reasoning（选择理由）。
示例：{"selected_agents": ["document_retrieval", "summary"], "reasoning": "用户需要从知识库检索信息并进行总结"}
"""
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行协调任务"""
        try:
            yield {
                "type": "status",
                "agent_type": "coordinator",
                "status": "running",
                "current_step": "分析用户请求"
            }
            
            llm_response = ""
            async for chunk in self._call_llm(
                prompt=self._build_prompt(task, context),
                stream=stream
            ):
                llm_response += chunk
            
            selected_agents = self._parse_agent_selection(llm_response)
            
            yield {
                "type": "planning",
                "content": llm_response,
                "agent_type": "coordinator",
                "selected_agents": selected_agents.get("selected_agents", []),
                "agent_tasks": {},
                "reasoning": selected_agents.get("reasoning", "")
            }
            
        except Exception as e:
            logger.error(f"CoordinatorAgent.execute 失败: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": f"协调失败: {str(e)}"
            }
    
    def _parse_agent_selection(self, response: str) -> Dict[str, Any]:
        """解析LLM的Agent选择结果"""
        try:
            import re
            import json
            
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
        except Exception as e:
            logger.warning(f"解析Agent选择失败: {e}")
        
        return self._fallback_selection(response)
    
    def _fallback_selection(self, query: str) -> Dict[str, Any]:
        """后备选择逻辑"""
        query_lower = query.lower()
        selected_agents = []
        
        has_url = bool(re.search(r'https?://[^\s]+', query))
        
        if has_url or any(kw in query_lower for kw in ["网页", "网站", "爬取", "抓取"]):
            selected_agents.append("crawl")
        elif any(kw in query_lower for kw in ["分析", "总结", "摘要", "情感"]):
            selected_agents.append("analyze")
        elif any(kw in query_lower for kw in ["运行", "执行", "运行代码", "执行代码"]):
            selected_agents.append("execute")
        elif any(kw in query_lower for kw in ["编写", "写代码", "生成代码", "代码示例"]):
            selected_agents.append("code")
        else:
            selected_agents.append("document_retrieval")
        
        selected_agents.append("summary")
        
        return {
            "selected_agents": selected_agents,
            "reasoning": "使用后备选择逻辑"
        }
