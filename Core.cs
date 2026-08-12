using UnityEngine;
using System.Collections;
using System;
using System.Text;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using JetBrains.Annotations;
using System.Linq;
using MelonLoader;
using static System.Net.Mime.MediaTypeNames;
using Unity.Baselib;
using HarmonyLib;
using System.Reflection;
using Il2CppTMPro;

[assembly: MelonInfo(typeof(PCBS2Online.Entry), "PCBS2Online", "0.1.1", "sharlios", null)]
[assembly: MelonGame("Epic Games Publishing", "PCBS2")]

namespace PCBS2Online
{
    public enum SessionType
    {
        None,
        Server,
        Client
    }

    public class Entry : MelonMod
    {
        public static Entry Instance { get; private set; } = new Entry();
        public static SessionType CurrentSession { get; set; } = SessionType.None;

        private GameObject localPlayerObject = null;
        private Vector3 lastPosition = Vector3.zero;
        private float movementThreshold = 0.01f; 

        public bool hasLoadedScene = false;

        public override void OnInitializeMelon()
        {
            LoggerInstance.Msg("Initialized.");
        }

        public override void OnSceneWasLoaded(int buildIndex, string sceneName)
        {
            LoggerInstance.Msg($"Scene {sceneName} with build index {buildIndex} has been loaded!");
            if (sceneName == "Stage_02_Workshop")
            {
                LoggerInstance.Msg("Loaded into workshop, initializing UDP");
                UDPSocket.Instance.InitializeUDP();
                UDPSocket.Instance.SendData("0001");
                hasLoadedScene = true;
            }

            if (sceneName == "Main_Menu")
            {
                LoggerInstance.Msg("Patching UI");

                GameObject mainHUD = GameObject.Find("MainMenuHUD");

                if (mainHUD != null)
                {
                    Transform headerTransform = mainHUD.transform.Find("NewMainMenu/MainMenu/Button2-FreeBuild/Header");
                    if (headerTransform != null)
                    {
                        TextMeshProUGUI titleComponent = headerTransform.GetComponent<TextMeshProUGUI>();
                        if (titleComponent != null)
                        {
                            titleComponent.text = "Free Build (Co-Op)";
                        }
                    }

                    Transform descriptionTransform = mainHUD.transform.Find("NewMainMenu/MainMenu/Button2-FreeBuild/Text");
                    if (descriptionTransform != null)
                    {
                        TextMeshProUGUI subtextComponent = descriptionTransform.GetComponent<TextMeshProUGUI>();
                        if (subtextComponent != null)
                        {
                            var melonInfo = (MelonInfoAttribute)Attribute.GetCustomAttribute(
                                System.Reflection.Assembly.GetExecutingAssembly(),
                                typeof(MelonInfoAttribute)
                            );
                            string currentVersion = melonInfo != null ? melonInfo.Version : "Unknown";
                            subtextComponent.text = $"PCBS2Online Version: {currentVersion}";
                        }
                    }
                }
                else
                {
                    LoggerInstance.Error("Could not find MainMenuHUD root object to patch UI elements.");
                }
            }


        }

        public override void OnApplicationQuit()
        {
            UDPSocket.Instance.OnDisable();
        }

        public override void OnLateUpdate()
        {
            if (!hasLoadedScene)
            {
                return;
            }

            if (localPlayerObject == null)
            {
                localPlayerObject = GameObject.Find("Player");

                if (localPlayerObject != null)
                {
                    LoggerInstance.Msg("Found Player gameobject");
                    lastPosition = localPlayerObject.transform.position;
                }
                return; 
            }

            Vector3 currentPosition = localPlayerObject.transform.position;

            if (Vector3.Distance(currentPosition, lastPosition) > movementThreshold)
            {
                lastPosition = currentPosition;

                string position = $"0003:{currentPosition.x},{currentPosition.y},{currentPosition.z}";

                UDPSocket.Instance.SendData(position);
            }
        }
    }

    public class UDPSocket
    {
        public static UDPSocket Instance { get; private set; } = new UDPSocket();
        private volatile bool isThreadRunning = false;
        private UDPSocket() { }
        // UDPSocket

        public bool isTxStarted = false;

        string IP = "127.0.0.1"; // local host
        int rxPort = 8000; // port to receive data from Python on
        int txPort = 8001; // port to send data to Python on

        // Create necessary UdpClient objects
        UdpClient client;
        IPEndPoint remoteEndPoint;
        Thread receiveThread; // Receiving Thread

        public void SendData(string message) // Use to send data to Python
        {
            try
            {
                byte[] data = Encoding.UTF8.GetBytes(message);
                MelonLogger.Msg($"Sending data: {message}");
                client.Send(data, data.Length, remoteEndPoint);
            }
            catch (Exception err)
            {
                MelonLogger.Msg(err.ToString());
            }
        }

        public void InitializeUDP() // Originally "Awake()"
        {
            // Create remote endpoint (to Matlab) 
            remoteEndPoint = new IPEndPoint(IPAddress.Parse(IP), txPort);

            // Create local client
            client = new UdpClient(rxPort);

            // local endpoint define (where messages are received)
            // Create a new thread for reception of incoming messages
            isThreadRunning = true;
            receiveThread = new Thread(new ThreadStart(ReceiveData));
            receiveThread.IsBackground = true;
            receiveThread.Start();

            // Initialize (seen in comments window)
            MelonLogger.Msg("UDP Comms Initialised");
        }

        // Receive data, update packets received
        void ReceiveData()
        {
            while (isThreadRunning)
            {
                try
                {
                    IPEndPoint anyIP = new IPEndPoint(IPAddress.Any, 0);
                    byte[] data = client.Receive(ref anyIP);
                    if (!isThreadRunning) break;
                    string text = Encoding.UTF8.GetString(data);
                    MelonLogger.Msg(text);
              
                    ProcessInput(text);
                }
                catch (SocketException)
                {
                    MelonLogger.Msg("UDP Socket closed.");
                }
                catch (Exception err)
                {
                    MelonLogger.Msg(err.ToString());
                }
            }
        }

        //Prevent crashes - close clients and threads properly!
        public void OnDisable()
        {
            isThreadRunning = false;
            if (client != null)
            {
                client.Close();
            }

            if (receiveThread != null && receiveThread.IsAlive)
                receiveThread.Join(500);
;
        }

        public void ProcessInput(string input)
        {
            if (!isTxStarted) // First data arrived so tx started
            {
                isTxStarted = true;
            }

            // Input from ReceiveData() is processed here.

            // ==========================================

            MelonLogger.Msg($"UDP: '{input}' received.");

            string decodedOpCode = input.Substring(0, 4);

            if (decodedOpCode == "0002")
            {
                Entry.CurrentSession = SessionType.Server;
                MelonLogger.Msg($"Set session type to server, ref: ({Entry.CurrentSession})");
                return;
            }

   

            MelonLogger.Msg($"Data: '{input}' could not be processed: Unknown Input.");

            // ==========================================
        }
    }
    }