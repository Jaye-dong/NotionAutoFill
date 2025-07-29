#!/usr/bin/env python3
"""
Debug script to check Notion record structure
"""

import asyncio
import os
import json
from dotenv import load_dotenv
from notion_client import NotionClient

# Load environment variables
load_dotenv()

async def debug_records():
    """Debug Notion records structure"""
    
    # Get configuration
    notion_token = os.getenv('NOTION_TOKEN')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    if not notion_token or not database_id:
        print("❌ Please set NOTION_TOKEN and NOTION_DATABASE_ID in .env file")
        return
    
    print("🔧 Debugging Notion records structure...")
    
    # Create client
    client = NotionClient(notion_token, database_id)
    
    # Get today's records
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"📅 Fetching records for {today}...")
    records = await client.get_time_records(today)
    
    if not records:
        print("❌ No records found for today")
        # Try to get any records without date filter
        print("🔍 Trying to get any records...")
        # We'll need to modify the client for this, let's just show the structure we expect
        return
    
    print(f"✅ Found {len(records)} records")
    
    # Show structure of first few records
    for i, record in enumerate(records[:3]):  # Show first 3 records
        print(f"\n📋 Record {i+1} structure:")
        print(f"   ID: {record.get('id', 'N/A')}")
        
        properties = record.get('properties', {})
        print(f"   Properties keys: {list(properties.keys())}")
        
        # Check the '记录' field specifically
        if '记录' in properties:
            record_prop = properties['记录']
            print(f"   记录 field type: {record_prop.get('type', 'N/A')}")
            print(f"   记录 field keys: {list(record_prop.keys())}")
            
            # Try to extract content
            content = ""
            if record_prop.get('type') == 'title' and record_prop.get('title'):
                content = ''.join([text.get('plain_text', '') for text in record_prop['title']])
                print(f"   记录 content (title): {content}")
            elif record_prop.get('type') == 'rich_text' and record_prop.get('rich_text'):
                content = ''.join([text.get('plain_text', '') for text in record_prop['rich_text']])
                print(f"   记录 content (rich_text): {content}")
            else:
                print(f"   记录 raw data: {json.dumps(record_prop, ensure_ascii=False, indent=2)}")
        
        # Check classification field
        if '分类' in properties:
            class_prop = properties['分类']
            print(f"   分类 field type: {class_prop.get('type', 'N/A')}")
            if class_prop.get('select'):
                print(f"   分类 current value: {class_prop['select'].get('name', 'N/A')}")
            else:
                print(f"   分类 current value: None")
        
        print("   " + "="*50)

if __name__ == "__main__":
    asyncio.run(debug_records()) 