#!/usr/bin/env python3
"""
OpenAI Client for Time Record Classification
Uses OpenAI API for more accurate AI classification
"""

import logging
import aiohttp
import json
from typing import Optional
import asyncio

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client for OpenAI API-based classification"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", base_url: str = None):
        """
        Initialize OpenAI client
        
        Args:
            api_key: OpenAI API key
            model: Model to use (gpt-4o-mini, gpt-4, gpt-3.5-turbo, etc.)
            base_url: Optional base URL for compatible APIs
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1"
        
        logger.info(f"OpenAI client initialized - model: {model}")

    async def classify(self, prompt: str) -> Optional[str]:
        """
        Classify time record using OpenAI API
        
        Args:
            prompt: The classification prompt
            
        Returns:
            Classification result or None if failed
        """
        try:
            logger.info("Sending classification request to OpenAI")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that classifies time tracking records. You must respond with exactly one of the provided category names, nothing else."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 50,
                "temperature": 0.1,
                "top_p": 1,
                "frequency_penalty": 0,
                "presence_penalty": 0
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("choices") and len(result["choices"]) > 0:
                            classification = result["choices"][0]["message"]["content"].strip()
                            logger.info(f"OpenAI classification result: {classification}")
                            return classification
                        else:
                            logger.warning("OpenAI returned empty response")
                            return None
                    else:
                        error_text = await response.text()
                        logger.error(f"OpenAI API error {response.status}: {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"OpenAI classification failed: {str(e)}")
            return None

    async def test_connection(self) -> bool:
        """Test connection to OpenAI API"""
        try:
            logger.info("Testing OpenAI connection...")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello, this is a connection test. Please respond with 'OK'."
                    }
                ],
                "max_tokens": 10,
                "temperature": 0
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("choices") and len(result["choices"]) > 0:
                            response_text = result["choices"][0]["message"]["content"].strip()
                            logger.info(f"OpenAI connection test successful: {response_text}")
                            return True
                        else:
                            logger.error("OpenAI connection test failed: empty response")
                            return False
                    else:
                        error_text = await response.text()
                        logger.error(f"OpenAI connection test failed {response.status}: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {str(e)}")
            return False 