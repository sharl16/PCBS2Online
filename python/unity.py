import time
import threading

from colorama import init as colorama_init
from colorama import Fore
from colorama import Style

import logging

_sock = None
_send_to_clients_func = None
_shared_state = {}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('unity.log')
    ]
)

logger = logging.getLogger("unity.py")
logger.setLevel(logging.INFO)


def initialize(sock_instance, ssType, broadcast_func=None, state_dict=None):
    global _sock
    global _send_to_clients_func
    global _shared_state
    _sock = sock_instance
    _send_to_clients_func = broadcast_func
    _shared_state = state_dict if state_dict is not None else {}

    if ssType in ["Server", "Client"]:
        _shared_state["sessionType"] = ssType
    else:
        logger.error(f"{Fore.RED}Invalid session type given: {Style.RESET_ALL}{ssType}")

def handle_udp_data(data):
    logger.info(f"{Fore.CYAN}Handling UDP Data: {data}{Style.RESET_ALL}")
    opcode = data[:4]
    logger.debug(f"Decoded opcode: {opcode}")
    if opcode == "0001":
        _shared_state["isUDPopen"] = True
        return
    if opcode == "0003":
        position = data[5:]
        logger.info(f"Got Host Player Object Position: {position}")
        return

    logger.error(f"{Fore.RED}Unknown OpCode: {opcode} {Style.RESET_ALL}")