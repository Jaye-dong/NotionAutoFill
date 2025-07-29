import asyncio
import os
from dotenv import load_dotenv
import json
from datetime import datetime
from notion_client import NotionClient

# Load environment variables
load_dotenv()

def get_record_content(record):
    """Extract content from a Notion record - same logic as in main.py"""
    try:
        # Get the 记录 property
        record_property = record.get('properties', {}).get('记录', {})
        
        if record_property.get('type') == 'title':
            # For title type, content is in the title array
            title_array = record_property.get('title', [])
            if title_array and len(title_array) > 0:
                # Get the plain text from the first title element
                return title_array[0].get('plain_text', '').strip()
        
        elif record_property.get('type') == 'rich_text':
            # For rich_text type, content is in the rich_text array
            rich_text_array = record_property.get('rich_text', [])
            if rich_text_array and len(rich_text_array) > 0:
                return rich_text_array[0].get('plain_text', '').strip()
        
        # If no content found, log the structure for debugging
        print(f"⚠️ No content found in record. Structure: {record_property}")
        return ""
        
    except Exception as e:
        print(f"❌ Error extracting record content: {e}")
        return ""

async def test_content_extraction():
    """Test content extraction from Notion records"""
    print("🧪 Testing Content Extraction Logic")
    print("=" * 50)
    
    # Get configuration
    notion_token = os.getenv('NOTION_TOKEN')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    if not notion_token or not database_id:
        print("❌ Missing NOTION_TOKEN or NOTION_DATABASE_ID in .env file")
        return
    
    # Create Notion client
    notion_client = NotionClient(notion_token, database_id)
    
    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"📅 Fetching records for {today}...")
    
    try:
        # Fetch records
        records = await notion_client.get_time_records(today)
        
        if not records:
            print("📝 No records found for today")
            return
        
        print(f"✅ Found {len(records)} records")
        print()
        
        # Test content extraction for each record
        for i, record in enumerate(records, 1):
            print(f"📋 Testing Record {i}:")
            print(f"   ID: {record.get('id', 'Unknown')}")
            
            # Extract content using our function
            content = get_record_content(record)
            print(f"   Extracted content: '{content}'")
            
            # Show classification status
            classification_prop = record.get('properties', {}).get('分类', {})
            if classification_prop.get('select'):
                current_classification = classification_prop['select'].get('name', 'None')
                print(f"   Current classification: {current_classification}")
            else:
                print(f"   Current classification: None (needs classification)")
            
            print("   " + "=" * 40)
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    asyncio.run(test_content_extraction()) 