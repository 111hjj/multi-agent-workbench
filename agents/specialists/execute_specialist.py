"""
执行专家 - 在沙箱中执行Python代码
"""
from typing import Dict, Any, Optional
import os
import subprocess
import tempfile


class ExecuteSpecialist:
    """执行专家 - 安全执行Python代码"""
    
    def __init__(self, model_name=None):
        """初始化执行专家"""
        self.model_name = model_name or os.getenv("OLLAMA_MODEL", "deepseek-r1:8b")
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    async def execute(self, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """
        执行代码任务
        
        Args:
            params: 参数，包含 code
            context: 上下文信息
            
        Returns:
            执行结果
        """
        try:
            code = params.get("code", "")
            print(f"ExecuteSpecialist: 开始执行代码...")
            
            result = await self._execute_code(code)
            
            analysis = await self._analyze_result(result)
            
            return f"执行结果：\n{result}\n\n分析：\n{analysis}"
            
        except Exception as e:
            print(f"ExecuteSpecialist: 执行失败: {e}")
            return f"执行失败: {str(e)}"
    
    async def _execute_code(self, code: str) -> str:
        """在沙箱中执行代码"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                result = subprocess.run(
                    ['python', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=tempfile.gettempdir()
                )
                
                if result.returncode == 0:
                    return result.stdout or "执行成功，无输出"
                else:
                    return f"执行失败：\n{result.stderr}"
                    
            finally:
                os.unlink(temp_file)
                
        except subprocess.TimeoutExpired:
            return "执行超时（30秒限制）"
        except Exception as e:
            return f"执行错误：{str(e)}"
    
    async def _analyze_result(self, result: str) -> str:
        """分析执行结果"""
        try:
            import requests
            
            prompt = f"""请分析以下代码执行结果：

{result}

请提供：
1. 结果解读
2. 关键发现
3. 潜在问题或建议"""

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                return result
                
        except Exception as e:
            print(f"结果分析失败: {e}")
            return result
