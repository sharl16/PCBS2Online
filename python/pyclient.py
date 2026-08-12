# Initialization

import time
import threading
import os

import socket
import configparser

import logging

from colorama import init as colorama_init
from colorama import Fore
from colorama import Style

import UDPComms as U
import subprocess
import sys

import glob
import unity

colorama_init()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('client.log')
    ]
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logger.debug(f"Logger active with level: {logging.getLevelName(logger.level)}")

config = configparser.ConfigParser()
config.read('config.ini')

verbose = config.getboolean("Logging", "verbose")

if verbose:
    logger.setLevel(logging.DEBUG)
    for handler in logger.handlers:
        handler.setLevel(logging.DEBUG)
    logger.debug(f"{Fore.CYAN}Verbose [DEBUG] logging enabled. Detailed messages will now be shown.{Style.RESET_ALL}")

# Python/Unity Communication:

isRunning = False

sock = U.UdpComms(udpIP="127.0.0.1", portTX=8002, portRX=8003, enableRX=True, suppressWarnings=False)

def ReceiveDataContinuous():
    while True:
        received_data = sock.ReadReceivedData()
        if received_data:
            print(f"Received from UDP: {received_data}")
            unity.handle_udp_data(received_data)
        time.sleep(0.01)

isRunning = True

thread = threading.Thread(target=ReceiveDataContinuous)
thread.start()

# ==========================================================

# Networking:

# Initialization: Server IP, Port, Client Socket

peer_ip = config['Client'].get('peer_address')
peer_port = int(config['Client'].get('peer_port'))

if verbose:
    logger.info(f"Server address: {Fore.CYAN}{peer_ip}{Style.RESET_ALL}")
    logger.info(f"Server port: {Fore.CYAN}{peer_port}{Style.RESET_ALL}")

if not peer_ip or not peer_port:
    input(f"{Fore.RED}Invalid peer IP or Port. Verify config.INI{Style.RESET_ALL}")
    exit()

isConnected = False

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print(f"{Fore.LIGHTBLUE_EX}Acting as Client!{Style.RESET_ALL}")

# Event Loop

def ConnectToServer():
    print(f"Attempting to connect on: {Fore.CYAN}{peer_ip}:{peer_port}{Style.RESET_ALL}..")
    try:
        client_socket.connect((peer_ip, peer_port))
        isConnected = True
    except Exception as e:
        print(f"{Fore.YELLOW}Failed to connect to {peer_ip}:{peer_port} / Reason: {e}{Style.RESET_ALL}")
        prompt = input("Press (y) to retry connection.")
        if str.lower(prompt) == "y":
            ConnectToServer()
        else:
            quit()


def handle_server():
    while True:
        try:
            data = client_socket.recv(512000)
            if not data:
                print(f"{Fore.YELLOW}Server disconnected!{Style.RESET_ALL}")
                break

            if data.startswith(b"TEXT"):
                decodedData = data[5:].decode('utf-8')
                print(f"Received from remote (text): {Fore.MAGENTA}{decodedData}{Style.RESET_ALL}")
                sock.SendData(decodedData)  
            elif data.startswith(b"BINARY"):
                binary_data = data[12:]
                print(f"Received binary data: {Fore.LIGHTCYAN_EX}{binary_data[:20]}...{Style.RESET_ALL}")   
            else:
                print(f"{Fore.YELLOW}Unknown data format received!{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}{e}{Style.RESET_ALL}")
            break


ConnectToServer()

server_thread = threading.Thread(target=handle_server)
server_thread.daemon = True  
server_thread.start()

# if not isConnected:
#     quit()

while True:
    message = input(f"Connected to: {Fore.CYAN}{peer_ip}:{peer_port}{Style.RESET_ALL}  ")
    # if message.lower() == 'exit':
    #     break
    client_socket.sendall(message.encode('utf-8'))
    print(f"Sent: {Fore.MAGENTA}{message}{Style.RESET_ALL}")
    time.sleep(0.01)