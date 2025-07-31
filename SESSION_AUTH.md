# Session-Based Authentication

The Dremio Reporting Server now supports **session-based authentication** that works without requiring a `.env` file and supports multiple concurrent users.

## 🔒 How It Works

### Session-Based Credentials
- **No .env file required**: Credentials are stored in browser sessions only
- **Multiple users**: Each browser session can have different Dremio credentials
- **Secure**: Credentials are never saved to disk or shared between users
- **Temporary**: Credentials are cleared when the browser session ends

### Backward Compatibility
- **Still supports .env files**: If a `.env` file exists, it will be used as fallback
- **Seamless transition**: Existing setups continue to work unchanged
- **Priority**: Session credentials take priority over .env file credentials

## 🚀 Usage

### 1. Start the Server
```bash
./run.sh
# or
python app.py
```

### 2. Configure Authentication
1. Open your browser to `http://localhost:5001`
2. You'll be redirected to the authentication page
3. Choose your Dremio type (Cloud or Software)
4. Enter your credentials:
   - **Dremio Cloud**: URL + Personal Access Token
   - **Dremio Software**: URL + Username/Password
5. Click "Connect to Dremio"

### 3. Use the Application
- Your credentials are stored in your browser session
- All features work normally (queries, reports, etc.)
- Other users can access the same server with different credentials

## 👥 Multi-User Support

### Concurrent Users
- **Multiple browser sessions**: Each can have different Dremio credentials
- **Isolated credentials**: User A's credentials don't affect User B
- **Independent connections**: Each user connects to their own Dremio instance

### Example Scenarios
1. **Team Development**: Multiple developers using different Dremio projects
2. **Multi-tenant**: Different customers accessing their own Dremio instances
3. **Testing**: Switch between different environments without restarting

## 🔧 Technical Details

### Session Storage
```python
# Credentials stored in Flask session
session['dremio_url'] = 'https://api.dremio.cloud'
session['auth_method'] = 'pat'
session['pat'] = 'your-token'
session['project_id'] = 'your-project-id'
```

### Client Creation
```python
# Each request creates a client with session credentials
def create_session_client():
    config = get_session_config()
    # Temporarily set environment variables
    # Create client with session config
    # Restore original environment
    return client
```

### Security Features
- **Session isolation**: Each browser session is completely isolated
- **No disk storage**: Credentials never written to files
- **Automatic cleanup**: Credentials cleared when session ends
- **Environment protection**: Original .env values are preserved

## 🧪 Testing

### Test Session Authentication
```bash
python test_session_auth.py
```

### Manual Testing
1. **Open two different browsers** (Chrome and Firefox)
2. **Configure different credentials** in each browser
3. **Verify isolation**: Each browser connects to different Dremio instances
4. **Test persistence**: Refresh pages, credentials should persist
5. **Test cleanup**: Clear browser data, should redirect to auth page

## 🔄 Migration from .env File

### Option 1: Keep .env File (Recommended)
- Keep your existing `.env` file as fallback
- Session credentials will take priority when configured
- Provides backup if session expires

### Option 2: Remove .env File
- Delete or rename your `.env` file
- All authentication will be session-based
- More secure for multi-user environments

### Option 3: Hybrid Approach
- Use `.env` for development/single-user
- Use session auth for production/multi-user
- Application automatically adapts

## 🛡️ Security Considerations

### Advantages
- ✅ **No credentials on disk**: More secure than .env files
- ✅ **User isolation**: Multiple users can't see each other's credentials
- ✅ **Session expiry**: Credentials automatically cleared
- ✅ **No shared state**: Each user has independent configuration

### Best Practices
- Use HTTPS in production to protect session cookies
- Configure appropriate session timeouts
- Use strong SECRET_KEY for session encryption
- Consider using secure session storage for production

## 🔍 Troubleshooting

### Common Issues

**"Authentication not configured" error**
- Clear your browser session: Go to `/clear-auth`
- Reconfigure your credentials through the auth page

**Multiple users interfering**
- Each browser session is isolated
- Use different browsers or incognito mode for testing
- Check that you're not sharing session cookies

**Credentials not persisting**
- Check that cookies are enabled in your browser
- Verify SECRET_KEY is set in your environment
- Session may have expired - reconfigure authentication

### Debug Information
```bash
# Check current session status
curl -b cookies.txt http://localhost:5001/api/test-connection

# Clear authentication
curl http://localhost:5001/clear-auth
```

## 📊 Comparison

| Feature | .env File | Session-Based | Hybrid |
|---------|-----------|---------------|--------|
| Multi-user | ❌ | ✅ | ✅ |
| Disk storage | ❌ | ✅ | ⚠️ |
| Easy setup | ✅ | ✅ | ✅ |
| Persistence | ✅ | ⚠️ | ✅ |
| Security | ⚠️ | ✅ | ✅ |

**Legend**: ✅ Good, ⚠️ Moderate, ❌ Limited
