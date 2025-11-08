# SabCare Installation Guide

## Installation Options

SabCare can be installed in two ways:
1. **Basic Installation** (Recommended for testing) - Core features only, no AI
2. **Full Installation** - Includes AI features (requires more dependencies)

## Option 1: Basic Installation (Recommended)

This installation includes all core features (patient management, IVR scheduling, Twilio integration) but uses fallback text generation instead of AI.

### Steps:

```bash
cd /Users/aloksinha/SabCare

# Install backend dependencies (core only)
cd backend
pip install -r requirements.txt

# Install frontend dependencies
cd ..
npm install

# Initialize database
cd backend
python init_db.py
```

### What Works:
- ✅ Patient management
- ✅ IVR schedule generation
- ✅ Twilio integration
- ✅ Call queue management
- ✅ Analytics
- ✅ Personalized messages (using fallback text generation)

### What's Not Included:
- ❌ AI-powered message generation (Gemma model)
- ❌ Advanced RAG system (semantic search)

## Option 2: Full Installation (With AI)

This installation includes AI features but requires more dependencies and system resources.

### Steps:

```bash
cd /Users/aloksinha/SabCare

# Install backend dependencies (core)
cd backend
pip install -r requirements.txt

# Install AI dependencies
pip install -r requirements-ai.txt

# Install frontend dependencies
cd ..
npm install

# Initialize database
cd backend
python init_db.py
```

### System Requirements for AI:
- **RAM**: At least 8GB (16GB recommended)
- **Storage**: At least 10GB free space (for model downloads)
- **CPU**: Multi-core processor recommended
- **GPU**: Optional but recommended for faster inference

### What's Included:
- ✅ All basic features
- ✅ AI-powered message generation (Gemma model)
- ✅ Advanced RAG system with semantic search
- ✅ Intelligent patient message processing

## Troubleshooting Installation

### Issue: torch installation fails

**Solution 1**: Install PyTorch separately based on your system:

```bash
# For CPU only (recommended for most systems)
pip install torch --index-url https://download.pytorch.org/whl/cpu

# For CUDA (if you have NVIDIA GPU)
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

**Solution 2**: Use basic installation (Option 1) which doesn't require torch

### Issue: transformers installation fails

**Solution**: Update pip first:
```bash
pip install --upgrade pip
pip install transformers
```

### Issue: Out of memory when loading AI model

**Solution**: 
- Use CPU mode (set `use_cpu: true` in `config.yaml`)
- Close other applications
- Use basic installation instead
- Consider using a smaller model

### Issue: npm dependencies fail

**Solution**:
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

## Verifying Installation

### Test Backend:
```bash
cd backend
python -c "from main import app; print('✅ Backend imports successfully')"
```

### Test Twilio:
```bash
cd backend
python test_twilio.py
```

### Test Frontend:
```bash
npm run dev
# Should start without errors
```

## Recommended Setup for Development

For development and testing, we recommend **Option 1 (Basic Installation)** because:
- Faster installation
- Fewer dependencies
- Lower system requirements
- All core features work
- AI features can be added later if needed

The system will automatically use fallback text generation which still provides personalized messages based on patient data.

## Adding AI Features Later

If you start with basic installation and want to add AI features later:

```bash
cd backend
pip install -r requirements-ai.txt
# Restart the backend server
```

The system will automatically detect and use AI features if available.

## Next Steps

After installation:
1. Configure Twilio credentials (already done)
2. Start backend: `cd backend && python -c "import sys; sys.path.append('.'); from main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)"`
3. Start frontend: `npm run dev`
4. Access: http://localhost:5173

## Support

If you encounter issues:
1. Check the error messages carefully
2. Verify Python version (3.8+)
3. Verify Node.js version (16+)
4. Try basic installation first
5. Check system resources (RAM, disk space)

