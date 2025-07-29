"""
Notion API Client for Time Record Management
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import aiohttp
import json

logger = logging.getLogger(__name__)


class NotionClient:
    """Client for interacting with Notion API"""
    
    def __init__(self, token: str, database_id: str):
        """Initialize Notion client"""
        self.token = token
        self.database_id = database_id
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        logger.info("Notion client initialized")
    
    async def get_time_records(self, target_date: str) -> List[Dict[str, Any]]:
        """Fetch time records for the specified date"""
        try:
            logger.info(f"Fetching time records for date: {target_date}")
            
            # Build query filter for today's records using the correct property name
            filter_query = {
                "filter": {
                    "property": "时间段",
                    "date": {
                        "equals": target_date
                    }
                }
            }
            
            # Make API request
            url = f"{self.base_url}/databases/{self.database_id}/query"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, json=filter_query) as response:
                    if response.status == 200:
                        data = await response.json()
                        pages = data.get('results', [])
                        
                        logger.info(f"Successfully fetched {len(pages)} time records")
                        return pages
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to fetch records: {response.status} - {error_text}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error fetching time records: {str(e)}")
            return []
    
    async def update_record_classification_and_type(self, record_id: str, classification: str, time_type: str) -> bool:
        """Update the classification and time type of a time record"""
        try:
            logger.info(f"Updating record {record_id} with classification: {classification} and time type: {time_type}")
            
            # Build update data for both classification and time type
            update_data = {
                "properties": {}
            }
            
            # Add classification if provided
            if classification:
                update_data["properties"]["分类"] = {
                    "select": {
                        "name": classification
                    }
                }
            
            # Add time type if provided
            if time_type:
                update_data["properties"]["时间类型"] = {
                    "select": {
                        "name": time_type
                    }
                }
            
            url = f"{self.base_url}/pages/{record_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, headers=self.headers, json=update_data) as response:
                    if response.status == 200:
                        logger.info(f"Successfully updated record {record_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to update record {record_id}: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error updating record {record_id}: {str(e)}")
            return False
    
    async def test_connection(self) -> bool:
        """Test connection to Notion API"""
        try:
            url = f"{self.base_url}/databases/{self.database_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Connection test successful. Database title: {data.get('title', [{}])[0].get('plain_text', 'Unknown')}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Connection test failed: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error testing connection: {str(e)}")
            return False
    
    async def get_classification_options(self) -> List[str]:
        """Get available classification options from the database schema"""
        try:
            logger.info("Fetching classification options from database schema")
            
            url = f"{self.base_url}/databases/{self.database_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        properties = data.get('properties', {})
                        
                        # Get options from 分类 field
                        classification_prop = properties.get('分类')
                        if classification_prop and classification_prop.get('type') == 'select':
                            options = classification_prop.get('select', {}).get('options', [])
                            option_names = [option.get('name', '') for option in options if option.get('name')]
                            logger.info(f"Found {len(option_names)} classification options: {option_names}")
                            return option_names
                        else:
                            logger.warning("分类 field not found or not a select field")
                            return []
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get database schema: {response.status} - {error_text}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error fetching classification options: {str(e)}")
            return []
    
    async def get_time_type_options(self) -> List[str]:
        """Get available time type options from the database schema"""
        try:
            logger.info("Fetching time type options from database schema")
            
            url = f"{self.base_url}/databases/{self.database_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        properties = data.get('properties', {})
                        
                        # Get options from 时间类型 field
                        time_type_prop = properties.get('时间类型')
                        if time_type_prop and time_type_prop.get('type') == 'select':
                            options = time_type_prop.get('select', {}).get('options', [])
                            option_names = [option.get('name', '') for option in options if option.get('name')]
                            logger.info(f"Found {len(option_names)} time type options: {option_names}")
                            return option_names
                        else:
                            logger.warning("时间类型 field not found or not a select field")
                            return []
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get database schema: {response.status} - {error_text}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error fetching time type options: {str(e)}")
            return []
    
    async def create_record(self, properties: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new record in the database"""
        try:
            logger.info("Creating new record in database")
            
            # Build the request data
            request_data = {
                "parent": {"database_id": self.database_id},
                "properties": properties
            }
            
            url = f"{self.base_url}/pages"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, json=request_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Successfully created record with ID: {data.get('id', 'Unknown')}")
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to create record: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error creating record: {str(e)}")
            return None