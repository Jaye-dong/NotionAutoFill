import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_config():
    """Check current configuration"""
    print("🔧 Configuration Check")
    print("=" * 30)
    
    # Check Notion configuration
    notion_token = os.getenv('NOTION_TOKEN')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    print("📊 Notion Configuration:")
    print(f"   NOTION_TOKEN: {'✅ Set' if notion_token else '❌ Missing'}")
    print(f"   NOTION_DATABASE_ID: {'✅ Set' if database_id else '❌ Missing'}")
    print()
    
    # Check AI provider configurations
    print("🤖 AI Provider Configurations:")
    
    # OpenAI/DeepSeek
    openai_key = os.getenv('OPENAI_API_KEY')
    openai_model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    openai_base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    
    print(f"   OpenAI/DeepSeek:")
    print(f"      API Key: {'✅ Set' if openai_key else '❌ Missing'}")
    print(f"      Model: {openai_model}")
    print(f"      Base URL: {openai_base_url}")
    
    # Claude
    claude_key = os.getenv('CLAUDE_API_KEY')
    claude_model = os.getenv('CLAUDE_MODEL', 'claude-3-haiku-20240307')
    
    print(f"   Claude:")
    print(f"      API Key: {'✅ Set' if claude_key else '❌ Missing'}")
    print(f"      Model: {claude_model}")
    
    # Ollama
    ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    ollama_model = os.getenv('OLLAMA_MODEL', 'llama2')
    
    print(f"   Ollama:")
    print(f"      URL: {ollama_url}")
    print(f"      Model: {ollama_model}")
    print()
    
    # Determine available providers
    available_providers = []
    if openai_key:
        if 'deepseek' in openai_base_url.lower():
            available_providers.append('DeepSeek')
        else:
            available_providers.append('OpenAI')
    if claude_key:
        available_providers.append('Claude')
    # Ollama doesn't require API key, so it's always potentially available
    available_providers.append('Ollama')
    
    print("🚀 Available Providers:")
    for provider in available_providers:
        print(f"   ✅ {provider}")
    
    if not available_providers:
        print("   ❌ No providers configured")
    
    return available_providers

if __name__ == "__main__":
    check_config() 