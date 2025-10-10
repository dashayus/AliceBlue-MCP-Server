# AliceBlue Trading MCP Server

[![smithery badge](https://smithery.ai/badge/@dashayus/aliceblue-mcp-server)](https://smithery.ai/server/@dashayus/aliceblue-mcp-server)

Interact with your AliceBlue trading account directly through Claude AI. Manage your stocks, mutual funds, and trading orders seamlessly.

## 🚀 Features

- 📊 Get portfolio holdings and positions
- 💰 Check account margins and funds  
- 📈 View order book and trade history
- 🔐 Secure authentication flow
- 🎯 Real-time market data

## 📋 Prerequisites

1. AliceBlue trading account
2. APP_CODE and API_SECRET from [AliceBlue Developer Portal](https://v2api.aliceblueonline.com/)

## 🔧 Installation

### Method 1: Smithery Cloud
1. Visit [Smithery](https://smithery.ai)
2. Search for "AliceBlue Trading MCP"
3. Click "Connect"
4. Enter your credentials:
   - APP_CODE
   - API_SECRET
5. Follow the authentication flow

### Method 2: Local Setup
```bash
git clone https://github.com/yourusername/aliceblue-mcp
cd aliceblue-mcp
pip install -r requirements.txt
python server.py
```

### Installing via Smithery

To install AliceBlue automatically via [Smithery](https://smithery.ai/server/@dashayus/aliceblue-mcp-server):

```bash
npx -y @smithery/cli install @dashayus/aliceblue-mcp-server
```
