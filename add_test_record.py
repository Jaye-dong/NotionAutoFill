import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime
from notion_client import NotionClient

# Load environment variables
load_dotenv()

async def add_test_record():
    """Add a test record without classification"""
    print("➕ Adding Test Record")
    print("=" * 30)
    
    # Get configuration
    notion_token = os.getenv('NOTION_TOKEN')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    if not notion_token or not database_id:
        print("❌ Missing NOTION_TOKEN or NOTION_DATABASE_ID in .env file")
        return
    
    # Create Notion client
    notion_client = NotionClient(notion_token, database_id)
    
    try:
        # Create a test record
        test_content = "写代码开发新功能"
        
        # Record properties (without classification)
        properties = {
            "记录": {
                "title": [
                    {
                        "text": {
                            "content": test_content
                        }
                    }
                ]
            },
            "时间段": {
                "date": {
                    "start": datetime.now().strftime('%Y-%m-%d')
                }
            }
        }
        
        print(f"📝 Creating test record: '{test_content}'")
        
        # Add the record
        result = await notion_client.create_record(properties)
        
        if result:
            print(f"✅ Test record created successfully!")
            print(f"   Record ID: {result.get('id', 'Unknown')}")
            print(f"   Content: {test_content}")
            print(f"   Classification: None (to be classified)")
        else:
            print("❌ Failed to create test record")
            
    except Exception as e:
        print(f"❌ Error creating test record: {e}")

if __name__ == "__main__":
    asyncio.run(add_test_record()) 