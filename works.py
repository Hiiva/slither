import asyncio
import websockets
import struct

game_server_url = "ws://95.216.38.155:444/slither"
header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Origin": "http://slither.io"
}

# Define constants for the packet types
PACKET_START_LOGIN = 99
PACKET_SET_USERNAME_AND_SKIN = 115
PACKET_VERIFY_CODE = 111
PACKET_PING = 251
PACKET_UPDATE_OWN_SNAKE = [252, 253, 254]

async def connect_to_server():
    async with websockets.connect(game_server_url, extra_headers=header) as websocket:
        print("Connected to the server.")

        # Send StartLogin packet
        await websocket.send(struct.pack("B", PACKET_START_LOGIN))
        print("Sent StartLogin packet.")

        # Wait for Pre-init response (packet "6")
        pre_init_response = await websocket.recv()
        print("Received Pre-init response:", pre_init_response)

        # Decode the secret and send the response back to the server
        secret = decode_pre_init_response(pre_init_response)
        await websocket.send(secret)
        print("Sent decoded secret.")

        # Send SetUsernameAndSkin packet
        nickname = "Player"
        skin_id = 0
        protocol_version = 11
        set_username_and_skin_packet = struct.pack(
            "BBB", PACKET_SET_USERNAME_AND_SKIN, protocol_version - 1, skin_id
        ) + struct.pack("B", len(nickname)) + nickname.encode()
        await websocket.send(set_username_and_skin_packet)
        print("Sent SetUsernameAndSkin packet.")

        # Send Ping packet
        await websocket.send(struct.pack("B", PACKET_PING))
        print("Sent Ping packet.")

        # Listen for incoming packets
        async for message in websocket:
            print("Received message:", message)

def decode_pre_init_response(response):
    # Implement the secret decoding logic from the provided Java code
    secret = [ord(c) for c in response.decode('latin-1')]
    result = decode_secret(secret)
    return bytes(result)

def decode_secret(secret):
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

if __name__ == "__main__":
    asyncio.run(connect_to_server())
