import os
from elevenlabs import Voice, VoiceSettings, generate,play
import elevenlabs
from elevenlabs import set_api_key
from openai import OpenAI
import speech_recognition as sr
import time
import numpy as np
import faster_whisper
import torch.cuda
import pyaudio, wave, collections, torch.cuda, numpy

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
set_api_key("aece25f51c8252ea4541f2b1604cac3d")


#Getting waiter input
times_mic = []
times_whisper = []
times_openai = []


def get_levels(data, long_term_noise_level, current_noise_level):
    pegel = numpy.abs(numpy.frombuffer(data, dtype=numpy.int16)).mean()
    long_term_noise_level = long_term_noise_level * 0.995 + pegel * (1.0 - 0.995)
    current_noise_level = current_noise_level * 0.920 + pegel * (1.0 - 0.920)
    return pegel, long_term_noise_level, current_noise_level


#streamed version of gpt
def gpt_generator(prompt): 
    i=0
    for chunk in client.chat.completions.create(
		model="gpt-3.5-turbo",
		messages=[
            {"role": "system", "content": "você é um agente que vai falar com um atendente de pizzaria para pedir uma pizza de calabresa e mussarela para ser entregue no endereço rua mourato coelho 208, ap 28. eu vou ser o atendente, espere pelos meus inputs. a forma de pagamento deve ser cartão de crédito. De respostas curtas e objetivas."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
		stream = True
	):
        # print("\nchunk #:",i)
        i=i+1
        if (text_chunk := chunk.choices[0].delta.content):
            print(text_chunk, end="", flush=True) 
            yield text_chunk



while True: 

    if times_mic != []:
        print('Average latencies:')
        print(f'Mic input: {np.average(times_mic)}')
        print(f'Speech to text: {np.average(times_whisper)}')
        print(f'Open AI: {np.average(times_openai)}')
        print("\n\n")
    


    #Old ASR AND STT
    # r = sr.Recognizer()  # initialize a recognizer object
    # with sr.Microphone() as source:  # use the microphone
    #     print("Fale alguma coisa :")
    #     tic = time.perf_counter()
    #     waiter_audio = r.listen(source)  # record the audio, store in audio wav file
    #     # print(waiter_audio)
    #     toc = time.perf_counter()
    #     times_mic.append(toc - tic)
    #     print(f"Delta_t get input from mic {times_mic[-1]}")


    #     tic = time.perf_counter()        
    #     waiter_input = r.recognize_whisper(waiter_audio, language='portuguese')
    #     toc = time.perf_counter()
    #     times_whisper.append(toc - tic)
    #     print(f"Delta_t whisper {times_whisper[-1]}")

    # print("Atendente disse: {}".format(waiter_input))



    #New AAD and STT
    audio = pyaudio.PyAudio()
    stream = audio.open(rate=16000, format=pyaudio.paInt16, channels=1, input=True, frames_per_buffer=512)
    audio_buffer = collections.deque(maxlen=int((16000 // 512) * 0.5))
    frames, long_term_noise_level, current_noise_level, voice_activity_detected = [], 0.0, 0.0, False

    print("\n\nSay something. ", end="", flush=True)
    while True:
        data = stream.read(512)
        pegel, long_term_noise_level, current_noise_level = get_levels(data, long_term_noise_level, current_noise_level)
        audio_buffer.append(data)

        if voice_activity_detected:
            frames.append(data)            
            if current_noise_level < ambient_noise_level + 100:
                break # voice actitivy ends 
        
        if not voice_activity_detected and current_noise_level > long_term_noise_level + 300:
            voice_activity_detected = True
            print("Voice detected, starting to capture it.\n")
            ambient_noise_level = long_term_noise_level
            frames.extend(list(audio_buffer))

    stream.stop_stream(), stream.close(), audio.terminate()        

    # Transcribe recording using whisper
    with wave.open("voice_record.wav", 'wb') as wf:
        wf.setparams((1, audio.get_sample_size(pyaudio.paInt16), 16000, 0, 'NONE', 'NONE'))
        wf.writeframes(b''.join(frames))
    
    tic = time.perf_counter()        
    audio_file= open("voice_record.wav", "rb")    
    waiter_input = client.audio.transcriptions.create(model="whisper-1", file=audio_file,response_format="text")
    toc = time.perf_counter()
    times_whisper.append(toc - tic)
    print(f"Delta_t whisper {times_whisper[-1]}")

    print("Atendente disse: {}".format(waiter_input))


    #NORMAL GPT
    #Sending waiter input to GPT to get the buyer input
    # tic = time.perf_counter()
    # prompt = waiter_input
    # completion = client.chat.completions.create(
    #     model="gpt-3.5-turbo",
    #     messages=[
    #         {"role": "system", "content": "você é um agente que vai falar com um atendente de pizzaria para pedir uma pizza de calabresa e mussarela para ser entregue no endereço rua mourato coelho 208, ap 28. eu vou ser o atendente, espere pelos meus inputs. a forma de pagamento deve ser cartão de crédito. De respostas curtas."},
    #         {"role": "user", "content": prompt},
    #     ],
    #     temperature=0.7,
    # )
    # buyer_input = completion.choices[0].message.content
    # toc = time.perf_counter()
    # times_openai.append(toc -tic)
    # print(f"Delta_t openai {times_openai[-1]}")
    # print(buyer_input)

    # audio_stream = generate(
    #   text=buyer_input,
    #   stream=True,
    #   model="eleven_multilingual_v1"
    # )

    #STREAMED GPT
    # WARNING! For this to work, you need to change something in the elevenlabs lib and switch to an elevenlabs paid plan
    # See this thread https://github.com/elevenlabs/elevenlabs-python/issues/136
    audio_stream = generate(
        text=gpt_generator(waiter_input),
        model='eleven_multilingual_v1',
        stream=True        
    )
    elevenlabs.stream(audio_stream)

