"""Agent基类 - 定义所有Agent的通用接口和功能"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncGenerator
from utils.logger import logger
from services.ollama_service import OllamaService

class BaseAgent(ABC):
    """Agent基类 - 所有Agent的基类"""
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.model_name = model_name or self.get_default_model()
        self.ollama_service = OllamaService(base_url=base_url, model_name=self.model_name)
        logger.info(f"{self.__class__.__name__} 初始化完成 - 模型: {self.model_name}")
    
    @abstractmethod
    def get_default_model(self) -> str:
        pass
    
    @abstractmethod
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        pass
    
    def get_tools(self) -> List[Any]:
        return []
    
    def get_prompt(self) -> str:
        return ""
    
    async def _call_llm(
        self,
        prompt: str,
        context: Optional[str] = None,
        stream: bool = False,
        options: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        async for chunk in self.ollama_service.generate(
            prompt=prompt,
            context=context,
            stream=stream,
            options=options
        ):
            yield chunk
    
    def _build_prompt(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        system_prompt = self.get_prompt()
        
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            return f"{system_prompt}\n\n上下文信息:\n{context_str}\n\n任务: {task}"
        
        return f"{system_prompt}\n\n任务: {task}"
