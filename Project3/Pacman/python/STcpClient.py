'''
    Copyright © 2019 by Phillip Chang
'''

import struct
import socket
from numpy import zeros, array


socketServer = None
infoServer = ["localhost", 8888]
'''
    *   請將 idTeam 改成組別    *
'''
idTeam = 4

def _Connect(ip, port):
    socketCurrent = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    addrServer = (ip, port)
    error = socketCurrent.connect_ex(addrServer)
    if (error == 0):
        print("Connect to server")
        return socketCurrent

    socketCurrent.close()
    return None


def _RecvUntil(socketRecv, cntByte):
    if (socketRecv is None):
        return None
    try:
        rbData = socketRecv.recv(cntByte)
    except socket.error as _:
        return None

    if (len(rbData) != cntByte):
        return None

    return rbData


def _SendAll(socketSend, rbData):
    if socketSend is None:
        return False
    try:
        resultSend = socketSend.sendall(rbData)
    except socket.error as e:
        print(e)
        return False

    return resultSend is None


def _ConnectToServer(cntRecursive=0):
    global socketServer
    global infoServer
    global idTeam

    if cntRecursive > 3:
        print("[Error] : maximum connection try reached!")
        return
    while socketServer is None:
        socketServer = _Connect(infoServer[0], infoServer[1])

    structHeader = struct.Struct("i")
    rbHeader = structHeader.pack(idTeam)
    if not _SendAll(socketServer, rbHeader):
        socketServer.close()
        socketServer = None
        _ConnectToServer(cntRecursive + 1)


def _ReconnectToServer():
    global socketServer

    if (socketServer is not None):
        socketServer.close()
        socketServer = None

    _ConnectToServer()


def GetMap():
    global socketServer

    if socketServer is None:
        _ConnectToServer()
        if socketServer is None:
            return True, 0, None, None

    # recv
    structHeader = struct.Struct("ii")
    structItem = struct.Struct("i")

    rbHeader = _RecvUntil(socketServer, structHeader.size)
    if rbHeader is None:
        print("[Error] : connection lose")
        socketServer.close()
        socketServer = None
        # return GetMap()
        return None, None, None, None

    (codeHeader, id_package) = structHeader.unpack(rbHeader)
    if codeHeader == 0:
        return True, 0, None, None

    # unpack parallel_wall
    parallel_wall = zeros([16, 17])
    for i in range(16):
        temp = []
        for _ in range(17):
            rbBoard = _RecvUntil(socketServer, structItem.size)
            if rbBoard is None:
                print("[Error] : connection lose")
                socketServer.close()
                socketServer = None
                # return GetMap()
                return None, None, None, None
            itemBoard = structItem.unpack(rbBoard)[0]
            temp.append(itemBoard)
        parallel_wall[i] = array(temp)

    # unpack vertical_wall
    vertical_wall = zeros([17, 16])
    for i in range(17):
        temp = []
        for _ in range(16):
            rbSheep = _RecvUntil(socketServer, structItem.size)
            if rbSheep is None:
                print("[Error] : connection lose")
                socketServer.close()
                socketServer = None
                #return GetMap()
                return None, None, None, None
            itemBoard = structItem.unpack(rbSheep)[0]
            temp.append(itemBoard)
        vertical_wall[i] = array(temp)

    # send success flag to server
    rbHeader = struct.pack("i", True)

    # retry once
    if not _SendAll(socketServer, rbHeader):
        print("[Error] : connection lose after get map")
        #_ReconnectToServer()
        return None,None,None,None

    return False, id_package, parallel_wall, vertical_wall


def GetGameStat():
    '''
    取得當前遊戲狀態

    return (stop_program, id_package, board, is_black)
    stop_program : True 表示當前應立即結束程式，False 表示遊戲繼續
    id_package : 當前狀態的 id，回傳移動訊息時需要使用
    playerStat: [x,y,n_landmine,super_time]
    ghostStat: [[x,y],[x,y],[x,y],[x,y]]
    '''
    global socketServer

    if socketServer is None:
        _ConnectToServer()
        if socketServer is None:
            return True, 0, None, None, None, None

    # recv
    structHeader = struct.Struct("ii")
    structItem = struct.Struct("i")
    structPosition = struct.Struct("ii")

    rbHeader = _RecvUntil(socketServer, structHeader.size)
    if rbHeader is None:
        print("[Error] : connection lose, stop program")
        socketServer.close()
        socketServer = None
        #return GetGameStat()
        return None, None, None, None, None, None

    (codeHeader, id_package) = structHeader.unpack(rbHeader)
    if codeHeader == 0:
        return True, 0, None, None, None, None

    # unpack player Stat
    playerStat = []
    for i in range(5):
        rbPlayer = _RecvUntil(socketServer, structItem.size)
        if rbPlayer is None:
            print("[Error] : connection lose, stop program")
            socketServer.close()
            socketServer = None
            # return GetGameStat()
            return None, None, None, None, None, None
        itemBoard = structItem.unpack(rbPlayer)[0]
        playerStat.append(itemBoard)

    # unpack other player Stat
    otherPlayerStat = []
    for i in range(3):
        itemBoard = []
        for j in range(5):
            #itemBoard = []
            rbPlayer = _RecvUntil(socketServer, structItem.size)
            if rbPlayer is None:
                print("[Error] : connection lose, stop program")
                socketServer.close()
                socketServer = None
                # return GetGameStat()
                return None, None, None, None, None, None
            itemBoard.append(structItem.unpack(rbPlayer)[0])
        otherPlayerStat.append(itemBoard)

    # unpack ghost condition
    ghostStat = []
    for i in range(4):
        rbGhost = _RecvUntil(socketServer, structPosition.size)
        if rbGhost is None:
            print("[Error] : connection lose, stop program")
            socketServer.close()
            socketServer = None
            # return GetGameStat()
            return None, None, None, None, None, None
        itemBoard = structPosition.unpack(rbGhost)
        ghostStat.append([itemBoard[0],itemBoard[1]])

    # unpack props condition
    propsStat = []
    rbNum = _RecvUntil(socketServer, structItem.size)
    if rbNum is None:
        print("[Error] : connection lose, stop program")
        socketServer.close()
        socketServer = None
        # return GetGameStat()
        return None, None, None, None, None, None
    n_props = structItem.unpack(rbNum)[0]

    structProps = struct.Struct("iii")
    for i in range(n_props):
        rbProps = _RecvUntil(socketServer, structProps.size)
        if rbProps is None:
            print("[Error] : connection lose, stop program")
            socketServer.close()
            socketServer = None
            #return GetGameStat()
            return None,None,None,None,None,None
        itemBoard = structProps.unpack(rbProps)
        propsStat.append([itemBoard[0], itemBoard[1], itemBoard[2]])

    return False, id_package, playerStat, otherPlayerStat, ghostStat, propsStat


def SendStep(id_package, move, landmine):
    '''
    向 server 傳達移動訊息
    id_package : 想要回復的訊息的 id_package
    move: move direction, 1: left, 2:right, 3: up, 4: down
    landmine: throw out landmine

    return 函數是否執行成功
    '''
    global socketServer

    if socketServer is None:
        print("[Error] : trying to send step before connection is established")
        
        return False

    # send

    structItem = struct.Struct("ii")

    #rbHeader = struct.pack("ii", 1, id_package)

    rbHeader = structItem.pack(move, landmine)

    # retry once
    if not _SendAll(socketServer, rbHeader):
        print("[Error] : connection lose when send step")
        #_ReconnectToServer()
        return False
    return True