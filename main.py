#!/usr/bin/env python3
"""
Notion Time Record Auto-Classification Tool
Automatically classifies time tracking records using OpenAI
"""

import os
import sys
import logging
import asyncio
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from notion_client import NotionClient
from openai_client import OpenAIClient

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('notion_auto_fill.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class TimeRecordClassifier:
    """Main class for time record classification"""
    
    def __init__(self):
        """Initialize the classifier with configuration from environment variables"""
        # Notion configuration
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.notion_database_id = os.getenv('NOTION_DATABASE_ID')
        
        # OpenAI configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        self.openai_base_url = os.getenv('OPENAI_BASE_URL')
        
        # Validate required configuration
        if not self.notion_token:
            raise ValueError("NOTION_TOKEN environment variable is required")
        if not self.notion_database_id:
            raise ValueError("NOTION_DATABASE_ID environment variable is required")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Initialize clients
        self.notion_client = NotionClient(self.notion_token, self.notion_database_id)
        self.openai_client = OpenAIClient(
            api_key=self.openai_api_key,
            model=self.openai_model,
            base_url=self.openai_base_url
        )
        
        logger.info("TimeRecordClassifier initialized")

    async def process_time_records(self, target_date: Optional[str] = None) -> bool:
        """
        Process and classify time records for a specific date
        
        Args:
            target_date: Date to process (YYYY-MM-DD format), defaults to today
            
        Returns:
            True if processing was successful, False otherwise
        """
        try:
            # Parse target date
            if target_date:
                try:
                    date_obj = datetime.strptime(target_date, '%Y-%m-%d')
                except ValueError:
                    logger.error(f"Invalid date format: {target_date}. Use YYYY-MM-DD")
                    return False
            else:
                date_obj = datetime.now()
            
            date_str = date_obj.strftime('%Y-%m-%d')
            logger.info(f"Processing time records for date: {date_str}")
            
            # Get classification options from database
            classification_options = await self.notion_client.get_classification_options()
            if not classification_options:
                logger.error("No classification options found in database")
                return False
            
            logger.info(f"Available classification options: {classification_options}")
            
            # Get time type options from database
            time_type_options = await self.notion_client.get_time_type_options()
            if not time_type_options:
                logger.warning("No time type options found in database")
            
            logger.info(f"Available time type options: {time_type_options}")
            
            # Get today's records from Notion
            records = await self.notion_client.get_time_records(date_str)
            if not records:
                logger.info(f"No time records found for {date_str}")
                return True
            
            logger.info(f"Found {len(records)} time records for {date_str}")
            
            # Process each record
            classified_count = 0
            for record in records:
                record_id = record.get('id')
                properties = record.get('properties', {})
                
                # Get current classification
                classification_prop = properties.get('分类', {})
                current_classification = None
                if classification_prop.get('type') == 'select' and classification_prop.get('select'):
                    current_classification = classification_prop['select']['name']
                
                # Get current time type
                time_type_prop = properties.get('时间类型', {})
                current_time_type = None
                if time_type_prop.get('type') == 'select' and time_type_prop.get('select'):
                    current_time_type = time_type_prop['select']['name']
                
                # Skip if already classified and typed
                if current_classification and current_time_type:
                    logger.info(f"Record {record_id} already classified as: {current_classification} and typed as: {current_time_type}")
                    continue
                
                # Get record content for classification
                content_text = self.get_record_content(record)
                
                if not content_text.strip():
                    logger.warning(f"Record {record_id} has no content, skipping")
                    continue
                
                logger.info(f"Processing record {record_id}: {content_text[:100]}...")
                
                # Classify the record if not already classified
                classification = current_classification
                if not classification:
                    classification = await self.classify_time_record(content_text, classification_options)
                
                # Determine time type if not already set
                time_type = current_time_type
                if not time_type and time_type_options:
                    time_type = await self.determine_time_type(content_text, time_type_options)
                
                # Update the record in Notion
                success = await self.notion_client.update_record_classification_and_type(
                    record_id, 
                    classification if classification else "", 
                    time_type if time_type else ""
                )
                if success:
                    classified_count += 1
                    if classification and time_type:
                        logger.info(f"Successfully classified record {record_id} as: {classification}, type: {time_type}")
                    elif classification:
                        logger.info(f"Successfully classified record {record_id} as: {classification}")
                    elif time_type:
                        logger.info(f"Successfully typed record {record_id} as: {time_type}")
                    else:
                        logger.info(f"Processed record {record_id} but no classification or type assigned")
                else:
                    logger.error(f"Failed to update record {record_id}")
            
            logger.info(f"Processing complete: {classified_count} records processed")
            return True
            
        except Exception as e:
            logger.error(f"Error processing time records: {str(e)}")
            return False

    async def classify_time_record(self, content: str, classification_options: List[str]) -> Optional[str]:
        """
        Classify a time record using OpenAI
        
        Args:
            content: The content of the time record
            classification_options: Available classification options
            
        Returns:
            Classification result or None if failed
        """
        try:
            # Build classification prompt
            prompt = self.build_classification_prompt(content, classification_options)
            
            # Get classification from OpenAI
            classification = await self.openai_client.classify(prompt)
            
            if not classification:
                logger.warning(f"OpenAI returned empty classification for: {content[:50]}...")
                return None
            
            # Validate classification against options
            # First try exact match
            if classification in classification_options:
                logger.info(f"Exact match found: {classification}")
                return classification
            
            # Try case-insensitive match
            for option in classification_options:
                if classification.lower() == option.lower():
                    logger.info(f"Case-insensitive match found: {option}")
                    return option
            
            # Try partial match
            for option in classification_options:
                if classification.lower() in option.lower() or option.lower() in classification.lower():
                    logger.info(f"Partial match found: {option}")
                    return option
            
            logger.warning(f"No matching classification found for '{classification}' in options: {classification_options}")
            return None
            
        except Exception as e:
            logger.error(f"Error classifying record: {str(e)}")
            return None

    async def determine_time_type(self, content: str, time_type_options: List[str]) -> Optional[str]:
        """
        Determine time type for a time record using OpenAI
        
        Args:
            content: The content of the time record
            time_type_options: Available time type options
            
        Returns:
            Time type result or None if failed
        """
        try:
            # Build time type determination prompt
            prompt = self.build_time_type_prompt(content, time_type_options)
            
            # Get time type from OpenAI
            time_type = await self.openai_client.classify(prompt)
            
            if not time_type:
                logger.warning(f"OpenAI returned empty time type for: {content[:50]}...")
                return None
            
            # Validate time type against options
            # First try exact match
            if time_type in time_type_options:
                logger.info(f"Exact time type match found: {time_type}")
                return time_type
            
            # Try case-insensitive match
            for option in time_type_options:
                if time_type.lower() == option.lower():
                    logger.info(f"Case-insensitive time type match found: {option}")
                    return option
            
            # Try partial match
            for option in time_type_options:
                if time_type.lower() in option.lower() or option.lower() in time_type.lower():
                    logger.info(f"Partial time type match found: {option}")
                    return option
            
            logger.warning(f"No matching time type found for '{time_type}' in options: {time_type_options}")
            return None
            
        except Exception as e:
            logger.error(f"Error determining time type: {str(e)}")
            return None

    def build_classification_prompt(self, content: str, classification_options: List[str]) -> str:
        """
        Build classification prompt for AI
        
        Args:
            content: The content to classify
            classification_options: Available classification options
            
        Returns:
            Formatted prompt string
        """
        options_str = "\n".join([f"- {option}" for option in classification_options])
        
        prompt = f"""Please classify the following time tracking record into one of the exact categories listed below.

Time Record: {content}

Available Categories:
{options_str}

Instructions:
1. Analyze the content of the time record
2. Choose the most appropriate category from the list above
3. Respond with ONLY the exact category name, nothing else
4. If none of the categories fit perfectly, choose the closest one

Classification:"""
        
        return prompt

    def build_time_type_prompt(self, content: str, time_type_options: List[str]) -> str:
        """
        Build time type determination prompt for AI
        
        Args:
            content: The content to determine time type for
            time_type_options: Available time type options
            
        Returns:
            Formatted prompt string
        """
        options_str = "\n".join([f"- {option}" for option in time_type_options])
        
        prompt = f"""Please determine the time type of the following time tracking record. Choose from one of the exact time types listed below.

Time Record: {content}

Available Time Types:
{options_str}

Instructions:
1. Analyze the content of the time record
2. Determine what type of work this represents
3. Choose the most appropriate time type from the list above
4. Respond with ONLY the exact time type name, nothing else
5. If none of the time types fit perfectly, choose the closest one

Time Type:"""
        
        return prompt

    def get_record_content(self, record):
        """Extract content from a Notion record"""
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
            logger.warning(f"No content found in record. Structure: {record_property}")
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting record content: {e}")
            return ""

    async def run(self, target_date: Optional[str] = None) -> bool:
        """
        Main execution method
        
        Args:
            target_date: Date to process (YYYY-MM-DD format)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Starting Notion Time Record Auto-Classification")
            
            # Process time records
            success = await self.process_time_records(target_date)
            
            if success:
                logger.info("Classification completed successfully")
            else:
                logger.error("Classification failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return False


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Notion Time Record Auto-Classification Tool")
    parser.add_argument(
        '--date',
        type=str,
        help='Target date to process (YYYY-MM-DD format). Defaults to today.'
    )
    
    args = parser.parse_args()
    
    try:
        classifier = TimeRecordClassifier()
        success = await classifier.run(args.date)
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"Failed to initialize classifier: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
