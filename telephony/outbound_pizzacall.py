import os, inspect
from dotenv import load_dotenv

load_dotenv('/Users/sanabria/Desktop/code/ai_callcenter/.env')

from vocode.streaming.agent.chat_gpt_agent import ChatGPTAgent
from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.models.transcriber import (
    DeepgramTranscriberConfig,
    PunctuationEndpointingConfig,
)
from vocode.streaming.models.synthesizer import AzureSynthesizerConfig
from vocode.streaming.telephony.conversation.outbound_call import OutboundCall
from vocode.streaming.telephony.config_manager.redis_config_manager import (
    RedisConfigManager,
)
from vocode.streaming.models.telephony import TwilioConfig


BASE_URL = os.environ["BASE_URL"]

from vocode.helpers import create_streaming_microphone_input_and_speaker_output


async def main():
    config_manager = RedisConfigManager()
    
    synthesizerConfig = AzureSynthesizerConfig.from_telephone_output_device()
    synthesizerConfig.voice_name = "pt-BR-DonatoNeural"
    synthesizerConfig.language_code = "pt-BR"

    transcriberConfig = DeepgramTranscriberConfig.from_telephone_input_device(
        endpointing_config=PunctuationEndpointingConfig(),
        mute_during_speech=True,
    )
    transcriberConfig.language = "pt-BR"
    transcriberConfig.model="nova-2"

    twilio_config = TwilioConfig(
        account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
        auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
        record=True,
    )

    outbound_call = OutboundCall(
        base_url=BASE_URL,
        twilio_config=twilio_config,
        to_phone="+5512982252000", #sana
        # to_phone="+5511988749242", #andré
        from_phone="+19787572232",
        config_manager=config_manager,
        transcriber_config= transcriberConfig,
        synthesizer_config= synthesizerConfig,
        agent_config=ChatGPTAgentConfig(
            initial_message=BaseMessage(text="Alô -"),
            prompt_preamble='''Você é um agente responsável por pedir uma pizza pelo telefone. Seja gentil nas interações. 
              Um atendente da pizzaria irá falar com você, você deve esperar pelos inputs dele e oferecer respostas diretas e curtas.
              Você deve solicitar uma pizza de portuguesa. Quando for perguntado, informe que é para entregar na Rua da Consolação 867. Se for perguntado, informe que o Cep é 05417000
              Se o atendente pedir para confirmar seu número de telefone, o número é 11988749242.
              Se for perguntado, você ainda não tem cadastro na pizzaria.
              Se o atendente perguntar você não vai querer refrigerante nem borda recheada.
              A forma de pagamento deve ser cartão de crédito na entrega, em hipótese alguma forneça dados de cartão de crédito durante a interação.
              Ao final, você deve perguntar o preço da pizza e o tempo para entrega.''',
            generate_responses=True,
            allow_agent_to_be_cut_off=True,
            model_name='gpt-3.5-turbo-1106',
            temperature=0.2
          # output_to_speaker=True
        )
        
    )

    input("Press enter to start call...")
    await outbound_call.start()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
