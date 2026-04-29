"""爬虫专家智能体 - 爬取网页内容"""
from typing import Dict, Any, Optional, AsyncGenerator, List
import re
from agents.base.base_agent import BaseAgent
from utils.logger import logger

class CrawlSpecialist(BaseAgent):
    """爬虫专家 - 爬取指定网页内容"""
    
    def get_default_model(self) -> str:
        return "deepseek-r1:8b"
    
    def get_prompt(self) -> str:
        return """你是一个网页爬虫专家。请总结爬取到的网页内容。
        
输出格式：
1. 网页标题
2. 主要内容摘要
3. 关键信息
"""
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行爬虫任务"""
        try:
            yield {
                "type": "status",
                "agent_type": "crawl",
                "status": "running",
                "current_step": "开始爬取..."
            }
            
            url = self._extract_url(task)
            if not url and context:
                url = context.get("url", "")
            
            if not url:
                yield {
                    "type": "complete",
                    "content": "未找到有效的URL",
                    "error": True,
                    "agent_type": "crawl"
                }
                return
            
            yield {
                "type": "status",
                "agent_type": "crawl",
                "status": "running",
                "current_step": f"爬取: {url[:50]}..."
            }
            
            result = await self._crawl_url(url)
            
            if result and isinstance(result, dict):
                status = result.get("status")
                if status == "success":
                    yield {
                        "type": "agent_status",
                        "agent_type": "crawl",
                        "status": "completed",
                        "progress": 100,
                        "details": f"爬取成功"
                    }
                    
                    yield {
                        "type": "complete",
                        "content": f"【爬取成功】\nURL: {url}\n\n【网页内容】\n{result.get('content', '')}\n\n【内容长度】: {result.get('content_length', 0)} 字符",
                        "sources": [url],
                        "confidence": 0.9,
                        "agent_type": "crawl"
                    }
                elif status == "skipped":
                    yield {
                        "type": "agent_status",
                        "agent_type": "crawl",
                        "status": "completed",
                        "progress": 100,
                        "details": "URL已爬取，跳过"
                    }
                    
                    yield {
                        "type": "complete",
                        "content": f"【爬取跳过】\nURL: {url}\n该URL已在之前爬取过，跳过重复爬取",
                        "sources": [url],
                        "confidence": 0.8,
                        "agent_type": "crawl"
                    }
                else:
                    yield {
                        "type": "complete",
                        "content": f"【爬取失败】\nURL: {url}\n错误: {result.get('error', '未知错误')}",
                        "error": True,
                        "agent_type": "crawl"
                    }
            else:
                yield {
                    "type": "complete",
                    "content": f"爬取失败，未能获取内容: {url}",
                    "error": True,
                    "agent_type": "crawl"
                }
                
        except Exception as e:
            logger.error(f"CrawlSpecialist.execute 失败: {e}", exc_info=True)
            yield {
                "type": "complete",
                "content": f"爬取失败: {str(e)}",
                "error": True,
                "agent_type": "crawl"
            }
    
    def _extract_url(self, text: str) -> str:
        """从文本中提取URL"""
        match = re.search(r'https?://[^\s]+', text)
        return match.group(0) if match else ""
    
    async def _crawl_url(self, url: str) -> str:
        """爬取网页内容"""
        try:
            from crawler.crawler import WebCrawler
            
            crawler = WebCrawler()
            return await crawler.crawl(url)
        except Exception as e:
            logger.error(f"爬取失败: {e}")
            return ""
