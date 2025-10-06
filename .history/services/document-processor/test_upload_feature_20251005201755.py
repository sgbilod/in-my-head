"""
Quick test script for document upload feature
Run after starting the FastAPI server
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8001"


def test_health():
    """Test health endpoint"""
    print("\n🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    print("✅ Health check passed!")


def test_upload_text_file():
    """Test uploading a text file"""
    print("\n📤 Testing document upload...")
    
    # Create a test file
    test_file = Path("test_upload.txt")
    test_file.write_text("This is a test document for In My Head!\n\nIt has multiple lines.")
    
    try:
        # Upload file
        with open(test_file, 'rb') as f:
            files = {'file': (test_file.name, f, 'text/plain')}
            data = {'tags': 'test,demo,automated'}
            
            response = requests.post(
                f"{BASE_URL}/documents/upload",
                files=files,
                data=data
            )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✅ Document uploaded successfully!")
            print(f"   ID: {result['id']}")
            print(f"   Title: {result['title']}")
            print(f"   Type: {result['document_type']}")
            print(f"   Status: {result['processing_status']}")
            print(f"   Word Count: {result['word_count']}")
            print(f"   Tags: {[tag['name'] for tag in result['tags']]}")
            return result['id']
        else:
            print(f"❌ Upload failed: {response.text}")
            return None
    
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()


def test_list_documents():
    """Test listing documents"""
    print("\n📋 Testing document list...")
    response = requests.get(f"{BASE_URL}/documents/")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Found {result['total']} documents")
        
        if result['documents']:
            print("\nFirst document:")
            doc = result['documents'][0]
            print(f"   ID: {doc['id']}")
            print(f"   Title: {doc['title']}")
            print(f"   Created: {doc['created_at']}")
    else:
        print(f"❌ List failed: {response.text}")


def test_get_document_content(doc_id):
    """Test getting document content"""
    print(f"\n📄 Testing get document content (ID: {doc_id})...")
    response = requests.get(f"{BASE_URL}/documents/{doc_id}/content")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Content retrieved!")
        print(f"Content preview: {result['content'][:100]}...")
    else:
        print(f"❌ Get content failed: {response.text}")


def test_api_docs():
    """Check if API docs are accessible"""
    print("\n📖 Checking API documentation...")
    response = requests.get(f"{BASE_URL}/docs")
    
    if response.status_code == 200:
        print(f"✅ API docs available at {BASE_URL}/docs")
    else:
        print(f"⚠️  API docs may not be accessible")


def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 DOCUMENT UPLOAD FEATURE TESTS")
    print("=" * 60)
    
    try:
        # Test basic health
        test_health()
        
        # Test API docs
        test_api_docs()
        
        # Test document upload
        doc_id = test_upload_text_file()
        
        # Test list documents
        test_list_documents()
        
        # Test get content
        if doc_id:
            test_get_document_content(doc_id)
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED!")
        print("=" * 60)
        print(f"\n🌐 Visit {BASE_URL}/docs for interactive API testing")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server")
        print("   Make sure the server is running:")
        print("   cd \"C:\\Users\\sgbil\\In My Head\"")
        print("   .\\scripts\\start-document-processor.ps1")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    main()
