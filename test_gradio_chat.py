#!/usr/bin/env python3

import asyncio
import logging
from rich.logging import RichHandler
import sys

import gradio_chat

if len(sys.argv) != 2:
    print("Usage: %s <Chat-Message>", file=sys.stderr)
    exit(1)

FORMAT = "%(name)-16s | %(message)s"
logging.basicConfig(level="NOTSET", format=FORMAT, datefmt="%X", handlers=[RichHandler()])
logger = logging.getLogger("Test")
logging.getLogger("websockets").setLevel(logging.INFO)
logging.getLogger("gradio_chat").setLevel(logging.DEBUG)

async def do_stuff():
    logger.info("Running...")
    async for (output, completed) in gradio_chat.configure_send_and_receive(sys.argv[1]):
        logger.info("» " + output)
        if completed:
            logger.info("Completed!")
    logger.info("Done")

asyncio.get_event_loop().run_until_complete(do_stuff())
