"""
AgentFlow Orchestrator - LangGraph-based workflow management
Coordinates multiple AI agents for comprehensive code analysis
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from agents.documenter import DocumenterAgent
# from agents.tester import TesterAgent
# from agents.security_auditor import SecurityAuditorAgent
# from agents.performance_optimizer import PerformanceOptimizerAgent
from utils.php_parser import PHPParser
from utils.database import DatabaseManager
from utils.redis_client import RedisClient

logger = logging.getLogger(__name__)

@dataclass
class AnalysisState:
    """State object for the analysis workflow"""
    session_id: str
    project_id: int
    files: List[Dict[str, str]] = field(default_factory=list)
    parsed_elements: Dict[str, Any] = field(default_factory=dict)
    agent_outputs: Dict[str, Any] = field(default_factory=dict)
    current_agent: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    progress: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for storage"""
        return {
            "session_id": self.session_id,
            "project_id": self.project_id,
            "files": self.files,
            "parsed_elements": self.parsed_elements,
            "agent_outputs": self.agent_outputs,
            "current_agent": self.current_agent,
            "errors": self.errors,
            "progress": self.progress,
            "metadata": self.metadata
        }

class AgentOrchestrator:
    """
    Main orchestrator for AgentFlow AI agents
    
    Manages the workflow graph and coordinates:
    - Code parsing and analysis
    - Agent execution and routing
    - Result aggregation and storage
    - Error handling and recovery
    """
    
    def __init__(self, db_manager: DatabaseManager, redis_client: RedisClient):
        self.db_manager = db_manager
        self.redis_client = redis_client
        self.php_parser = PHPParser()
        
        # Initialize AI agents
        self.agents = {
            "documenter": DocumenterAgent(),
            # "tester": TesterAgent(),
            # "security_auditor": SecurityAuditorAgent(),
            # "performance_optimizer": PerformanceOptimizerAgent()
        }
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
        
        # Track active sessions
        self.active_sessions: Dict[str, AnalysisState] = {}
        
        logger.info(f"AgentOrchestrator initialized with {len(self.agents)} agents")
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create the state graph
        workflow = StateGraph(AnalysisState)
        
        # Add nodes for each step
        workflow.add_node("parse_code", self._parse_code)
        workflow.add_node("route_to_agents", self._route_to_agents)
        workflow.add_node("run_documenter", self._run_documenter)
        # workflow.add_node("run_tester", self._run_tester)
        # workflow.add_node("run_security_auditor", self._run_security_auditor)
        # workflow.add_node("run_performance_optimizer", self._run_performance_optimizer)
        workflow.add_node("collect_results", self._collect_results)
        workflow.add_node("store_results", self._store_results)
        workflow.add_node("handle_errors", self._handle_errors)
        
        # Define the workflow edges
        workflow.set_entry_point("parse_code")
        
        # Main flow
        workflow.add_edge("parse_code", "route_to_agents")
        workflow.add_edge("route_to_agents", "run_documenter")
        # workflow.add_edge("run_documenter", "run_tester")
        # workflow.add_edge("run_tester", "run_security_auditor")
        # workflow.add_edge("run_security_auditor", "run_performance_optimizer")
        workflow.add_edge("run_documenter", "collect_results")
        workflow.add_edge("collect_results", "store_results")
        workflow.add_edge("store_results", END)
        
        # Error handling
        workflow.add_edge("handle_errors", END)
        
        # Add conditional edges for error handling
        workflow.add_conditional_edges(
            "parse_code",
            self._should_continue,
            {
                "continue": "route_to_agents",
                "error": "handle_errors"
            }
        )
        
        # Compile the workflow
        return workflow.compile()
    
    async def run_analysis(
        self,
        session_id: str,
        project_id: int,
        files: List[Dict[str, str]],
        agents_config: Optional[Dict[str, bool]] = None,
        model: str = "llama-3-70b",
        tone: str = "professional"
    ) -> Dict[str, Any]:
        """
        Run the complete analysis workflow
        
        Args:
            session_id: Unique session identifier
            project_id: Database project ID
            files: List of files with path and content
            agents_config: Which agents to run
            model: LLM model to use
            tone: Tone for agent responses
        
        Returns:
            Analysis results and metadata
        """
        try:
            logger.info(f"Starting analysis for session {session_id}, project {project_id}")
            
            # Update session status
            await self.db_manager.update_session_status(session_id, "in_progress")
            
            # Initialize analysis state
            state = AnalysisState(
                session_id=session_id,
                project_id=project_id,
                files=files,
                metadata={
                    "model": model,
                    "tone": tone,
                    "agents_config": agents_config or {},
                    "started_at": datetime.utcnow().isoformat()
                }
            )
            
            # Store state in memory and Redis
            self.active_sessions[session_id] = state
            await self.redis_client.set(f"session:{session_id}", state.to_dict())
            
            # Run the workflow
            config = {"configurable": {"thread_id": session_id}}
            result = await self.workflow.ainvoke(state, config)
            
            # Update final status
            await self.db_manager.update_session_status(session_id, "completed")
            
            logger.info(f"Analysis completed for session {session_id}")
            
            # Cleanup
            del self.active_sessions[session_id]
            await self.redis_client.delete(f"session:{session_id}")
            
            return result.agent_outputs
            
        except Exception as e:
            logger.error(f"Analysis failed for session {session_id}: {e}")
            
            # Update session status
            await self.db_manager.update_session_status(
                session_id, 
                "failed", 
                error_message=str(e)
            )
            
            # Cleanup
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            await self.redis_client.delete(f"session:{session_id}")
            
            raise
    
    async def _parse_code(self, state: AnalysisState) -> AnalysisState:
        """Parse uploaded code files to extract structural elements"""
        try:
            logger.info(f"Parsing code for session {state.session_id}")
            
            state.current_agent = "parser"
            state.progress["parsing"] = {"status": "started", "files_processed": 0}
            
            parsed_elements = {}
            
            for i, file_data in enumerate(state.files):
                try:
                    file_path = file_data["path"]
                    file_content = file_data["content"]
                    
                    # Parse PHP files
                    if file_path.endswith('.php'):
                        elements = await self.php_parser.parse_php_file(file_content, file_path)
                        parsed_elements[file_path] = elements
                    
                    # Parse other file types as needed
                    elif file_path.endswith(('.js', '.vue')):
                        elements = await self.php_parser.parse_js_file(file_content, file_path)
                        parsed_elements[file_path] = elements
                    
                    state.progress["parsing"]["files_processed"] = i + 1
                    
                except Exception as e:
                    logger.warning(f"Failed to parse file {file_data['path']}: {e}")
                    state.errors.append(f"Parse error in {file_data['path']}: {str(e)}")
            
            state.parsed_elements = parsed_elements
            state.progress["parsing"]["status"] = "completed"
            
            logger.info(f"Code parsing completed for session {state.session_id}")
            return state
            
        except Exception as e:
            logger.error(f"Code parsing failed: {e}")
            state.errors.append(f"Code parsing failed: {str(e)}")
            return state
    
    async def _route_to_agents(self, state: AnalysisState) -> AnalysisState:
        """Route parsed code to appropriate agents based on configuration"""
        try:
            logger.info(f"Routing to agents for session {state.session_id}")
            
            state.current_agent = "router"
            state.progress["routing"] = {"status": "started"}
            
            # Determine which agents to run based on configuration
            agents_to_run = state.metadata.get("agents_config", {})
            
            if not agents_to_run:
                # Default to all agents if no config provided
                agents_to_run = {name: True for name in self.agents.keys()}
            
            state.progress["routing"]["agents_to_run"] = list(agents_to_run.keys())
            state.progress["routing"]["status"] = "completed"
            
            logger.info(f"Routing completed for session {state.session_id}")
            return state
            
        except Exception as e:
            logger.error(f"Agent routing failed: {e}")
            state.errors.append(f"Agent routing failed: {str(e)}")
            return state
    
    async def _run_documenter(self, state: AnalysisState) -> AnalysisState:
        """Run the documenter agent"""
        try:
            if not state.metadata.get("agents_config", {}).get("documenter", True):
                logger.info(f"Skipping documenter for session {state.session_id}")
                return state
            
            logger.info(f"Running documenter agent for session {state.session_id}")
            
            state.current_agent = "documenter"
            state.progress["documenter"] = {"status": "started"}
            
            # Run documenter agent
            documenter = self.agents["documenter"]
            results = await documenter.analyze(
                parsed_elements=state.parsed_elements,
                project_id=state.project_id,
                model=state.metadata.get("model"),
                tone=state.metadata.get("tone")
            )
            
            state.agent_outputs["documenter"] = results
            state.progress["documenter"]["status"] = "completed"
            
            logger.info(f"Documenter agent completed for session {state.session_id}")
            return state
            
        except Exception as e:
            logger.error(f"Documenter agent failed: {e}")
            state.errors.append(f"Documenter agent failed: {str(e)}")
            return state
    
    async def _run_tester(self, state: AnalysisState) -> AnalysisState:
        """Run the tester agent"""
        try:
            if not state.metadata.get("agents_config", {}).get("tester", True):
                logger.info(f"Skipping tester for session {state.session_id}")
                return state
            
            logger.info(f"Running tester agent for session {state.session_id}")
            
            state.current_agent = "tester"
            state.progress["tester"] = {"status": "started"}
            
            # Run tester agent
            tester = self.agents["tester"]
            results = await tester.analyze(
                parsed_elements=state.parsed_elements,
                project_id=state.project_id,
                model=state.metadata.get("model"),
                tone=state.metadata.get("tone")
            )
            
            state.agent_outputs["tester"] = results
            state.progress["tester"]["status"] = "completed"
            
            logger.info(f"Tester agent completed for session {state.session_id}")
            return state
            
        except Exception as e:
            logger.error(f"Tester agent failed: {e}")
            state.errors.append(f"Tester agent failed: {str(e)}")
            return state
    
    async def _run_security_auditor(self, state: AnalysisState) -> AnalysisState:
        """Run the security auditor agent"""
        try:
            if not state.metadata.get("agents_config", {}).get("security_auditor", True):
                logger.info(f"Skipping security auditor for session {state.session_id}")
                return state
            
            logger.info(f"Running security auditor agent for session {state.session_id}")
            
            state.current_agent = "security_auditor"
            state.progress["security_auditor"] = {"status": "started"}
            
            # Run security auditor agent
            auditor = self.agents["security_auditor"]
            results = await auditor.analyze(
                parsed_elements=state.parsed_elements,
                project_id=state.project_id,
                model=state.metadata.get("model"),
                tone=state.metadata.get("tone")
            )
            
            state.agent_outputs["security_auditor"] = results
            state.progress["security_auditor"]["status"] = "completed"
            
            logger.info(f"Security auditor agent completed for session {state.session_id}")
            return state
            
        except Exception as e:
            logger.error(f"Security auditor agent failed: {e}")
            state.errors.append(f"Security auditor agent failed: {str(e)}")
            return state
    
    async def _run_performance_optimizer(self, state: AnalysisState) -> AnalysisState:
        """Run the performance optimizer agent"""
        try:
            if not state.metadata.get("agents_config", {}).get("performance_optimizer", True):
                logger.info(f"Skipping performance optimizer for session {state.session_id}")
                return state
            
            logger.info(f"Running performance optimizer agent for session {state.session_id}")
            
            state.current_agent = "performance_optimizer"
            state.progress["performance_optimizer"] = {"status": "started"}
            
            # Run performance optimizer agent
            optimizer = self.agents["performance_optimizer"]
            results = await optimizer.analyze(
                parsed_elements=state.parsed_elements,
                project_id=state.project_id,
                model=state.metadata.get("model"),
                tone=state.metadata.get("tone")
            )
            
            state.agent_outputs["performance_optimizer"] = results
            state.progress["performance_optimizer"]["status"] = "completed"
            
            logger.info(f"Performance optimizer agent completed for session {state.session_id}")
            return state
            
        except Exception as e:
            logger.error(f"Performance optimizer agent failed: {e}")
            state.errors.append(f"Performance optimizer agent failed: {str(e)}")
            return state
    
    async def _collect_results(self, state: AnalysisState) -> AnalysisState:
        """Collect and aggregate results from all agents"""
        try:
            logger.info(f"Collecting results for session {state.session_id}")
            
            state.current_agent = "collector"
            state.progress["collection"] = {"status": "started"}
            
            # Aggregate all agent outputs
            aggregated_results = {
                "session_id": state.session_id,
                "project_id": state.project_id,
                "timestamp": datetime.utcnow().isoformat(),
                "agents_run": list(state.agent_outputs.keys()),
                "results": state.agent_outputs,
                "metadata": state.metadata,
                "errors": state.errors
            }
            
            state.agent_outputs["aggregated"] = aggregated_results
            state.progress["collection"]["status"] = "completed"
            
            logger.info(f"Results collection completed for session {state.session_id}")
            return state
            
        except Exception as e:
            logger.error(f"Results collection failed: {e}")
            state.errors.append(f"Results collection failed: {str(e)}")
            return state
    
    async def _store_results(self, state: AnalysisState) -> AnalysisState:
        """Store analysis results in database"""
        try:
            logger.info(f"Storing results for session {state.session_id}")
            
            state.current_agent = "storer"
            state.progress["storage"] = {"status": "started"}
            
            # Store agent outputs in database
            for agent_type, output in state.agent_outputs.items():
                if agent_type == "aggregated":
                    continue
                
                await self.db_manager.store_agent_output(
                    project_id=state.project_id,
                    agent_type=agent_type,
                    output_type=self._get_output_type(agent_type),
                    content=output
                )
            
            state.progress["storage"]["status"] = "completed"
            
            logger.info(f"Results storage completed for session {state.session_id}")
            return state
            
        except Exception as e:
            logger.error(f"Results storage failed: {e}")
            state.errors.append(f"Results storage failed: {str(e)}")
            return state
    
    async def _handle_errors(self, state: AnalysisState) -> AnalysisState:
        """Handle errors that occurred during analysis"""
        try:
            logger.info(f"Handling errors for session {state.session_id}")
            
            state.current_agent = "error_handler"
            state.progress["error_handling"] = {"status": "started"}
            
            # Log errors and update session
            if state.errors:
                error_summary = "; ".join(state.errors)
                await self.db_manager.update_session_status(
                    state.session_id,
                    "failed",
                    error_message=error_summary
                )
            
            state.progress["error_handling"]["status"] = "completed"
            
            logger.info(f"Error handling completed for session {state.session_id}")
            return state
            
        except Exception as e:
            logger.error(f"Error handling failed: {e}")
            return state
    
    def _should_continue(self, state: AnalysisState) -> str:
        """Determine if workflow should continue or handle errors"""
        if state.errors:
            return "error"
        return "continue"
    
    def _get_output_type(self, agent_type: str) -> str:
        """Map agent type to output type"""
        mapping = {
            "documenter": "documentation",
            "tester": "tests",
            "security_auditor": "security_report",
            "performance_optimizer": "performance_report"
        }
        return mapping.get(agent_type, "other")
    
    def get_agents_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            name: {
                "active": agent.is_active,
                "last_run": agent.last_run,
                "total_runs": agent.total_runs
            }
            for name, agent in self.agents.items()
        }
    
    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of an analysis session"""
        # Check memory first
        if session_id in self.active_sessions:
            state = self.active_sessions[session_id]
            return {
                "session_id": session_id,
                "status": "in_progress",
                "current_agent": state.current_agent,
                "progress": state.progress,
                "errors": state.errors
            }
        
        # Check Redis
        cached_state = await self.redis_client.get(f"session:{session_id}")
        if cached_state:
            return {
                "session_id": session_id,
                "status": "cached",
                "current_agent": cached_state.get("current_agent"),
                "progress": cached_state.get("progress"),
                "errors": cached_state.get("errors")
            }
        
        # Check database
        return await self.db_manager.get_analysis_session(session_id)
