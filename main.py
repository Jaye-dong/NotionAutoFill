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
        self.next_action_database_id = os.getenv('NEXT_ACTION_DATABASE_ID')
        
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
        self.notion_client = NotionClient(
            self.notion_token, 
            self.notion_database_id,
            self.next_action_database_id
        )
        self.openai_client = OpenAIClient(
            api_key=self.openai_api_key,
            model=self.openai_model,
            base_url=self.openai_base_url
        )
        
        logger.info("TimeRecordClassifier initialized")

    async def process_time_records(self, target_date: Optional[str] = None) -> bool:
        """
        Process and classify time records
        
        Args:
            target_date: Date to process (YYYY-MM-DD format), if None processes all unclassified records
            
        Returns:
            True if processing was successful, False otherwise
        """
        try:
            # Parse target date if provided
            date_str = None
            if target_date:
                try:
                    date_obj = datetime.strptime(target_date, '%Y-%m-%d')
                    date_str = date_obj.strftime('%Y-%m-%d')
                    logger.info(f"Processing unclassified time records for date: {date_str}")
                except ValueError:
                    logger.error(f"Invalid date format: {target_date}. Use YYYY-MM-DD")
                    return False
            else:
                logger.info("Processing all unclassified time records")
            
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
            
            # Get records from Notion
            records = await self.notion_client.get_time_records(date_str)
            if not records:
                if date_str:
                    logger.info(f"No unclassified time records found for {date_str}")
                else:
                    logger.info("No unclassified time records found")
                return True
            
            if date_str:
                logger.info(f"Found {len(records)} unclassified time records for {date_str}")
            else:
                logger.info(f"Found {len(records)} unclassified time records")
            
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
        options_str = "\n".join([f"{i+1}. {option}" for i, option in enumerate(classification_options)])

        prompt = f"""你是一个时间分类助手,需要将用户的活动分类到以下8个类别:

1. 深度工作:需要专注思考的工作(写代码、调试复杂bug、技术方案设计)
2. 浅层工作:必要但不需要深度思考(会议、邮件、打包编译、写文档)
3. 被动工作:被打断、被迫做的工作(传包、救火、客户突发问题)
4. 主动学习:有目的的学习(看书、看课程、刷题)
5. 假装学习:看似在学但没投入(打开书但走神、报了课但没学)
6. 生活必需:日常必需活动(通勤、做饭、吃饭、洗澡、家务)
7. 恢复休息:真正恢复精力(睡觉、运动、高质量社交、高质量陪伴)
8. 无效拖延:既没产出也没恢复(刷手机、看视频、发呆、逃避任务)

【关键判断规则】:

## 工作类的区分:
- "写代码、调试、技术攻坚" → 深度工作
- "开会、写日报、处理编译" → 浅层工作
- "被打断、传包、救火" → 被动工作
- 用户明确说"摸鱼"、"拖延" → 无效拖延

## 学习类的区分:
- 用户说"认真看"、"做笔记"、"有收获" → 主动学习
- 用户说"走神"、"没看进去"、"打开但没学" → 假装学习
- "看技术文章"但在工作时间 → 可能是无效拖延(需要用户澄清)

## 休息类的区分:
- "睡觉"、"运动"、"和朋友吃饭" → 恢复休息
- "刷手机"、"看视频" → 默认为无效拖延
- 除非用户明确说"看了高质量电影"、"玩游戏很投入" → 才是恢复休息

## 生活必需的识别:
- "通勤"、"做饭"、"吃饭"、"洗澡"、"买菜"、"家务" → 生活必需

## 特殊情况:
- 如果用户说"该做X但在做Y" → Y是无效拖延
- 如果用户说"陪伴"但没说质量 → 默认恢复休息

用户记录: {content}

数据库中可用的分类选项:
{options_str}

请根据上述规则,从数据库中可用的选项里选择最匹配的一个类别。只需要回复精确的类别名称,不要有任何其他内容。

分类:"""

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

    async def process_next_actions(self) -> bool:
        """
        Process and assess next action records with AI
        
        Returns:
            True if processing was successful, False otherwise
        """
        try:
            if not self.next_action_database_id:
                logger.info("Next action database ID not configured, skipping next actions")
                return True
                
            logger.info("Processing next action records for AI assessment")
            
            # Get field options from next action database
            field_options = await self.notion_client.get_next_action_field_options()
            logger.info(f"Available field options: {field_options}")
            
            # Get next action records from Notion
            records = await self.notion_client.get_next_actions()
            if not records:
                logger.info("No next action records found that need AI assessment")
                return True
            
            logger.info(f"Found {len(records)} next action records to assess")
            
            # Process each record
            processed_count = 0
            for record in records:
                record_id = record.get('id')
                properties = record.get('properties', {})
                
                # Get record content
                task_name = self.get_next_action_content(record)
                
                if not task_name.strip():
                    logger.warning(f"Next action {record_id} has no task name, skipping")
                    continue
                
                logger.info(f"Processing next action {record_id}: {task_name[:100]}...")
                
                # Check which fields need to be filled
                current_energy = self.extract_property_text(properties.get('精力消耗', {}))
                current_estimates = self.extract_property_text(properties.get('Estimates', {}))
                current_context = self.extract_property_text(properties.get('情景', {}))
                
                # Get AI assessment for missing fields
                assessment = await self.assess_next_action(record, field_options)
                
                if not assessment:
                    logger.warning(f"Failed to get AI assessment for next action {record_id}")
                    continue
                
                # Prepare fields to update
                energy_cost = assessment.get('energy_cost') if not current_energy else None
                estimates = assessment.get('estimates') if not current_estimates else None
                context = assessment.get('context') if not current_context else None
                
                # Update the record in Notion
                success = await self.notion_client.update_next_action_fields(
                    record_id, energy_cost, estimates, context
                )
                if success:
                    processed_count += 1
                    updates = []
                    if energy_cost: updates.append(f"精力消耗: {energy_cost}")
                    if estimates: updates.append(f"Estimates: {estimates}")
                    if context: updates.append(f"情景: {context}")
                    logger.info(f"Successfully updated next action {record_id} with: {', '.join(updates)}")
                else:
                    logger.error(f"Failed to update next action {record_id}")
            
            logger.info(f"Next action processing complete: {processed_count} records processed")
            return True
            
        except Exception as e:
            logger.error(f"Error processing next actions: {str(e)}")
            return False

    async def assess_next_action(self, record: Dict[str, Any], field_options: Dict[str, List[str]]) -> Optional[Dict[str, str]]:
        """
        Assess a next action record using AI to determine energy cost, estimates, and context
        
        Args:
            record: The next action record
            field_options: Available options for select fields
            
        Returns:
            Dict with energy_cost, estimates, context or None if failed
        """
        try:
            # Build assessment prompt
            prompt = self.build_next_action_assessment_prompt(record, field_options)
            
            # Get assessment from OpenAI
            assessment_response = await self.openai_client.classify(prompt)
            
            if not assessment_response:
                logger.warning(f"OpenAI returned empty assessment for next action")
                return None
            
            # Parse the structured response
            assessment = self.parse_assessment_response(assessment_response, field_options)
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error assessing next action: {str(e)}")
            return None

    def build_next_action_assessment_prompt(self, record: Dict[str, Any], field_options: Dict[str, List[str]]) -> str:
        """
        Build assessment prompt for next action AI analysis
        
        Args:
            record: The next action record
            field_options: Available options for select fields
            
        Returns:
            Formatted prompt string
        """
        properties = record.get('properties', {})
        
        # Extract task name
        task_name = self.get_next_action_content(record)
        
        # Extract any existing context
        existing_energy = self.extract_property_text(properties.get('精力消耗', {}))
        existing_estimates = self.extract_property_text(properties.get('Estimates', {}))
        existing_context = self.extract_property_text(properties.get('情景', {}))
        
        # Build options strings
        energy_options_str = ""
        if '精力消耗' in field_options:
            energy_options_str = ", ".join(field_options['精力消耗'])
        
        estimates_options_str = ""
        if 'Estimates' in field_options:
            estimates_options_str = ", ".join(field_options['Estimates'])
        
        context_options_str = ""
        if '情景' in field_options:
            context_options_str = ", ".join(field_options['情景'])
        
        prompt = f"""Please assess the following task and provide values for the requested fields.

Task Name: {task_name}

Current Values:
- Energy Cost: {existing_energy if existing_energy else 'Not set'}
- Time Estimate: {existing_estimates if existing_estimates else 'Not set'}
- Context/Scenario: {existing_context if existing_context else 'Not set'}

Please provide assessments for the fields that are "Not set":

1. Energy Cost (choose from: {energy_options_str if energy_options_str else 'any appropriate level like Low, Medium, High'}):
   Consider the mental/physical effort required

2. Time Estimate (choose from: {estimates_options_str if estimates_options_str else 'any appropriate estimate like 15min, 30min, 1h, 2h'}):
   Select the most appropriate time estimate

3. Context/Scenario (choose from: {context_options_str if context_options_str else 'any appropriate context'}):
   When/where is this task best performed?

Please respond in this exact format:
ENERGY_COST: [your assessment]
ESTIMATES: [your assessment]
CONTEXT: [your assessment]

If a field already has a value, respond with "SKIP" for that field.

Assessment:"""
        
        return prompt

    def parse_assessment_response(self, response: str, field_options: Dict[str, List[str]]) -> Dict[str, str]:
        """
        Parse AI assessment response into structured data
        
        Args:
            response: AI response string
            field_options: Available options for validation
            
        Returns:
            Dict with parsed assessments
        """
        assessment = {}
        
        try:
            lines = response.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == 'ENERGY_COST' and value != 'SKIP':
                        # Validate against available options
                        if '精力消耗' in field_options:
                            matched_option = self.find_best_match(value, field_options['精力消耗'])
                            if matched_option:
                                assessment['energy_cost'] = matched_option
                        else:
                            assessment['energy_cost'] = value
                    
                    elif key == 'ESTIMATES' and value != 'SKIP':
                        # Validate against available options
                        if 'Estimates' in field_options:
                            matched_option = self.find_best_match(value, field_options['Estimates'])
                            if matched_option:
                                assessment['estimates'] = matched_option
                        else:
                            assessment['estimates'] = value
                    
                    elif key == 'CONTEXT' and value != 'SKIP':
                        # Validate against available options
                        if '情景' in field_options:
                            matched_option = self.find_best_match(value, field_options['情景'])
                            if matched_option:
                                assessment['context'] = matched_option
                        else:
                            assessment['context'] = value
            
            logger.info(f"Parsed assessment: {assessment}")
            return assessment
            
        except Exception as e:
            logger.error(f"Error parsing assessment response: {e}")
            return {}

    def find_best_match(self, ai_value: str, options: List[str]) -> Optional[str]:
        """Find the best matching option for an AI-provided value"""
        if not ai_value or not options:
            return None
        
        # Exact match
        if ai_value in options:
            return ai_value
        
        # Case-insensitive match
        for option in options:
            if ai_value.lower() == option.lower():
                return option
        
        # Partial match
        for option in options:
            if ai_value.lower() in option.lower() or option.lower() in ai_value.lower():
                return option
        
        logger.warning(f"No match found for '{ai_value}' in options: {options}")
        return None

    def get_next_action_content(self, record: Dict[str, Any]) -> str:
        """Extract task name from a next action record"""
        try:
            properties = record.get('properties', {})
            
            # Try common field names for task name
            for field_name in ['Task name', 'Task Name', 'Name', 'Title', '任务名称', '任务']:
                if field_name in properties:
                    return self.extract_property_text(properties[field_name])
            
            # If no specific task name field found, log the structure for debugging
            logger.warning(f"No task name field found in next action record. Available properties: {list(properties.keys())}")
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting next action content: {e}")
            return ""

    def extract_property_text(self, property_data: Dict[str, Any]) -> str:
        """Extract text from various Notion property types"""
        try:
            prop_type = property_data.get('type')
            
            if prop_type == 'title':
                title_array = property_data.get('title', [])
                if title_array and len(title_array) > 0:
                    return title_array[0].get('plain_text', '').strip()
            
            elif prop_type == 'rich_text':
                rich_text_array = property_data.get('rich_text', [])
                if rich_text_array and len(rich_text_array) > 0:
                    return rich_text_array[0].get('plain_text', '').strip()
            
            elif prop_type == 'select':
                select_data = property_data.get('select')
                if select_data:
                    return select_data.get('name', '').strip()
            
            elif prop_type == 'number':
                number = property_data.get('number')
                return str(number) if number is not None else ''
            
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting property text: {e}")
            return ""

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

    async def run(self, target_date: Optional[str] = None, mode: str = "time") -> bool:
        """
        Main execution method
        
        Args:
            target_date: Date to process (YYYY-MM-DD format) - only for time records
            mode: Processing mode - "time", "next_actions", or "both"
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Starting Notion Auto-Classification Tool - Mode: {mode}")
            
            success = True
            
            # Process time records
            if mode in ["time", "both"]:
                logger.info("Processing time records...")
                time_success = await self.process_time_records(target_date)
                success = success and time_success
                
                if time_success:
                    logger.info("Time record classification completed successfully")
                else:
                    logger.error("Time record classification failed")
            
            # Process next actions
            if mode in ["next_actions", "both"]:
                logger.info("Processing next actions...")
                next_actions_success = await self.process_next_actions()
                success = success and next_actions_success
                
                if next_actions_success:
                    logger.info("Next action classification completed successfully")
                else:
                    logger.error("Next action classification failed")
            
            if success:
                logger.info("All classification tasks completed successfully")
            else:
                logger.error("Some classification tasks failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return False


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Notion Auto-Classification Tool")
    parser.add_argument(
        '--date',
        type=str,
        help='Target date to process (YYYY-MM-DD format). Only applies to time records. If not specified, processes all unclassified time records.'
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=['time', 'next_actions', 'both'],
        default='time',
        help='Processing mode: "time" for time records, "next_actions" for next actions, "both" for both databases. Defaults to "time".'
    )
    
    args = parser.parse_args()
    
    try:
        classifier = TimeRecordClassifier()
        success = await classifier.run(args.date, args.mode)
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"Failed to initialize classifier: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
