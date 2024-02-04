from openai import OpenAI
import itertools
import pandas as pd
from dotenv import load_dotenv
import os
import json
# from flask import Flask
from app import app

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
load_dotenv(override=True)


def read_transcript (file_path):
    with open(file_path, 'r') as file:
        content = file.read().replace("Speaker 0","Vendedor").replace("Speaker 1", "Aluno")
        print(content)
    return content


# transcript = read_transcript('test.txt')
# len_transcript = len(transcript)
# print(len_transcript)

# from openai import OpenAI
# client = OpenAI()

# completion = client.chat.completions.create(
#   model="gpt-3.5-turbo-1106",
#   messages=[
#     {
#     	"role": "system", 
#     	"content": f'''
# 	    	Você é um assistente pessoal de vendedor de uma empresa chamada DNC, que vende cursos profissionalizantes de tecnologia. 
# 	    	Seu papel é receber uma transcrição de uma reunião de vendas de um vendedor com um aluno e ajudar esse vendedor a
# 	    	entender como foi a reunião e o que ele poderia fazer para aumentar as chances de vender.
# 	    	A principal proposta de valor da DNC é empregabilidade, ou seja ajudar o aluno a se capacitar para conseguir um emprego ou fazer uma transição de carreira
# 			A metodologia de vendas é consultiva, o vendedor idealmente precisa entender as necessidades do aluno, seu objetivo de carreira e vida, o que te incomoda atualmente, 
# 			aonde quer chegar e oferecer um curso que o ajude nesses objetivos. Ele também precisa entender as objeções do aluno a 
# 			comprar o curso e contorná-las.

# 			############### TRANSCRIÇÃO #############
# 			{transcript[int(len_transcript/2):]}
#     	'''
# 	},
#     {
#     	"role": "user", 
#     	"content": "Quais os principais pontos em que o vendedor se saiu bem?"}
#   ]
# )
# print(completion.choices[0].message)



# # app = Flask(__name__)

# @app.route('/')
# def index():
# 		return 'Web App with Python Flask!'

app.run(host='0.0.0.0', port=81,debug=True)