from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter
from opentelemetry.sdk.resources import Resource
from collections import defaultdict


class PrintDurationSpanExporter(SpanExporter):
    def __init__(self):
        super().__init__()
        self.spans = defaultdict(list)

    def export(self, spans):
        for span in spans:
            duration_ns = span.end_time - span.start_time
            duration_s = duration_ns / 1e9
            self.spans[span.name].append(duration_s)

    def shutdown(self):
        for name, durations in self.spans.items():
            print(f"{name}: {sum(durations) / len(durations)}")


trace.set_tracer_provider(TracerProvider(resource=Resource.create({})))
trace.get_tracer_provider().add_span_processor(
    SimpleSpanProcessor(PrintDurationSpanExporter())
)



import asyncio
import logging
import signal
import vocode
import os
from dotenv import load_dotenv

load_dotenv()

# these can also be set as environment variables
vocode.setenv(
    OPENAI_API_KEY=os.getenv('OPENAI_API_KEY'),
    AZURE_SPEECH_KEY=os.getenv('AZURE_SPEECH_KEY'),
    AZURE_SPEECH_REGION=os.getenv('AZURE_SPEECH_REGION'),
    DEEPGRAM_API_KEY=os.getenv('DEEPGRAM_API_KEY'),
    ELEVEN_LABS_API_KEY=os.getenv('ELEVEN_LABS_API_KEY')
)

from vocode.streaming.streaming_conversation import StreamingConversation
from vocode.helpers import create_streaming_microphone_input_and_speaker_output
from vocode.streaming.transcriber import *
from vocode.streaming.agent import *
from vocode.streaming.synthesizer import *
from vocode.streaming.models.transcriber import *
from vocode.streaming.models.agent import *
from vocode.streaming.models.synthesizer import *
from vocode.streaming.models.message import BaseMessage


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def main():
    (
        microphone_input,
        speaker_output,
    ) = create_streaming_microphone_input_and_speaker_output(
        use_default_devices=True,
        # logger=logger,
        use_blocking_speaker_output=False,  # this moves the playback to a separate thread, set to False to use the main thread
    )

    synthesizerConfig = AzureSynthesizerConfig.from_output_device(speaker_output)
    synthesizerConfig.voice_name = "pt-BR-AntonioNeural"
    synthesizerConfig.language_code = "pt"
    synthesizer = AzureSynthesizer(
            synthesizerConfig,
            logger=logger
        )


    # synthesizerConfig = ElevenLabsSynthesizerConfig.from_output_device(speaker_output)
    # synthesizerConfig.model_id = 'eleven_multilingual_v2'
    # # synthesizerConfig.voice_id = 'pNInz6obpgDQGcFmaJgB' 
    # synthesizerConfig.voice_id = 'NGS0ZsC7j4t4dCWbPdgO' # Dyego, portugues
    # synthesizer = ElevenLabsSynthesizer(
    #     synthesizerConfig,
    #     logger=logger
    # )


    transcriberConfig = DeepgramTranscriberConfig.from_input_device(
                microphone_input, endpointing_config=PunctuationEndpointingConfig(),
                # mute_during_speech=True,
            )
    transcriberConfig.language = "pt-BR"
    transcriberConfig.model="nova-2"

    conversation = StreamingConversation(
        output_device=speaker_output,
        transcriber=DeepgramTranscriber(
            transcriberConfig,
            logger=logger
        ),
        agent=ChatGPTAgent(
            ChatGPTAgentConfig(
                initial_message=BaseMessage(text="Alô -"),
                prompt_preamble='''Você é um agente responsável por pedir uma pizza pelo telefone. 
                  Um atendente da pizzaria irá falar com você, você deve oferecer respostas diretas e curtas.
                  Você deve solicitar uma pizza de portuguesa, para entregar na Rua da Consolação 867.
                  Se o atendente pedir para confirmar seu número de telefone, o número é 11988749242.
                  Ao final, você deve perguntar o preço da pizza e o tempo para entrega.''',
                #   send_filler_audio=True,
                #   allow_agent_to_be_cut_off=True,
                  model_name='gpt-3.5-turbo-1106',
                  temperature=0.2,
                  logger=logger
            )
        ),
        synthesizer=synthesizer,
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