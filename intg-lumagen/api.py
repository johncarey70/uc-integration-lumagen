"""API Module."""

import asyncio

import ucapi

loop = asyncio.new_event_loop()
api = ucapi.IntegrationAPI(loop)
