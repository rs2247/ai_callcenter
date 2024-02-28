
import time,os,subprocess
from openai import OpenAI
import itertools
import json
from fuzzywuzzy import fuzz
import numpy as np
from dotenv import load_dotenv
# from deepgram import DeepgramClient, DeepgramClientOptions, PrerecordedOptions
from deepgram import Deepgram
import asyncio

load_dotenv('../.env')
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
DEEPGRAM_API_KEY = os.environ["DEEPGRAM_API_KEY"]


async def deepgram_trancribe(audio_filepath,transcript_filepath):
    print("AUDIO FILENAME", audio_filepath)

    #DEEPGRAM V3
    # config = DeepgramClientOptions(
    #     api_key = DEEPGRAM_API_KEY
    # )
    # deepgram = DeepgramClient("", config)
    # deepgram.SetHttpClientTimeout(TimeSpan.FromSeconds(300));
    # with open(audio_filename, "rb") as file:
    #     buffer_data = file.read()
    # payload: FileSource = {
    #     "buffer": buffer_data,
    # }
    # options = PrerecordedOptions(
    #     model="nova-2",
    #     smart_format=True,
    #     utterances=True,
    #     punctuate=True,
    #     diarize=True,
    #     language="pt-BR",
    # )
    # response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options,timeout=300)

    #DEEPGRAM V2
    deepgram = Deepgram(DEEPGRAM_API_KEY)
    audio = open(audio_filepath, 'rb')

    source = {
        'buffer': audio,'mimetype': 'audio/wav'
    }

    response = await asyncio.create_task(
        deepgram.transcription.prerecorded(
            source,
            {
                'smart_format': 'true',
                'model':'nova-2',
                'utterances':True,
                'punctuate':True,
                # 'diarize':True,
                'multichannel': True,
                'language': 'pt-BR',
                # 'filler_words':True
            }
        )
    )

    # Write the response to the console
    print(json.dumps(response, indent=4))    
    
    # filename_no_extension = os.path.splitext(os.path.basename(audio_filepath))[0]
    # directory_path = os.path.dirname(audio_filepath)
    # transcript_filepath = directory_path + '/transcripts/' + filename_no_extension + '.txt'
    
    with open(transcript_filepath, 'w',  encoding='utf-8') as json_file:


        '''
        Full transcription payload. To get a readable version deepgram recomends using stg like
        cat deepgram_transcript.txt | jq -r ".results.utterances[] | \"[Speaker:\(.speaker)] \(.transcript)\""
        in the output file. But I did some tests and it seems that this utterances processing messes with the diarization
        '''
        # json.dump(
        #     response,
        #     json_file,
        #     indent=4,
        #     ensure_ascii=False
        # )    


        # json_file.write(response['results']['channels'][0]['alternatives'][0]['paragraphs']['transcript'])
        json_file.write(response['results']['paragraphs']['transcript'])


async def run_transcription(calls_directory):
    audio_filename_list = [file for file in os.listdir(calls_directory) if file.endswith('.wav')]
    
    for audio_filename in audio_filename_list:
    
        audio_filepath = calls_directory + '/' + audio_filename        
        transcript_filepath = calls_directory  + '/transcripts/' + audio_filename.replace('wav','txt')
        
        print(audio_filepath, '\n',transcript_filepath)
        print('\n')

        await deepgram_trancribe(audio_filepath,transcript_filepath)



async def main():
    
    await run_transcription(os.getcwd() + '/calls')
    # filename = current_folder+'/calls/caio_fernanda.wav'
    # await run_deepgram(filename)

if __name__ == "__main__":
    asyncio.run(main())
    