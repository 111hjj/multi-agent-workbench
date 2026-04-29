"""分析专家智能体 - 分析文本内容"""
from typing import Dict, Any, Optional, AsyncGenerator, List
from agents.base.base_agent import BaseAgent
from utils.logger import logger

class AnalyzeSpecialist(BaseAgent):
    """分析专家 - 分析文本内容（摘要、情感分析等）"""
    
    def get_default_model(self) -> str:
        return "deepseek-r1:8b"
    
    def get_prompt(self) -> str:
        return """你是一个文本分析专家。请对以下文本进行全面分析：

文本内容：
{text}

请从以下几个方面进行分析：
1. 文本的主要内容和主题
2. 关键信息和要点
3. 可能的情感倾向（积极/中性/消极）
4. 总结和建议

输出详细的分析报告。
"""
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行分析任务"""
        try:
            yield {
                "type": "status",
                "agent_type": "analyze",
                "status": "running",
                "current_step": "开始分析..."
            }
            
            text = task
            if context and context.get("text"):
                text = context["text"]
            
            yield {
                "type": "status",
                "agent_type": "analyze",
                "status": "running",
                "current_step": "分析文本..."
            }
            
            prompt = self.get_prompt().format(text=text[:3000])
            
            analysis_result = ""
            async for chunk in self._call_llm(prompt=prompt, stream=stream):
                analysis_result += chunk
                if stream:
                    yield {
                        "type": "chunk",
                        "content": chunk,
                        "agent_type": "analyze",
                        "current_step": "生成分析报告..."
                    }
            
            yield {
                "type": "agent_status",
                "agent_type": "analyze",
                "status": "completed",
                "progress": 100
            }
            
            yield {
                "type": "complete",
                "content": analysis_result,
                "sources": [],
                "confidence": 0.85,
                "agent_type": "analyze"
            }
                
        except Exception as e:
            logger.error(f"AnalyzeSpecialist.execute 失败: {e}", exc_info=True)
            yield {
                "type": "complete",
                "content": f"分析失败: {str(e)}",
                "error": True,
                "agent_type": "analyze"
            }
