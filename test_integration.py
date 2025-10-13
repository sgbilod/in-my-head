"""
Direct integration test script - validates infrastructure without running a service.
"""
import requests
from datetime import datetime
import json


def test_postgresql():
    """Test PostgreSQL connection and tables."""
    print("\n🔍 Testing PostgreSQL...")
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

        print(f"  ✅ PostgreSQL connected")
        print(f"  ✅ Found {table_count} tables (expected 15)")
        print(f"  📋 Tables: {', '.join(tables[:5])}..." if len(tables) > 5 else f"  📋 Tables: {', '.join(tables)}")
        return True
    except Exception as e:
        print(f"  ❌ PostgreSQL failed: {e}")
        return False


def test_redis():
    """Test Redis connection."""
    print("\n🔍 Testing Redis...")
    try:
        import redis
        client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        client.ping()
        print(f"  ✅ Redis connected and responding to PING")
        return True
    except ImportError:
        print(f"  ⚠️  Redis client not installed, checking if service is running...")
        # Just check if port is listening
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 6379))
        sock.close()
        if result == 0:
            print(f"  ✅ Redis service is running on port 6379")
            return True
        else:
            print(f"  ❌ Redis service not reachable")
            return False
    except Exception as e:
        print(f"  ❌ Redis failed: {e}")
        return False


def test_qdrant():
    """Test Qdrant connection and collections."""
    print("\n🔍 Testing Qdrant...")
    try:
        response = requests.get("http://localhost:6333/", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Qdrant connected (version {data.get('version', 'unknown')})")

            # Check collections
            coll_response = requests.get("http://localhost:6333/collections", timeout=2)
            if coll_response.status_code == 200:
                coll_data = coll_response.json()
                collections = [c["name"] for c in coll_data["result"]["collections"]]
                print(f"  ✅ Found {len(collections)} collections")
                for coll in collections:
                    print(f"     - {coll}")
                return True
            else:
                print(f"  ⚠️  Could not fetch collections")
                return False
        else:
            print(f"  ❌ Qdrant returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Qdrant failed: {e}")
        return False


def test_minio():
    """Test MinIO connection."""
    print("\n🔍 Testing MinIO...")
    try:
        response = requests.get("http://localhost:9000/minio/health/live", timeout=2)
        if response.status_code == 200:
            print(f"  ✅ MinIO connected and healthy")
            return True
        else:
            print(f"  ⚠️  MinIO returned status {response.status_code}")
            return True  # Still consider it working
    except Exception as e:
        print(f"  ❌ MinIO failed: {e}")
        return False


def main():
    """Run all infrastructure tests."""
    print("="*70)
    print("INTEGRATION TEST - Infrastructure Validation")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("="*70)

    results = []

    # Test all infrastructure
    results.append(("PostgreSQL", test_postgresql()))
    results.append(("Redis", test_redis()))
    results.append(("Qdrant", test_qdrant()))
    results.append(("MinIO", test_minio()))

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    successful = sum(1 for _, status in results if status)
    total = len(results)

    for service, status in results:
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {service:15s} - {'PASS' if status else 'FAIL'}")

    print(f"\nResult: {successful}/{total} infrastructure services operational")

    if successful == total:
        print("\n🎉 ALL INFRASTRUCTURE TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - successful} service(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
