"""Agent工作流编排 - 管理多Agent协作"""
from typing import Dict, Any, Optional, List, AsyncGenerator
import asyncio
import time
from utils.logger import logger

class AgentWorkflow:
    """Agent工作流编排器 - 管理多Agent协作"""
    
    def __init__(self):
        self.coordinator = None
        self.expert_agents = {}
        self._agent_configs_cache = {}
    
    async def _init_coordinator(self, generation_config: Optional[Dict[str, Any]] = None):
        if self.coordinator is None:
            from agents.coordinator.coordinator import CoordinatorAgent
            
            model_name = None
            if generation_config:
                model_name = generation_config.get("llm_model")
            
            self.coordinator = CoordinatorAgent(model_name=model_name)
    
    async def _get_expert_agent(self, agent_type: str, generation_config: Optional[Dict[str, Any]] = None):
        if agent_type not in self.expert_agents:
            agent_class = self._get_agent_class(agent_type)
            if agent_class:
                model_name = None
                if generation_config:
                    model_name = generation_config.get("llm_model")
                
                self.expert_agents[agent_type] = agent_class(model_name=model_name)
            else:
                logger.warning(f"未知的Agent类型: {agent_type}")
                return None
        return self.expert_agents.get(agent_type)
    
    def _get_agent_class(self, agent_type: str):
        agent_map = {
            "document_retrieval": self._import_agent("agents.specialists.retrieve_specialist.RetrieveSpecialist"),
            "crawl": self._import_agent("agents.specialists.crawl_specialist.CrawlSpecialist"),
            "analyze": self._import_agent("agents.specialists.analyze_specialist.AnalyzeSpecialist"),
            "execute": self._import_agent("agents.specialists.execute_specialist.ExecuteSpecialist"),
            "retrieve": self._import_agent("agents.specialists.retrieve_specialist.RetrieveSpecialist"),
            "summary": self._import_agent("agents.summary.summary.Summary"),
            "concept_explanation": self._import_agent("agents.specialists.analyze_specialist.AnalyzeSpecialist"),
            "code": self._import_agent("agents.specialists.code_specialist.CodeSpecialist"),
        }
        return agent_map.get(agent_type)
    
    def _import_agent(self, import_path: str):
        try:
            module_path, class_name = import_path.rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
        except Exception as e:
            logger.warning(f"导入Agent失败 {import_path}: {e}")
            return None
    
    async def execute_workflow(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        enabled_agents: Optional[List[str]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        try:
            generation_config = context.get("generation_config") if context else None
            await self._init_coordinator(generation_config)
            
            logger.info(f"AgentWorkflow: 开始规划任务 - {query[:50]}...")
            
            planning_context = context or {}
            planning_context["query"] = query
            
            selected_agents_from_coordinator = None
            agent_tasks = {}
            planning_reasoning = ""
            
            async for planning_result in self.coordinator.execute(
                task=query,
                context=planning_context,
                stream=False
            ):
                if planning_result.get("type") == "planning":
                    selected_agents_from_coordinator = planning_result.get("selected_agents")
                    agent_tasks = planning_result.get("agent_tasks", {})
                    planning_reasoning = planning_result.get("reasoning", "")
                    
                    yield {
                        "type": "planning",
                        "content": planning_result.get("content", ""),
                        "agent_type": "coordinator",
                        "selected_agents": selected_agents_from_coordinator,
                        "agent_tasks": agent_tasks,
                        "reasoning": planning_reasoning
                    }
            
            if enabled_agents:
                agent_types = enabled_agents
                logger.info(f"AgentWorkflow: 使用手动指定的Agent列表: {agent_types}")
            elif selected_agents_from_coordinator:
                agent_types = selected_agents_from_coordinator
                logger.info(f"AgentWorkflow: 协调型Agent选择了 {len(agent_types)} 个Agent")
            else:
                agent_types = ["concept_explanation"]
            
            valid_agent_types = ["document_retrieval", "formula_analysis", "code_analysis",
                               "concept_explanation", "example_generation", "summary",
                               "scientific_coding", "crawl", "execute",
                               "retrieve", "analyze", "code"]
            agent_types = [a for a in agent_types if a in valid_agent_types]
            
            if not agent_types:
                agent_types = ["concept_explanation"]
            
            logger.info(f"AgentWorkflow: 将执行 {len(agent_types)} 个专家Agent")
            
            expert_context = context or {}
            expert_context["query"] = query
            if agent_tasks:
                expert_context["agent_tasks"] = agent_tasks
            
            agent_results = []
            
            for agent_type in agent_types:
                if stream:
                    yield {
                        "type": "agent_status",
                        "agent_type": agent_type,
                        "status": "running",
                        "current_step": "开始工作...",
                        "progress": 0,
                        "started_at": int(time.time() * 1000)
                    }
                
                try:
                    agent = await self._get_expert_agent(agent_type, generation_config)
                    if not agent:
                        logger.warning(f"AgentWorkflow: {agent_type} 未找到，跳过")
                        if stream:
                            yield {
                                "type": "agent_status",
                                "agent_type": agent_type,
                                "status": "error",
                                "details": "Agent未找到"
                            }
                        continue
                    
                    result_content = ""
                    sources = []
                    confidence = 0.5
                    progress = 0
                    
                    async for result in agent.execute(task=query, context=expert_context, stream=stream):
                        if result.get("type") == "complete":
                            result_content = result.get("content", "")
                            sources = result.get("sources", [])
                            confidence = result.get("confidence", 0.5)
                            progress = 100
                            
                            if stream:
                                yield {
                                    "type": "agent_status",
                                    "agent_type": agent_type,
                                    "status": "completed",
                                    "progress": 100,
                                    "completed_at": int(time.time() * 1000)
                                }
                            
                            yield {
                                "type": "agent_result",
                                "agent_type": agent_type,
                                "content": result_content,
                                "sources": sources,
                                "confidence": confidence
                            }
                        elif result.get("type") == "agent_status" or result.get("type") == "status":
                            progress = result.get("progress", progress)
                            if stream:
                                yield {
                                    "type": "agent_status",
                                    "agent_type": agent_type,
                                    "status": result.get("status", "running"),
                                    "current_step": result.get("current_step"),
                                    "progress": progress,
                                    "details": result.get("details")
                                }
                        elif result.get("type") == "chunk":
                            result_content += result.get("content", "")
                            progress = min(progress + 2, 95)
                            if stream:
                                yield {
                                    "type": "agent_status",
                                    "agent_type": agent_type,
                                    "status": "running",
                                    "current_step": result.get("current_step", "正在生成内容..."),
                                    "progress": progress
                                }
                    
                    agent_results.append({
                        "agent_type": agent_type,
                        "content": result_content,
                        "sources": sources,
                        "confidence": confidence,
                        "error": False
                    })
                    
                except Exception as e:
                    logger.error(f"AgentWorkflow: {agent_type} 执行失败: {e}", exc_info=True)
                    error_msg = f"执行失败: {str(e)}"
                    agent_results.append({
                        "agent_type": agent_type,
                        "content": error_msg,
                        "error": True
                    })
                    if stream:
                        yield {
                            "type": "agent_status",
                            "agent_type": agent_type,
                            "status": "error",
                            "details": error_msg
                        }
            
            yield {
                "type": "complete",
                "agent_results": agent_results,
                "total_agents": len(agent_types),
                "successful_agents": len([r for r in agent_results if not r.get("error")])
            }
        
        except Exception as e:
            logger.error(f"AgentWorkflow: 工作流执行失败: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": f"工作流执行失败: {str(e)}"
            }
