"""
FastAPI server for AgentFlow Python AI Agents
Provides REST API endpoints for code analysis and agent orchestration
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from orchestrator.graph import AgentOrchestrator
from utils.php_parser import PHPParser
from utils.database import DatabaseManager
from utils.redis_client import RedisClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AgentFlow AI Agents API",
    description="Multi-Agent AI System for Automated Documentation and Testing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API requests/responses
class ProjectAnalysisRequest(BaseModel):
    project_id: int
    files: List[Dict[str, str]] = Field(..., description="List of files with path and content")
    agents_config: Optional[Dict[str, Any]] = Field(
        default={
            "documenter": True,
            "tester": True,
            "security_auditor": True,
            "performance_optimizer": True
        },
        description="Configuration for which agents to run"
    )
    model: Optional[str] = Field(default="llama-3-70b", description="LLM model to use")
    tone: Optional[str] = Field(default="professional", description="Tone for agent responses")

class AnalysisResponse(BaseModel):
    session_id: str
    status: str
    message: str
    estimated_time: Optional[int] = None

class AnalysisStatusResponse(BaseModel):
    session_id: str
    status: str
    progress: Dict[str, Any]
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, str]

# Global instances
orchestrator: Optional[AgentOrchestrator] = None
db_manager: Optional[DatabaseManager] = None
redis_client: Optional[RedisClient] = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global orchestrator, db_manager, redis_client
    
    try:
        # Initialize database connection
        db_manager = DatabaseManager()
        await db_manager.connect()
        logger.info("Database connection established")
        
        # Initialize Redis client
        redis_client = RedisClient()
        await redis_client.connect()
        logger.info("Redis connection established")
        
        # Initialize agent orchestrator
        orchestrator = AgentOrchestrator(db_manager, redis_client)
        logger.info("Agent orchestrator initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if db_manager:
        await db_manager.close()
    if redis_client:
        await redis_client.close()
    logger.info("Services shutdown complete")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    services_status = {}
    
    # Check database
    try:
        if db_manager:
            await db_manager.ping()
            services_status["database"] = "healthy"
        else:
            services_status["database"] = "not_initialized"
    except Exception as e:
        services_status["database"] = f"unhealthy: {str(e)}"
    
    # Check Redis
    try:
        if redis_client:
            await redis_client.ping()
            services_status["redis"] = "healthy"
        else:
            services_status["redis"] = "not_initialized"
    except Exception as e:
        services_status["redis"] = f"unhealthy: {str(e)}"
    
    # Check orchestrator
    if orchestrator:
        services_status["orchestrator"] = "healthy"
    else:
        services_status["orchestrator"] = "not_initialized"
    
    return HealthResponse(
        status="healthy" if all("healthy" in status for status in services_status.values()) else "degraded",
        timestamp=datetime.utcnow().isoformat(),
        services=services_status
    )

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_project(
    request: ProjectAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Start code analysis with AI agents
    
    This endpoint initiates the analysis pipeline:
    1. Parses uploaded files
    2. Routes to appropriate AI agents
    3. Collects and aggregates results
    4. Stores analysis in database
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent orchestrator not available")
    
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create analysis session in database
        await db_manager.create_analysis_session(
            project_id=request.project_id,
            session_uuid=session_id,
            agents_config=request.agents_config
        )
        
        # Start analysis in background
        background_tasks.add_task(
            orchestrator.run_analysis,
            session_id=session_id,
            project_id=request.project_id,
            files=request.files,
            agents_config=request.agents_config,
            model=request.model,
            tone=request.tone
        )
        
        logger.info(f"Analysis started for project {request.project_id}, session {session_id}")
        
        return AnalysisResponse(
            session_id=session_id,
            status="started",
            message="Analysis started successfully",
            estimated_time=len(request.files) * 30  # Rough estimate: 30 seconds per file
        )
        
    except Exception as e:
        logger.error(f"Failed to start analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")

@app.get("/status/{session_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(session_id: str):
    """Get the current status of an analysis session"""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        session = await db_manager.get_analysis_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Analysis session not found")
        
        # Get progress information
        progress = await db_manager.get_session_progress(session_id)
        
        # Get results if completed
        results = None
        if session["status"] == "completed":
            results = await db_manager.get_session_results(session_id)
        
        return AnalysisStatusResponse(
            session_id=session_id,
            status=session["status"],
            progress=progress,
            results=results,
            error=session.get("error_message")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analysis status: {str(e)}")

@app.post("/upload-files")
async def upload_files(
    project_id: int,
    files: List[UploadFile] = File(...),
    agents_config: Optional[str] = None
):
    """
    Upload files for analysis
    
    Alternative endpoint for file uploads when you have actual files
    instead of file content in JSON
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent orchestrator not available")
    
    try:
        # Parse agents config if provided
        config = {}
        if agents_config:
            config = json.loads(agents_config)
        
        # Process uploaded files
        file_data = []
        for file in files:
            content = await file.read()
            file_data.append({
                "path": file.filename,
                "content": content.decode('utf-8')
            })
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create analysis session
        await db_manager.create_analysis_session(
            project_id=project_id,
            session_uuid=session_id,
            agents_config=config
        )
        
        # Start analysis
        asyncio.create_task(
            orchestrator.run_analysis(
                session_id=session_id,
                project_id=project_id,
                files=file_data,
                agents_config=config
            )
        )
        
        return {
            "session_id": session_id,
            "status": "started",
            "files_uploaded": len(files),
            "message": "File upload and analysis started successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to upload files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload files: {str(e)}")

@app.get("/projects/{project_id}/summary")
async def get_project_summary(project_id: int):
    """Get a summary of analysis results for a project"""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        summary = await db_manager.get_project_summary(project_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get project summary: {str(e)}")

@app.get("/agents/status")
async def get_agents_status():
    """Get the status of all AI agents"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent orchestrator not available")
    
    try:
        return {
            "agents": orchestrator.get_agents_status(),
            "total_agents": len(orchestrator.agents),
            "active_agents": len([a for a in orchestrator.agents.values() if a.is_active])
        }
    except Exception as e:
        logger.error(f"Failed to get agents status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agents status: {str(e)}")

@app.post("/agents/{agent_type}/test")
async def test_agent(agent_type: str, test_data: Dict[str, Any]):
    """Test a specific agent with sample data"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent orchestrator not available")
    
    try:
        if agent_type not in orchestrator.agents:
            raise HTTPException(status_code=404, detail=f"Agent type '{agent_type}' not found")
        
        agent = orchestrator.agents[agent_type]
        result = await agent.test_agent(test_data)
        
        return {
            "agent_type": agent_type,
            "test_result": result,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test agent {agent_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test agent: {str(e)}")

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

if __name__ == "__main__":
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )
