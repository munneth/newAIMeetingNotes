# Zoom Bot Integration

This directory contains the Zoom Meeting SDK integration for the AI Meeting Notes project.

## Structure

```
zoom-bot/
└── py-zoom-meeting-sdk/     # Zoom Meeting SDK Python bindings
    ├── sample_program/      # Example bot implementation
    ├── src/                 # SDK source code
    └── test_scripts/        # Testing utilities
```

## Setup

1. **Install dependencies:**

   ```bash
   cd zoom-bot/py-zoom-meeting-sdk
   docker compose run --rm develop
   pip install zoom-meeting-sdk
   ```

2. **Configure environment:**
   Create a `.env` file in `zoom-bot/py-zoom-meeting-sdk/` with:

   ```
   ZOOM_APP_CLIENT_ID=<your zoom app's client id>
   ZOOM_APP_CLIENT_SECRET=<your zoom app's client secret>
   MEETING_ID=<id of meeting on your developer account>
   MEETING_PWD=<password of meeting on your developer account, taken from URL>
   DEEPGRAM_API_KEY=<your deepgram API key (optional)>
   ```

3. **Run the sample bot:**
   ```bash
   python sample_program/sample.py
   ```

## Integration with AI Meeting Notes

The zoom-bot will be integrated with the main application to:

- Join meetings automatically
- Record audio and video
- Transcribe speech in real-time
- Generate meeting summaries using AI

## Requirements

- Docker
- Zoom App credentials (Client ID and Secret)
- Active Zoom meeting
- Deepgram API key (optional, for transcription)
