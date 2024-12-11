import json
import random
import math
from channels.generic.websocket import AsyncWebsocketConsumer

class GameConsumer(AsyncWebsocketConsumer):
    # Class-level dictionary to track player states
    players = {}

    async def connect(self):
        self.room_group_name = "racing_game_room"

        # Limit to 2 players
        if len(self.channel_layer.groups.get(self.room_group_name, [])) >= 2:
            await self.close()
            return

        # Assign a unique player ID
        self.player_id = len(self.players) + 1

        # Initial player state
        initial_position = self.get_initial_position(self.player_id)
        self.players[self.player_id] = {
            'x': initial_position['x'],
            'y': initial_position['y'],
            'angle': 0,
            'speed': 0,
            'controls': {
                'ArrowUp': False, 'ArrowDown': False, 
                'ArrowLeft': False, 'ArrowRight': False,
                'w': False, 's': False, 
                'a': False, 'd': False
            }
        }

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Notify all players about new connection
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "notify_player_joined",  # Changed this line
                "player_id": self.player_id
            }
        )

    # Add this method to handle player joined notification
    async def notify_player_joined(self, event):
        await self.send(text_data=json.dumps({
            "type": "player_joined",
            "player_id": event['player_id']
        }))

    def get_initial_position(self, player_id):
        # Define initial positions for players
        center_x, center_y = 400, 400
        track_points = [
            {'x': center_x - 200, 'y': center_y - 300},
            {'x': center_x + 250, 'y': center_y - 250}
        ]
        return track_points[player_id - 1]

    async def disconnect(self, close_code):
        # Check if player_id exists before trying to use it
        if hasattr(self, 'player_id'):
            # Remove player from tracking
            if self.player_id in self.players:
                del self.players[self.player_id]

            await self.channel_layer.group_discard(
                self.room_group_name, 
                self.channel_name
            )

            # Notify other players
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "notify_player_left",  # Changed this line
                    "player_id": self.player_id
                }
            )

    # Add this method to handle player left notification
    async def notify_player_left(self, event):
        await self.send(text_data=json.dumps({
            "type": "player_left",
            "player_id": event['player_id']
        }))

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)

            if data["type"] == "player_input" and hasattr(self, 'player_id'):
                # Update player controls
                self.players[self.player_id]['controls'] = data.get(f'player{self.player_id}', {})

                # Simulate game state update
                updated_players = self.update_game_state()

                # Broadcast updated game state
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "game_event",
                        "player1": updated_players.get(1, {}),
                        "player2": updated_players.get(2, {})
                    }
                )

        except json.JSONDecodeError:
            print("Invalid JSON received")

    def update_game_state(self):
        # Basic physics simulation
        for player_id, player in self.players.items():
            controls = player['controls']
            
            # Safely check controls with .get() method
            # Use False as default if key doesn't exist
            if controls.get('ArrowUp', False) or controls.get('w', False):
                player['speed'] = min(player['speed'] + 0.1, 5)
            if controls.get('ArrowDown', False) or controls.get('s', False):
                player['speed'] = max(player['speed'] - 0.1, -2.5)
            
            if controls.get('ArrowLeft', False) or controls.get('a', False):
                player['angle'] -= 0.05 * (1 if player['speed'] != 0 else 0)
            if controls.get('ArrowRight', False) or controls.get('d', False):
                player['angle'] += 0.05 * (1 if player['speed'] != 0 else 0)

            # Move car
            player['x'] += math.cos(player['angle']) * player['speed']
            player['y'] += math.sin(player['angle']) * player['speed']
            
            # Gradual deceleration
            player['speed'] *= 0.98

        return self.players

    async def game_event(self, event):
        await self.send(text_data=json.dumps({
            "type": "game_event",
            "player1": event["player1"],
            "player2": event["player2"],
        }))