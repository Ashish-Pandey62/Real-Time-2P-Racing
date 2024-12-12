import json
import random
import math
from channels.generic.websocket import AsyncWebsocketConsumer


class GameConsumer(AsyncWebsocketConsumer):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.player_laps = {1: 0, 2: 0}
        self.game_finished = False
        # self.winner = None
   
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
                    "type": "notify_player_left",  
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

                
                updated_players = await self.update_game_state()

                # Broadcast updated game state
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "send_game_event",
                        "player1": updated_players.get(1, None),
                        "player2": updated_players.get(2, None)
                    }
                )

        except json.JSONDecodeError:
            print("Invalid JSON received")

    async def send_game_event(self, event):
        await self.send(text_data=json.dumps({
            "type": "game_event",
            "game_finished": event.get("game_finished", False),
            # "winner": event.get("winner", None),
            "player1": event.get("player1", {}),
            "player2": event.get("player2", {})
        }))
        
        
    LAPS_TO_WIN = 3
    
    
    def check_lap_completion(self, player_id, player):
   
        
        lap_completion_zones = [
            {'x': self.CENTER_X - 200, 'y': self.CENTER_Y - 300},
            {'x': self.CENTER_X + 250, 'y': self.CENTER_Y - 250}
        ]

        
        for zone in lap_completion_zones:
            dx = player['x'] - zone['x']
            dy = player['y'] - zone['y']
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < 50:  # Adjust threshold as needed
                self.player_laps[player_id] += 1
                
                # Check if player has won
                if self.player_laps[player_id] >= self.LAPS_TO_WIN:
                    self.game_finished = True
                    # self.winner = player_id
                    return True
    
        return False

    async def update_game_state(self):
        for player_id, player in self.players.items():
            original_x = player['x']
            original_y = player['y']
            original_speed = player['speed']
            
            controls = player['controls']
            
            
            if controls.get('ArrowUp', False) or controls.get('w', False):
                player['speed'] = min(player['speed'] + 0.1, player['maxSpeed'])
            if controls.get('ArrowDown', False) or controls.get('s', False):
                player['speed'] = max(player['speed'] - 0.1, -2.5)
            
            # Steering
            if controls.get('ArrowLeft', False) or controls.get('a', False):
                player['angle'] -= 0.05 * (1 if player['speed'] != 0 else 0)
            if controls.get('ArrowRight', False) or controls.get('d', False):
                player['angle'] += 0.05 * (1 if player['speed'] != 0 else 0)

            
            new_x = player['x'] + math.cos(player['angle']) * player['speed']
            new_y = player['y'] + math.sin(player['angle']) * player['speed']
            
            
            track_collision = self.check_track_collision({'x': new_x, 'y': new_y, 'width': player['width'], 'height': player['height']})
            
            if not track_collision:
                player['x'] = new_x
                player['y'] = new_y
            else:
                
                player['speed'] *= -0.3  
            
            
            other_player_id = 3 - player_id  
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
                    
                    
                    player['x'] += math.cos(player['angle']) * 10
                    player['y'] += math.sin(player['angle']) * 10
                    other_player['x'] -= math.cos(other_player['angle']) * 10
                    other_player['y'] -= math.sin(other_player['angle']) * 10
            
           
            self.check_lap_completion(player_id, player)
            
            # Friction
            player['speed'] *= 0.98

        
        if self.game_finished:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "send_game_event",
                    "game_finished": True,
                    # "winner": self.winner,
                    "player1": self.players.get(1, {}),
                    "player2": self.players.get(2, {})
                }
            )

        return self.players
    
    def check_track_collision(self, player):
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
        
        
        collision_threshold = (
            (player1['width'] + player2['width']) / 2 + 
            (player1['height'] + player2['height']) / 2
        ) * 0.5
        
        return distance < collision_threshold
    
    
    