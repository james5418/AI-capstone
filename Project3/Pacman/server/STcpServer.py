from re import T
import struct
import socket
import subprocess
from sys import path


def Listen(port, cntListen):
    socketListen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    addrServer = ('localhost', port)
    socketListen.bind(addrServer)
    socketListen.listen(cntListen)

    return socketListen

# return (result, flagTimeout)


def _RecvUntil(socketRecv, cntByte):
    if(socketRecv is None):
        return (None, False)
    try:
        rbData = socketRecv.recv(cntByte)
    except socket.timeout:
        return (None, True)
    except socket.error as _:
        return (None, False)

    if(len(rbData) != cntByte):
        return (None, False)

    return (rbData, False)

# return (result, flagTimeout)


def _SendAll(socketSend, rbData):
    if(socketSend is None):
        return (False, False)
    try:
        resultSend = socketSend.sendall(rbData)
    except socket.timeout:
        return (False, True)
    except socket.error as e:
        print(e)
        return (False, False)

    return (resultSend is None, False)


socketListen = None
portListen = 8888

pathExe = ["", "", "", ""]
idPlayer = [-1, -1, -1, -1]
socketPlayer = [None, None, None, None]
idPackage = 0

secTimeout = 20


def _SendExitCode(socketClient):
    structHeader = struct.Struct("ii")
    rbHeader = structHeader.pack(0, 0)
    _SendAll(socketClient, rbHeader)

# return (flagSuccess, socketClient)


def _TryAccept(idTeam):
    global socketListen
    global portListen

    try:
        (socketClient, _) = socketListen.accept()
    except socket.timeout:
        return (False, None)
    except:
        print("[Error] : accept fail, trying to recreate listen socket!")
        socketListen.close()
        socketListen = Listen(portListen, 50)
        socketListen.settimeout(secTimeout)
        return _TryAccept(idTeam)
    else:
        socketClient.settimeout(secTimeout)
        structHeader = struct.Struct("i")
        (rbHeader, _) = _RecvUntil(socketClient, structHeader.size)
        if(rbHeader is None):
            socketClient.close()
            print("[Error] : recv team id fail, retry...")
            return _TryAccept(idTeam)

        idTeamRecv = structHeader.unpack(rbHeader)[0]
        if(idTeamRecv != idTeam):
            _SendExitCode(socketClient)
            socketClient.close()
            print("[Error] : team id not match, should be ",
                  idTeam, " but recv ", idTeamRecv)
            return _TryAccept(idTeam)

        return (True, socketClient)

# kill and spawn


def _WaitConnection(indexPlayer, idTeam, flagDirectlySpawn, pathExe):
    global socketPlayer

    if(not flagDirectlySpawn):
        (flagSuccess, socketClient) = _TryAccept(idTeam)
        if(flagSuccess):
            socketPlayer[indexPlayer] = socketClient
            return True
    # spawn process
    # subprocess.Popen(["taskkill", "/im", "Sample.exe"])

    if indexPlayer == 3:
        subprocess.Popen("python ../python/Qlearning_6.py")
    elif(len(pathExe) != 0):
        subprocess.Popen([pathExe])
    (flagSuccess, socketClient) = _TryAccept(idTeam)
    if(flagSuccess):
        socketPlayer[indexPlayer] = socketClient
    else:
        print("[Error] : team id ", idTeam, "\'s exe doesn't connect in!")
    return flagSuccess


def _CleanUpPlayer():
    global socketPlayer
    global idPackage

    idPackage = 0
    for i in range(4):
        if(socketPlayer[i] is not None):
            # send exit code
            _SendExitCode(socketPlayer[i])
            socketPlayer[i].close()
            socketPlayer[i] = None

        # force process to be killed
        subprocess.Popen(["taskkill", "/im", pathExe[i]])


'''
    嘗試啟動兩位玩家的執行檔並等待連線
'''


def StartMatch(idTeam1, pathExe1, idTeam2, pathExe2, idTeam3, pathExe3, idTeam4, pathExe4):
    global socketListen
    global portListen
    global pathExe
    global idPlayer

    if(socketListen is None):
        socketListen = Listen(portListen, 50)
        socketListen.settimeout(secTimeout)

    _CleanUpPlayer()
    idPlayer = [idTeam1, idTeam2, idTeam3, idTeam4]
    pathExe = [pathExe1, pathExe2, pathExe3, pathExe4]

    for i in range(4):
        if(not _WaitConnection(i, idPlayer[i], True, pathExe[i])):
            _CleanUpPlayer()
            return (False, idPlayer[i])

    return (True, -1)


def StopMatch():
    _CleanUpPlayer()


def SendMap(indexPlayer, p_wall, v_wall):
    global pathExe
    global idPlayer
    global socketPlayer
    global idPackage

    if(socketPlayer[indexPlayer] is None):
        print("[Error] : lose connection for team ",
        idPlayer[indexPlayer])
        return 2

    structHeader = struct.Struct("ii")
    structItem = struct.Struct("i")
    # pack parallel_wall
    rbHeader = structHeader.pack(1, idPackage)
    for i in range(16):
        for j in range(17):
            rbHeader += structItem.pack(p_wall[i][j])

    # pack vertical_wall
    for i in range(17):
        for j in range(16):
            rbHeader += structItem.pack(v_wall[i][j])

    (flagSuccess, flagTimeout) = _SendAll(socketPlayer[indexPlayer], rbHeader)
    if(flagTimeout):
        print("[Error] : send board timeout for team ", idPlayer[indexPlayer])
        if(socketPlayer[indexPlayer] != None):
            socketPlayer[indexPlayer].close()
            socketPlayer[indexPlayer] = None
        return 1
    if(not flagSuccess):
        print("[Error] : send board maximum retry reach!")
        return 2
    (rbHeader, flagTimeout) = _RecvUntil(
            socketPlayer[indexPlayer], struct.Struct("i").size)
    if rbHeader == None:
        return 1
    rbHeader = struct.Struct("i").unpack(rbHeader)[0]
    if rbHeader == 1:
        return 0
    return 2

def Sendend(indexPlayer):
    global pathExe
    global idPlayer
    global socketPlayer
    global idPackage

    if(socketPlayer[indexPlayer] is not None):
        structHeader = struct.Struct("ii")
        rbHeader = structHeader.pack(1, idPackage)
        # send
        (flagSuccess, flagTimeout) = _SendAll(socketPlayer[indexPlayer], rbHeader)
        if(flagTimeout):
            print("[Error] : send board timeout for team ", idPlayer[indexPlayer])
            return 1
        if(not flagSuccess):
            return 2 
        return 0

def Sendstatus(indexPlayer, ghost, hero, food):
    global pathExe
    global idPlayer
    global socketPlayer
    global idPackage

    if(socketPlayer[indexPlayer] is None):
        print("[Error] : lose connection for team ",
        idPlayer[indexPlayer])
        return (2, None)

    # pack
    structHeader = struct.Struct("ii")
    structItem = struct.Struct("i")
    structPos=struct.Struct("ii")
    structProps=struct.Struct("iii")

    rbHeader = structHeader.pack(1, idPackage)

    # pack playerStat
    for i in range(5):
        rbHeader += structItem.pack(hero[indexPlayer][i])

    # pack other playerStat
    for i in range(4):
        if i!=indexPlayer:
            for j in range(5):
                rbHeader += structItem.pack(hero[i][j])

    # pack ghostStat
    for i in range(4):
        rbHeader += structPos.pack(ghost[i][0],ghost[i][1])

    # pack propsStat
    n_props=len(food)
    rbHeader += structItem.pack(n_props)
    for i in range(n_props):
        rbHeader += structProps.pack(food[i][0], food[i][1],food[i][2])

    # send
    (flagSuccess, flagTimeout) = _SendAll(socketPlayer[indexPlayer], rbHeader)
    if(flagTimeout):
        print("[Error] : send board timeout for team ", idPlayer[indexPlayer])
        return 1, None
    if(not flagSuccess):
        return 2, None
    
    # receive
    (rbHeader, flagTimeout) = _RecvUntil(
            socketPlayer[indexPlayer], struct.Struct("ii").size)
    if rbHeader is not None:
        action = struct.Struct("ii").unpack(rbHeader)
        action = (action[0], action[1])
        return 0, action
    return 2, None

    