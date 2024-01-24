# Environment

I suggest creating a python venv to avoid potential version conflicts

    python -m venv ai_callcenter
    source ai_callcenter/bin/activate


# Installation

    pip install 'vocode[io]'
    pip install python-dotenv
    pip install matplotlib
    pip install elevenlabs==0.2.24 # Latest version gives version conflict in pydantic package
    pip install poetry

# Config keys

Create a .env file with the API keys from each provider

    OPENAI_API_KEY=
    AZURE_SPEECH_KEY=
    AZURE_SPEECH_REGION=
    DEEPGRAM_API_KEY=
    TWILIO_ACCOUNT_SID=
    TWILIO_AUTH_TOKEN=
    BASE_URL= //if running phone calls

# Run locally
 
    python main.py

# Run with Twilio

Install nrgok package, create an account and add the authentication token following [Ngrok Getting Started](https://ngrok.com/docs/getting-started/)

Set up hosting so that Twilio can hit your server:
 
    ngrok http 3000

Update in the .env file the URL that is tunneling localhost 3000 without https://. Get this URL from the output of ngrok, ex: 
 
    BASE_URL=asdf1234.ngrok.app 

Install Docker following website's tutorial
  
On another shell, go to the telephony directory and start the server: 
 
    cd telephony
    docker build -t vocode-telephony-app .
    docker-compose up
  
On another shell, run the pizzabot caller
 
    poetry install  //install dependencies and start a new env, since this script needs pydantic v2.x and vocode still doesn't support it
                    //poetry ref https://python-poetry.org/docs/basic-usage/
    poetry run python outbound_pizzacall.py
