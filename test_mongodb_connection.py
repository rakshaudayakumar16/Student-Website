"""
MongoDB Connection Test Script
Run this to check if MongoDB is accessible
"""
from pymongo import MongoClient
import sys

def test_connection(port):
    try:
        print(f"Testing connection to MongoDB on port {port}...")
        client = MongoClient(f'mongodb://localhost:{port}/', serverSelectionTimeoutMS=3000)
        client.server_info()
        print(f"[SUCCESS] Connected to MongoDB on port {port}")
        return True
    except Exception as e:
        print(f"[FAILED] {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("MongoDB Connection Test")
    print("=" * 50)
    
    # Test common ports
    ports = [27017, 27018]
    connected = False
    
    for port in ports:
        if test_connection(port):
            connected = True
            print(f"\n[SUCCESS] MongoDB is running on port {port}")
            print("You can use this port in app.py")
            break
        print()
    
    if not connected:
        print("\n" + "=" * 50)
        print("MongoDB is not accessible on any tested port")
        print("=" * 50)
        print("\nTroubleshooting:")
        print("1. Check if MongoDB is installed")
        print("2. Check if MongoDB service is running:")
        print("   - Windows: Open Services (services.msc) and look for 'MongoDB'")
        print("   - Or run: net start MongoDB")
        print("3. Try starting MongoDB manually:")
        print("   - Open Command Prompt as Administrator")
        print("   - Navigate to MongoDB bin folder")
        print("   - Run: mongod")
        print("4. Check MongoDB configuration file for the port")
        sys.exit(1)
    else:
        print("\n[SUCCESS] Connection test passed!")

