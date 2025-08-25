# AI Meeting Notes

An intelligent meeting assistant that automatically joins Zoom meetings, records audio/video, transcribes speech, and generates AI-powered meeting summaries.

## Project Structure

```
newAIMeetingNotes/
├── frontend/                 # Next.js web application
│   └── meeting-mash/        # Main frontend app with shadcn/ui
├── backend/                 # Backend API (to be implemented)
├── zoom-bot/               # Zoom Meeting SDK integration
│   └── py-zoom-meeting-sdk/ # Python Zoom bot
└── docker-compose.yml      # Docker orchestration
```

## Components

### Frontend (`frontend/meeting-mash/`)

- **Next.js 15** with App Router
- **shadcn/ui** components with blue theme
- **Auth.js** for authentication
- **TypeScript** for type safety

### Zoom Bot (`zoom-bot/`)

- **Python Zoom Meeting SDK** integration
- **Docker** containerized environment
- **Real-time audio/video recording**
- **Speech transcription** (Deepgram integration)

### Backend (Planned)

- **API endpoints** for meeting management
- **AI processing** for meeting summaries
- **Database** for storing meeting data

## Quick Start

### Frontend

```bash
cd frontend/meeting-mash
npm install
npm run dev
```

### Zoom Bot

```bash
cd zoom-bot/py-zoom-meeting-sdk
# Follow setup instructions in zoom-bot/README.md
```

## Features

- 🔐 **Authentication** with Auth.js
- 🎥 **Zoom Integration** with Meeting SDK
- 🎨 **Modern UI** with shadcn/ui components
- 📝 **AI Meeting Summaries** (planned)
- 🔄 **Real-time Transcription** (planned)

## Development

This project uses a microservices architecture with:

- **Frontend**: Next.js web app
- **Backend**: API server (to be implemented)
- **Zoom Bot**: Python bot for meeting integration
- **Docker**: Containerized development environment
