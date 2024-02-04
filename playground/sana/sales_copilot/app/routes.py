from openai import OpenAI
import os,json
from flask import render_template
from app import app
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def load_transcript(file_path):
    with open(file_path, 'r') as file:
        transcript = file.read().replace("Speaker 0","Vendedor").replace("Speaker 1", "Aluno")
    return transcript

def load_gpt_buffer(file_path):
    with open(file_path, 'r') as file:
        gpt_answer = json.load(file)

    return gpt_answer


def ask_gpt(transcript):

    completion = client.chat.completions.create(
        # model="gpt-3.5-turbo-1106",
        model="gpt-4-turbo-preview",
        messages=[{
            "role": "system", 
            "content": f'''
              Você é um assistente pessoal de vendedor de uma empresa chamada DNC, que vende cursos profissionalizantes de tecnologia. 
              Seu papel é receber uma transcrição de uma reunião de vendas de um vendedor com um aluno e ajudar esse vendedor a
              entender como foi a reunião e o que ele poderia fazer para aumentar as chances de vender.
              A principal proposta de valor da DNC é empregabilidade, ou seja ajudar o aluno a se capacitar para conseguir um emprego ou fazer uma transição de carreira
              A metodologia de vendas é consultiva, o vendedor idealmente precisa entender as necessidades do aluno, seu objetivo de carreira e vida, o que te incomoda atualmente, 
              aonde quer chegar e oferecer um curso que o ajude nesses objetivos. Ele também precisa entender as objeções do aluno a 
              comprar o curso e contorná-las.

              ############### TRANSCRIÇÃO #############
              {transcript}
            '''
        },
        {
            "role": "user", 
            "content": '''
                Responda às seguintes perguntas em bullet points: 
                Quais as motivações do aluno para procurar a DNC? Respostas devem ser separadas por ;
                Quais as principais objeções mencionadas pelo aluno que podem impedi-lo de comprar o curso? Respostas devem ser separadas por ;
                Qual o orçamento disponível pelo aluno para comprar o curso? 
                Quais foram as principais dúvidas do aluno sobre o curso? Respostas devem ser separadas por ;
                O aluno citou algum concorrente? Se sim, retorne o trecho em que o aluno fala de algum concorrente
                O aluno decidiu comprar o curso? 
                Quais são os próximos passos?
                O vendedor fez perguntas para entender as necessidades do aluno? De uma resposta direta (Sim ou Não), uma explicação e trechos da transcrição que justifiquem a resposta. Os trechos devem ter 40 palavras ou mais e devem ser separados por ; 
                O vendedor conseguiu criar conexão emocional e empatia com o aluno? De uma resposta direta (Sim ou Não), uma explicação e trechos da transcrição que justifiquem a resposta. Os trechos devem ter 40 palavras ou mais e devem ser separados por ; 
                O vendedor demonstrou conhecimento sobre os cursos apresentados? De uma resposta direta (Sim ou Não), uma explicação e trechos da transcrição que justifiquem a resposta. Os trechos devem ter 40 palavras ou mais e devem ser separados por ; 
                O vendedor conseguiu quebrar as principais objeções do aluno? De uma resposta direta (Sim ou Não), uma explicação e trechos da transcrição que justifiquem a resposta. Os trechos devem ter 40 palavras ou mais e devem ser separados por ; 
                O vendedor construiu credibilidade na marca da DNC? De uma resposta direta (Sim ou Não), uma explicação e trechos da transcrição que justifiquem a resposta. Os trechos devem ter 40 palavras ou mais e devem ser separados por ; 
                O vendedor ofereceu um curso que coubesse no orçamento do aluno? De uma resposta direta (Sim ou Não), uma explicação e trechos da transcrição que justifiquem a resposta. Os trechos devem ter 40 palavras ou mais e devem ser separados por ; 
                O vendedor criou senso de urgência no aluno para que ele desse um prazo para a resposta? De uma resposta direta (Sim ou Não), uma explicação e trechos da transcrição que justifiquem a resposta. Os trechos devem 40 palavras ou mais e devem ser separados por ; 
                O vendedor foi conciso e objetivo na sua fala? De uma resposta direta (Sim ou Não), uma explicação e diga quantos porcento do diálogo foi falado pelo vendedor


                Responda com uma string no seguinte formato:
                {
                    "Aluno": { 
                        "Motivações": "",

                        "Objeções": "",

                        "Orçamento":"",

                        "Dúvidas": "",

                        "Concorrentes":{
                            nomes:"",
                            trechos: ""
                        },

                        "Decisão": "Sim"/"Não"

                        "Próximos_passos":""
                    }
                    "Vendedor":{
                        "Perguntas":{
                            "resposta": "Sim"/"Não",
                            "explicação": "",
                            "trechos": ""
                        },
                        "Conexão":{
                            "resposta": "Sim"/"Não",
                            "explicação": "",
                            "trechos": ""
                        },
                        "Conhecimento":{
                            "resposta": "Sim"/"Não",
                            "explicação": "",
                            "trechos": ""
                        },
                        "Objeções":{
                            "resposta": "Sim"/"Não",
                            "explicação": "",
                            "trechos": ""
                        },
                        "Credibilidade":{
                            "resposta": "Sim"/"Não",
                            "explicação": "",
                            "trechos": ""
                        },
                        "Orçamento":{
                            "resposta": "Sim"/"Não",
                            "explicação": "",
                            "trechos": ""
                        },
                        "Urgência":{
                            "resposta": "Sim"/"Não",
                            "explicação": "",
                            "trechos": ""
                        }
                        "Objetividade":{
                            "resposta": "Sim"/"Não",
                            "explicação": "",
                            "percentual_vendedor": ""
                        }
                    }
               }
                '''
        }]

    )

    print(completion.choices[0].message.content)
    return completion.choices[0].message.content



@app.route('/')
def index():
    transcript = load_transcript('test.txt')
    # ask_gpt(transcript)
    gpt_answer = load_gpt_buffer('gpt_answer.txt')
    return render_template( 
        'index.html', 
        transcript = transcript.replace('\n', '<br>'),
        customer_insights = gpt_answer['Aluno'],
        salesperson_performance = gpt_answer['Vendedor']
    )

# @app.route('/details')
# def details():
#     return render_template('index.html')


    


