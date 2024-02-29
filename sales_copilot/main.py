
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


def load_transcript(transcript_filepath):
    with open(transcript_filepath, 'r') as file:
        transcript = file.read()
    return transcript

def extract_feature_alta_empregabilidade(transcript):
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        # model="gpt-4-turbo-preview",
        messages=[{
            "role": "system", 
            "content": f'''
              Você é um agente de qualidade de um time de vendas da Escola DNC. Seu papel é analisar a transcrição abaixo de uma conversas
              entre um vendedor e um cliente e identificar se ele está agindo da forma como é esperado. 
              Se está dizendo o pitch de vendas corretamente, criando rapport com os clientes, etc
              Para contexto, a Escola DNC vende cursos online de dados, marketing, projetos, dentre outros. 

              #### TRANSCRIÇÃO ####
              {transcript}

            '''
        },
        {
            "role": "user", 
            "content": f'''

              #### INSTRUÇÃO ####
              Cheque se na transcrição acima é mencionado explicitamente sobre a alta taxa de empregabilidade dos alunos da DNC depois de formados.
              
              #### PASSO 1 ####
              Verifique se existe um trecho que menciona explicitamente a alta taxa de empregabilidade

              #### PASSO 2 ####
              Avalie se esse trecho explicitamente cita que a empregabilidade dos alunos da DNC depois de formados é alta, por exemplo citando os noventa e oito porcento de taxa de empregabilidade

              #### FORMATO DESEJADO ####
              {{
                alta_empregabilidade: <sim/não>
                trecho: <se a resposta for sim, traga um trecho da transcrição que mencione a alta taxa de empregabilidade>
              }}  

              #### EXEMPLOS SIM ####
              "tanto que a dnc tem a maior taxa de empregabilidade do Brasil" 
              "...tanto que nossa taxa de empregabilidade hoje depois da formação em até três meses é de noventa e oito vírgula cinco por cento. Ricardo por isso que a gente promete a devolução do dinheiro porque a gente sabe que é bom nisso, empregabilidade."
              "Hoje a nossa taxa é de noventa e oito vírgula sete, que significa isso? A cada cem alunos que a gente matricula, noventa e oito conseguem emprego, consegue atingir seu objetivo, seja de cargo, seja de salário, ou seja ele de faixa aí, em até seis meses após a formação."
              "a maior empregabilidade aqui do Brasil"

              #### EXEMPLOS NÃO ####
              "a parte de dados, é que a gente possui programa de carreira certa, aí tem a mentoria de carreira, onde a gente vai te guiar no mercado de trabalho até a área de dados, com consultoria né a gente vai te ajudar a entrar no processo seletivo aí avançando no processo seletivo, assim como a gente vai te ajudar a otimizar o seu currículo coisa pra educação"
              "por por conta que a gente tem acesso a aulas gravadas, que você vai ter flexibilidade naquilo que você precisa, no seu tempo, você independente disso, você vai ter certificados vitalícios, reconhecidos pelo MEC, a gente vai ser vai te dar mentoria, tem aulas ao vivo, tem com alunos, e dentre os projetos que você pode fazer com empresas reais, sabe, a Ifood, PicPay, Ambev, Azul, trabalham com a gente."
              "faz conclui o passo do curso, aí você libera o embutido, que se você não tiver formado em até seis meses, a gente devolve todo o dinheiro do curso que você investiu."
            '''
        }],
        temperature=0.2
    )
    return completion.choices[0].message.content


async def deepgram_trancribe(audio_filepath,transcript_filepath):

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
    # print(json.dumps(response, indent=4))    
    
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


async def run_transcription(calls_directory, transcripts_directory):
    audio_filename_list = [file for file in os.listdir(calls_directory) if file.endswith('.wav')]
    
    for audio_filename in audio_filename_list:
        
        if audio_filename in ['athos_anderson.wav','athos_lorenzo.wav','caio_fernanda.wav','caio_gabriela.wav','ellen_fernando.wav','ellen_wallance.wav','josueh_gabriel.wav','lauraoliveira_marcemilio.wav','lucaspena_joao.wav']:
            continue


        audio_filepath = calls_directory + '/' + audio_filename        
        transcript_filepath = transcripts_directory + '/' + audio_filename.replace('wav','txt')
        
        await deepgram_trancribe(audio_filepath,transcript_filepath)
        


async def main():
    
    #TRANSCRIPTION
    # await run_transcription(os.getcwd() + '/calls', os.getcwd() + '/transcripts')
    
    #EXTRACTING FEATURES
    # transcript = load_transcript(os.getcwd() + '/transcripts/josueh_alexei.txt')
    # transcript = load_transcript(os.getcwd() + '/transcripts/josueh_adeilson.txt')
    transcript_filename_list = [file for file in os.listdir(os.getcwd() + '/transcripts') if file.endswith('.txt')]
    for transcript_filename in transcript_filename_list:
        transcript = load_transcript(os.getcwd() + '/transcripts/' + transcript_filename)
        
        print(transcript_filename)
        feature = extract_feature_alta_empregabilidade(transcript)
        print(feature)
        print("\n\n")

    # filename = current_folder+'/calls/caio_fernanda.wav'
    # await run_deepgram(filename)

if __name__ == "__main__":
    asyncio.run(main())
    