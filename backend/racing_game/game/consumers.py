import json
from channels.generic.websocket import AsyncWebsocketConsumer

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "racing_game_room"
        
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print("WebSocket connection established.")

        
        
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        
        # Broadcast received data to all players
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "game_event",
                "data": data,
            }
        )
        
    async def game_event(self, event):
        await self.send(text_data=json.dumps(event["data"]))