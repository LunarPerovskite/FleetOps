import asyncio
import websockets

async def test():
    try:
        async with websockets.connect('ws://localhost:8000/ws') as ws:
            await ws.send('{"type": "heartbeat"}')
            response = await ws.recv()
            print('Received:', response)
    except Exception as e:
        print('Error:', e)

asyncio.run(test())
