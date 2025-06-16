from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from app.services.sql_generator import get_generator
from app.services.schema_reader import SchemaReader
from app.services.voice_service import get_voice_service
import time
from datetime import datetime, timedelta
import uvicorn

app = FastAPI(
    title="Natural Language to SQL API",
    description="API for converting natural language to SQL queries",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
sql_generator = get_generator()
schema_reader = SchemaReader()

# Rate limiting
RATE_LIMIT_WINDOW = 60  # 1 minute
RATE_LIMIT_MAX_REQUESTS = 30  # 30 requests per minute
request_history = {}

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)

class QueryResponse(BaseModel):
    sql: str
    results: List[Dict]
    execution_time: float

class VoiceQueryResponse(BaseModel):
    query: str
    sql: str
    results: List[Dict]
    execution_time: float

async def check_rate_limit(request: Request):
    """Check if the request is within rate limits."""
    client_ip = request.client.host
    current_time = time.time()
    
    # Clean up old requests
    request_history[client_ip] = [
        req_time for req_time in request_history.get(client_ip, [])
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]
    
    # Check rate limit
    if len(request_history.get(client_ip, [])) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later."
        )
    
    # Add current request
    if client_ip not in request_history:
        request_history[client_ip] = []
    request_history[client_ip].append(current_time)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all unhandled exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred",
            "error": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Natural Language to SQL API",
        "version": "1.0.0",
        "endpoints": {
            "/schema": "Get database schema",
            "/query": "Convert natural language to SQL and execute",
            "/voice-query": "Process a voice query and convert it to SQL"
        },
        "rate_limit": {
            "requests_per_minute": RATE_LIMIT_MAX_REQUESTS,
            "window_seconds": RATE_LIMIT_WINDOW
        }
    }

@app.get("/schema")
async def get_schema():
    """Get the database schema."""
    try:
        return {
            "schema": schema_reader.get_schema_summary(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve schema: {str(e)}"
        )

@app.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    rate_limit: None = Depends(check_rate_limit)
):
    """Convert natural language to SQL and execute the query."""
    start_time = time.time()
    try:
        sql, results = sql_generator.generate_and_execute(request.question)
        execution_time = time.time() - start_time
        
        return QueryResponse(
            sql=sql,
            results=results,
            execution_time=execution_time
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid query: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Query execution failed: {str(e)}"
        )

@app.post("/voice-query", response_model=VoiceQueryResponse)
async def process_voice_query(
    rate_limit: None = Depends(check_rate_limit)
):
    """Process a voice query and convert it to SQL."""
    start_time = time.time()
    try:
        # Get voice service instance
        voice_service = get_voice_service()
        
        # Process voice input
        query = voice_service.process_voice_query()
        if not query:
            raise HTTPException(
                status_code=400,
                detail="Could not process voice input"
            )
        
        # Generate and execute SQL
        sql, results = sql_generator.generate_and_execute(query)
        execution_time = time.time() - start_time
        
        # Speak the results
        voice_service.speak(f"Found {len(results)} results. Here they are:")
        for i, result in enumerate(results[:3], 1):  # Speak first 3 results
            voice_service.speak(f"Result {i}: {result}")
        if len(results) > 3:
            voice_service.speak(f"And {len(results) - 3} more results.")
        
        return VoiceQueryResponse(
            query=query,
            sql=sql,
            results=results,
            execution_time=execution_time
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid query: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Query execution failed: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    ) 