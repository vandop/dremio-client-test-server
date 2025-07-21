# How to Refresh the Devcontainer

This guide explains different ways to refresh your devcontainer when you need to apply changes or resolve issues.

## Quick Reference

| Scenario | Method | Time | Data Loss |
|----------|--------|------|-----------|
| Minor config changes | Reload Window | ~30s | None |
| Dockerfile changes | Rebuild Container | ~2-5min | None |
| Major issues/cleanup | Full Rebuild | ~3-7min | None |
| Complete reset | Delete & Rebuild | ~5-10min | Extensions/settings |

## Method 1: Reload Window (Fastest)

**When to use**: Minor changes to devcontainer.json settings, extensions, or environment variables.

### Steps:
1. **Command Palette**: Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (macOS)
2. **Search**: Type "Developer: Reload Window"
3. **Execute**: Press Enter

### What it does:
- Reloads VS Code window
- Re-reads devcontainer.json configuration
- Applies new settings and extensions
- **Does NOT** rebuild the container

### Use cases:
- Added new VS Code extensions
- Changed VS Code settings
- Modified environment variables
- Updated port forwarding configuration

## Method 2: Rebuild Container (Recommended)

**When to use**: Changes to Dockerfile, requirements.txt, or when you want to ensure everything is fresh.

### Steps:
1. **Command Palette**: Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (macOS)
2. **Search**: Type "Dev Containers: Rebuild Container"
3. **Execute**: Press Enter
4. **Wait**: Container will rebuild and restart (2-5 minutes)

### What it does:
- Rebuilds the Docker image from Dockerfile
- Installs all dependencies fresh
- Runs postCreateCommand (our setup script)
- Preserves your workspace files
- Maintains VS Code extensions and settings

### Use cases:
- Modified Dockerfile
- Updated requirements.txt
- Added system packages
- Want to ensure clean environment
- Troubleshooting dependency issues

## Method 3: Rebuild Without Cache (Deep Clean)

**When to use**: Major issues, corrupted dependencies, or when normal rebuild doesn't work.

### Steps:
1. **Command Palette**: Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (macOS)
2. **Search**: Type "Dev Containers: Rebuild Container Without Cache"
3. **Execute**: Press Enter
4. **Wait**: Complete rebuild from scratch (3-7 minutes)

### What it does:
- Rebuilds Docker image without using cached layers
- Downloads all dependencies fresh
- Ensures no corrupted cached data
- Runs complete setup from beginning

### Use cases:
- Corrupted Docker cache
- Persistent dependency issues
- Major system changes
- When rebuild with cache fails

## Method 4: Complete Reset (Nuclear Option)

**When to use**: Severe issues, want to start completely fresh, or testing clean setup.

### Steps:
1. **Close VS Code** completely
2. **Delete container and image**:
   ```bash
   # List devcontainers
   docker ps -a | grep dremio-reporting-server
   
   # Stop and remove container
   docker stop <container-name>
   docker rm <container-name>
   
   # Remove image
   docker images | grep dremio-reporting-server
   docker rmi <image-name>
   ```
3. **Reopen in VS Code**
4. **Select "Reopen in Container"**

### What it does:
- Completely removes container and image
- Forces fresh build from scratch
- Resets all container-specific settings
- **May lose**: VS Code extensions installed in container

## Troubleshooting Common Issues

### Issue: "Container failed to start"
**Solution**: Try Method 3 (Rebuild Without Cache)

### Issue: "JDBC driver not found"
**Solution**: 
1. Try Method 2 (Rebuild Container)
2. If that fails, manually run: `bash .devcontainer/setup-devcontainer.sh`

### Issue: "Java/Python dependencies missing"
**Solution**: Method 3 (Rebuild Without Cache) - ensures fresh dependency installation

### Issue: "Port already in use"
**Solution**: 
1. Method 1 (Reload Window) first
2. If that fails, Method 2 (Rebuild Container)

### Issue: "VS Code extensions not working"
**Solution**: Method 1 (Reload Window) - reloads extension configuration

## Monitoring Rebuild Progress

### During rebuild, you can monitor:
1. **VS Code Output Panel**: Shows build progress
2. **Docker Desktop**: Shows container status
3. **Terminal**: If rebuild fails, check terminal output

### Expected rebuild times:
- **First build**: 5-10 minutes (downloads base images)
- **Subsequent builds**: 2-5 minutes (uses cached layers)
- **Without cache**: 3-7 minutes (rebuilds everything)

## Best Practices

### 1. Save your work first
Always save and commit your code before rebuilding

### 2. Use appropriate method
- Minor changes → Reload Window
- Dockerfile changes → Rebuild Container
- Major issues → Rebuild Without Cache

### 3. Check logs
If rebuild fails, check the output panel for specific error messages

### 4. Verify after rebuild
After rebuild completes:
- Check Java version: `java -version`
- Verify JDBC driver: `ls -la jdbc-drivers/`
- Test setup: `python test_java_setup.py`

## Automated Setup Verification

After any rebuild, the devcontainer automatically:
1. ✅ Verifies Java 17 installation
2. ✅ Downloads JDBC driver if missing
3. ✅ Tests Python dependencies
4. ✅ Creates .env template if needed
5. ✅ Provides setup status summary

## Quick Commands Reference

```bash
# Check container status
docker ps | grep dremio-reporting-server

# View container logs
docker logs <container-name>

# Manual setup verification
bash .devcontainer/setup-devcontainer.sh

# Test Java setup
python test_java_setup.py

# Check JDBC driver
ls -la jdbc-drivers/dremio-jdbc-driver-LATEST.jar
```

## When to Contact Support

If you continue having issues after trying Method 4 (Complete Reset):
1. Check Docker Desktop is running
2. Verify sufficient disk space (>5GB free)
3. Check network connectivity
4. Review error messages in VS Code output panel

The devcontainer is designed to be self-healing and should work reliably with these refresh methods.
