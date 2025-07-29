#!/usr/bin/env python3
"""
Simple test script for DeepSeek API connection
"""

import asyncio
import os
from dotenv import load_dotenv
from openai_client import OpenAIClient

# Load environment variables
load_dotenv()

async def test_deepseek():
    """Test DeepSeek API connection"""
    
    # Get configuration from environment
    api_key = os.getenv('OPENAI_API_KEY')
    model = os.getenv('OPENAI_MODEL', 'deepseek-chat')
    base_url = os.getenv('OPENAI_BASE_URL', 'https://api.deepseek.com')
    
    if not api_key or api_key == 'your_deepseek_api_key_here':
        print("❌ Please set your DeepSeek API key in .env file")
        print("   OPENAI_API_KEY=sk-your-actual-deepseek-api-key")
        return False
    
    print(f"🔧 Testing DeepSeek API connection...")
    print(f"   Model: {model}")
    print(f"   Base URL: {base_url}")
    print(f"   API Key: {api_key[:10]}...{api_key[-4:]}")
    
    # Create client
    client = OpenAIClient(api_key=api_key, model=model, base_url=base_url)
    
    # Test connection
    print("\n🔍 Testing connection...")
    success = await client.test_connection()
    
    if success:
        print("✅ DeepSeek API connection successful!")
        
        # Test classification
        print("\n🧠 Testing classification...")
        test_prompt = """Please classify the following time tracking record into one of the exact categories listed below.

Time Record: 开会讨论项目进展

Available Categories:
- 工作
- 学习
- 娱乐
- 运动
- 其他

Instructions:
1. Analyze the content of the time record
2. Choose the most appropriate category from the list above
3. Respond with ONLY the exact category name, nothing else
4. If none of the categories fit perfectly, choose the closest one

Classification:"""
        
        result = await client.classify(test_prompt)
        if result:
            print(f"✅ Classification test successful: {result}")
        else:
            print("❌ Classification test failed")
            
        return True
    else:
        print("❌ DeepSeek API connection failed!")
        print("   Please check:")
        print("   1. Your API key is correct")
        print("   2. You have sufficient credits")
        print("   3. Your internet connection")
        return False

if __name__ == "__main__":
    asyncio.run(test_deepseek()) 