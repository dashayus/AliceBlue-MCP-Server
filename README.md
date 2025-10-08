# AliceBlue Trading MCP Server

Interact with your AliceBlue trading account directly through Claude AI. Manage your stocks, mutual funds, and trading orders seamlessly.

## Features

- 📊 Get portfolio holdings and positions
- 💰 Check account margins and funds
- 📈 View order book and trade history
- 🔐 Secure authentication flow

## Setup Instructions

### 1. Get AliceBlue Credentials

1. Visit [AliceBlue Developer Portal](https://v2api.aliceblueonline.com/)
2. Register your application to get:
   - **APP_CODE**
   - **API_SECRET**
3. Set redirect URL to: `https://smithery.ai/callback`

### 2. Authentication Flow

1. **Get Login URL**: Use `get_login_url` with your APP_CODE
2. **Login**: Open the URL and complete AliceBlue login
3. **Get Auth Code**: Copy `userId` and `authCode` from redirect URL
4. **Generate Checksum**: Use `generate_checksum` with userId, authCode, and API_SECRET
5. **Complete Login**: Use `complete_login` with generated checksum and userId
6. **Store Session**: Save the `user_session` for all future API calls

### 3. Available Tools

- `get_login_url` - Start authentication flow
- `generate_checksum` - Generate authentication checksum  
- `complete_login` - Complete login and get session
- `get_profile` - Get user profile
- `get_holdings` - Get stock holdings
- `get_positions` - Get trading positions
- `get_order_book` - Get order book
- `get_margins` - Get account margins

## Deployment

This MCP server is deployed on [Smithery](https://smithery.ai). To connect:

1. Go to Smithery MCP directory
2. Find "AliceBlue Trading MCP"
3. Click "Connect"
4. Enter your credentials when prompted

## Security

- Credentials are securely stored by Smithery
- All API calls use HTTPS
- No sensitive data is logged