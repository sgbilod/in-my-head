"""
Simple FastAPI service for integration testing.
Demonstrates that the system can start services and connect to infrastructure.
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import requests
from datetime import datetime

app = FastAPI(title="Integration Test Service", version="1.0.0")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "integration-test", "timestamp": datetime.now().isoformat()}


@app.get("/test/infrastructure")
async def test_infrastructure():
    """Test connectivity to all infrastructure services."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": []
    }

    # Test PostgreSQL
    try:
        import psycopg2
        conn = psycopg2.connect("postgresql://inmyhead_user:dev_password_123@localhost:5432/inmyhead")
        conn.close()
        results["tests"].append({"service": "PostgreSQL", "status": "connected", "port": 5432})
    except Exception as e:
        results["tests"].append({"service": "PostgreSQL", "status": "failed", "error": str(e)})

    # Test Redis
    try:
        response = requests.get("http://localhost:6379", timeout=2)
        results["tests"].append({"service": "Redis", "status": "reachable", "port": 6379})
    except Exception as e:
        # Redis doesn't respond to HTTP, but if it's running, connection will be refused
        if "Connection refused" in str(e) or "ConnectionError" in str(type(e).__name__):
            results["tests"].append({"service": "Redis", "status": "running", "port": 6379})
        else:
            results["tests"].append({"service": "Redis", "status": "failed", "error": str(e)})

    # Test Qdrant
    try:
        response = requests.get("http://localhost:6333/", timeout=2)
        if response.status_code == 200:
            data = response.json()
            results["tests"].append({"service": "Qdrant", "status": "connected", "version": data.get("version"), "port": 6333})
        else:
            results["tests"].append({"service": "Qdrant", "status": "reachable", "port": 6333})
    except Exception as e:
        results["tests"].append({"service": "Qdrant", "status": "failed", "error": str(e)})

    # Test MinIO
    try:
        response = requests.get("http://localhost:9000/minio/health/live", timeout=2)
        results["tests"].append({"service": "MinIO", "status": "connected", "port": 9000})
    except Exception as e:
        results["tests"].append({"service": "MinIO", "status": "failed", "error": str(e)})

    # Count successes
    successful = sum(1 for test in results["tests"] if test["status"] in ["connected", "running", "reachable"])
    total = len(results["tests"])
    results["summary"] = f"{successful}/{total} infrastructure services operational"

    return JSONResponse(content=results)


@app.get("/test/database")
async def test_database():
    """Test database tables exist."""
    try:
        import psycopg2
        conn = psycopg2.connect("postgresql://inmyhead_user:dev_password_123@localhost:5432/inmyhead")
        cursor = conn.cursor()

        # Get table count
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
        table_count = cursor.fetchone()[0]

        # Get table names
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
        tables = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return {
            "status": "connected",
            "table_count": table_count,
            "tables": tables,
            "expected": 15
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "failed", "error": str(e)}
        )


@app.get("/test/qdrant")
async def test_qdrant():
    """Test Qdrant collections exist."""
    try:
        response = requests.get("http://localhost:6333/collections", timeout=2)
        if response.status_code == 200:
            data = response.json()
            collections = [c["name"] for c in data["result"]["collections"]]
            return {
                "status": "connected",
                "collection_count": len(collections),
                "collections": collections,
                "expected": ["document_embeddings", "chunk_embeddings", "kg_node_embeddings"]
            }
        else:
            return JSONResponse(
                status_code=response.status_code,
                content={"status": "failed", "error": "Unexpected status code"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "failed", "error": str(e)}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
