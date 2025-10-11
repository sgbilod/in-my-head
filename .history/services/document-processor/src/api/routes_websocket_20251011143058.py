"""
WebSocket router for real-time job updates.

Provides:
- WebSocket endpoint for job status
- Real-time progress updates
- Automatic monitoring
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse

from ..jobs import JobManager, celery_app
from .websocket_manager import connection_manager, JobMonitor

# Create router
router = APIRouter(prefix="/api/v1/ws", tags=["websocket"])

# Initialize job manager
job_manager = JobManager(celery_app)


@router.websocket("/jobs/{job_id}")
async def websocket_job_status(
    websocket: WebSocket,
    job_id: str,
):
    """
    WebSocket endpoint for real-time job updates.
    
    Connect to receive:
    - Status changes
    - Progress updates
    - Results
    - Errors
    
    Message format:
    ```json
    {
        "type": "status|progress|result|error",
        "job_id": "abc123",
        "data": {...},
        "timestamp": "2025-10-11T12:00:00Z"
    }
    ```
    
    Example (JavaScript):
    ```javascript
    const ws = new WebSocket("ws://localhost:8000/api/v1/ws/jobs/abc123");
    
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        console.log(`Type: ${message.type}`);
        console.log(`Data:`, message.data);
    };
    
    ws.onerror = (error) => {
        console.error("WebSocket error:", error);
    };
    
    ws.onclose = () => {
        console.log("WebSocket closed");
    };
    ```
    
    Example (Python):
    ```python
    import asyncio
    import websockets
    import json
    
    async def monitor_job(job_id):
        uri = f"ws://localhost:8000/api/v1/ws/jobs/{job_id}"
        
        async with websockets.connect(uri) as websocket:
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                
                print(f"Type: {data['type']}")
                print(f"Data: {data['data']}")
                
                if data['type'] in ['result', 'error']:
                    break
    
    asyncio.run(monitor_job("abc123"))
    ```
    """
    # Connect
    await connection_manager.connect(websocket, job_id)
    
    # Start monitoring
    monitor = JobMonitor(job_manager, connection_manager)
    await monitor.start_monitoring(job_id)
    
    try:
        # Keep connection alive and handle messages
        while True:
            # Wait for messages (for bidirectional communication)
            data = await websocket.receive_text()
            
            # Echo received messages (optional)
            # await websocket.send_text(f"Received: {data}")
    
    except WebSocketDisconnect:
        # Client disconnected
        connection_manager.disconnect(websocket)
        monitor.stop_monitoring()
    
    except Exception as e:
        # Error occurred
        connection_manager.disconnect(websocket)
        monitor.stop_monitoring()


@router.get("/test")
async def websocket_test_page():
    """
    Test page for WebSocket connection.
    
    Returns:
        HTML page with WebSocket test client
    """
    html = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>WebSocket Test</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                }
                #messages {
                    border: 1px solid #ccc;
                    height: 400px;
                    overflow-y: scroll;
                    padding: 10px;
                    margin: 20px 0;
                    background: #f5f5f5;
                }
                .message {
                    margin: 5px 0;
                    padding: 5px;
                    background: white;
                    border-left: 3px solid #007bff;
                }
                .status { border-left-color: #007bff; }
                .progress { border-left-color: #ffc107; }
                .result { border-left-color: #28a745; }
                .error { border-left-color: #dc3545; }
                input, button {
                    padding: 10px;
                    margin: 5px;
                    font-size: 16px;
                }
            </style>
        </head>
        <body>
            <h1>WebSocket Job Monitor</h1>
            
            <div>
                <input type="text" id="jobId" placeholder="Enter Job ID" />
                <button onclick="connect()">Connect</button>
                <button onclick="disconnect()">Disconnect</button>
            </div>
            
            <div id="status">Status: Disconnected</div>
            
            <div id="messages"></div>
            
            <script>
                let ws = null;
                
                function connect() {
                    const jobId = document.getElementById("jobId").value;
                    if (!jobId) {
                        alert("Please enter a job ID");
                        return;
                    }
                    
                    const url = `ws://localhost:8000/api/v1/ws/jobs/${jobId}`;
                    ws = new WebSocket(url);
                    
                    ws.onopen = () => {
                        document.getElementById("status").textContent = "Status: Connected";
                        addMessage("info", "Connected to job " + jobId);
                    };
                    
                    ws.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        addMessage(data.type, JSON.stringify(data.data, null, 2));
                    };
                    
                    ws.onerror = (error) => {
                        addMessage("error", "WebSocket error: " + error);
                    };
                    
                    ws.onclose = () => {
                        document.getElementById("status").textContent = "Status: Disconnected";
                        addMessage("info", "Disconnected");
                    };
                }
                
                function disconnect() {
                    if (ws) {
                        ws.close();
                        ws = null;
                    }
                }
                
                function addMessage(type, text) {
                    const messages = document.getElementById("messages");
                    const message = document.createElement("div");
                    message.className = "message " + type;
                    message.innerHTML = `<strong>${type.toUpperCase()}:</strong><br><pre>${text}</pre>`;
                    messages.appendChild(message);
                    messages.scrollTop = messages.scrollHeight;
                }
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html)
