#!/usr/bin/env python3
"""
Debug script to inspect Notion database schema
"""

import asyncio
import json
from config import Config
from notion_client import NotionClient

async def debug_database():
    """Debug the database structure"""
    print("Debugging Notion Database Schema")
    print("=" * 50)
    
    config = Config.from_environment()
    if not config.is_valid():
        print("Invalid configuration")
        return
    
    notion_client = NotionClient(config.notion_token, config.database_id)
    
    try:
        # Get database schema
        import aiohttp
        url = f"{notion_client.base_url}/databases/{config.database_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=notion_client.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    print("Database Properties:")
                    properties = data.get('properties', {})
                    for prop_name, prop_info in properties.items():
                        prop_type = prop_info.get('type', 'unknown')
                        print(f"  - {prop_name}: {prop_type}")
                        
                        # Show select options for 分类 field
                        if prop_name == '分类' and prop_type == 'select':
                            select_options = prop_info.get('select', {}).get('options', [])
                            if select_options:
                                print(f"    Available options:")
                                for option in select_options:
                                    print(f"      * {option.get('name', 'Unknown')}")
                            else:
                                print(f"    No options found")
                    
                    print(f"\nTotal properties: {len(properties)}")
                    
                    # Also try to get a few sample records
                    print("\nSample Records:")
                    query_url = f"{notion_client.base_url}/databases/{config.database_id}/query"
                    query_data = {"page_size": 3}
                    
                    async with session.post(query_url, headers=notion_client.headers, json=query_data) as query_response:
                        if query_response.status == 200:
                            query_result = await query_response.json()
                            results = query_result.get('results', [])
                            
                            for i, page in enumerate(results):
                                print(f"\nRecord {i+1}:")
                                page_props = page.get('properties', {})
                                for prop_name, prop_value in page_props.items():
                                    # Simplify the display
                                    if prop_value.get('type') == 'title':
                                        title_text = ''.join([t.get('plain_text', '') for t in prop_value.get('title', [])])
                                        print(f"  {prop_name}: {title_text}")
                                    elif prop_value.get('type') == 'rich_text':
                                        rich_text = ''.join([t.get('plain_text', '') for t in prop_value.get('rich_text', [])])
                                        print(f"  {prop_name}: {rich_text}")
                                    elif prop_value.get('type') == 'date':
                                        date_info = prop_value.get('date')
                                        if date_info:
                                            print(f"  {prop_name}: {date_info.get('start', 'N/A')} - {date_info.get('end', 'N/A')}")
                                    elif prop_value.get('type') == 'number':
                                        print(f"  {prop_name}: {prop_value.get('number', 'N/A')}")
                                    elif prop_value.get('type') == 'select':
                                        select_info = prop_value.get('select')
                                        if select_info:
                                            print(f"  {prop_name}: {select_info.get('name', 'N/A')}")
                                    else:
                                        print(f"  {prop_name}: {prop_value.get('type', 'unknown type')}")
                        else:
                            print("Failed to fetch sample records")
                    
                else:
                    error_text = await response.text()
                    print(f"Failed to get database schema: {response.status} - {error_text}")
                    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(debug_database()) 