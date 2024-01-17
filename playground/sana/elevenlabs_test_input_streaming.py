#Quando usamos a versão streamada do ElevenLabs o sotaque sai totalmente americano. Na versão sem streaming, o sotaque sai de Brasileiro

from elevenlabs import generate, stream


## VERSÃO STREAMADA ##
def text_stream():
    yield "O endereço é"
    yield "Rua Mourato coelho 208"


audio = generate(
    text=text_stream(),
    model='eleven_multilingual_v1',
    stream=True, 
    api_key = "aece25f51c8252ea4541f2b1604cac3d"
)

# Stream the audio directly 
stream(audio)


## VERSÃO SEM STREAMING ##

audio = generate(
  text=" O endereço é rua mourato coelho 208",
  stream=True,
  model="eleven_multilingual_v1"
)
stream(audio)