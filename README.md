# PCBS2Online

A MelonMod that adds **barebones** online functionalty to PC Building Simulator 2.

It works by setting up communication between Unity and a Python script over UDP. 
The Python script handles the networking backend.

There are two python scripts, one acting as the server host, and the other as a client.
Python host communicates with the client over TCP, using a local network and a Tailnet to avoid the hassle
of setting up *secure* port forwarding
(https://tailscale.com/)

Two-way communication between Python 3 and Unity (C#) - Y. T. Elashry
(https://github.com/Siliconifier/Python-Unity-Socket-Communication)

Based on CMSOnline:
(https://github.com/sharl16/CMSOnline)
