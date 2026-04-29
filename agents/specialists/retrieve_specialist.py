"""检索专家智能体 - 从本地知识库检索相关文档"""
from typing import Dict, Any, Optional, AsyncGenerator, List
from agents.base.base_agent import BaseAgent
from utils.logger import logger

class RetrieveSpecialist(BaseAgent):
    """检索专家 - 从向量数据库检索相关文档"""
    
    def get_default_model(self) -> str:
        return "deepseek-r1:8b"
    
    def get_prompt(self) -> str:
        return """你是一个文档检索专家。根据用户的查询，从知识库中检索最相关的信息。
        
请分析检索结果，用自然、友好的语言总结给用户。
"""
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行检索任务"""
        try:
            yield {
                "type": "status",
                "agent_type": "retrieve",
                "status": "running",
                "current_step": "开始检索..."
            }
            
            query = task
            if context and context.get("query"):
                query = context["query"]
            
            yield {
                "type": "status",
                "agent_type": "retrieve",
                "status": "running",
                "current_step": f"检索查询: {query[:30]}..."
            }
            
            results = await self._retrieve_documents(query)
            
            if results:
                yield {
                    "type": "agent_status",
                    "agent_type": "retrieve",
                    "status": "completed",
                    "progress": 100,
                    "details": f"检索到 {len(results)} 条结果"
                }
                
                yield {
                    "type": "complete",
                    "content": self._format_results(results),
                    "sources": [r.get("metadata", {}).get("source", "unknown") for r in results],
                    "confidence": 0.8,
                    "agent_type": "retrieve"
                }
            else:
                yield {
                    "type": "complete",
                    "content": "未检索到相关文档",
                    "sources": [],
                    "confidence": 0.3,
                    "agent_type": "retrieve"
                }
                
        except Exception as e:
            logger.error(f"RetrieveSpecialist.execute 失败: {e}", exc_info=True)
            yield {
                "type": "complete",
                "content": f"检索失败: {str(e)}",
                "error": True,
                "agent_type": "retrieve"
            }
    
    async def _retrieve_documents(self, query: str) -> List[Dict[str, Any]]:
        """从向量数据库检索文档"""
        try:
            from rag.retriever import HybridRetriever
            
            retriever = HybridRetriever(top_k=5)
            return await retriever.retrieve(query)
        except Exception as e:
            logger.error(f"检索失败: {e}")
            return []
    
    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """格式化检索结果"""
        formatted = []
        for i, result in enumerate(results, 1):
            source = result.get("metadata", {}).get("source", "未知来源")
            text = result.get("text", "")[:500]
            score = result.get("score", 0)
            
            formatted.append(f"【{i}】来源: {source}\n相似度: {score:.2f}\n内容:\n{text}...\n")
        
        return "\n".join(formatted)
