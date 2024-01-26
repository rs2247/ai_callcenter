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

load_dotenv()

PROD = (os.getenv('PROD').lower()=='true')
if PROD:
    try:
        from vocode.streaming.telephony.conversation.outbound_call import OutboundCall
        from vocode.streaming.telephony.config_manager.redis_config_manager import (
            RedisConfigManager,
        )
        BASE_URL = os.environ["BASE_URL"]
        PHONE_NUMBER = os.environ["PHONE_NUMBER"]
    
    except:
        raise Exception("Error loading libraries necessary for phone calls. Make sure you are using poetry to run the script to avoid dependency errors")



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


# trace.set_tracer_provider(TracerProvider(resource=Resource.create({})))
# trace.get_tracer_provider().add_span_processor(
#     SimpleSpanProcessor(PrintDurationSpanExporter())
# )


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


async def main():
    
    system_definition = {
        'transcriber':{
            'class':DeepgramTranscriber,
            'configClass':DeepgramTranscriberConfig,
            'endpointing_config':TimeEndpointingConfig(),
            # 'endpointing_config':PunctuationEndpointingConfig()
            'configVars':{
                'language':"pt-BR",
                'model':"nova-2"
            }
        },
        'synthesizer':{
            'class':AzureSynthesizer,
            'configClass':AzureSynthesizerConfig,
            'configVars':{
                'voice_name': 'pt-BR-DonatoNeural',
                'language_code':'pt-BR'
            }
        },
        'agent':{
            'class':ChatGPTAgent,
            'configClass':ChatGPTAgentConfig,
            'configVars':{
                # 'initial_message': BaseMessage(text="Alô -"),
                'prompt_preamble': '''
                  ### Instrução ###
                  Você é um agente responsável por pedir uma pizza pelo telefone. Seja curto e direto ao ponto. 
                  Um atendente da pizzaria irá falar com você, você deve esperar pelos inputs dele e oferecer respostas diretas e curtas.
                  Você deve solicitar uma pizza pequena de portuguesa.
                  Quando for perguntado, informe que é para entregar na Rua da Consolação 867, apartamento 28. 
                  Se for perguntado, informe que o Cep é 05417000
                  Se o atendente pedir para confirmar seu número de telefone, o número é 11988749242.
                  Se for perguntado, você ainda não tem cadastro na pizzaria.
                  Se o atendente perguntar, você não vai querer refrigerante nem borda recheada.
                  A forma de pagamento deve ser cartão de crédito na entrega, em hipótese alguma forneça dados de cartão de crédito durante a interação.
                  Caso a atendente não informe, pergunte o tempo para entrega.
                  Inicie a conversa com Oi

                  ### Exemplo ###
                  Atendente: Bem vindo à pizzaria, como posso te ajudar? 
                  AI: Oi, gostaria de pedir uma pizza.
                  Atendente: Você já possui cadastro?
                  AI: Não tenho não
                  Atendente: Qual seu CEP? 
                  AI: Meu CEP é 05417000
                  Atendente: Qual vai ser o pedido?
                  AI: Uma pizza de portuguesa
                  Atendente: Você gostaria de bebida?
                  AI: Não precisa não
                  Atendente: Ok, ficou 70 reais, qual a forma de pagamento?
                  AI: Vai ser cartão de crédito na entrada
                  Atendente: Ok, mais alguma coisa?
                  AI: Quanto tempo para entregar? 
                  Atendente: 30 minutos. Posso te ajudar em algo mais?
                  AI: Não, obrigado

                  ''',
                'generate_responses':True,
                'allow_agent_to_be_cut_off':True,
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
            mute_during_speech=True,
        )
        synthesizerConfig = system_definition['synthesizer']['configClass'].from_output_device(speaker_output)

    
    #setting config objects params
    for component_name, component_config in (['transcriber',transcriberConfig],['synthesizer',synthesizerConfig]):
        for var_name,var_value in system_definition[component_name]['configVars'].items():
            setattr(component_config,var_name, var_value)
        print(component_config,"\n")

    #running
    if PROD:
        outbound_call = OutboundCall(
            base_url=BASE_URL,
            to_phone=PHONE_NUMBER,
            from_phone="+19787572232",
            config_manager=config_manager,
            transcriber_config= transcriberConfig,
            synthesizer_config= synthesizerConfig,
            agent_config= agentConfig
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
            conversation.receive_audio(chunk)


if __name__ == "__main__":
    asyncio.run(main())