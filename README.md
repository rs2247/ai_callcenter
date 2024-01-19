# Environment

I suggest creating a python venv to avoid potential version conflicts

    python -m venv ai_callcenter
    source ai_callcenter/bin/activate


# Installation

    pip install 'vocode[io]'
    pip install python-dotenv
    pip install matplotlib
    pip install elevenlabs==0.2.24 # Latest version gives version conflict in pydantic package

# Config keys

Create a .env file with the API keys from each provider

    OPENAI_API_KEY=
    AZURE_SPEECH_KEY=
    AZURE_SPEECH_REGION=

# Run

    python main.py