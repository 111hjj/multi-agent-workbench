"""代码生成专家 - 生成Python代码"""
from typing import Dict, Any, Optional, AsyncGenerator
import os
from agents.base.base_agent import BaseAgent
from utils.logger import logger

class CodeSpecialist(BaseAgent):
    """代码生成专家 - 生成高质量Python代码"""
    
    def get_default_model(self) -> str:
        return "deepseek-r1:8b"
    
    def get_prompt(self) -> str:
        return """你是一个专业的Python代码生成专家。
请根据用户的需求，生成高质量、可运行的Python代码。

要求：
1. 代码必须正确、完整、可运行
2. 添加必要的注释
3. 提供清晰的函数说明和参数说明
4. 包含示例用法
5. 处理可能的异常情况

输出格式：
```python
# 代码说明
def function_name(params):
    \"\"\"函数说明\"\"\"
    # 实现代码
    pass

# 示例用法
if __name__ == "__main__":
    result = function_name(args)
    print(result)
```
"""
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行代码生成任务"""
        try:
            yield {
                "type": "status",
                "agent_type": "code",
                "status": "running",
                "current_step": "分析需求并生成代码",
                "progress": 0
            }
            
            prompt = self._build_prompt(task, context)
            
            code_result = ""
            async for chunk in self._call_llm(prompt, stream=True):
                code_result += chunk
                progress = min(int(len(code_result) / 20), 95)
                
                if stream:
                    yield {
                        "type": "status",
                        "agent_type": "code",
                        "status": "running",
                        "current_step": "正在生成代码...",
                        "progress": progress
                    }
            
            yield {
                "type": "complete",
                "content": f"【代码生成完成】\n\n{code_result}",
                "sources": [],
                "confidence": 0.9,
                "agent_type": "code"
            }
            
        except Exception as e:
            logger.error(f"CodeSpecialist.execute 失败: {e}", exc_info=True)
            yield {
                "type": "complete",
                "content": f"代码生成失败: {str(e)}",
                "sources": [],
                "confidence": 0.3,
                "agent_type": "code"
            }
    
    def _build_prompt(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """构建代码生成提示"""
        base_prompt = self.get_prompt()
        return f"{base_prompt}\n\n用户需求：\n{task}"
