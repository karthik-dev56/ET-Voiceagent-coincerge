from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import AgentSession, Agent, RoomInputOptions,ChatContext
# from livekit.plugins.google.beta import realtime
from livekit.plugins import (
    openai,
    murf,
    noise_cancellation,
    google,
    deepgram

)
# from mcp_client import MCPServerSse
# from mcp_client.agent_tools import MCPToolsIntegration
from tools import submit_user_profile, call_emergency
from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION
from mem0 import AsyncMemoryClient
import json
import logging
import os
import re

load_dotenv()

class Assistant(Agent):
    def __init__(self, chat_ctx=None) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=openai.LLM(
                model="deepseek-chat",
                # voice="Aoede",
                base_url="https://api.deepseek.com",
                temperature=0.2,
                # max_output_tokens=200
            ),
            stt=deepgram.STT(
                model="nova-3",
                language="en",
            ),
            tts=murf.TTS(
                voice="hi-IN-Sunaina",
                style="Conversational",
                speed=0.7,
                pitch=0
            ),
            tools=[submit_user_profile, call_emergency],
            chat_ctx=chat_ctx
        )


def extract_user_name(chat_context):
    """Extract user's name from chat context"""
    for item in chat_context.items:
        if item.type == 'message' and item.role == 'user':
            content = ''.join(item.content) if isinstance(item.content, list) else str(item.content)
            # Look for patterns like "My name is John", "I'm Sarah", "Call me Mike", etc.
            name_patterns = [
                r"(?:my name is|i'm|i am|call me|it's)\s+([a-zA-Z]+)",
                r"^([a-zA-Z]+)$",  # Single word that could be a name
                r"name\s*[:=]\s*([a-zA-Z]+)",
            ]

            for pattern in name_patterns:
                match = re.search(pattern, content.lower())
                if match:
                    name = match.group(1).strip().capitalize()
                    # Verify it's likely a name (not common words)
                    if len(name) > 1 and name not in ['yes', 'no', 'ok', 'sure', 'maybe', 'good', 'fine']:
                        return name
    return None

async def shutdown_hook(chat_ctx: ChatContext, mem0: AsyncMemoryClient, memory_str: str):
    logging.info("Shutting down, saving chat context to memory...")

    # Extract user name from chat context
    user_name = extract_user_name(chat_ctx)
    if not user_name:
        user_name = "unknown_user"  # Fallback

    user_id = f"{user_name.lower()}_et_user"

    messages_formatted = []
    logging.info(f"Chat context messages: {chat_ctx.items}")

    for item in chat_ctx.items:
        if item.type != 'message':
            continue
        content_str = ''.join(item.content) if isinstance(item.content, list) else str(item.content)

        if memory_str and memory_str in content_str:
            continue
        if item.role in ['user', 'assistant']:
            messages_formatted.append({
                "role": item.role,
                "content": content_str.strip()
            })

    logging.info(f"Formatted messages to add to memory for user {user_id}: {messages_formatted}")
    await mem0.add(messages_formatted, user_id=user_id)
    logging.info(f"Chat context saved to memory for user: {user_id}")

async def entrypoint(ctx: agents.JobContext):

    session = AgentSession()
    mem0 = AsyncMemoryClient()

    # Start with no user-specific memory since we need to ask for name first
    initial_ctx = ChatContext()
    memory_str = ''

    # Initial greeting that asks for name
    initial_ctx.add_message(
        role="assistant",
        content="Starting fresh conversation. Ask for user's name first to personalize the experience."
    )


    # mcp_server = MCPServerSse(
    #     params={"url": os.environ.get("N8N_MCP_SERVER_URL")},
    #     cache_tools_list=True,
    #     name="SSE MCP Server"
    # )

    # agent = await MCPToolsIntegration.create_agent_with_tools(
    #     agent_class=Assistant, agent_kwargs={"chat_ctx": initial_ctx},
    #     mcp_servers=[mcp_server]
    # )


    await session.start(
        room = ctx.room,
        agent = Assistant(chat_ctx=initial_ctx),
        room_input_options = RoomInputOptions(
            # video_enabled = True,
            noise_cancellation =  noise_cancellation.BVC()
        )
    )

    await ctx.connect()

    

    await session.generate_reply(
        instructions = SESSION_INSTRUCTION
    )

    ctx.add_shutdown_callback(lambda:shutdown_hook(session._agent.chat_ctx,mem0,memory_str))

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
