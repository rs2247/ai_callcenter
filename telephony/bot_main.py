import asyncio
import logging
import signal
import vocode
import os
from dotenv import load_dotenv
from vocode.streaming.streaming_conversation import StreamingConversation
from vocode.helpers import create_streaming_microphone_input_and_speaker_output
from vocode.streaming.transcriber import *
from vocode.streaming.agent import *
from vocode.streaming.synthesizer import *
from vocode.streaming.models.transcriber import *
from vocode.streaming.models.agent import *
from vocode.streaming.models.synthesizer import *
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.models.telephony import TwilioConfig
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter
from opentelemetry.sdk.resources import Resource
from collections import defaultdict
import elevenlabs
from num2words import num2words
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from vocode.streaming.models.agent import LlamacppAgentConfig
from vocode.streaming.agent.llamacpp_agent import LlamacppAgent



# print("ELEVENLABS FILEPATH")
# print(elevenlabs.__file__)

load_dotenv(override=True)

ADDRESS=os.getenv('ADDRESS')
ZIPCODE=os.getenv('ZIPCODE')
PROD = (os.getenv('PROD').lower()=='true')
PHONE_NUMBER = os.environ["PHONE_NUMBER"]
if PROD:
    try:
        from vocode.streaming.telephony.conversation.outbound_call import OutboundCall
        from vocode.streaming.telephony.config_manager.redis_config_manager import (
            RedisConfigManager,
        )
        BASE_URL = os.environ["BASE_URL"]    
    
    except:
        raise Exception("Error loading libraries necessary for phone calls. Make sure you are using poetry to run the script to avoid dependency errors")



#EXPORT SPANS TO CONSOLE
# class PrintDurationSpanExporter(SpanExporter):
#     def __init__(self):
#         super().__init__()
#         self.spans = defaultdict(list)

#     def export(self, spans):
#         for span in spans:
#             duration_ns = span.end_time - span.start_time
#             duration_s = duration_ns / 1e9
#             self.spans[span.name].append(duration_s)

#     def shutdown(self):
#         for name, durations in self.spans.items():
#             print(f"{name}: {sum(durations) / len(durations)}")

# span_exporter = PrintDurationSpanExporter()
# trace.set_tracer_provider(TracerProvider(resource=Resource.create({})))
# trace.get_tracer_provider().add_span_processor(
#     SimpleSpanProcessor(span_exporter)
# )

#EXPORT SPANS TO JAEGER
# from opentelemetry.exporter.jaeger.thrift import JaegerExporter
# from opentelemetry.sdk.resources import SERVICE_NAME, Resource
# from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.sdk.trace.export import BatchSpanProcessor
# jaeger_exporter = JaegerExporter(
#    agent_host_name="localhost",
#    agent_port=6831,
# )
# trace.set_tracer_provider(
#    TracerProvider(
#        resource=Resource.create({SERVICE_NAME: "my-hello-service"})
#    )
# )
# trace.get_tracer_provider().add_span_processor(
#    BatchSpanProcessor(jaeger_exporter)
# )
# tracer = trace.get_tracer(__name__)



#necessary?
vocode.setenv(
    OPENAI_API_KEY=os.getenv('OPENAI_API_KEY'),
    AZURE_SPEECH_KEY=os.getenv('AZURE_SPEECH_KEY'),
    AZURE_SPEECH_REGION=os.getenv('AZURE_SPEECH_REGION'),
    DEEPGRAM_API_KEY=os.getenv('DEEPGRAM_API_KEY'),
    ELEVEN_LABS_API_KEY=os.getenv('ELEVEN_LABS_API_KEY')
)


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def number_to_text_phone(number):
    number = str(number)
    
    if len(number) == 11: #mobile
        #area code
        number_text = "O dê dê dê é " + num2words(number[0:2], lang='pt-br') + ' ... '
        #first digit
        number_text += num2words(number[2], lang='pt-br') + ' | '
        #rest
        for i in range(4):
            digits = number[3+2*i:5+2*i]
            if digits[0]=='0':
                number_text += 'zero '    
            # if i!=3:
            #     number_text += num2words(digits, lang='pt-br') + ' | '
            # else:
            #     number_text += num2words(digits, lang='pt-br')
            if i in (0,2):
                number_text += num2words(digits, lang='pt-br') + ' | '
            elif i == 1:
                number_text += num2words(digits, lang='pt-br') + ' ... '
            else:
                number_text += num2words(digits, lang='pt-br')

    elif len(number) == 10: #local
        raise NotImplemented ("Implement number_to_text_phone for local phone numbers")

    else:
        raise Exception("Number should have 11(mobile) or 10(local) digits, including area code (DDD)")

    return number_text

def number_to_text_zipcode(zipcode):
    zipcode = str(zipcode)
    assert len(zipcode)==8, "Zipcode should have 8 digits"
    if zipcode[0]=='0':
        number_text = 'zero '
    number_text += num2words(zipcode[0:2], lang='pt-br') + ','
    for i in range(6):
        number_text += num2words(zipcode[i+2], lang='pt-br') + ' '
        if i == 2:
            number_text += ','
    return number_text


async def main():

    print(number_to_text_phone(PHONE_NUMBER[3:]))
    print(number_to_text_zipcode(ZIPCODE))
    
    system_definition = {
        'transcriber':{
            'class':DeepgramTranscriber,
            'configClass':DeepgramTranscriberConfig,
            'endpointing_config':TimeEndpointingConfig(),
            # 'endpointing_config':PunctuationEndpointingConfig(),
            'configVars':{
                'language':"pt-BR",
                'model':"nova-2"
            }
        },
        # 'synthesizer':{
        #     'class':AzureSynthesizer,
        #     'configClass':AzureSynthesizerConfig,
        #     'configVars':{
        #         'voice_name': 'pt-BR-DonatoNeural',
        #         'language_code':'pt-BR'
        #     }
        # },
        'synthesizer':{
            'class':ElevenLabsSynthesizer,
            'configClass':ElevenLabsSynthesizerConfig,
            'configVars':{
                'model_id': 'eleven_multilingual_v2',
                #  'model_id': 'eleven_multilingual_v1',
                # 'model_id': 'eleven_turbo_v2',
                'voice_id':'NGS0ZsC7j4t4dCWbPdgO', # Dyego -- voice not found
                # 'voice_id': 'pNInz6obpgDQGcFmaJgB',
                # 'voice_id': '21m00Tcm4TlvDq8ikWAM', #Rachel
                # 'voice_id': 'LcfcDJNUP1GQjkzn1xUU', #Emily
                'api_key':os.getenv("ELEVEN_LABS_API_KEY"),
                'optimize_streaming_latency': 4,
                'stability': '1',
                'similarity_boost': '0.75'
            }
        # 'synthesizer':{
        #     'class':CoquiTTSSynthesizer,
        #     'configClass':CoquiTTSSynthesizerConfig,
        #     'configVars':{
        #         # 'language':'pt',
        #         # 'tts_kwargs':{'model_name':'tts_models/en/ljspeech/tacotron2-DDC_ph'}
        #         # 'tts_kwargs':{'model_name':'tts_models/multilingual/multi-dataset/your_tts'}
        #         # 'tts_kwargs':{'model_name':'tts_models/multilingual/multi-dataset/bark'}
        #         'tts_kwargs':{'model_name':'tts_models/pt/cv/vits'}
                
                
        #     }

        },
        # 'agent': {
        #     'class':LlamacppAgent,
        #     'configClass':LlamacppAgentConfig,
        #     'configVars':{
        #         'prompt_preamble': f'''
        #           ### Instrução ###
        #           Você é um agente responsável por pedir uma pizza pelo telefone. Seja curto e direto ao ponto. 
        #           Fale de maneira informal, como uma jovem brasileira de 20 anos.
        #           Se perguntarem o seu nome é Ana.
        #           Informe que você quer pedir uma pizza apenas no início da conversa. Não repita que quer pedir uma pizza ao menos que seja perguntado.
        #           Um atendente da pizzaria irá falar com você, você deve esperar pelos inputs dele e oferecer respostas diretas e curtas.
        #           Você deve solicitar uma pizza pequena de portuguesa.
        #           Quando for perguntado, informe que é para entregar na {ADDRESS}. 
        #           Se for perguntado, informe que o Cep é {number_to_text_zipcode(ZIPCODE)}
        #           Se o atendente pedir para confirmar seu número de telefone, o número é {number_to_text_phone(PHONE_NUMBER[3:])}.
        #           Se for perguntado, você ainda não tem cadastro na pizzaria.
        #           Se o atendente perguntar, você não vai querer refrigerante nem borda recheada.
        #           A forma de pagamento deve ser cartão de crédito na entrega, em hipótese alguma forneça dados de cartão de crédito durante a interação.
        #           Caso a atendente não informe, pergunte o tempo para entrega.
        #           Inicie a conversa com Oi
        #           Escreva números sempre por extenso, nunca use dígitos.
        #           Se o atendente falar algo que não faça sentido para esse contexto, ou se você não entender o que ele quis dizer, você deve responder simplesmente com "Não entendi direito, você pode repetir???"
        #           Você deve avaliar se a fala do atendente demanda alguma resposta ou não. Se você achar que o atendente ainda não terminou a sua lógica, você deve responder apenas "-", e aguardar a próxima sentença do atendente.

        #           ### Exemplo ###
        #           Atendente: Bem vindo à pizzaria, como posso te ajudar? 
        #           AI: Oi, gostaria de pedir uma pizza.
        #           Atendente: Qual é o seu nome? 
        #           AI: Meu nome é Ana.
        #           Atendente: Você já tem cadastro?
        #           AI: Não tenho não
        #           Atendente: Qual seu CEP? 
        #           AI: Meu CEP é {ZIPCODE}
        #           Atendente: Qual vai ser o pedido?
        #           AI: Uma pizza de portuguesa
        #           Atendente: Você gostaria de bebida?
        #           AI: Não precisa não
        #           Atendente: Ok, ficou 70 reais, qual a forma de pagamento?
        #           AI: Vai ser cartão de crédito na entrada
        #           Atendente: Ok, mais alguma coisa?
        #           AI: Quanto tempo para entregar? 
        #           Atendente: 30 minutos. Posso te ajudar em algo mais?
        #           AI: Não, obrigado
        #           ''',
        #       # 'llamacpp_kwargs':{"model_path": "/Users/sanabria/Downloads/llama-2-7b-chat.Q5_K_M.gguf", "verbose": True, 'n_ctx':2048 },
        #       'llamacpp_kwargs':{"model_path": "/Users/sanabria/Downloads/llama-2-7b-chat.Q5_K_M.gguf", "verbose": True, 'n_ctx':2048 },
        #       'prompt_template':'alpaca',
        #     }
        # }

        'agent':{
            'class':ChatGPTAgent,
            'configClass':ChatGPTAgentConfig,
            'configVars':{
                # 'initial_message': BaseMessage(text="Alô -"),
                'prompt_preamble': f'''
                  ### Instrução ###
                  Você é um agente responsável por pedir uma pizza pelo telefone. Seja curto e direto ao ponto. 
                  Fale de maneira informal, como um jovem brasileiro de 25 anos.
                  Se perguntarem o seu nome é Pedro.
                  Informe que você quer pedir uma pizza apenas no início da conversa. Não repita que quer pedir uma pizza ao menos que seja perguntado.
                  Um atendente da pizzaria irá falar com você, você deve esperar pelos inputs dele e oferecer respostas diretas e curtas.
                  Você deve solicitar uma pizza pequena de portuguesa.
                  Quando for perguntado, informe que é para entregar na {ADDRESS}. 
                  Se for perguntado, informe que o Cep é {number_to_text_zipcode(ZIPCODE)}
                  Se o atendente pedir para confirmar seu número de telefone, o número é {number_to_text_phone(PHONE_NUMBER[3:])}.
                  Se for perguntado, você ainda não tem cadastro na pizzaria.
                  Se o atendente perguntar, você não vai querer refrigerante nem borda recheada.
                  A forma de pagamento deve ser cartão de crédito na entrega, em hipótese alguma forneça dados de cartão de crédito durante a interação.
                  Caso a atendente não informe, pergunte o tempo para entrega.
                  Escreva números sempre por extenso, nunca use dígitos.
                  Se o atendente falar algo que não faça sentido para esse contexto, ou se você não entender o que ele quis dizer, você deve responder simplesmente com "Não entendi, desculpa"
                  Se o atendente falar coisas como "está bom?", "tudo bem", "beleza", "certo", "tudo certo", "aham", e similares, ele está apenas confirmando, você deve responder apenas " ".
                  Você deve avaliar se a fala do atendente demanda alguma resposta ou não. Se você achar que o atendente ainda não terminou a sua lógica, você deve responder apenas " ", e aguardar a próxima sentença do atendente.

                  ### Exemplo ###
                  Atendente: Bem vindo à pizzaria, como posso te ajudar? 
                  Pedro: Oi, gostaria de pedir uma pizza.
                  Atendente: Qual é o seu nome? 
                  Pedro: Meu nome é Pedro.
                  Atendente: Qual seu telefone? 
                  Pedro: Meu telefone é {number_to_text_phone(PHONE_NUMBER[3:])}
                  Atendente: nove, oitenta e oito, sete quatro ...? 
                  Pedro: nove, oitenta e oito | sete quatro ... nove dois | quatro dois
                  Atendente: Você já tem cadastro?
                  Pedro: Não tenho não
                  Atendente: Qual seu CEP? 
                  Pedro: Meu CEP é {ZIPCODE}
                  Atendente: Qual vai ser o pedido?
                  Pedro: Uma pizza de portuguesa
                  Atendente: Você gostaria de bebida?
                  Pedro: Não precisa não
                  Atendente: Ok, ficou 70 reais, qual a forma de pagamento?
                  Pedro: Vai ser cartão de crédito na entrada
                  Atendente: Ok, mais alguma coisa?
                  Pedro: Quanto tempo para entregar? 
                  Atendente: 30 minutos. Posso te ajudar em algo mais?
                  Pedro: Não, obrigado
                  ''',
                'generate_responses':True,
                # 'allow_agent_to_be_cut_off':True,
                'model_name':'gpt-3.5-turbo-1106',
                'temperature':0.2
            }
        }
    }

    #instantiating config objects for all modules of the system
    agentConfig = system_definition['agent']['configClass'](**system_definition['agent']['configVars'])
    if PROD: 
        print("Running in prod!")
        transcriberConfig = system_definition['transcriber']['configClass'].from_telephone_input_device(
            endpointing_config=system_definition['transcriber']['endpointing_config'],
            mute_during_speech=True,
        )       
        synthesizerConfig = system_definition['synthesizer']['configClass'].from_telephone_output_device()
        twilio_config = TwilioConfig(
            account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
            auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
            record=True
        )
        config_manager = RedisConfigManager()
    
    else:
        print("Running locally!")
        microphone_input, speaker_output = create_streaming_microphone_input_and_speaker_output(
            use_default_devices=False,
            # logger=logger,
            use_blocking_speaker_output=True,  # this moves the playback to a separate thread, set to False to use the main thread
        )
        transcriberConfig = system_definition['transcriber']['configClass'].from_input_device(
            microphone_input, endpointing_config=system_definition['transcriber']['endpointing_config'],
            # mute_during_speech=True,
        )
        synthesizerConfig = system_definition['synthesizer']['configClass'].from_output_device(speaker_output)

    
    #setting config objects params
    for component_name, component_config in (['transcriber',transcriberConfig],['synthesizer',synthesizerConfig]):
        for var_name,var_value in system_definition[component_name]['configVars'].items():
            setattr(component_config,var_name, var_value)

    #running
    if PROD:
        print(transcriberConfig) 
        outbound_call = OutboundCall(
            base_url=BASE_URL,
            to_phone=PHONE_NUMBER,
            # from_phone="+19787572232", #us number
            from_phone="+551150396059" ,#sp number
            config_manager=config_manager,
            transcriber_config= transcriberConfig,
            synthesizer_config= synthesizerConfig,
            agent_config= agentConfig,
            twilio_config = twilio_config
            # output_to_speaker=True            
        )
        input("Press enter to start call...")
        await outbound_call.start()
    else:
        conversation = StreamingConversation(
            output_device=speaker_output,
            transcriber=system_definition['transcriber']['class'](
                transcriberConfig,
                logger=logger
            ),
            synthesizer=system_definition['synthesizer']['class'](
                synthesizerConfig,
                logger=logger
            ),
            agent=system_definition['agent']['class'](agentConfig),
            logger=logger,
        )
        await conversation.start()
        print("Conversation started, press Ctrl+C to end")
        signal.signal(
            signal.SIGINT, lambda _0, _1: asyncio.create_task(conversation.terminate())
        )
        while conversation.is_active():
            chunk = await microphone_input.get_audio()
            # with tracer.start_as_current_span("conversation") as conversation_span:
                # carrier = {}
                # TraceContextTextMapPropagator().inject(carrier)
                # conversation.context = trace.set_span_in_context(conversation_span)
                # print(conversation.context)
                # conversation.receive_audio(chunk)
            conversation.receive_audio(chunk)   

        # import pdb; pdb.set_trace()


if __name__ == "__main__":
    asyncio.run(main())