''' 
pyserver.py

A Python-based program to manage multiplayer sessions for 
C̶M̶S̶O̶n̶l̶i̶n̶e̶ (̶C̶M̶S̶2̶1̶ M̶u̶l̶t̶i̶p̶l̶a̶y̶e̶r̶ M̶o̶d̶) PC Building Simulator 2
Acting as server host.
'''

import time
import threading
import os
import json
import sys
import asyncio

import socket
import configparser
import subprocess

import logging

from colorama import init as colorama_init
from colorama import Fore
from colorama import Style

import UDPComms as U
import unity

colorama_init() 

isUDPopen = False

# =========================================================================================================================================================
# Initialization

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('server.log')
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

# =========================================================================================================================================================
# Python / Unity Communication Logic:

sock = U.UdpComms(udpIP="127.0.0.1", portTX=8000, portRX=8001, enableRX=True, suppressWarnings=False)

def ReceiveDataContinuous():
    while True:
        received_data = sock.ReadReceivedData()
        if received_data:
            logger.info(f"Received from UDP: {received_data}")
            unity.handle_udp_data(received_data)
        time.sleep(0.01)

thread = threading.Thread(target=ReceiveDataContinuous)
thread.start()

# =========================================================================================================================================================
# Initialization: Server IP, Port

server_ip = config['Server'].get('server_address')
server_port = int(config['Server'].get('server_port'))

if not server_ip or not server_port:
    input(f"{Fore.RED}Invalid server IP or Port. Verify config.INI{Style.RESET_ALL}")
    exit()

if verbose:
    logger.info(f"Server address: {Fore.CYAN}{server_ip}{Style.RESET_ALL}")
    logger.info(f"Server port: {Fore.CYAN}{server_port}{Style.RESET_ALL}")

# =========================================================================================================================================================
# Initialization: Server Socket, Clients Object, Communication Mode

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected_clients = []
connected_clients_status = connected_clients.copy()

communicationMode = config['Server'].get('communication_mode')

# =========================================================================================================================================================
# Initialization: Security (Whitelist)

whitelist_enabled = config.getboolean("Security", "whitelist")
whitelisted_addresses = config.get("Security", "whitelisted_addresses").split(", ")
whitelisted_addresses = [ip.strip() for ip in whitelisted_addresses]

if whitelist_enabled:
    logger.info(f"{Fore.CYAN}Whitelist is enabled!{Style.RESET_ALL}")
    logger.debug(f"Whitelisted IPs: {Fore.CYAN}{whitelisted_addresses}{Style.RESET_ALL}")
else:
    logger.info(f"Whitelist is {Fore.LIGHTRED_EX}disabled!{Style.RESET_ALL}")
    logger.warning(f"{Fore.YELLOW}You are not using a whitelist.{Style.RESET_ALL}")

logger.info(f"{Fore.LIGHTBLUE_EX}Acting as Server!{Style.RESET_ALL}")

logger.debug("pyserver.py is initialized from this point.")
# pyserver.py is initialized from this point.

# =========================================================================================================================================================
# Networking

def start_server():
    server_socket.bind((server_ip, server_port))
    server_socket.listen(5)
    logger.info(f"Server listening on {Fore.CYAN}{server_ip}:{server_port}{Style.RESET_ALL}")

    while True:
        client_socket, client_address = server_socket.accept()
        client_ip = client_address[0]
        if not client_ip in whitelisted_addresses and whitelist_enabled:
            logger.warning(f"{Fore.YELLOW}IP: {client_address} is not in the whitelist. Terminating connection.{Style.RESET_ALL}")
            client_socket.close()
        else:
            logger.info(f"Client: {Fore.CYAN}{client_address}{Style.RESET_ALL} is now connected to server.")
            connected_clients.append(client_socket)
            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.start()

def handle_client(client_socket):
    while True:
        try:
            data = client_socket.recv(512000)
            if not data:
                break
            decodedData = data.decode('utf-8')  
            logger.info(f"Received data from client: {decodedData}")
        except Exception as e:
            logger.error(f"{Fore.RED}{e}{Style.RESET_ALL}")
            break

    client_socket.close()

def sendToClients(message):
    for client in connected_clients:    
        try:
            if isinstance(message, bytes):  # binary data
                client.sendall(b"BINARY:"+message)
                logger.info(f"Sent Binary: {Fore.LIGHTCYAN_EX}{message[:20]}..{Style.RESET_ALL}")
            else:  # string data
                client.sendall(b"TEXT:"+message.encode('utf-8'))
                logger.info(f"Sent: {Fore.MAGENTA}{message}{Style.RESET_ALL}")
            
        except Exception as e:
            logger.error(f"{Fore.RED}Exception: {e}{Style.RESET_ALL}")

# =========================================================================================================================================================
# Event Loop

server_thread = threading.Thread(target=start_server)
server_thread.start()

# =========================================================================================================================================================
# pyserver specifics

shared_state = {
    "sessionType": "None",
    "isUDPopen": False
}

unity.initialize(sock, "Server", sendToClients, shared_state)

def wait_for_udp():
    logger.info(f"{Fore.CYAN} Waiting for UDP {Style.RESET_ALL}")
    while shared_state["isUDPopen"] == False:
        time.sleep(0.1)
    logger.info(f"{Fore.CYAN} UDP is ready, signaling session type (server){Style.RESET_ALL}")
    sock.SendData("0002")

threading.Thread(target=wait_for_udp, daemon=True).start()

