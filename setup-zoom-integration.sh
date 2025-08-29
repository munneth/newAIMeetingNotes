#!/bin/bash

echo "🚀 Setting up Real Zoom Integration for AI Meeting Notes"
echo "========================================================"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Zoom App Credentials
# Get these from https://marketplace.zoom.us/develop/create
ZOOM_APP_CLIENT_ID=your_zoom_client_id_here
ZOOM_APP_CLIENT_SECRET=your_zoom_client_secret_here

# Optional: JWT Token (if using JWT authentication)
ZOOM_JWT_TOKEN=your_jwt_token_here

# Deepgram API Key (for transcription)
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# Redis Configuration
REDIS_URL=redis://localhost:6379

# API Configuration
API_BASE_URL=http://localhost:3000
EOF
    echo "✅ .env file created!"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🔧 Next Steps:"
echo "=============="
echo ""
echo "1. 📋 Create Zoom App:"
echo "   - Go to: https://marketplace.zoom.us/develop/create"
echo "   - Sign in with your Zoom account"
echo "   - Click 'Develop' → 'Build App'"
echo "   - Choose 'Meeting SDK' app type"
echo "   - Fill in app details"
echo ""
echo "2. 🔑 Get Your Credentials:"
echo "   - Copy your 'Client ID' and 'Client Secret'"
echo "   - Update the .env file with your actual values"
echo ""
echo "3. ⚙️  Configure App Settings:"
echo "   - In your Zoom App settings, enable:"
echo "     * Meeting SDK"
echo "     * Join Meeting"
echo "     * Record Meeting"
echo ""
echo "4. 🚀 Start the Application:"
echo "   - Run: docker compose up -d --build"
echo ""
echo "5. 🧪 Test Real Integration:"
echo "   - Add a meeting through the frontend"
echo "   - The bot will now actually join your Zoom meetings!"
echo ""
echo "📖 For detailed setup instructions, see:"
echo "   https://marketplace.zoom.us/docs/guides/build/meeting-sdk-app"
echo ""
echo "⚠️  Important Notes:"
echo "   - Your Zoom App needs to be approved for production use"
echo "   - For testing, you can use the development environment"
echo "   - Make sure your Zoom account has the necessary permissions"
echo ""

