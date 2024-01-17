# A ideia desse teste é ficar repeting a mesma frase 'How are you' múltiplas vezes. Uma vez ele faz o TTS com o Faster Whisper e outra com o Whisper
# Resultado: FastWhisper tem uma latência de ~0.5s enquanto o Whisper entrega um resultado perto de ~1s nos modelos tiny. 
# No modelo tiny.en a performance de entendimento foi boa, mas no modelo multilinguagem e setado para pt foi muito ruim, quase não entendia o que eu falava
# Vale testar todos os tamanhos de modelos, estão todos aqui https://huggingface.co/Systran


import elevenlabs, pyaudio, wave, numpy, collections, faster_whisper, torch.cuda
import time,os
from openai import OpenAI


client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
elevenlabs.set_api_key("aece25f51c8252ea4541f2b1604cac3d")


model, answer, history = faster_whisper.WhisperModel(model_size_or_path="small", device='cuda' if torch.cuda.is_available() else 'cpu', cpu_threads = 8), "", []


def get_levels(data, long_term_noise_level, current_noise_level):
    pegel = numpy.abs(numpy.frombuffer(data, dtype=numpy.int16)).mean()
    long_term_noise_level = long_term_noise_level * 0.995 + pegel * (1.0 - 0.995)
    current_noise_level = current_noise_level * 0.920 + pegel * (1.0 - 0.920)
    return pegel, long_term_noise_level, current_noise_level

select_whisper = True
while True:
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
    tic = time.perf_counter()        
    with wave.open("voice_record.wav", 'wb') as wf:
        wf.setparams((1, audio.get_sample_size(pyaudio.paInt16), 16000, 0, 'NONE', 'NONE'))
        wf.writeframes(b''.join(frames))
    
    toc = time.perf_counter()
    print(f"Delta audio file whisper {toc - tic}")

    
    tic = time.perf_counter()        
    if select_whisper:    
        # FASTER WHISPER
        print("Using FasterWhisper")
        print(select_whisper)
        user_text = " ".join(seg.text for seg in model.transcribe("voice_record.wav", language='pt')[0])
    else:
        # NORMAL WHISPER
        print("Using Whisper")
        print(select_whisper)
        audio_file= open("voice_record.wav", "rb")
        user_text = client.audio.transcriptions.create(model="whisper-1", file=audio_file,response_format="text", language='pt')
    select_whisper = not select_whisper


    toc = time.perf_counter()
    print(f"Delta_t whisper {toc - tic}")
    print(f'>>>{user_text}\n<<< ', end="", flush=True)
    history.append({'role': 'user', 'content': user_text})
