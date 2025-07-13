#!/bin/bash

# AI News Digest - Environment Setup Script

echo "🚀 Setting up AI News Digest environment..."

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << 'EOF'
# AI News Digest - Environment Variables
# Get your API key from: https://fireworks.ai/account/api-keys
FIREWORKS_API_KEY=your_fireworks_api_key_here

# Optional: Flask configuration
# FLASK_ENV=development
# FLASK_PORT=8080
EOF
    echo "✅ .env file created!"
    echo "⚠️  Please edit .env and add your actual Fireworks API key"
else
    echo "✅ .env file already exists"
fi

# Create reports directory if it doesn't exist
if [ ! -d "reports" ]; then
    echo "📁 Creating reports directory..."
    mkdir -p reports
    echo "✅ Reports directory created!"
else
    echo "✅ Reports directory already exists"
fi

echo ""
echo "🔧 Next steps:"
echo "1. Edit .env file and add your Fireworks API key"
echo "2. Run: pip install -r requirements.txt"
echo "3. Run: python app.py"
echo "4. Open: http://localhost:8080"
echo ""
echo "📖 For more information, see README.md" 