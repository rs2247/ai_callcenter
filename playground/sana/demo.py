from elevenlabs import Voice, VoiceSettings, generate,play, stream
from elevenlabs import set_api_key
from openai import OpenAI
import speech_recognition as sr

client = OpenAI(api_key="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")


set_api_key("aece25f51c8252ea4541f2b1604cac3d")
# openai.api_key = "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" ## OpenAI Key


# audio = generate(
#     text="Oi eu gostaria de comprar uma pizza de calabresa com tomate",
#     voice=Voice(
#         voice_id='EXAVITQu4vr4xnSDxMaL',
#         settings=VoiceSettings(stability=0.4, similarity_boost=0.5, style=0.0, use_speaker_boost=True)
#     ),
#     model="eleven_multilingual_v1"
# )

# play(audio)

################

# from elevenlabs import voices, generate

# voices = voices()
# audio = generate(text="Hello there!", voice=voices[0])

# for voice in voices:
#     print(voice)
#     print('\n')


################

# audio_stream = generate(
#   text="Oi eu gostaria de comprar ...... uma pizza de calabresa",
#   stream=True,
#   model="eleven_multilingual_v1"
# )

# stream(audio_stream)

###############


while True: 

    
    #Getting waiter input
    r = sr.Recognizer()  # initialize a recognizer object
    with sr.Microphone() as source:  # use the microphone
        print("Fale alguma coisa :")
        waiter_audio = r.listen(source)  # record the audio, store in audio wav file
        # print(waiter_audio)
        waiter_input = r.recognize_whisper(waiter_audio, language='portuguese')
    print("Atendente disse: {}".format(waiter_input))
    

    #Sending waiter input to GPT to get the buyer input
    # prompt = input("Usuário: ")
    # print(prompt)
    prompt = waiter_input

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "você é um agente que vai falar com um atendente de pizzaria para pedir uma pizza de calabresa e mussarela para ser entregue no endereço rua mourato coelho 208, ap 28. eu vou ser o atendente, espere pelos meus inputs. a forma de pagamento deve ser cartão de crédito. De respostas curtas."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    buyer_input = completion.choices[0].message.content
    print(buyer_input)

    #Converting the buyer input to audio
    audio_stream = generate(
      text=buyer_input,
      stream=True,
      model="eleven_multilingual_v1"
    )

    stream(audio_stream)
