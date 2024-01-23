import os
from dotenv import load_dotenv

load_dotenv('/Users/sanabria/Desktop/code/ai_callcenter/.env')
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.models.agent import AgentConfig, AgentType, ChatGPTAgentConfig
from vocode.streaming.telephony.conversation.outbound_call import OutboundCall
from vocode.streaming.telephony.config_manager.redis_config_manager import (
    RedisConfigManager,
)

from speller_agent import SpellerAgentConfig

BASE_URL = os.environ["BASE_URL"]


async def main():
    config_manager = RedisConfigManager()

    outbound_call = OutboundCall(
        base_url=BASE_URL,
        # to_phone="+15555555555",
        to_phone="+5512982252000",
        from_phone="+19787572232",
        config_manager=config_manager,
        # agent_config=SpellerAgentConfig(generate_responses=False,type=AgentType.CHAT_GPT),
        agent_config=ChatGPTAgentConfig(
            initial_message=BaseMessage(text="What up"),
            prompt_preamble="Have a pleasant conversation about life",
            generate_responses=True,
        )
    )

    input("Press enter to start call...")
    await outbound_call.start()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
