"""
Simple Qdrant connection test using HTTP requests only.
No dependencies required beyond Python standard library.
"""

import json
import sys
try:
    from urllib.request import urlopen, Request
    from urllib.error import URLError
except ImportError:
    print("Error: Required modules not available")
    sys.exit(1)


def test_qdrant_connection():
    """Test Qdrant connection and collections."""
    print("\n" + "="*70)
    print("QDRANT CONNECTION TEST")
    print("="*70 + "\n")

    qdrant_url = "http://localhost:6333"

    # Test 1: Health check
    print("1. Testing Qdrant health...")
    try:
        response = urlopen(f"{qdrant_url}", timeout=5)
        health = json.loads(response.read())
        print(f"   ✓ Qdrant is running: v{health.get('version', 'unknown')}")
    except URLError as e:
        print(f"   ✗ Cannot connect to Qdrant: {e}")
        print(f"      Make sure Qdrant is running on {qdrant_url}")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

    print()

    # Test 2: List collections
    print("2. Listing collections...")
    try:
        response = urlopen(f"{qdrant_url}/collections", timeout=5)
        data = json.loads(response.read())
        collections = data.get("result", {}).get("collections", [])

        if collections:
            print(f"   ✓ Found {len(collections)} collection(s):")
            for coll in collections:
                print(f"      - {coll['name']}")
        else:
            print("   ⚠ No collections found yet (this is OK for first run)")
    except Exception as e:
        print(f"   ✗ Failed to list collections: {e}")
        return False

    print()

    # Test 3: Create test collection
    print("3. Testing collection creation...")
    collection_name = "test_collection"

    # First, try to delete if exists
    try:
        req = Request(
            f"{qdrant_url}/collections/{collection_name}",
            method="DELETE"
        )
        urlopen(req, timeout=5)
        print(f"   ✓ Deleted existing test collection")
    except:
        pass  # Collection might not exist

    # Create collection
    try:
        collection_config = {
            "vectors": {
                "size": 384,
                "distance": "Cosine"
            }
        }

        req = Request(
            f"{qdrant_url}/collections/{collection_name}",
            data=json.dumps(collection_config).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method="PUT"
        )
        response = urlopen(req, timeout=5)
        result = json.loads(response.read())

        if result.get("status") == "ok":
            print(f"   ✓ Created test collection '{collection_name}'")
        else:
            print(f"   ⚠ Unexpected response: {result}")
    except Exception as e:
        print(f"   ✗ Failed to create collection: {e}")
        return False

    print()

    # Test 4: Insert test vector
    print("4. Testing vector insertion...")
    try:
        test_point = {
            "points": [
                {
                    "id": 1,
                    "vector": [0.1] * 384,
                    "payload": {
                        "title": "Test Document",
                        "test": True
                    }
                }
            ]
        }

        req = Request(
            f"{qdrant_url}/collections/{collection_name}/points",
            data=json.dumps(test_point).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method="PUT"
        )
        response = urlopen(req, timeout=5)
        result = json.loads(response.read())

        if result.get("status") == "ok":
            print("   ✓ Inserted test vector")
        else:
            print(f"   ⚠ Unexpected response: {result}")
    except Exception as e:
        print(f"   ✗ Failed to insert vector: {e}")
        return False

    print()

    # Test 5: Search test
    print("5. Testing vector search...")
    try:
        search_query = {
            "vector": [0.1] * 384,
            "limit": 5,
            "with_payload": True
        }

        req = Request(
            f"{qdrant_url}/collections/{collection_name}/points/search",
            data=json.dumps(search_query).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        response = urlopen(req, timeout=5)
        result = json.loads(response.read())

        results = result.get("result", [])
        if results:
            print(f"   ✓ Search returned {len(results)} result(s)")
            print(f"      - Top score: {results[0]['score']:.4f}")
            print(f"      - Payload: {results[0]['payload']}")
        else:
            print("   ⚠ Search returned no results")
    except Exception as e:
        print(f"   ✗ Search failed: {e}")
        return False

    print()

    # Cleanup
    print("6. Cleaning up...")
    try:
        req = Request(
            f"{qdrant_url}/collections/{collection_name}",
            method="DELETE"
        )
        urlopen(req, timeout=5)
        print("   ✓ Deleted test collection")
    except Exception as e:
        print(f"   ⚠ Cleanup failed: {e}")

    print()

    # Summary
    print("="*70)
    print("✓ ALL TESTS PASSED - QDRANT IS OPERATIONAL")
    print("="*70)
    print()
    print("Qdrant is ready for AI Engine!")
    print()
    print("Next Steps:")
    print("1. Install AI Engine dependencies:")
    print("   cd services/ai-engine")
    print("   python -m venv venv")
    print("   venv\\Scripts\\activate")
    print("   pip install -r requirements.txt")
    print()
    print("2. Start AI Engine service:")
    print("   .\\start-ai-engine.ps1")
    print()
    print("3. Run embedding migration:")
    print("   python scripts\\migrate_embeddings_to_qdrant.py")
    print()

    return True


if __name__ == "__main__":
    try:
        success = test_qdrant_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
