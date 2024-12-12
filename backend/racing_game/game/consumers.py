import json
import random
import math
from channels.generic.websocket import AsyncWebsocketConsumer


class GameConsumer(AsyncWebsocketConsumer):
   
    players = {}
    
   
    CENTER_X = 400
    CENTER_Y = 400
    OUTER_TRACK_RADIUS = 400
    INNER_TRACK_RADIUS = 250
    
    async def connect(self):
        self.room_group_name = "racing_game_room"

        # 2 players race onlyy
        if len(self.channel_layer.groups.get(self.room_group_name, [])) >= 2:
            await self.close()
            return

    #    player id
        self.player_id = len(self.players) + 1

        # Initial player state
        initial_position = self.get_initial_position(self.player_id)
        self.players[self.player_id] = {
            'x': initial_position['x'],
            'y': initial_position['y'],
            'angle': 0,
            'speed': 0,
            'maxSpeed': 5,
            'width': 60,
            'height': 30,
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
                "type": "notify_player_joined",
                "player_id": self.player_id
            }
        )

    # 
    async def notify_player_joined(self, event):
        await self.send(text_data=json.dumps({
            "type": "player_joined",
            "player_id": event['player_id']
        }))

    def get_initial_position(self, player_id):
        
        center_x, center_y = 400, 400
        track_points = [
            {'x': center_x - 200, 'y': center_y - 300},
            {'x': center_x + 250, 'y': center_y - 250}
        ]
        return track_points[player_id - 1]

    async def disconnect(self, close_code):
       
        if hasattr(self, 'player_id'):
            # Remove player from tracking
            if self.player_id in self.players:
                del self.players[self.player_id]

            await self.channel_layer.group_discard(
                self.room_group_name, 
                self.channel_name
            )

          
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "notify_player_left",  # Changed this line
                    "player_id": self.player_id
                }
            )

    async def notify_player_left(self, event):
        await self.send(text_data=json.dumps({
            "type": "player_left",
            "player_id": event['player_id']
        }))

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)

            if data["type"] == "player_input" and hasattr(self, 'player_id'):
               
                self.players[self.player_id]['controls'] = data.get(f'player{self.player_id}', {})

                
                updated_players = self.update_game_state()

                # Broadcast updated game state
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "send_game_event",
                        "player1": updated_players.get(1, {}),
                        "player2": updated_players.get(2, {})
                    }
                )

        except json.JSONDecodeError:
            print("Invalid JSON received")

    async def send_game_event(self, event):
        await self.send(text_data=json.dumps({
            "type": "game_event",
            "player1": event.get("player1", {}),
            "player2": event.get("player2", {})
        }))

    def update_game_state(self):
        for player_id, player in self.players.items():
            original_x = player['x']
            original_y = player['y']
            original_speed = player['speed']
            
            controls = player['controls']
            
            # Acceleration and deceleration
            if controls.get('ArrowUp', False) or controls.get('w', False):
                player['speed'] = min(player['speed'] + 0.1, player['maxSpeed'])
            if controls.get('ArrowDown', False) or controls.get('s', False):
                player['speed'] = max(player['speed'] - 0.1, -2.5)
            
            # Steering
            if controls.get('ArrowLeft', False) or controls.get('a', False):
                player['angle'] -= 0.05 * (1 if player['speed'] != 0 else 0)
            if controls.get('ArrowRight', False) or controls.get('d', False):
                player['angle'] += 0.05 * (1 if player['speed'] != 0 else 0)

            # Move car
            new_x = player['x'] + math.cos(player['angle']) * player['speed']
            new_y = player['y'] + math.sin(player['angle']) * player['speed']
            
            # Track Collision Detection
            track_collision = self.check_track_collision({'x': new_x, 'y': new_y, 'width': player['width'], 'height': player['height']})
            
            if not track_collision:
                player['x'] = new_x
                player['y'] = new_y
            else:
                # More realistic track collision response
                player['speed'] *= -0.3  
                
            
            # Car Collision Detection
            other_player_id = 3 - player_id  # Switch between 1 and 2
            if other_player_id in self.players:
                other_player = self.players[other_player_id]
                
                car_collision = self.check_car_collision({
                    'x': player['x'], 
                    'y': player['y'], 
                    'width': player['width'], 
                    'height': player['height']
                }, {
                    'x': other_player['x'], 
                    'y': other_player['y'], 
                    'width': other_player['width'], 
                    'height': other_player['height']
                })
                
                if car_collision:
                    
                    temp_speed = player['speed']
                    player['speed'] = other_player['speed'] * 0.5
                    other_player['speed'] = temp_speed * 0.5
                    
                    # Swap positions slightly
                    player['x'] += math.cos(player['angle']) * 10
                    player['y'] += math.sin(player['angle']) * 10
                    other_player['x'] -= math.cos(other_player['angle']) * 10
                    other_player['y'] -= math.sin(other_player['angle']) * 10
            
            # Friction
            player['speed'] *= 0.98

        return self.players

      
    def check_track_collision(self, player):
        """
        More precise track collision detection
        """
        dx = player['x'] - self.CENTER_X
        dy = player['y'] - self.CENTER_Y
        distance_from_center = math.sqrt(dx**2 + dy**2)
        
        car_diagonal = math.sqrt((player['width']/2)**2 + (player['height']/2)**2)
        
        return (
            distance_from_center + car_diagonal > self.OUTER_TRACK_RADIUS or 
            distance_from_center - car_diagonal < self.INNER_TRACK_RADIUS
        )

    def check_car_collision(self, player1, player2):
        dx = player1['x'] - player2['x']
        dy = player1['y'] - player2['y']
        distance = math.sqrt(dx**2 + dy**2)
        
        # Adjusted collision threshold considering car dimensions
        collision_threshold = (
            (player1['width'] + player2['width']) / 2 + 
            (player1['height'] + player2['height']) / 2
        ) * 0.5
        
        return distance < collision_threshold