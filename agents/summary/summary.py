"""总结器 - 汇总所有子任务的结果"""
from typing import List, Dict, Any, Optional, AsyncGenerator
from agents.base.base_agent import BaseAgent
from utils.logger import logger

class Summary(BaseAgent):
    """总结器 - 汇总所有子任务的结果"""
    
    def get_default_model(self) -> str:
        return "deepseek-r1:8b"
    
    def get_prompt(self) -> str:
        return """你是一个总结专家。请基于以下子任务的执行结果，为用户问题提供全面、准确的回答。

用户问题：{query}

子任务执行结果：
{results_text}

请提供：
1. 对用户问题的直接回答
2. 关键信息汇总
3. 重要发现或结论
4. 如有需要，提供进一步建议

请用清晰、结构化的方式组织你的回答：
"""
    
    async def summarize(self, query: str, subtask_results: List[Dict[str, Any]]) -> str:
        """
        汇总所有子任务的结果
        
        Args:
            query: 原始用户问题
            subtask_results: 子任务结果列表
            
        Returns:
            最终汇总结果
        """
        try:
            logger.info(f"Summary: 开始汇总 {len(subtask_results)} 个子任务结果...")
            
            results_text = self._format_results(subtask_results)
            
            summary = await self._generate_summary(query, results_text)
            
            return summary
            
        except Exception as e:
            logger.error(f"Summary.summarize 失败: {e}", exc_info=True)
            return self._simple_summary(subtask_results)
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行总结任务"""
        try:
            yield {
                "type": "status",
                "agent_type": "summary",
                "status": "running",
                "current_step": "开始汇总..."
            }
            
            query = task
            subtask_results = context.get("subtask_results", []) if context else []
            
            summary_result = await self.summarize(query, subtask_results)
            
            yield {
                "type": "agent_status",
                "agent_type": "summary",
                "status": "completed",
                "progress": 100
            }
            
            yield {
                "type": "complete",
                "content": summary_result,
                "sources": [],
                "confidence": 0.9,
                "agent_type": "summary"
            }
            
        except Exception as e:
            logger.error(f"Summary.execute 失败: {e}", exc_info=True)
            yield {
                "type": "complete",
                "content": f"总结失败: {str(e)}",
                "error": True,
                "agent_type": "summary"
            }
    
    def _format_results(self, subtask_results: List[Dict[str, Any]]) -> str:
        """格式化子任务结果"""
        formatted = []
        
        for i, item in enumerate(subtask_results):
            subtask = item.get("subtask", {})
            result = item.get("result", "")
            
            task_type = subtask.get("type", "unknown")
            params = subtask.get("params", {})
            
            formatted.append(f"""
=== 子任务 {i+1} ===
类型: {task_type}
参数: {params}
结果:
{result}
""")
        
        return "\n".join(formatted)
    
    async def _generate_summary(self, query: str, results_text: str) -> str:
        """生成最终总结"""
        try:
            prompt = self.get_prompt().format(query=query, results_text=results_text[:5000])
            
            summary_result = ""
            async for chunk in self._call_llm(prompt=prompt, stream=False):
                summary_result += chunk
            
            return summary_result
                
        except Exception as e:
            logger.error(f"生成总结失败: {e}", exc_info=True)
            return self._simple_summary_from_text(results_text)
    
    def _simple_summary(self, subtask_results: List[Dict[str, Any]]) -> str:
        """简单汇总（后备方案）"""
        results = []
        for item in subtask_results:
            subtask = item.get("subtask", {})
            result = item.get("result", "")
            task_type = subtask.get("type", "unknown")
            results.append(f"[{task_type}] {result[:200]}")
        
        return "\n\n".join(results)
    
    def _simple_summary_from_text(self, results_text: str) -> str:
        """从文本生成简单总结"""
        lines = results_text.split("\n")
        summary_lines = [line for line in lines if line.strip() and not line.startswith("===")]
        return "\n".join(summary_lines[:20])