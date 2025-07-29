# Notion Time Record Auto-Classification Tool

A Python tool that automatically classifies time tracking records in Notion using AI models like OpenAI GPT and DeepSeek.

## Features

- 🤖 **AI-Powered Classification**: Uses OpenAI GPT, DeepSeek, or other OpenAI-compatible models
- 📊 **Notion Integration**: Seamlessly works with your existing Notion time tracking database
- 🎯 **Smart Matching**: Automatically matches AI classifications with your existing Notion categories
- 📅 **Flexible Date Processing**: Process records for today, specific dates, or date ranges
- 🔧 **Easy Configuration**: Simple environment variable configuration
- 📝 **Comprehensive Logging**: Detailed logging for monitoring and debugging

## Prerequisites

- Python 3.8 or higher
- Notion account with API access
- AI API key (OpenAI, DeepSeek, or other OpenAI-compatible service)
- A Notion database with time tracking records

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd notionAutoFill
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```

4. Edit `.env` file with your credentials:

### For OpenAI:
```env
# Notion Configuration
NOTION_TOKEN=your_notion_integration_token_here
NOTION_DATABASE_ID=your_notion_database_id_here

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1
```

### For DeepSeek (推荐，性价比高):
```env
# Notion Configuration
NOTION_TOKEN=your_notion_integration_token_here
NOTION_DATABASE_ID=your_notion_database_id_here

# DeepSeek Configuration
OPENAI_API_KEY=your_deepseek_api_key_here
OPENAI_MODEL=deepseek-chat
OPENAI_BASE_URL=https://api.deepseek.com
```

### For DeepSeek Reasoning Model (推理能力更强):
```env
# Notion Configuration
NOTION_TOKEN=your_notion_integration_token_here
NOTION_DATABASE_ID=your_notion_database_id_here

# DeepSeek Reasoning Configuration
OPENAI_API_KEY=your_deepseek_api_key_here
OPENAI_MODEL=deepseek-reasoner
OPENAI_BASE_URL=https://api.deepseek.com
```

## Notion Database Setup

Your Notion database should have these properties:
- `时间段` (Date): The date of the time record
- `记录` (Rich Text): Description of the activity
- `分类` (Select): Category/classification field with predefined options

## Usage

### Basic Usage

Process today's records:
```bash
python main.py
```

Process specific date:
```bash
python main.py --date 2024-01-15
```

### Command Line Options

- `--date YYYY-MM-DD`: Process records for a specific date
- `--help`: Show help message

### Examples

```bash
# Process today's records
python main.py

# Process records for January 15, 2024
python main.py --date 2024-01-15

# Process records for yesterday
python main.py --date 2024-01-14
```

## How It Works

1. **Fetch Records**: Retrieves time records from your Notion database for the specified date
2. **Get Categories**: Fetches available classification options from your database schema
3. **AI Classification**: Uses your configured AI model to classify each unclassified record
4. **Smart Matching**: Matches AI responses with your existing categories using exact, case-insensitive, and partial matching
5. **Update Database**: Updates the classification field in Notion for successfully classified records

## AI Provider Configuration

### OpenAI
- **Best for**: High accuracy, reliable service
- **Cost**: Moderate to high
- **Models**: `gpt-4o-mini`, `gpt-4o`, `gpt-3.5-turbo`
- **Setup**: Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)

### DeepSeek (推荐)
- **Best for**: Cost-effective, high performance
- **Cost**: Very low (much cheaper than OpenAI)
- **Models**: 
  - `deepseek-chat`: General purpose chat model
  - `deepseek-reasoner`: Enhanced reasoning capabilities
- **Setup**: Get API key from [DeepSeek Platform](https://platform.deepseek.com/api_keys)

### Other OpenAI-Compatible APIs
The tool works with any OpenAI-compatible API by setting the appropriate `OPENAI_BASE_URL`:
- Azure OpenAI
- Local models via Ollama (with OpenAI compatibility)
- OpenRouter
- Other providers

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `NOTION_TOKEN` | Your Notion integration token | Yes | - |
| `NOTION_DATABASE_ID` | Your Notion database ID | Yes | - |
| `OPENAI_API_KEY` | Your AI API key | Yes | - |
| `OPENAI_MODEL` | AI model to use | No | `gpt-4o-mini` |
| `OPENAI_BASE_URL` | API endpoint URL | No | `https://api.openai.com/v1` |

### Getting Your API Keys

#### DeepSeek API Key (推荐)
1. Visit [DeepSeek Platform](https://platform.deepseek.com/api_keys)
2. Create an account and get your API key
3. DeepSeek offers very competitive pricing

#### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create an account and get your API key
3. Note: OpenAI requires payment setup

#### Notion Credentials
1. **Notion Token**: 
   - Go to [Notion Developers](https://www.notion.so/my-integrations)
   - Create a new integration
   - Copy the "Internal Integration Token"

2. **Database ID**:
   - Open your Notion database in browser
   - Copy the ID from the URL: `https://notion.so/your-workspace/DATABASE_ID?v=...`

3. **Grant Access**:
   - In your Notion database, click "..." → "Add connections"
   - Select your integration

## Logging

The tool creates detailed logs in:
- `notion_auto_fill.log`: File-based logging
- Console output: Real-time progress

Log levels include:
- INFO: General operation progress
- WARNING: Non-critical issues
- ERROR: Critical errors that prevent operation

## Troubleshooting

### Common Issues

1. **"No classification options found"**
   - Ensure your database has a "分类" select field with options
   - Check that your integration has access to the database

2. **"AI connection test failed"**
   - Verify your API key is correct
   - Check your internet connection
   - For DeepSeek: Ensure you have sufficient credits
   - For OpenAI: Ensure you have sufficient credits

3. **"Failed to fetch records"**
   - Verify your Notion token and database ID
   - Ensure the database has a "时间段" date field
   - Check that your integration has read access

### Debug Mode

For detailed debugging, check the log file `notion_auto_fill.log` which contains comprehensive information about:
- API requests and responses
- Classification attempts and results
- Database operations
- Error details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you encounter any issues or have questions:
1. Check the troubleshooting section above
2. Review the log files for detailed error information
3. Create an issue in the repository with:
   - Error messages
   - Steps to reproduce
   - Your configuration (without sensitive data) 