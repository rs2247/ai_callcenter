# A ideia desse teste é ficar repeting a mesma frase 'How are you' múltiplas vezes. Uma vez ele faz o TTS com o Faster Whisper e outra com o Whisper
# Resultado: FastWhisper tem uma latência de ~0.5s enquanto o Whisper entrega um resultado perto de ~1s nos modelos tiny. 
# No modelo tiny.en a performance de entendimento foi boa, mas no modelo multilinguagem e setado para pt foi muito ruim, quase não entendia o que eu falava
# Vale testar todos os tamanhos de modelos, estão todos aqui https://huggingface.co/Systran


import elevenlabs, pyaudio, wave, numpy, collections, faster_whisper, torch.cuda
import time,os,subprocess
from openai import OpenAI
import itertools
import pandas as pd
import plotly.express as px
from fuzzywuzzy import fuzz
import numpy as np




client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
elevenlabs.set_api_key("aece25f51c8252ea4541f2b1604cac3d")


model, answer, history = faster_whisper.WhisperModel(model_size_or_path="base", device='cuda' if torch.cuda.is_available() else 'cpu', cpu_threads = 8), "", []


def get_levels(data, long_term_noise_level, current_noise_level):
    pegel = numpy.abs(numpy.frombuffer(data, dtype=numpy.int16)).mean()
    long_term_noise_level = long_term_noise_level * 0.995 + pegel * (1.0 - 0.995)
    current_noise_level = current_noise_level * 0.920 + pegel * (1.0 - 0.920)
    return pegel, long_term_noise_level, current_noise_level


##listens to the mic, collects the speech and writes to voice_record.wav
def get_speech():
    audio = pyaudio.PyAudio()
    stream = audio.open(rate=16000, format=pyaudio.paInt16, channels=1, input=True, frames_per_buffer=512)
    audio_buffer = collections.deque(maxlen=int((16000 // 512) * 0.5))
    frames, long_term_noise_level, current_noise_level, voice_activity_detected = [], 0.0, 0.0, False

    print("\n\nSay 'How are you'. ", end="", flush=True)
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
            print("Voice detected!Starting to capture it.\n")
            ambient_noise_level = long_term_noise_level
            frames.extend(list(audio_buffer))

    stream.stop_stream(), stream.close(), audio.terminate()        

    # Transcribe recording using whisper
    with wave.open("voice_record.wav", 'wb') as wf:
        wf.setparams((1, audio.get_sample_size(pyaudio.paInt16), 16000, 0, 'NONE', 'NONE'))
        wf.writeframes(b''.join(frames))


def run_whisper(audio_filename="voice_record.wav"):
    audio_file= open(audio_filename, "rb")
    user_text = client.audio.transcriptions.create(model="whisper-1", file=audio_file,response_format="text", language='pt', prompt= 'Bem vindo à Pizzaria. Hmm eu vou escolher a pizza de calabresa e de mussarela. O pagamento vai ser no cartão de crédito')
    return user_text

def run_whisper_cpp (audio_filename="voice_record.wav",model='base',threads=4, processors=1):
    subprocess.run([
        "/Users/sanabria/Desktop/code/whisper.cpp/main", 
        "-m", f"/Users/sanabria/Desktop/code/whisper.cpp/models/ggml-{model}.bin",
        "-f",f"/Users/sanabria/Desktop/code/ai_callcenter/playground/sana/{audio_filename}",
        "-l", "pt",
        "--output-txt",
        "-of","/Users/sanabria/Desktop/code/ai_callcenter/playground/sana/voice_record_transcript",
        "-p",str(processors),
        "-t",str(threads)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT
    ) 
    with open("voice_record_transcript.txt", "r") as f:
        user_text = f.read()
    
    return user_text


def run_faster_whisper(audio_filename="voice_record.wav"):
    user_text = " ".join(seg.text for seg in model.transcribe(audio_filename, language='pt')[0])
    return user_text

def run_implementation(whisper_implementation,implementation_args, implementation_name,ground_truth=""):
    tic = time.perf_counter()
    user_text = whisper_implementation(**implementation_args)
    toc = time.perf_counter()
    #Logging
    short_user_text= user_text.replace("\n","--")
    print(f'{implementation_name} -> {short_user_text} -> {round(toc-tic,3)}')    
    if ground_truth!="":
        accuracy = fuzz.ratio(ground_truth,short_user_text)
    else:
        accuracy = np.nan
    return user_text, toc - tic,accuracy


#If you dont record a new audio, make sure you have an audio sample with named voice_record.wav in the same folder of this script
multiple_audio = input("Benchmark em múltiplos áudios?[y/N]")
if multiple_audio == 'y':

    # audio_list = ['bem_vindo_pizzaria.wav','long_slow.wav','long_fast.wav','fast_low_quality.wav','long_phone.wav']
    #filenames and ground truths
    audio_list = {
        'bem_vindo_pizzaria.wav':'Bem vindo à Pizzaria!',
        'long_slow.wav':'Bem vindo à Pizzaria. Meu nome é Renato. Como posso te ajudar?',
        'long_fast.wav':'Bem vindo à Pizzaria, tudo bem? Meu nome é Renato, o que que você vai querer hoje?',
        'fast_low_quality.wav':'Oi tudo bem? Eu queria uma pizza de calabresa por favor Isso Vê pra entrega pra mim tá? E o endereço é Rua Morato Coelho 208 Obrigado',
        'long_phone.wav':'Oi, bom dia, tudo bem? Meu nome é Renato e eu queria pedir uma pizza de calabresa para entregar. Meu telefone é 12 982252000.'
    }

    df = pd.DataFrame({
        'audio_file':[],
        'model':[],
        'latency':[],
        'accuracy':[],
        'transcript':[],
        'audio_ground_truth':[]
    })

    implementations_dict = {
       'whisper':run_whisper,
       'faster_whisper':run_faster_whisper,
       'whisper_cpp':run_whisper_cpp
    }
    for audio_filename,audio_ground_truth in audio_list.items():
        for model_name,model_method in implementations_dict.items():
            
            if model_name !='whisper_cpp':
                transcript, latency,accuracy = run_implementation(model_method,{'audio_filename':audio_filename},model_name,audio_ground_truth)
                df = pd.concat([df, pd.DataFrame({
                        'audio_file':[audio_filename],
                        'model':[model_name],
                        'latency':[latency],
                        'accuracy':[accuracy],
                        'transcript':[transcript],
                        'audio_ground_truth':[audio_ground_truth]
                    })], ignore_index=True)
            else:
                #WHISPER CPP
                # for model,processors,threads in list(itertools.product(['tiny','base','small'],[1,2],[1,4,9])):
                for base_model_name,processors,threads in list(itertools.product(['base','small','medium'],[1],[4,8])):
                    model_name = f'whisper_cpp_{base_model_name}_processors:{processors}_threads:{threads}'
                    transcript, latency,accuracy = run_implementation(
                        model_method, 
                        {'audio_filename':audio_filename,'model':base_model_name,'threads':threads, 'processors':processors},
                        model_name,
                        audio_ground_truth
                    )

                    df = pd.concat([df, pd.DataFrame({
                        'audio_file':[audio_filename],
                        'model':[model_name],
                        'latency':[latency],
                        'accuracy':[accuracy],
                        'transcript':[transcript],
                        'audio_ground_truth':[audio_ground_truth]
                    })], ignore_index=True)



        
    fig = px.bar(df, x='audio_file',y ='latency', color='model', barmode='group',hover_data = ['transcript','audio_ground_truth','accuracy'])
    # fig = px.scatter(df, x="latency", y="accuracy", color="model", hover_data=['transcript','audio_file'])
    fig.show()
    print(df)



else:
    get_new_speech = input("Você gostaria de gravar um novo áudio para benchmark?[y/N]")
    if get_new_speech == 'y':
        get_speech()

    # NORMAL WHISPER
    run_implementation(run_whisper,{},'whisper')

    #FASTER WHISPER
    run_implementation(run_faster_whisper,{},'faster_whisper')


    #WHISPER CPP
    # for model,processors,threads in list(itertools.product(['tiny','base','small'],[1,2],[1,4,9])):
    for model_name,processors,threads in list(itertools.product(['base','small','medium'],[1],[4,8])):
        run_implementation(run_whisper_cpp, {'model':model_name,'threads':threads, 'processors':processors},f'whisper_cpp_{model}_processors:{processors}_threads:{threads}')


