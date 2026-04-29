"""Ollama服务封装"""
import os
import json
import requests
from typing import Optional, AsyncGenerator, Dict, Any
from utils.logger import logger

class OllamaService:
    """Ollama服务封装类"""
    
    def __init__(self, base_url: Optional[str] = None, model_name: Optional[str] = None):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = model_name or os.getenv("OLLAMA_MODEL", "deepseek-r1:8b")
        logger.info(f"OllamaService 初始化 - 地址: {self.base_url}, 模型: {self.model_name}")
    
    async def generate(
        self,
        prompt: str,
        context: Optional[str] = None,
        stream: bool = False,
        options: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        调用Ollama生成回复
        
        Args:
            prompt: 提示词
            context: 上下文信息
            stream: 是否流式输出
            options: 模型选项
        
        Yields:
            生成的文本片段
        """
        try:
            if context:
                full_prompt = f"{context}\n\n{prompt}"
            else:
                full_prompt = prompt
            
            payload = {
                "model": self.model_name,
                "prompt": full_prompt,
                "stream": stream,
                "options": options or {
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                stream=stream,
                timeout=120
            )
            response.raise_for_status()
            
            if stream:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode("utf-8"))
                            if "response" in data:
                                yield data["response"]
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
            else:
                data = response.json()
                if "response" in data:
                    yield data["response"]
        
        except Exception as e:
            logger.error(f"OllamaService.generate 失败: {e}", exc_info=True)
            raise
    
    async def chat(
        self,
        messages: list,
        stream: bool = False,
        options: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        调用Ollama进行对话
        
        Args:
            messages: 消息列表
            stream: 是否流式输出
            options: 模型选项
        
        Yields:
            生成的文本片段
        """
        try:
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": stream,
                "options": options or {
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                stream=stream,
                timeout=120
            )
            response.raise_for_status()
            
            if stream:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode("utf-8"))
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
            else:
                data = response.json()
                if "message" in data and "content" in data["message"]:
                    yield data["message"]["content"]
        
        except Exception as e:
            logger.error(f"OllamaService.chat 失败: {e}", exc_info=True)
            raise
    
    def list_models(self) -> list:
        """获取可用模型列表"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=30)
            response.raise_for_status()
            return response.json().get("models", [])
        except Exception as e:
            logger.error(f"OllamaService.list_models 失败: {e}", exc_info=True)
            return []
