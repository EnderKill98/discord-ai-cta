'''
This lib attempts to communitate with gradio and fake inputs into the
chat of the text-generation-webui in chat mode and stream the output.

The names for functions are assumed, I have not searched for documentation
on this and simply reversed the recorded websocket traffic from my browser.

A lot of values are still hard copied into here and should be made configurable
at some point (or request state from webui). Using the webui at the same time
may or may not mess up state as they seem somewhat seperated by the different
session hashes.

TODO: Add an option to use the proper streaming chat api. Currently using this
      hack because for some reason I can't get the api to run on my system.
'''

import json
import logging
import os
import random
import websockets
from bs4 import BeautifulSoup
import html2text

logger = logging.getLogger("gradio_chat")

GRADIO_QUEUE_URL = os.environ['GRADIO_WS_QUEUE_JOIN_URL']
gradio_session_hash = ''.join([ random.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(11) ])

async def configure(your_name="You"):
    '''If not run before send_chat, it won't work.'''
    gradio_fn_index = 51
    async with websockets.connect(GRADIO_QUEUE_URL, ping_interval=None) as websocket:
        while True:
            incoming_data = await websocket.recv()
            incoming_data = json.loads(incoming_data)
            #logger.debug("Got:", incoming_data)

            match incoming_data['msg']:
                case 'send_hash':
                    await websocket.send(json.dumps({ "fn_index": gradio_fn_index, "session_hash": gradio_session_hash }))
                    logger.debug("Answered to send_hash:")
                case 'send_data':
                    await websocket.send(json.dumps({
                        "fn_index": gradio_fn_index,
                        "data": [200,-1,0.72,0.73,0,1,1.1,1,0,0,True,0,1,1,False,True,False,2048,"",True,"NovelAI-Storywriter",True,your_name,"Kitten","*Kitten purrs* meow!","Kitten's Persona: Kitten is a cute cat. But never in a sexual or otherwise NSFW way! Politics, harming someone or one self are not topics that Kitten talks about.\nScenario: Kitten is a cute cat that wants love.\n\nKitten is home to a Discord server called \"Server Scanning Inc\" or short \"SSI\" which likes to scan for Minecraft servers and toy around with Minecraft exploits and hacks. The famous Youtuber LiveOverflow is also on this Discord Server who does hacking related Videos and recently made a Minecraft Series about hacking in the context of Minecraft.\n\nThe term Cat should never be used as cats are referred to as Cta on this discord server. Honbra and Ender_Schesi are bottoms, no matter what they say. EnderKill98 owns Kitten.\n\n<START>\nYou: Hello!\nKitten: *Kitten looks up at user and purrs* meow 😺",2048,1,False,"chat","None","Kitten","EnderKill98","Assistant","This is a conversation with your Assistant. The Assistant is very helpful and is eager to chat with you and answer your questions.","","cai-chat",0,True,False,False,False,False,"None","None","llama",0,15000],
                        "event_data": None,
                        "session_hash": gradio_session_hash,
                    }))
                    logger.debug("Answered to send_data")
                case "process_starts":
                    logger.debug("Process Starts")
                case "process_generating":
                    logger.debug("Process Generating")
                case "process_completed":
                    logger.debug("Process Completed")
                    await websocket.close()
                    return
                case "estimation":
                    logger.debug("Got estimation")
                    pass
                case _:
                    logger.warning(f"Received unknown message of type {incoming_data['msg']}")
                    logger.debug(f"Full response was: {incoming_data}")

async def send_chat(chat_message):
    gradio_fn_index = 52 # Likely something like "component chat input"
    async with websockets.connect(GRADIO_QUEUE_URL, ping_interval=None) as websocket:
        while True:
            incoming_data = await websocket.recv()
            incoming_data = json.loads(incoming_data)
            #logger.debug("Got:", incoming_data)

            match incoming_data['msg']:
                case 'send_hash':
                    await websocket.send(json.dumps({ "fn_index": gradio_fn_index, "session_hash": gradio_session_hash }))
                    logger.debug("Answered to send_hash:")
                case 'send_data':
                    await websocket.send(json.dumps({ "fn_index": gradio_fn_index, "session_hash": gradio_session_hash, "data": [ chat_message ], "event_data": None }))
                    logger.debug("Answered to send_data")
                case "process_starts":
                    logger.debug("Process Starts")
                case "process_generating":
                    logger.debug("Process Generating")
                case "process_completed":
                    logger.debug("Process Completed")
                    await websocket.close()
                    return
                case "estimation":
                    logger.debug("Got estimation")
                    pass
                case _:
                    logger.warning(f"Received unknown message of type {incoming_data['msg']}")
                    logger.debug(f"Full response was: {incoming_data}")

async def read_chat():
    gradio_fn_index = 53 # Likely something like "component chat window / messages"
    async with websockets.connect(GRADIO_QUEUE_URL, ping_interval=None) as websocket:
        while True:
            incoming_data = await websocket.recv()
            incoming_data = json.loads(incoming_data)
            #logger.debug("Got:", incoming_data)

            match incoming_data['msg']:
                case 'send_hash':
                    await websocket.send(json.dumps({ "fn_index": gradio_fn_index, "session_hash": gradio_session_hash }))
                    logger.debug("Answered to send_hash:")
                case 'send_data':
                    await websocket.send(json.dumps({ "fn_index": gradio_fn_index, "session_hash": gradio_session_hash, "data": [ None, None ], "event_data": None }))
                    logger.debug("Answered to send_data")
                case "process_starts":
                    logger.debug("Process Starts")
                case "process_generating":
                    logger.debug("Process Generating...")
                    yield incoming_data["output"]["data"][0], False
                case "process_completed":
                    logger.debug("Process Completed")
                    yield incoming_data["output"]["data"][0], True
                    await websocket.close()
                    return
                case "estimation":
                    logger.debug("Got estimation")
                    pass
                case _:
                    logger.warning(f"Received unknown message of type {incoming_data['msg']}")
                    logger.debug(f"Full response was: {incoming_data}")


async def pre_set_context():
    gradio_fn_index = 76
    async with websockets.connect(GRADIO_QUEUE_URL, ping_interval=None) as websocket:
        while True:
            incoming_data = await websocket.recv()
            incoming_data = json.loads(incoming_data)
            #logger.debug("Got:", incoming_data)

            match incoming_data['msg']:
                case 'send_hash':
                    await websocket.send(json.dumps({ "fn_index": gradio_fn_index, "session_hash": gradio_session_hash }))
                    logger.debug("Answered to send_hash:")
                case 'send_data':
                    await websocket.send(json.dumps({ "fn_index": gradio_fn_index, "data": [], "event_data": None, "session_hash": gradio_session_hash }))
                    logger.debug("Answered to send_data")
                case "process_starts":
                    logger.debug("Process Starts")
                case "process_generating":
                    logger.debug("Process Generating")
                case "process_completed":
                    logger.debug("Process Completed")
                    await websocket.close()
                    return
                case "estimation":
                    logger.debug("Got estimation")
                    pass
                case _:
                    logger.warning(f"Received unknown message of type {incoming_data['msg']}")
                    logger.debug(f"Full response was: {incoming_data}")

async def set_context(first_message_from_bot="*Kitten purrs* meow!"):
    '''Follow up to clear_history. May do the actual clear'''
    gradio_fn_index = 77
    async with websockets.connect(GRADIO_QUEUE_URL, ping_interval=None) as websocket:
        while True:
            incoming_data = await websocket.recv()
            incoming_data = json.loads(incoming_data)
            #logger.debug("Got:", incoming_data)

            match incoming_data['msg']:
                case 'send_hash':
                    await websocket.send(json.dumps({ "fn_index": gradio_fn_index, "session_hash": gradio_session_hash }))
                    logger.debug("Answered to send_hash:")
                case 'send_data':
                    await websocket.send(json.dumps({
                        "fn_index": gradio_fn_index,
                        "data": [first_message_from_bot, "chat"],
                        "event_data": None,
                        "session_hash": gradio_session_hash,
                    }))
                    logger.debug("Answered to send_data")
                case "process_starts":
                    logger.debug("Process Starts")
                case "process_generating":
                    logger.debug("Process Generating")
                case "process_completed":
                    logger.debug("Process Completed")
                    await websocket.close()
                    return
                case "estimation":
                    logger.debug("Got estimation")
                    pass
                case _:
                    logger.warning(f"Received unknown message of type {incoming_data['msg']}")
                    logger.debug(f"Full response was: {incoming_data}")

async def pre_stop(your_name="You"):
    '''TODO: Fix'''
    gradio_fn_index = 81
    async with websockets.connect(GRADIO_QUEUE_URL, ping_interval=None) as websocket:
        while True:
            incoming_data = await websocket.recv()
            incoming_data = json.loads(incoming_data)
            #logger.debug("Got:", incoming_data)

            match incoming_data['msg']:
                case 'send_hash':
                    await websocket.send(json.dumps({ "fn_index": gradio_fn_index, "session_hash": gradio_session_hash }))
                    logger.debug("Answered to send_hash:")
                case 'send_data':
                    await websocket.send(json.dumps({
                        "fn_index": gradio_fn_index,
                        "data": [your_name, "Kitten", "chat", "cai-chat"],
                        "event_data": None,
                        "session_hash": gradio_session_hash,
                    }))
                    logger.debug("Answered to send_data")
                case "process_starts":
                    logger.debug("Process Starts")
                case "process_generating":
                    logger.debug("Process Generating")
                case "process_completed":
                    logger.debug("Process Completed")
                    await websocket.close()
                    return
                case "estimation":
                    logger.debug("Got estimation")
                    pass
                case _:
                    logger.warning(f"Received unknown message of type {incoming_data['msg']}")
                    logger.debug(f"Full response was: {incoming_data}")

async def stop():
    '''TODO: Fix'''
    gradio_fn_index = 54
    async with websockets.connect(GRADIO_QUEUE_URL, ping_interval=None) as websocket:
        while True:
            incoming_data = await websocket.recv()
            incoming_data = json.loads(incoming_data)
            #logger.debug("Got:", incoming_data)

            match incoming_data['msg']:
                case 'send_hash':
                    await websocket.send(json.dumps({ "fn_index": gradio_fn_index, "session_hash": gradio_session_hash }))
                    logger.debug("Answered to send_hash:")
                case 'send_data':
                    await websocket.send(json.dumps({
                        "fn_index": gradio_fn_index,
                        "data": [ "chat" ],
                        "event_data": None,
                        "session_hash": gradio_session_hash,
                    }))
                    logger.debug("Answered to send_data")
                case "process_starts":
                    logger.debug("Process Starts")
                case "process_generating":
                    logger.debug("Process Generating")
                case "process_completed":
                    logger.debug("Process Completed")
                    await websocket.close()
                    return
                case "estimation":
                    logger.debug("Got estimation")
                    pass
                case _:
                    logger.warning(f"Received unknown message of type {incoming_data['msg']}")
                    logger.debug(f"Full response was: {incoming_data}")

def find_last_message(html_text):
    soup = BeautifulSoup(html_text, features="lxml")
    html_content = None
    for el in soup.find_all("div", { 'class': 'message' }):
        #content = soup.find("div", { 'class': 'message-body' }).get_text()
        html_content = str(soup.find("div", { 'class': 'message-body' }))
    return markdownify(html_content).strip()

def markdownify(html_text):
    # https://stackoverflow.com/q/45034227
    h = html2text.HTML2Text()
    # Options to transform URL into absolute links
    h.body_width = 0
    h.protect_links = True
    h.wrap_links = False
    #h.baseurl = url
    md_text = h.handle(html_text)
    return md_text

async def configure_send_and_receive(chat_message, your_name="You"):
    logger.debug(f"configure send and receive for message {repr(chat_message)}...")
    logger.debug("configure() start")
    await configure(your_name)
    logger.debug("configure() end")

    logger.debug("send_chat() start")
    await send_chat(chat_message)
    logger.debug("send_chat() end")

    logger.debug("read_chat() start")
    async for (output, completed) in read_chat():
        yield find_last_message(output), completed
    logger.debug("read_chat() end")
