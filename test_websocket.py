import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/api/pipeline/ws"
    try:
        async with websockets.connect(uri) as websocket:
            print("WebSocket connected successfully")
            
            # Send a test message
            await websocket.send("test message")
            print("Sent test message")
            
            # Receive response
            response = await websocket.recv()
            print(f"Received: {response}")
            
            # Wait for state updates
            for i in range(3):
                message = await websocket.recv()
                data = json.loads(message)
                print(f"State update {i+1}: {data.get('status', 'unknown')}")
            
            print("WebSocket test completed successfully")
            
    except Exception as e:
        print(f"WebSocket test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
