# ChatGPT API Debugging Guide

## Problem Symptoms
- All items are labeled as "White" and "Casual"
- All items are categorized as "TOPS" (should be shoes, dresses, pants, etc.)
- Complete misclassification

## Possible Causes

### 1. API Key Not Configured (Most Likely)
If `VITE_OPENAI_API_KEY` is not set, ChatGPT API will not be called, and the system will use fallback values:
- category: 'shirt' → displayed as 'TOPS'
- color: 'white' → displayed as 'White'
- style: 'casual' → displayed as 'Casual'

### 2. Invalid API Key
If the API key is invalid or expired, the API call will fail and fallback values will be used.

### 3. API Call Failure
Network errors, API limits, or other errors causing call failure.

## Debugging Steps

### Step 1: Check API Key Configuration

1. Check if `.env` file exists (in `website/` directory)
2. Check if `.env` file contains `VITE_OPENAI_API_KEY`
3. Ensure API key format is correct (starts with `sk-`)

```bash
# In website/ directory
cat .env | grep VITE_OPENAI_API_KEY
```

### Step 2: Check Browser Console

1. Open browser developer tools (F12)
2. Switch to Console tab
3. Upload an item
4. Check log output:

**If you see these logs, the API was called:**
```
🔄 Calling ChatGPT API to analyze item...
🔍 Starting ChatGPT analysis...
📥 ChatGPT raw response: {...}
✅ Parsed analysis: {...}
✅ Item analysis received: {...}
```

**If you see these logs, the API was not called or failed:**
```
❌ OpenAI API key is not configured...
❌ Analysis failed! Error: ...
⚠️ Using fallback values (shirt, white, casual) - these are WRONG!
```

### Step 3: Check Network Requests

1. Open browser developer tools (F12)
2. Switch to Network tab
3. Upload an item
4. Look for requests to `api.openai.com`
5. Check request status:
   - 200 OK: API call successful
   - 401 Unauthorized: Invalid API key
   - 429 Too Many Requests: API rate limit
   - Other errors: Check error details

## Solutions

### Solution 1: Configure API Key

1. Create or edit `.env` file in `website/` directory:
```bash
VITE_OPENAI_API_KEY=sk-your-actual-api-key-here
```

2. Restart development server:
```bash
npm run dev
```

3. Clear browser cache and refresh page

### Solution 2: Verify API Key

1. Visit OpenAI API settings page: https://platform.openai.com/api-keys
2. Confirm API key is valid and not expired
3. Check API usage limits and balance

### Solution 3: Check API Limits

1. Confirm account has sufficient balance
2. Check if rate limit is reached
3. View API usage in OpenAI account

## Test API Key

You can run this command in the browser console to test the API key:

```javascript
// Run in browser console
const apiKey = import.meta.env.VITE_OPENAI_API_KEY;
console.log('API Key configured:', apiKey ? 'Yes (length: ' + apiKey.length + ')' : 'No');
```

## Common Errors

### Error 1: "OpenAI API key is not configured"
- **Cause**: `.env` file does not contain `VITE_OPENAI_API_KEY`
- **Solution**: Add API key to `.env` file and restart server

### Error 2: "401 Unauthorized"
- **Cause**: Invalid or expired API key
- **Solution**: Generate new API key and update `.env` file

### Error 3: "429 Too Many Requests"
- **Cause**: API rate limit reached
- **Solution**: Wait a moment and try again, or upgrade OpenAI account

### Error 4: "Network error"
- **Cause**: Network connection issue or CORS error
- **Solution**: Check network connection, confirm access to `api.openai.com`

## Verify Fix

After fixing, upload a new item and check:

1. **Browser Console** should show:
   - ✅ ChatGPT API call successful logs
   - ✅ Correct category, color, style values

2. **Wardrobe Page** should show:
   - ✅ Correct categories (shoes, dresses, pants, etc., not all TOPS)
   - ✅ Correct colors (green, brown, blue, etc., not all White)
   - ✅ Correct styles (not all Casual)

## If Problem Persists

1. Check complete error messages in browser console
2. Check API requests and responses in Network tab
3. Try manually calling `analyzeClothingItem` function in browser console
4. Check if ChatGPT API response format is correct
