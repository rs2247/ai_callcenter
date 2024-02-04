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
                # O vendedor conseguiu quebrar as principais objeções do aluno? De uma resposta direta (Sim ou Não), uma explicação e trechos da transcrição que justifiquem a resposta. Os trechos devem ter 40 palavras ou mais e devem ser separados por ; 
                # Macro        
                #     - O vendedor conseguiu criar conexão emocional e empatia com o aluno? 
                #     - O vendedor foi conciso e objetivo na sua fala? De uma resposta direta (Sim ou Não) e uma explicação que contenha o percentual do diálogo que foi falado pelo vendedor (entre 0 e 100%)

        {
            "role": "user", 
            "content": '''
                ################################## INSTRUÇÃO #################################
                Responda às seguintes perguntas em bullet points: 
                - Quais as motivações do aluno para procurar a DNC? Respostas devem ser separadas por ;
                - Quais as principais objeções mencionadas pelo aluno que podem impedi-lo de comprar o curso? Respostas devem ser separadas por ;
                - Qual o orçamento disponível pelo aluno para comprar o curso? 
                - Quais foram as principais dúvidas do aluno sobre o curso? Respostas devem ser separadas por ;
                - O aluno citou algum concorrente? Se sim, retorne o trecho em que o aluno fala de algum concorrente
                - O aluno decidiu comprar o curso? 
                - Quais são os próximos passos?
                
                Para as perguntas abaixo forneça uma resposta direta (Sim ou Não), uma explicação da sua resposta e trechos (um ou mais) da transcrição que justifiquem a resposta caso ela seja Sim. Os trechos devem ter 60 palavras ou mais e devem ser separados por ; 
                Abertura
                    - O vendedor se apresentou e cumprimentou o aluno? 
                Discovery                    
                    - O vendedor perguntou qual o objetivo do aluno ao comprar esse curso?
                    - O vendedor perguntou qual curso o aluno tem interesse?
                    - O vendedor perguntou se o aluno já fez ensino superior ou não? 
                Pitch de vendas    
                    - O vendedor explicou o conteúdo dos cursos e como eles atenderiam as necessidades do aluno?  
                    - O vendedor explicou que os cursos são ministrados por professores que tem experiência de mercado e não por acadêmicos?   
                    - O vendedor explicou que os cursos acompanham projetos práticos e não são apenas teóricos? 
                    - O vendedor perguntou se as opções de curso apresentadas faziam sentido para o aluno?
                Closing    
                    - O vendedor conseguiu descobrir quanto o aluno gostaria de gastar no curso? 
                    - O vendedor explicou o preço e as diferenças formas de pagar o curso? 
                    - O vendedor ofereceu um curso que coubesse no orçamento do aluno? 
                    - O vendedor tentou fechar a venda durante a ligação ou exigiu do aluno um prazo para a resposta? 


                ################################## FORMATO DA RESPOSTA #################################
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
                        "Abertura":{
                            "Apresentação":{
                                "resposta": "Sim"/"Não",
                                "explicação": "",
                                "trechos": ""
                            }
                        },
                        "Discovery": {
                            "Objetivo":{
                                "resposta": "Sim"/"Não",
                                "explicação": "",
                                "trechos": ""
                            },
                            "Curso":{
                                "resposta": "Sim"/"Não",
                                "explicação": "",
                                "trechos": ""
                            },
                            "Ensino_superior":{
                                "resposta": "Sim"/"Não",
                                "explicação": "",
                                "trechos": ""
                            }
                        },
                        "Pitch de vendas":{
                            "Conteúdo":{
                                "resposta": "Sim"/"Não",
                                "explicação": "",
                                "trechos": ""
                            },
                            "Professores":{
                                "resposta": "Sim"/"Não",
                                "explicação": "",
                                "trechos": ""
                            },
                            "Projetos":{
                                "resposta": "Sim"/"Não",
                                "explicação": "",
                                "trechos": ""
                            },
                            "Faz_sentido":{
                                "resposta": "Sim"/"Não",
                                "explicação": "",
                                "trechos": ""
                            }
                        },  
                        "Closing":{
                            "Orçamento":{
                                "resposta": "Sim"/"Não",
                                "explicação": "",
                                "trechos": ""
                            },
                            "Preficicação":{
                                "resposta": "Sim"/"Não",
                                "explicação": "",
                                "trechos": ""
                            },
                            "Match_orçamento_curso":{
                                "resposta": "Sim"/"Não",
                                "explicação": "",
                                "trechos": ""
                            },
                            "Fechamento":{
                                "resposta": "Sim"/"Não",
                                "explicação": "",
                                "trechos": ""
                            }
                        },
                    }
               }
            '''
        }]

    )

    print(completion.choices[0].message.content)
    return json.loads(completion.choices[0].message.content)



@app.route('/')
def index():
    transcript = load_transcript('test.txt')
    
    # gpt_answer = ask_gpt(transcript)
    
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


    


