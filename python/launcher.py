import tkinter as tk
import sys
import subprocess
import configparser
import os

config = configparser.ConfigParser()
config.read("config.ini")

game_path = r"C:\Games\PC Building Simulator 2\PCBS2.exe"

# Extract the directory containing the executable
game_directory = os.path.dirname(game_path)

def initialize(sessionType):
    subprocess.Popen(game_path, cwd=game_directory)

def start_server():
    initialize("Server")
    root.destroy()
    import pyserver
    sys.exit()

def start_client():
    initialize("Client")
    root.destroy()
    import pyclient
    sys.exit()

root = tk.Tk()
root.title("CMSOnline")
root.geometry("345x110")

server_btn = tk.Button(root, text="Start Server", command=start_server)
server_btn.grid(row=2, column=0, columnspan=2, pady=5)

client_btn = tk.Button(root, text="Start Client", command=start_client)
client_btn.grid(row=3, column=0, columnspan=2, pady=5)

tk.Label(root, text="Username:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
hostPlrName = tk.Text(root, height=1, width=30)
hostPlrName.grid(row=0, column=1, padx=5, pady=5)

root.mainloop()