import json
from channels.generic.websocket import AsyncWebsocketConsumer

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "racing_game_room"
        
        # Limit connections if needed
        if len(self.channel_layer.groups.get(self.room_group_name, [])) >= 2:
            await self.close()
            return
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print(f"WebSocket connection established: {self.channel_name}")

        # Notify other players of new connection
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "player_joined",
                "player": self.channel_name
            }
        )
        
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Notify other players of disconnection
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "player_left",
                "player": self.channel_name
            }
        )
        
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            
            # Broadcast received data to all players
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "game_event",
                    "data": data,
                }
            )
        except json.JSONDecodeError:
            print("Invalid JSON received")
        
    async def game_event(self, event):
        await self.send(text_data=json.dumps(event["data"]))
    
    async def player_joined(self, event):
        await self.send(text_data=json.dumps({
            "type": "player_joined",
            "player": event['player']
        }))
    
    async def player_left(self, event):
        await self.send(text_data=json.dumps({
            "type": "player_left",
            "player": event['player']
        }))