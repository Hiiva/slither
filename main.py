import asyncio
import websockets
import struct
import time
import random
import logging
import math
import pygame
from pygame.locals import *
from datetime import datetime
import os

# Set up logging
os.makedirs('logs', exist_ok=True)
log_filename = datetime.now().strftime('logs/%Y%m%d_%H%M%S.log')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename=log_filename)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger = logging.getLogger(__name__)
logger.addHandler(console_handler)

# Pygame settings
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
BG_COLOR = (0, 0, 0)

class SlitherClient:
    def __init__(self):
        self.ws = None
        self.snakes = {}
        self.foods = {}
        self.preys = {}
        self.leaderboard = []
        self.player_id = None
        self.player_snake = None
        self.protocol_version = 11
        self.game_radius = 21600
        self.speed_multiplier = 0
        self.sector_size = 0
        self.mscps = 0
        self.angle = 0
        self.speed = 1
        self.alive = False
        self.server_url = "ws://95.216.38.155:444/slither"
        self.server_version = None
        self.game_started = False
        self.last_ping_time = 0
        self.pong_received = True
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0
        self.boosting = False
        self.player_rank = 0
        self.player_count = 0
        self.background_image = pygame.image.load('assets/bg54.jpg')
        self.background_rect = self.background_image.get_rect()
        self.last_rotation_time = 0
        self.last_boost_time = 0
        self.rotation_interval = 0.1  # 100 ms interval for rotation packets
        self.boost_interval = 0.1  # 100 ms interval for boost packets
        self.sector_count_along_edge = 0
        self.spangdv = 0
        self.nsp1 = 0
        self.nsp2 = 0
        self.nsp3 = 0
        self.mamu = 0
        self.manu2 = 0
        self.cst = 0
        self.default_snake_length = 0
        self.food_colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
            (255, 165, 0),  # Orange
            (128, 0, 128),  # Purple
            (255, 255, 255) # White
        ]
        self.snake_colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
            (255, 165, 0),  # Orange
            (128, 0, 128),  # Purple
            (255, 255, 255), # White
            (139, 0, 0),    # Dark Red
            (0, 139, 0),    # Dark Green
            (0, 0, 139),    # Dark Blue
            (139, 139, 0),  # Dark Yellow
            (139, 0, 139),  # Dark Magenta
            (0, 139, 139),  # Dark Cyan
            (255, 69, 0),   # Orange Red
            (128, 128, 0),  # Olive
            (128, 0, 0),    # Maroon
            (0, 128, 0),    # Green
            (0, 0, 128),    # Navy
            (128, 128, 128),# Gray
            (255, 215, 0),  # Gold
            (255, 140, 0),  # Dark Orange
            (255, 165, 79), # Lemon Chiffon
            (255, 182, 193),# Light Pink
            (255, 20, 147), # Deep Pink
            (255, 105, 180),# Hot Pink
            (255, 69, 0),   # Tomato
            (255, 160, 122),# Light Coral
            (255, 99, 71),  # Dark Salmon
            (255, 127, 80), # Coral
            (255, 228, 196),# Bisque
            (255, 235, 205),# Blanched Almond
            (255, 245, 238),# Wheat
            (255, 248, 220),# Cornsilk
            (255, 250, 205),# Lemon Chiffon
            (255, 255, 224),# Light Yellow
            (255, 255, 240),# Ivory
            (240, 255, 240),# Honeydew
            (240, 255, 255),# Azure
            (245, 245, 245),# White Smoke
            (245, 255, 250),# Mint Cream
            (248, 248, 255),# Ghost White
            (250, 235, 215),# Antique White
            (250, 240, 230),# Linen
            (253, 245, 230),# Old Lace
            (255, 228, 181),# Moccasin
            (255, 228, 196),# Bisque
            (255, 228, 225),# Misty Rose
            (255, 239, 213),# Papaya Whip
            (255, 239, 219),# Blanched Almond
            (255, 240, 245),# Lavender Blush
            (255, 248, 220),# Cornsilk
            (255, 250, 205),# Lemon Chiffon
            (255, 250, 240),# Floral White
            (255, 255, 240),# Ivory
            (255, 255, 255) # White
        ]


        # Initialize pygame
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Slither.io Client')
        self.clock = pygame.time.Clock()

    async def connect(self):
        async with websockets.connect(self.server_url, extra_headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Origin": "http://slither.io"
        }) as websocket:
            self.ws = websocket
            logger.info(f"Connected to server: {self.server_url}")
            try:
                await self.initial_connect()
                await self.listen()
            except websockets.ConnectionClosedError as e:
                logger.error(f"Connection closed with error: {e}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")

    async def initial_connect(self):
        await self.ws.send(struct.pack("B", 99))  # Send StartLogin packet
        logger.debug("Sent StartLogin packet.")

        pre_init_response = await self.ws.recv()  # Wait for Pre-init response (packet "6")
        logger.debug(f"Received Pre-init response: {pre_init_response}")

        secret = self.decode_pre_init_response(pre_init_response)
        await self.ws.send(secret)
        logger.debug("Sent decoded secret.")

        self.send_initial_setup()

    def send_initial_setup(self, nickname="PythonBot", custom_skin=None):
        nickname = nickname[:24]
        skin = random.randint(0, 38)
        msg = struct.pack('BBB', 115, self.protocol_version - 1, skin)
        msg += struct.pack('B', len(nickname))
        msg += nickname.encode('utf-8')
        if custom_skin:
            custom_skin_bytes = bytearray(custom_skin)
            msg += struct.pack('B', len(custom_skin_bytes))
            msg += custom_skin_bytes
        else:
            msg += struct.pack('BB', 0, 255)
        logger.debug(f"Sending initial setup: {msg.hex()}")
        asyncio.create_task(self.ws.send(msg))

    def decode_pre_init_response(self, response):
        secret = [ord(c) for c in response.decode('latin-1')]
        result = self.decode_secret(secret)
        return bytes(result)

    def decode_secret(self, secret):
        result = [0] * 24
        global_value = 0
        for i in range(24):
            value1 = secret[17 + i * 2]
            if value1 <= 96:
                value1 += 32
            value1 = (value1 - 98 - i * 34) % 26
            if value1 < 0:
                value1 += 26

            value2 = secret[18 + i * 2]
            if value2 <= 96:
                value2 += 32
            value2 = (value2 - 115 - i * 34) % 26
            if value2 < 0:
                value2 += 26

            interim_result = (value1 << 4) | value2
            offset = 97 if interim_result >= 97 else 65
            interim_result -= offset
            if i == 0:
                global_value = 2 + interim_result
            result[i] = (interim_result + global_value) % 26 + offset
            global_value += 3 + interim_result

        return result

    def handle_rotation(self, data, msg_type):
        try:
            snake_id, = struct.unpack('!H', data[:2])
            parsing_logic = {
                'e': lambda d: (d[2:5], d[2:4], d[2:3]),
                'E': lambda d: (d[2:4], d[2:3]),
                '3': lambda d: (d[2:4], d[2:3]),
                '4': lambda d: (d[2:5], d[2:4], d[2:3]),
                '5': lambda d: (d[2:4], d[2:3])
            }

            for part in parsing_logic[msg_type](data):
                if len(part) == 3:
                    ang, wang, sp = struct.unpack('!BBB', part)
                    self.update_snake_rotation(snake_id, ang, wang, sp)
                elif len(part) == 2:
                    ang, sp = struct.unpack('!BB', part)
                    self.update_snake_rotation(snake_id, ang, None, sp)
                elif len(part) == 1:
                    ang, = struct.unpack('!B', part)
                    self.update_snake_rotation(snake_id, ang, None, None)
        except struct.error as e:
            logger.error(f"Error parsing rotation packet: {e}")

    def update_snake_rotation(self, snake_id, ang=None, wang=None, sp=None):
        if snake_id in self.snakes:
            if ang is not None:
                self.snakes[snake_id]['ang'] = ang * 2 * math.pi / 256
            if wang is not None:
                self.snakes[snake_id]['wang'] = wang * 2 * math.pi / 256
            if sp is not None:
                self.snakes[snake_id]['sp'] = sp / 18
            logger.debug(f"Updated snake rotation: id={snake_id}, ang={self.snakes[snake_id].get('ang')}, wang={self.snakes[snake_id].get('wang')}, sp={self.snakes[snake_id].get('sp')}")

    async def listen(self):
        handlers = {
            "a": self.handle_initial_setup,
            "6": self.handle_6_message,
            "v": self.handle_v_message,
            "n": lambda data: self.handle_increase_snake(data, 'n'),
            "N": lambda data: self.handle_increase_snake(data, 'N'),
            "g": lambda data: self.handle_move_snake(data, 'g'),
            "G": lambda data: self.handle_move_snake(data, 'G'),
            "l": self.handle_leaderboard,
            "F": lambda data: self.handle_add_food(data, 'F'),
            "f": lambda data: self.handle_add_food(data, 'f'),
            "b": lambda data: self.handle_add_food(data, 'b'),
            "c": self.handle_eat_food,
            "u": self.handle_minimap_update,
            "s": self.handle_snake_presence,
            "W": self.handle_add_sector,
            "w": self.handle_remove_sector,
            "j": self.handle_update_prey,
            "y": self.handle_prey_presence,
            "o": self.handle_verify_code_response,
            "k": self.handle_kill_message,
            "p": self.handle_pong,
            "m": self.handle_global_highscore,
            "e": lambda data: self.handle_rotation(data, 'e'),
            "E": lambda data: self.handle_rotation(data, 'E'),
            "3": lambda data: self.handle_rotation(data, '3'),
            "4": lambda data: self.handle_rotation(data, '4'),
            "5": lambda data: self.handle_rotation(data, '5'),
            "h": self.handle_update_snake_fullness,
            "r": self.handle_remove_snake_part,
        }

        async for message in self.ws:
            msg_type = chr(message[2])
            logger.debug(f"Received message type: {msg_type}")
            logger.debug(f"Raw message: {message.hex()}")
            if msg_type in handlers:
                handlers[msg_type](message[3:])
            else:
                logger.warning(f"Unknown message type: {msg_type}")

    def handle_increase_snake(self, data, msg_type):
        logger.debug(f"Handling increase snake message '{msg_type}'")
        try:
            snake_id, = struct.unpack('!H', data[:2])
            if snake_id not in self.snakes:
                logger.warning(f"Snake {snake_id} not found for increase update")
                return

            if msg_type == 'n':
                x, y = struct.unpack('!HH', data[2:6])
            elif msg_type == 'N':
                if not self.snakes[snake_id]['body']:
                    logger.warning(f"Snake {snake_id} has no body parts for relative increase update")
                    return
                dx, dy = struct.unpack('!BB', data[2:4])
                last_x, last_y = self.snakes[snake_id]['body'][-1]
                x = last_x + (dx - 128)
                y = last_y + (dy - 128)
            else:
                logger.error(f"Unknown increase snake message type: {msg_type}")
                return

            fam, = struct.unpack('!I', b'\x00' + data[6:9])
            fam /= 16777215

            self.snakes[snake_id]['body'].append((x, y))
            self.snakes[snake_id]['fam'] = fam

            logger.debug(f"Increased snake: id={snake_id}, x={x}, y={y}, fam={fam}")
        except struct.error as e:
            logger.error(f"Error parsing increase snake '{msg_type}' packet: {e}")

    def handle_move_snake(self, data, msg_type):
        logger.debug(f"Handling move snake message '{msg_type}'")
        try:
            snake_id, = struct.unpack('!H', data[:2])
            if snake_id not in self.snakes:
                logger.warning(f"Snake {snake_id} not found for movement update")
                return

            if msg_type == 'g':
                x, y = struct.unpack('!HH', data[2:6])
            elif msg_type == 'G':
                if not self.snakes[snake_id]['body']:
                    logger.warning(f"Snake {snake_id} has no body parts for relative movement update")
                    return
                dx, dy = struct.unpack('!BB', data[2:4])
                last_x, last_y = self.snakes[snake_id]['body'][-1]
                x = last_x + (dx - 128)
                y = last_y + (dy - 128)
            else:
                logger.error(f"Unknown move snake message type: {msg_type}")
                return

            # Remove the oldest body part to simulate movement
            if len(self.snakes[snake_id]['body']) > 1:
                self.snakes[snake_id]['body'].pop(0)

            self.snakes[snake_id]['body'].append((x, y))
            if len(self.snakes[snake_id]['body']) > 100:
                self.snakes[snake_id]['body'] = self.snakes[snake_id]['body'][-100:]

            logger.debug(f"Moved snake: id={snake_id}, x={x}, y={y}")
        except struct.error as e:
            logger.error(f"Error parsing move snake '{msg_type}' packet: {e}")

    def handle_snake_presence(self, data):
        logger.debug("Handling snake presence message")

        if len(data) == 6:
            snake_id, = struct.unpack('!H', data[:2])
            status, = struct.unpack('!B', data[2:3])
            if status == 0:
                logger.debug(f"Snake {snake_id} left range")
                if snake_id in self.snakes:
                    del self.snakes[snake_id]
            elif status == 1:
                logger.debug(f"Snake {snake_id} died")
                if snake_id in self.snakes:
                    del self.snakes[snake_id]
            else:
                logger.warning(f"Unexpected status for snake presence: {status}")

        elif len(data) >= 31:
            try:
                snake_id, = struct.unpack('!H', data[:2])
                ehang, = struct.unpack('!I', b'\x00' + data[2:5])
                ehang = ehang * 2 * math.pi / 16777215
                dir, = struct.unpack('!B', data[5:6])
                dir -= 48
                wang, = struct.unpack('!I', b'\x00' + data[6:9])
                wang = wang * 2 * math.pi / 16777215
                speed, = struct.unpack('!H', data[9:11])
                speed /= 1000
                fam, = struct.unpack('!I', b'\x00' + data[11:14])
                fam /= 16777215
                skin, = struct.unpack('!B', data[14:15])
                x, = struct.unpack('!I', b'\x00' + data[15:18])
                x /= 5
                y, = struct.unpack('!I', b'\x00' + data[18:21])
                y /= 5
                name_len, = struct.unpack('!B', data[21:22])
                name = data[22:22 + name_len].decode('utf-8', errors='replace')
                custom_skin_len, = struct.unpack('!B', data[22 + name_len:23 + name_len])
                custom_skin = data[23 + name_len:23 + name_len + custom_skin_len] if custom_skin_len > 0 else None

                body_parts = [(x, y)]  # Initialize with the head part
                for i in range(1, self.default_snake_length):
                    body_parts.append((x - i * 5, y))  # Add body parts behind the head

                snake_color = self.snake_colors[skin % len(self.snake_colors)]

                self.snakes[snake_id] = {
                    'body': body_parts,
                    'fam': fam,
                    'skin': skin,
                    'x': x,
                    'y': y,
                    'speed': speed,
                    'ehang': ehang,
                    'wang': wang,
                    'dir': dir,
                    'name': name,
                    'custom_skin': custom_skin,
                    'ang': ehang,  # Initialize angle
                    'sp': speed,   # Initialize speed
                    'color': snake_color  # Add color to snake data
                }

                logger.debug(f"Snake {snake_id} added: x={x}, y={y}, fam={fam}, skin={skin}, speed={speed}, name={name}, custom_skin={custom_skin}, body_parts={body_parts}")
                if self.player_id is None:
                    self.player_id = snake_id
                    self.player_snake = self.snakes[snake_id]
                    self.camera_x = x
                    self.camera_y = y
                    logger.info(f"Player snake ID set to {snake_id}")

            except struct.error as e:
                logger.error(f"Error parsing snake presence packet: {e}")

        elif len(data) == 3:
            # Handle the 3-byte packet
            snake_id, = struct.unpack('!H', data[:2])
            status, = struct.unpack('!B', data[2:3])
            if status == 0:
                logger.debug(f"Snake {snake_id} left range")
                if snake_id in self.snakes:
                    del self.snakes[snake_id]
            elif status == 1:
                logger.debug(f"Snake {snake_id} died")
                if snake_id in self.snakes:
                    del self.snakes[snake_id]
            else:
                logger.warning(f"Unexpected status for snake presence: {status}")

        else:
            logger.warning(f"Unexpected packet length for snake presence: {len(data)}")
            logger.warning(f"Raw data: {data.hex()}")
            
    def handle_kill_message(self, data):
        logger.debug("Handling kill message")
        try:
            killer_snake_id, total_kills = struct.unpack('!HB', data[:3])
            total_kills /= 16777215
            logger.info(f"Kill message: Killer snake ID={killer_snake_id}, Total kills={total_kills}")
        except struct.error as e:
            logger.error(f"Error parsing kill message: {e}")

    def handle_prey_presence(self, data):
        logger.debug("Handling prey presence message")

        parsing_logic = {
            5: lambda d: self.handle_prey_left_range(d),
            7: lambda d: self.handle_prey_eaten(d),
            22: lambda d: self.handle_prey_added(d),
            19: lambda d: self.handle_prey_added(d),
            2: lambda d: self.handle_prey_left_range(d)
        }

        if len(data) in parsing_logic:
            parsing_logic[len(data)](data)
        else:
            logger.warning(f"Unexpected packet length for prey presence: {len(data)}")
            logger.warning(f"Raw data: {data.hex()}")

    def handle_prey_left_range(self, data):
        prey_id, = struct.unpack('!H', data[:2])
        logger.debug(f"Prey {prey_id} left range")
        if prey_id in self.preys:
            del self.preys[prey_id]

    def handle_prey_eaten(self, data):
        prey_id, eater_snake_id = struct.unpack('!HH', data[:4])
        logger.debug(f"Prey {prey_id} eaten by snake {eater_snake_id}")
        if prey_id in self.preys:
            del self.preys[prey_id]

    def handle_prey_added(self, data):
        try:
            prey_id, color, x, y, size, direction, wanted_angle, current_angle, speed = struct.unpack('!HBHHBBHHH', data[:22])
            x = x * 3 + 1
            y = y * 3 + 1
            size /= 5
            direction -= 48
            wanted_angle = wanted_angle * 2 * math.pi / 16777215
            current_angle = current_angle * 2 * math.pi / 16777215
            speed /= 1000

            logger.debug(f"Prey {prey_id} added: x={x}, y={y}, size={size}, color={color}, direction={direction}, wanted_angle={wanted_angle}, current_angle={current_angle}, speed={speed}")
            self.preys[prey_id] = {
                'x': x,
                'y': y,
                'size': size,
                'color': color,
                'direction': direction,
                'wanted_angle': wanted_angle,
                'current_angle': current_angle,
                'speed': speed
            }
        except struct.error as e:
            logger.error(f"Error parsing 19-byte prey presence packet: {e}")

    def handle_update_snake_fullness(self, data):
        try:
            snake_id, = struct.unpack('!H', data[:2])
            fam, = struct.unpack('!I', b'\x00' + data[2:5])
            fam /= 16777215

            if snake_id in self.snakes:
                if isinstance(self.snakes[snake_id], dict):
                    self.snakes[snake_id]['fam'] = fam
                    logger.debug(f"Updated snake fullness: id={snake_id}, fam={fam}")

                    # Update player snake fullness
                    if snake_id == self.player_id:
                        self.player_snake['fam'] = fam
                else:
                    logger.warning(f"Snake {snake_id} is not a dictionary")
            else:
                logger.warning(f"Snake {snake_id} not found for fullness update")
        except struct.error as e:
            logger.error(f"Error parsing update snake fullness: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

    def handle_remove_snake_part(self, data):
        logger.debug("Handling remove snake part message")
        try:
            snake_id, = struct.unpack('!H', data[:2])
            if snake_id not in self.snakes:
                logger.warning(f"Snake {snake_id} not found for removal update")
                return

            if len(data) == 5:
                # Variant 1: Remove the last part of the snake
                if self.snakes[snake_id]['body']:
                    self.snakes[snake_id]['body'].pop()
                    logger.debug(f"Removed last part of snake: id={snake_id}")
                else:
                    logger.warning(f"Snake {snake_id} has no body parts to remove")

            elif len(data) == 8:
                # Variant 2: Remove the last part and update fam
                fam, = struct.unpack('!I', b'\x00' + data[5:8])
                fam /= 16777215

                if self.snakes[snake_id]['body']:
                    self.snakes[snake_id]['body'].pop()
                    self.snakes[snake_id]['fam'] = fam
                    logger.debug(f"Removed last part of snake and updated fam: id={snake_id}, fam={fam}")
                else:
                    logger.warning(f"Snake {snake_id} has no body parts to remove")

            else:
                logger.warning(f"Unexpected packet length for remove snake part: {len(data)}")
                logger.warning(f"Raw data: {data.hex()}")

        except struct.error as e:
            logger.error(f"Error parsing remove snake part packet: {e}")

    def handle_initial_setup(self, data):
        logger.debug("Handling initial setup message")
        try:
            self.game_radius, = struct.unpack('!I', b'\x00' + data[:3])
            self.mscps, = struct.unpack('!H', data[3:5])
            self.sector_size, = struct.unpack('!H', data[5:7])
            self.sector_count_along_edge, = struct.unpack('!H', data[7:9])
            self.spangdv, = struct.unpack('!B', data[9:10])
            self.nsp1, = struct.unpack('!H', data[10:12])
            self.nsp2, = struct.unpack('!H', data[12:14])
            self.nsp3, = struct.unpack('!H', data[14:16])
            self.mamu, = struct.unpack('!H', data[16:18])
            self.manu2, = struct.unpack('!H', data[18:20])
            self.cst, = struct.unpack('!H', data[20:22])
            self.protocol_version, = struct.unpack('!B', data[22:23])

            logger.debug(f"Initial setup: game_radius={self.game_radius}, mscps={self.mscps}, sector_size={self.sector_size}, "
                        f"sector_count_along_edge={self.sector_count_along_edge}, spangdv={self.spangdv}, nsp1={self.nsp1}, "
                        f"nsp2={self.nsp2}, nsp3={self.nsp3}, mamu={self.mamu}, manu2={self.manu2}, cst={self.cst}, "
                        f"protocol_version={self.protocol_version}")

        except struct.error as e:
            logger.error(f"Error parsing initial setup packet: {e}")

    def handle_6_message(self, data):
        logger.debug("Handling '6' message")
        self.server_version = data.decode()
        logger.debug(f"Server version: {self.server_version}")
        if self.is_valid_version(self.server_version):
            self.got_server_version(self.server_version)
        else:
            logger.warning("Invalid server version received")

    def is_valid_version(self, s):
        return all(65 <= ord(c) <= 122 for c in s)

    def got_server_version(self, server_version):
        secret = [ord(c) for c in server_version]
        decoded_secret = self.decode_secret(secret)
        logger.debug(f"Decoded secret: {decoded_secret.hex()}")
        asyncio.create_task(self.ws.send(decoded_secret))

    def handle_v_message(self, data):
        logger.debug("Handling 'v' message")
        logger.debug(f"Raw 'v' message data: {data.hex()}")
        logger.info("Player died")
        self.alive = False

    def handle_add_food(self, data, msg_type):
        logger.debug(f"Handling add food message '{msg_type}'")
        try:
            index = 0
            while index < len(data):
                color_index, = struct.unpack('!B', data[index:index + 1])
                color = self.food_colors[color_index]
                x, = struct.unpack('!H', data[index + 1:index + 3])
                y, = struct.unpack('!H', data[index + 3:index + 5])
                size, = struct.unpack('!B', data[index + 5:index + 6])
                size /= 5

                food_id = (y * self.game_radius * 3) + x
                self.foods[(x, y)] = {
                    'color': color,
                    'size': size
                }

                logger.debug(f"Added food: id={food_id}, x={x}, y={y}, color={color}, size={size}")
                index += 6
        except struct.error as e:
            logger.error(f"Error parsing add food packet '{msg_type}': {e}")

    def handle_eat_food(self, data):
        logger.debug("Handling eat food message")
        try:
            x, = struct.unpack('!H', data[:2])
            y, = struct.unpack('!H', data[2:4])
            eater_snake_id, = struct.unpack('!H', data[4:6])

            food_id = (y * self.game_radius * 3) + x
            food_info = self.foods.get((x, y))

            if food_info is not None:
                del self.foods[(x, y)]
                logger.debug(f"Food eaten: id={food_id}, x={x}, y={y}, eater_snake_id={eater_snake_id}, color={food_info['color']}, size={food_info['size']}")
            else:
                logger.warning(f"Food not found: id={food_id}")
        except struct.error as e:
            logger.error(f"Error parsing eat food packet: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

    def handle_minimap_update(self, data):
        logger.debug("Handling minimap update")
        minimap_data = []
        index = 0
        for _ in range(80 * 80):
            if index >= len(data):
                break
            value = data[index]
            if value >= 128:
                minimap_data.extend([0] * (value - 128))
                index += 1
            else:
                for bit in range(7, -1, -1):
                    if (value & (1 << bit)) != 0:
                        minimap_data.append(1)
                    else:
                        minimap_data.append(0)
                index += 1

        logger.debug(f"Minimap update: {len(minimap_data)} pixels")

        if not self.game_started:
            self.start_game()

    def handle_leaderboard(self, data):
        try:
            self.player_rank = data[0]
            player_count, = struct.unpack('!H', data[3:5])

            leaderboard = []
            index = 5
            for _ in range(10):  # Top 10 players
                if index >= len(data):
                    break
                snake_length, = struct.unpack('!H', data[index:index+2])
                index += 2

                fam, = struct.unpack('!I', b'\x00' + data[index:index+3])
                fam /= 16777215
                index += 3

                color = data[index]
                index += 1

                username_length = data[index]
                index += 1
                username_bytes = data[index:index+username_length]
                index += username_length

                # Replace null characters and decode
                username = username_bytes.replace(b'\x00', b'').decode('utf-8', errors='replace')

                score = int(15 * (snake_length / 10 + fam / 4 - 1) - 5)
                leaderboard.append({
                    'username': username,
                    'score': score,
                    'snake_length': snake_length,
                    'color': color
                })

            self.leaderboard = leaderboard
            self.player_count = player_count
            logger.debug(f"Updated leaderboard: {self.leaderboard}")
            logger.debug(f"Player rank: {self.player_rank}/{self.player_count}")
        except Exception as e:
            logger.error(f"Error handling leaderboard: {e}")
            logger.error(f"Raw data: {data.hex()}")

    def start_game(self):
        logger.info("Starting the game")
        self.game_started = True
        self.send_play_packet()
        self.start_game_loop()

    def send_play_packet(self):
        logger.debug("Sending play packet")
        play_packet = struct.pack('B', 115)
        play_packet += struct.pack('B', self.protocol_version - 1)
        play_packet += struct.pack('B', random.randint(0, 38))

        nickname = "PythonBot"
        play_packet += struct.pack('B', len(nickname))
        play_packet += nickname.encode('utf-8')

        play_packet += struct.pack('BB', 0, 255)

        asyncio.create_task(self.ws.send(play_packet))
        logger.debug(f"Sent play packet: {play_packet.hex()}")

    def handle_add_sector(self, data):
        logger.debug("Handling add sector")
        x, y = struct.unpack('BB', data[:2])
        logger.debug(f"Added sector: x={x}, y={y}")

    def handle_remove_sector(self, data):
        logger.debug("Handling remove sector")
        x, y = struct.unpack('BB', data[:2])
        logger.debug(f"Removed sector: x={x}, y={y}")

    def handle_update_prey(self, data):
        logger.debug("Handling update prey")
        prey_id, = struct.unpack('!H', data[:2])
        x, y = struct.unpack('!hh', data[2:6])
        logger.debug(f"Updated prey: id={prey_id}, x={x}, y={y}")
        self.preys[prey_id] = {'x': x, 'y': y}

    def handle_verify_code_response(self, data):
        logger.debug("Handling verify code response")
        logger.debug(f"Raw 'o' message data: {data.hex()}")

    def handle_pong(self, data):
        self.pong_received = True
        logger.debug("Received pong from server")

    async def send_ping(self):
        while self.alive:
            current_time = time.time()
            if current_time - self.last_ping_time >= 0.25 and self.pong_received:
                ping_packet = struct.pack('B', 251)
                try:
                    await self.ws.send(ping_packet)
                    logger.debug("Sent ping packet")
                    self.last_ping_time = current_time
                    self.pong_received = False
                except websockets.ConnectionClosedError as e:
                    logger.error(f"Error sending ping: {e}")
                    break
            await asyncio.sleep(0.25)


    async def game_loop(self):
        while True:
            await self.handle_input()
            self.update_camera()
            if self.alive:
                self.update_player_snake()
            await asyncio.sleep(0.016)  # ~60 FPS

    def update_camera(self):
        if self.player_id is not None and self.player_id in self.snakes:
            player_snake = self.snakes[self.player_id]
            if player_snake['body']:
                head_x, head_y = player_snake['body'][-1]
                # Smoothly interpolate the camera position
                self.camera_x = self.camera_x * 0.9 + head_x * 0.1
                self.camera_y = self.camera_y * 0.9 + head_y * 0.1
                logger.debug(f"Updated camera position: ({self.camera_x}, {self.camera_y})")
            else:
                logger.warning("Player snake has no body parts")
        else:
            logger.warning("Player snake not found for camera update")

    async def handle_input(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.alive = False
                pygame.quit()
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # Mouse wheel up
                    self.zoom *= 1.1
                elif event.button == 5:  # Mouse wheel down
                    self.zoom /= 1.1
                elif event.button == 1:  # Left mouse button
                    if not self.boosting:
                        self.send_boost(True)
                        self.boosting = True
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left mouse button
                    if self.boosting:
                        self.send_boost(False)
                        self.boosting = False

        if pygame.mouse.get_focused():
            current_time = time.time()
            if current_time - self.last_rotation_time >= self.rotation_interval:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                snake_head_screen_x, snake_head_screen_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
                delta_x = mouse_x - snake_head_screen_x
                delta_y = mouse_y - snake_head_screen_y
                angle = math.atan2(delta_y, delta_x)
                byte1 = int(angle * 256 / (2 * math.pi)) & 0xFF
                byte2 = (self.speed_multiplier << 5) & 0xE0
                self.send_rotation(byte1, byte2)
                logger.debug(f"Calculated angle: {angle}, byte1: {byte1}, byte2: {byte2}")
                self.last_rotation_time = current_time

    def send_rotation(self, byte1, byte2):
        msg = struct.pack('BB', byte1, byte2)
        asyncio.create_task(self.ws.send(msg))
        logger.debug(f"Sent rotation packet: {msg.hex()}")

    def start_game_loop(self):
        self.alive = True
        asyncio.create_task(self.game_loop())
        asyncio.create_task(self.draw_loop())
        asyncio.create_task(self.send_ping())
        self.update_camera()

    async def draw_loop(self):
        while True:
            try:
                self.screen.fill(BG_COLOR)
                self.draw_background()
                self.draw_elements()
                self.draw_leaderboard()
                self.draw_debug_info()
                if not self.alive:
                    self.draw_you_died()
                pygame.display.flip()
                await asyncio.sleep(0.016)  # ~60 FPS
            except pygame.error as e:
                logger.error(f"Pygame error in draw loop: {e}")
                break

    def draw_background(self):
        # Calculate the position to start drawing the background
        start_x = int(-(self.camera_x % self.background_rect.width))
        start_y = int(-(self.camera_y % self.background_rect.height))

        # Draw the background image in a continuous manner
        for y in range(start_y, SCREEN_HEIGHT, self.background_rect.height):
            for x in range(start_x, SCREEN_WIDTH, self.background_rect.width):
                self.screen.blit(self.background_image, (x, y))

    def draw_you_died(self):
        font = pygame.font.Font(None, 72)
        text_surface = font.render("You Died!", True, (255, 0, 0))
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        self.screen.blit(text_surface, text_rect)

    def send_boost(self, boosting):
        msg = struct.pack('B', 253 if boosting else 254)
        asyncio.create_task(self.ws.send(msg))
        logger.debug(f"Sent boost: {boosting}")

    def calculate_thickness(self, fam):
        base_thickness = 5  # Base thickness
        max_thickness = 20  # Maximum thickness
        return base_thickness + (max_thickness - base_thickness) * fam

    def draw_snake(self, snake, color):
        if not snake['body']:
            logger.warning(f"Snake has no body parts: {snake}")
            return

        # Load font for rendering snake names
        font = pygame.font.Font(None, 24)

        # Draw lines connecting the snake parts
        for i in range(len(snake['body']) - 1):
            x1, y1 = snake['body'][i]
            x2, y2 = snake['body'][i + 1]
            screen_x1, screen_y1 = self.world_to_screen((x1, y1))
            screen_x2, screen_y2 = self.world_to_screen((x2, y2))
            thickness = self.calculate_thickness(snake['fam'])
            pygame.draw.line(self.screen, color, (screen_x1, screen_y1), (screen_x2, screen_y2), max(1, int(thickness * self.zoom)))

        # Draw the head of the snake as a slightly larger circle
        head_x, head_y = snake['body'][-1]
        screen_head_x, screen_head_y = self.world_to_screen((head_x, head_y))
        thickness = self.calculate_thickness(snake['fam'])
        pygame.draw.circle(self.screen, color, (screen_head_x, screen_head_y), max(1, int((thickness + 2) * self.zoom)))

        # Draw the snake's name above the head
        name = snake.get('name', '').strip()
        if not name:
            name = "(No Name)"
        name_surface = font.render(name, True, (255, 255, 255))
        name_rect = name_surface.get_rect(center=(screen_head_x, screen_head_y - 20))

        # Add a small black outline for readability
        outline_surface = font.render(name, True, (0, 0, 0))
        outline_positions = [(name_rect.x - 1, name_rect.y - 1), (name_rect.x + 1, name_rect.y - 1),
                             (name_rect.x - 1, name_rect.y + 1), (name_rect.x + 1, name_rect.y + 1)]
        for pos in outline_positions:
            self.screen.blit(outline_surface, pos)

        # Blit the name surface on top of the outline
        self.screen.blit(name_surface, name_rect)

    def update_player_snake(self):
        if self.player_id is not None and self.player_id in self.snakes:
            player_snake = self.snakes[self.player_id]

            # Update position using the last known position
            if player_snake['body']:
                self.camera_x, self.camera_y = player_snake['body'][-1]
            elif 'x' in player_snake and 'y' in player_snake:
                self.camera_x, self.camera_y = player_snake['x'], player_snake['y']

            # Update direction and speed
            self.angle = player_snake.get('ang', self.angle)
            self.speed = player_snake.get('sp', self.speed)

            # Update fullness
            self.player_snake['fam'] = player_snake.get('fam', self.player_snake.get('fam', 0))

            logger.debug(f"Updated player snake: id={self.player_id}, position=({self.camera_x}, {self.camera_y}), angle={self.angle}, speed={self.speed}, fam={self.player_snake['fam']}")
        else:
            logger.warning("Player snake not found for update")

    def draw_elements(self):
        """
        Draw all game elements on the screen.
        """
        # Draw snakes
        for snake_id, snake in self.snakes.items():
            if snake['body']:
                x, y = snake['body'][-1]
                if self.is_in_range(x, y):
                    self.draw_snake(snake, snake['color'])

        # Draw food
        for (x, y), food in self.foods.items():
            if self.is_in_range(x, y):
                self.draw_food(x, y, food['color'], food['size'])

        # Draw prey
        for prey_id, prey in self.preys.items():
            if self.is_in_range(prey['x'], prey['y']):
                self.draw_prey(prey)

    def draw_food(self, x, y, color, size):
        screen_x, screen_y = self.world_to_screen((x, y))
        pygame.draw.circle(self.screen, color, (screen_x, screen_y), max(1, int(size * self.zoom)))

    def draw_prey(self, prey):
        screen_x, screen_y = self.world_to_screen((prey['x'], prey['y']))
        pygame.draw.circle(self.screen, (0, 0, 255), (screen_x, screen_y), max(1, int(prey['size'] * self.zoom)))

    def draw_debug_info(self):
        font = pygame.font.Font(None, 24)
        debug_info = [
            f"Camera: ({self.camera_x:.2f}, {self.camera_y:.2f})",
            f"Zoom: {self.zoom:.2f}",
            f"Player Snake: {self.player_snake is not None}",
            f"Snakes: {len(self.snakes)}",
            f"Foods: {len(self.foods)}",
            f"Preys: {len(self.preys)}",
        ]
        y = SCREEN_HEIGHT - 24 * len(debug_info) - 10
        for info in debug_info:
            surface = font.render(info, True, (255, 255, 255))
            self.screen.blit(surface, (10, y))
            y += 24

    def get_visible_range(self):
        half_width = (SCREEN_WIDTH / 2) / self.zoom
        half_height = (SCREEN_HEIGHT / 2) / self.zoom
        return (self.camera_x - half_width, self.camera_y - half_height, 
                self.camera_x + half_width, self.camera_y + half_height)

    def handle_victory_message(self, data):
        logger.debug("Handling victory message")
        message = data.decode('utf-8', errors='replace')
        logger.info(f"Victory message: {message}")

    def handle_global_highscore(self, data):
        try:
            length, fam = struct.unpack('!HH', data[:4])
            length /= 16777215
            fam /= 16777215
            name_len = data[9]
            winner_name = data[10:10 + name_len].decode('utf-8', errors='replace')
            message_start = 10 + name_len
            message_len = len(data) - message_start
            winner_message = data[message_start:message_start + message_len].decode('utf-8', errors='replace')
            logger.info(f"Global highscore - Name: {winner_name}, Message: {winner_message}, Length: {length}, Fam: {fam}")
        except Exception as e:
            logger.error(f"Error handling global highscore: {e}")
            logger.error(f"Raw data: {data.hex()}")

    def draw_leaderboard(self):
        font = pygame.font.Font(None, 24)
        x = 10
        y = 10  # Start position for the first player
        spacing = 30  # Spacing between each player

        # Display player rank
        player_rank_text = f"Your rank: {self.player_rank}/{self.player_count}"
        surface_rank = font.render(player_rank_text, True, (255, 255, 255))
        self.screen.blit(surface_rank, (x, y))
        y += spacing

        # Display top 10 players
        for i, player in enumerate(self.leaderboard[:10], 1):
            username = player['username'].replace('\x00', '')  # Remove null characters
            score = player['score']  # Use the pre-calculated score
            text = f"{i}. {username}: {score}"
            color = self.snake_colors[player['color'] % len(self.snake_colors)]
            surface = font.render(text, True, color)
            self.screen.blit(surface, (x, y))
            y += spacing  # Move to the next vertical position

    def is_in_range(self, snake_x, snake_y):
        visible_range = max(SCREEN_WIDTH, SCREEN_HEIGHT) / 2 / self.zoom
        return abs(snake_x - self.camera_x) <= visible_range and abs(snake_y - self.camera_y) <= visible_range


    def world_to_screen(self, pos):
        x, y = pos
        screen_x = int((x - self.camera_x) * self.zoom + SCREEN_WIDTH / 2)
        screen_y = int((y - self.camera_y) * self.zoom + SCREEN_HEIGHT / 2)
        return screen_x, screen_y

    def screen_to_world(self, pos):
        screen_x, screen_y = pos
        world_x = (screen_x - SCREEN_WIDTH / 2) / self.zoom + self.camera_x
        world_y = (screen_y - SCREEN_HEIGHT / 2) / self.zoom + self.camera_y
        return world_x, world_y

def main():
    client = SlitherClient()

    logger.info(f"Connecting to server")
    return client.connect()

if __name__ == "__main__":
    asyncio.run(main())
