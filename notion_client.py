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
    
    def __init__(self, token: str, database_id: str, next_action_database_id: str = None):
        """Initialize Notion client"""
        self.token = token
        self.database_id = database_id
        self.next_action_database_id = next_action_database_id
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        logger.info("Notion client initialized")
    
    async def get_time_records(self, target_date: str = None) -> List[Dict[str, Any]]:
        """Fetch time records - either for a specific date or all unclassified records"""
        try:
            if target_date:
                logger.info(f"Fetching unclassified time records for date: {target_date}")
                # Build query filter for the date range AND unclassified records
                filter_query = {
                    "filter": {
                        "and": [
                            {
                                "property": "时间段",
                                "date": {
                                    "on_or_after": f"{target_date}T00:00:00+08:00"
                                }
                            },
                            {
                                "property": "时间段",
                                "date": {
                                    "on_or_before": f"{target_date}T23:59:59+08:00"
                                }
                            },
                            {
                                "property": "分类",
                                "select": {
                                    "is_empty": True
                                }
                            }
                        ]
                    }
                }
            else:
                logger.info("Fetching all unclassified time records")
                # Build query filter for unclassified records only
                filter_query = {
                    "filter": {
                        "property": "分类",
                        "select": {
                            "is_empty": True
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
    
    async def update_record_classification(self, record_id: str, classification: str) -> bool:
        """Update the classification of a time record"""
        try:
            logger.info(f"Updating record {record_id} with classification: {classification}")

            # Build update data for classification
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
            else:
                logger.warning(f"No classification provided for record {record_id}")
                return False

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
        """Get available classification options from the database schema (excluding '未分类')"""
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
                            # Filter out "未分类" option
                            option_names = [option.get('name', '') for option in options
                                          if option.get('name') and option.get('name') != '未分类']
                            logger.info(f"Found {len(option_names)} classification options (excluding '未分类'): {option_names}")
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
    
    async def get_next_actions(self) -> List[Dict[str, Any]]:
        """Fetch all next action records that need AI assessment"""
        try:
            if not self.next_action_database_id:
                logger.warning("Next action database ID not configured")
                return []
                
            logger.info("Fetching next action records that need AI assessment")
            
            # Query records where Status is "To Do" AND any of the AI fields are empty
            filter_query = {
                "filter": {
                    "and": [
                        {
                            "property": "Status",
                            "status": {
                                "equals": "To Do"
                            }
                        },
                        {
                            "or": [
                                {
                                    "property": "精力消耗",
                                    "select": {
                                        "is_empty": True
                                    }
                                },
                                {
                                    "property": "Estimates",
                                    "select": {
                                        "is_empty": True
                                    }
                                },
                                {
                                    "property": "情景",
                                    "select": {
                                        "is_empty": True
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
            
            # Make API request
            url = f"{self.base_url}/databases/{self.next_action_database_id}/query"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, json=filter_query) as response:
                    if response.status == 200:
                        data = await response.json()
                        pages = data.get('results', [])
                        
                        logger.info(f"Successfully fetched {len(pages)} next action records")
                        return pages
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to fetch next actions: {response.status} - {error_text}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error fetching next actions: {str(e)}")
            return []
    
    async def get_next_action_field_options(self) -> Dict[str, List[str]]:
        """Get available options for energy cost and context fields from the database schema"""
        try:
            if not self.next_action_database_id:
                logger.warning("Next action database ID not configured")
                return {}
                
            logger.info("Fetching next action field options from database schema")
            
            url = f"{self.base_url}/databases/{self.next_action_database_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        properties = data.get('properties', {})
                        
                        field_options = {}
                        
                        # Get options from 精力消耗 field
                        energy_prop = properties.get('精力消耗')
                        if energy_prop and energy_prop.get('type') == 'select':
                            options = energy_prop.get('select', {}).get('options', [])
                            option_names = [option.get('name', '') for option in options if option.get('name')]
                            field_options['精力消耗'] = option_names
                            logger.info(f"Found {len(option_names)} energy cost options: {option_names}")
                        
                        # Get options from Estimates field
                        estimates_prop = properties.get('Estimates')
                        if estimates_prop and estimates_prop.get('type') == 'select':
                            options = estimates_prop.get('select', {}).get('options', [])
                            option_names = [option.get('name', '') for option in options if option.get('name')]
                            field_options['Estimates'] = option_names
                            logger.info(f"Found {len(option_names)} estimates options: {option_names}")
                        
                        # Get options from 情景 field
                        context_prop = properties.get('情景')
                        if context_prop and context_prop.get('type') == 'select':
                            options = context_prop.get('select', {}).get('options', [])
                            option_names = [option.get('name', '') for option in options if option.get('name')]
                            field_options['情景'] = option_names
                            logger.info(f"Found {len(option_names)} context options: {option_names}")
                        
                        return field_options
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get next action database schema: {response.status} - {error_text}")
                        return {}
                        
        except Exception as e:
            logger.error(f"Error fetching next action field options: {str(e)}")
            return {}
    
    async def update_next_action_fields(self, record_id: str, energy_cost: str = None, 
                                      estimates: str = None, context: str = None) -> bool:
        """Update the AI-assessed fields of a next action record"""
        try:
            logger.info(f"Updating next action {record_id} with AI assessments")
            
            # Build update data for the fields that need updating
            update_data = {"properties": {}}
            
            if energy_cost:
                update_data["properties"]["精力消耗"] = {
                    "select": {"name": energy_cost}
                }
            
            if estimates:
                update_data["properties"]["Estimates"] = {
                    "select": {"name": estimates}
                }
            
            if context:
                update_data["properties"]["情景"] = {
                    "select": {"name": context}
                }
            
            if not update_data["properties"]:
                logger.warning(f"No fields to update for next action {record_id}")
                return True
            
            url = f"{self.base_url}/pages/{record_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, headers=self.headers, json=update_data) as response:
                    if response.status == 200:
                        fields_updated = list(update_data["properties"].keys())
                        logger.info(f"Successfully updated next action {record_id} fields: {fields_updated}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to update next action {record_id}: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error updating next action {record_id}: {str(e)}")
            return False