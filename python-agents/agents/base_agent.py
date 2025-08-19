"""
Base Agent Class for AgentFlow AI Agents
Provides common functionality and interface for all specialized agents
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

logger = logging.getLogger(__name__)

@dataclass
class AgentConfig:
    """Configuration for an AI agent"""
    model: str = "llama-3-70b"
    temperature: float = 0.1
    max_tokens: int = 4000
    tone: str = "professional"
    system_prompt: str = ""
    tools: List[str] = field(default_factory=list)

@dataclass
class AgentResult:
    """Result from an agent's analysis"""
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    tokens_used: Optional[int] = None

class BaseAgent(ABC):
    """
    Abstract base class for all AI agents
    
    Each agent should implement:
    - analyze(): Main analysis method
    - get_system_prompt(): Agent-specific system prompt
    - process_response(): Process LLM response
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self.llm = None
        self.is_active = True
        self.last_run = None
        self.total_runs = 0
        self.total_tokens = 0
        
        # Initialize LLM based on configuration
        self._initialize_llm()
        
        logger.info(f"Initialized {self.__class__.__name__}")
    
    def _initialize_llm(self):
        """Initialize the language model"""
        try:
            # Use OpenRouter for model routing
            self.llm = ChatOpenAI(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                openai_api_base="https://openrouter.ai/api/v1",
                openai_api_key=self._get_openrouter_key()
            )
            logger.info(f"LLM initialized with model: {self.config.model}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            self.is_active = False
    
    def _get_openrouter_key(self) -> str:
        """Get OpenRouter API key from environment"""
        import os
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        return api_key
    
    @abstractmethod
    async def analyze(
        self,
        parsed_elements: Dict[str, Any],
        project_id: int,
        model: Optional[str] = None,
        tone: Optional[str] = None
    ) -> AgentResult:
        """
        Main analysis method - must be implemented by subclasses
        
        Args:
            parsed_elements: Parsed code elements from the parser
            project_id: Database project ID
            model: Override default model
            tone: Override default tone
        
        Returns:
            AgentResult with analysis data
        """
        pass
    
    @abstractmethod
    def get_system_prompt(self, tone: str = "professional") -> str:
        """
        Get the system prompt for this agent
        
        Args:
            tone: Tone for the agent (professional, friendly, strict, etc.)
        
        Returns:
            System prompt string
        """
        pass
    
    @abstractmethod
    def process_response(self, response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the LLM response into structured data
        
        Args:
            response: Raw response from LLM
            context: Context information for processing
        
        Returns:
            Processed and structured data
        """
        pass
    
    async def _call_llm(
        self,
        messages: List[Any],
        context: Dict[str, Any]
    ) -> AgentResult:
        """
        Make a call to the language model
        
        Args:
            messages: List of messages to send to LLM
            context: Context for processing the response
        
        Returns:
            AgentResult with processed data
        """
        start_time = time.time()
        
        try:
            if not self.is_active or not self.llm:
                raise RuntimeError("Agent is not active or LLM not initialized")
            
            # Add system message if not present
            if not any(isinstance(msg, SystemMessage) for msg in messages):
                system_prompt = self.get_system_prompt(self.config.tone)
                messages.insert(0, SystemMessage(content=system_prompt))
            
            # Call the LLM
            response = await self.llm.ainvoke(messages)
            
            # Process the response
            processed_data = self.process_response(response.content, context)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Update agent stats
            self.last_run = datetime.utcnow()
            self.total_runs += 1
            
            # Estimate token usage (rough calculation)
            estimated_tokens = self._estimate_tokens(messages, response.content)
            self.total_tokens += estimated_tokens
            
            logger.info(f"LLM call completed in {processing_time:.2f}s, estimated tokens: {estimated_tokens}")
            
            return AgentResult(
                success=True,
                data=processed_data,
                metadata={
                    "model": self.config.model,
                    "tone": self.config.tone,
                    "processing_time": processing_time,
                    "estimated_tokens": estimated_tokens
                },
                processing_time=processing_time,
                tokens_used=estimated_tokens
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"LLM call failed: {e}")
            
            return AgentResult(
                success=False,
                data={},
                metadata={
                    "model": self.config.model,
                    "tone": self.config.tone,
                    "processing_time": processing_time,
                    "error": str(e)
                },
                errors=[str(e)],
                processing_time=processing_time
            )
    
    def _estimate_tokens(self, messages: List[Any], response: str) -> int:
        """Estimate token usage for the conversation"""
        # Rough estimation: 1 token ≈ 4 characters
        total_chars = sum(len(str(msg.content)) for msg in messages) + len(response)
        return int(total_chars / 4)
    
    async def test_agent(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test the agent with sample data
        
        Args:
            test_data: Sample data for testing
        
        Returns:
            Test results
        """
        try:
            logger.info(f"Testing agent {self.__class__.__name__}")
            
            # Create a simple test context
            test_context = {
                "test_mode": True,
                "test_data": test_data
            }
            
            # Create test messages
            test_message = HumanMessage(content=f"Test data: {json.dumps(test_data, indent=2)}")
            
            # Call LLM with test data
            result = await self._call_llm([test_message], test_context)
            
            return {
                "agent_type": self.__class__.__name__,
                "test_result": result.data,
                "success": result.success,
                "processing_time": result.processing_time,
                "errors": result.errors
            }
            
        except Exception as e:
            logger.error(f"Agent test failed: {e}")
            return {
                "agent_type": self.__class__.__name__,
                "test_result": {},
                "success": False,
                "processing_time": 0.0,
                "errors": [str(e)]
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "active": self.is_active,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "total_runs": self.total_runs,
            "total_tokens": self.total_tokens,
            "model": self.config.model,
            "tone": self.config.tone
        }
    
    def update_config(self, new_config: AgentConfig):
        """Update agent configuration"""
        self.config = new_config
        self._initialize_llm()
        logger.info(f"Configuration updated for {self.__class__.__name__}")
    
    def reset_stats(self):
        """Reset agent statistics"""
        self.last_run = None
        self.total_runs = 0
        self.total_tokens = 0
        logger.info(f"Statistics reset for {self.__class__.__name__}")
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(model={self.config.model}, active={self.is_active})"
    
    def __repr__(self) -> str:
        return self.__str__()
