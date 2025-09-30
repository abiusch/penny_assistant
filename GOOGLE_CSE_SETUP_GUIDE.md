# 🔧 Google Custom Search Engine Setup Guide

## Overview

This guide explains how to set up Google Custom Search Engine (CSE) API to replace the unreliable DuckDuckGo search in Penny's research system.

## Prerequisites

1. Google Cloud Account (free tier available)
2. Access to Google Cloud Console
3. Basic understanding of API keys and environment variables

## Step-by-Step Setup

### 1. Google Cloud Console Setup

#### 1.1 Create/Select Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Note your project ID

#### 1.2 Enable Custom Search API
1. Go to [APIs & Services > Library](https://console.cloud.google.com/apis/library)
2. Search for "Custom Search API"
3. Click "Custom Search JSON API"
4. Click "ENABLE"

#### 1.3 Create API Key
1. Go to [APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials)
2. Click "CREATE CREDENTIALS" > "API key"
3. Copy the generated API key
4. **Optional**: Click "RESTRICT KEY" to limit to Custom Search API only

### 2. Custom Search Engine Setup

#### 2.1 Create Search Engine
1. Go to [Google Custom Search Engine](https://cse.google.com/cse/all)
2. Click "Add" to create new search engine
3. Configure:
   - **Sites to search**: Enter `*` to search the entire web
   - **Language**: English (or preferred language)
   - **Name**: "Penny Assistant Search" (or any name)
4. Click "CREATE"

#### 2.2 Get Engine ID
1. In your CSE control panel, click "Setup"
2. In "Basics" section, find "Search engine ID"
3. Copy the Engine ID (format: `xxxxxxxxx:xxxxxxxxx`)

#### 2.3 Configure Search Settings
1. In CSE control panel, go to "Setup" > "Basics"
2. Ensure "Search the entire web" is enabled
3. Set "SafeSearch" to "Moderate" (recommended)
4. Turn OFF "Image search" (text results only)
5. Click "UPDATE"

### 3. Environment Configuration

#### 3.1 Update .env File
Add these lines to your `.env` file:

```bash
# Google Custom Search API Configuration
GOOGLE_CSE_API_KEY=your_actual_api_key_here
GOOGLE_CSE_ENGINE_ID=your_actual_engine_id_here

# Optional: Set daily search limit (default: 90)
GOOGLE_CSE_DAILY_LIMIT=90
```

#### 3.2 Example Configuration
```bash
# Real example (replace with your actual values)
GOOGLE_CSE_API_KEY=AIzaSyB1234567890abcdefghijklmnopqrstuvwx
GOOGLE_CSE_ENGINE_ID=a1b2c3d4e5f6g7h8i:j9k0l1m2n3o4p
GOOGLE_CSE_DAILY_LIMIT=90
```

### 4. Testing Your Setup

#### 4.1 Basic Test
```bash
# Test Google CSE directly
python3 google_cse_search.py

# Test complete integration
python3 test_google_cse_integration.py
```

#### 4.2 Research Pipeline Test
```bash
# Test with Penny's research system
python3 -c "
from research_first_pipeline import ResearchFirstPipeline
pipeline = ResearchFirstPipeline()
response = pipeline.think('What are recent AI developments?')
print(response)
"
```

## Cost Information

### Free Tier Limits
- **100 search queries per day** - FREE
- **10,000 queries per month** - FREE
- Perfect for personal/development use

### Paid Tier (if needed)
- **$5 per 1,000 additional queries**
- Only charged if you exceed free tier
- Can set billing alerts to monitor usage

### Cost Estimation
```
Personal use: $0/month (under free tier)
Light production: $5-15/month
Heavy production: $20-50/month
```

## Usage Monitoring

The implementation includes automatic usage tracking:

```python
# Check usage stats
from google_cse_search import GoogleCSESearch

async with GoogleCSESearch() as search:
    stats = search.get_usage_stats()
    print(f"Today: {stats['today_searches']}/{stats['daily_limit']}")
    print(f"Status: {stats['status']}")
```

## Troubleshooting

### Common Issues

#### API Key Problems
```
Error: "GOOGLE_CSE_API_KEY environment variable not set"
```
**Fix**: Check `.env` file has correct API key without quotes

#### Engine ID Problems
```
Error: "Invalid cx parameter"
```
**Fix**: Verify Engine ID format is correct (contains colon)

#### Rate Limit Issues
```
Error: "Daily quota exceeded"
```
**Fix**: Wait until next day or upgrade to paid tier

#### Permission Errors
```
Error: "API access forbidden"
```
**Fix**: Ensure Custom Search API is enabled in Google Cloud Console

### Testing Fallback
The system includes DuckDuckGo fallback when Google CSE fails:

```python
# Force fallback test
search_params = {"query": "test", "engine": "duckduckgo"}
```

## Security Best Practices

### API Key Security
1. **Never commit API keys** to version control
2. **Use .env files** for local development
3. **Use environment variables** in production
4. **Restrict API key** to specific APIs only

### Rate Limiting
1. Monitor daily usage to avoid surprise charges
2. Set up billing alerts in Google Cloud Console
3. Implement usage caps in production

## Expected Performance

### With Google CSE
- **Response time**: 1-3 seconds
- **Result quality**: High (Google's algorithm)
- **Reliability**: 99.9% uptime
- **Coverage**: Entire web searchable

### Fallback (DuckDuckGo)
- **Response time**: 2-5 seconds
- **Result quality**: Moderate
- **Reliability**: Variable (current issues)
- **Coverage**: Limited instant answers

## Verification Checklist

Before going live, verify:

- [ ] Google Cloud project created
- [ ] Custom Search API enabled
- [ ] API key generated and restricted
- [ ] Custom Search Engine created and configured
- [ ] Environment variables set correctly
- [ ] Basic search test passes
- [ ] Integration test passes
- [ ] Boston Dynamics query works without fabrication
- [ ] Usage tracking functional
- [ ] Fallback mechanism works

## Production Deployment

For production use:

1. **Set up monitoring** for API usage and costs
2. **Configure alerts** for approaching rate limits
3. **Test failover** scenarios
4. **Document** API key rotation procedures
5. **Set billing limits** in Google Cloud Console

## Support Resources

- [Google CSE Documentation](https://developers.google.com/custom-search/v1/overview)
- [Google Cloud Console](https://console.cloud.google.com/)
- [Custom Search Engine Panel](https://cse.google.com/cse/all)
- [API Pricing](https://developers.google.com/custom-search/v1/overview#pricing)

---

**Result**: Reliable, high-quality search results for Penny's research capabilities with automatic fallback and cost monitoring.