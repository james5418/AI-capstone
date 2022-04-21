import struct
import socket
import subprocess


def Listen(port, cntListen):
    socketListen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    addrServer = ('localhost', port)
    socketListen.bind(addrServer)
    socketListen.listen(cntListen)

    return socketListen


# return (result, flagTimeout)


def _RecvUntil(socketRecv, cntByte):
    if (socketRecv is None):
        return (None, False)
    try:
        rbData = socketRecv.recv(cntByte)
    except socket.timeout:
        return (None, True)
    except socket.error as _:
        return (None, False)

    if (len(rbData) != cntByte):
        return (None, False)

    return (rbData, False)


# return (result, flagTimeout)


def _SendAll(socketSend, rbData):
    if (socketSend is None):
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

secTimeout = 6


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
        if (rbHeader is None):
            socketClient.close()
            print("[Error] : recv team id fail, retry...")
            return _TryAccept(idTeam)

        idTeamRecv = structHeader.unpack(rbHeader)[0]
        if (idTeamRecv != idTeam):
            _SendExitCode(socketClient)
            socketClient.close()
            print("[Error] : team id not match, should be ",
                  idTeam, " but recv ", idTeamRecv)
            return _TryAccept(idTeam)

        return (True, socketClient)


# kill and spawn


def _WaitConnection(indexPlayer, idTeam, flagDirectlySpawn, pathExe):
    global socketPlayer

    if (not flagDirectlySpawn):
        (flagSuccess, socketClient) = _TryAccept(idTeam)
        if (flagSuccess):
            socketPlayer[indexPlayer] = socketClient
            return True
    # spawn process
    # subprocess.Popen(["taskkill", "/im", "Sample.exe"])
    if indexPlayer == 1:
        subprocess.Popen("python ../agent.py")
    elif (len(pathExe) != 0):
        subprocess.Popen([pathExe])
    # if (len(pathExe) != 0):
        # subprocess.Popen([pathExe])
    (flagSuccess, socketClient) = _TryAccept(idTeam)
    if (flagSuccess):
        socketPlayer[indexPlayer] = socketClient
    else:
        print("[Error] : team id ", idTeam, "\'s exe doesn't connect in!")
    return flagSuccess, indexPlayer


def _CleanUpPlayer():
    global socketPlayer
    global idPackage

    idPackage = 0
    for i in range(4):
        if (socketPlayer[i] is not None):
            # send exit code
            _SendExitCode(socketPlayer[i])
            socketPlayer[i].close()
            socketPlayer[i] = None

        # force process to be killed
        subprocess.Popen(["taskkill", "/im", pathExe[i]])


'''
    嘗試啟動玩家的執行檔並等待連線
'''


def StartMatch(players, paths):
    global socketListen
    global portListen
    global pathExe
    global idPlayer

    if (socketListen is None):
        socketListen = Listen(portListen, 50)
        socketListen.settimeout(secTimeout)

    _CleanUpPlayer()
    idPlayer = players
    pathExe = paths

    for i in range(4):
        if not _WaitConnection(i, idPlayer[i], True, pathExe[i]):
            _CleanUpPlayer()
            return False, idPlayer[i]

    return (True, -1)


def StopMatch():
    _CleanUpPlayer()




'''
    傳送地圖給玩家選擇初始位置
    indexPlayer : 輪到玩家1~4
    
'''
def SendInitMap(indexPlayer, mapStat, cntRecursive=0):
    global pathExe
    global idPlayer
    global socketPlayer
    global idPackage

    if socketPlayer[indexPlayer] is None:

        if cntRecursive > 3:
            print("[Error] : lose connection after timeout for team ",
                  idPlayer[indexPlayer])
            return 2, None

        (flagSuccess, socketClient) = _TryAccept(idPlayer[indexPlayer])
        if not flagSuccess:
            return SendInitMap(indexPlayer, mapStat)

        socketPlayer[indexPlayer] = socketClient

    idPackage += 1
    structHeader = struct.Struct("ii")
    structItem = struct.Struct("i")

    # gameFlag =1: keep going; =0: game over
    rbHeader = structHeader.pack(1, idPackage)

    # pack teamID(1~4)
    rbHeader += structItem.pack(indexPlayer+1)

    # pack map
    for i in range(12):
        for j in range(12):
            rbHeader += structItem.pack(mapStat[i][j])


    # only retry once
    (flagSuccess, flagTimeout) = _SendAll(socketPlayer[indexPlayer], rbHeader)
    if (flagTimeout):
        print("[Error] : send board timeout for team ", idPlayer[indexPlayer])
        if (socketPlayer[indexPlayer] != None):
            socketPlayer[indexPlayer].close()
            socketPlayer[indexPlayer] = None
        return (1, None)
    if (not flagSuccess):
        if cntRecursive > 3:
            print("[Error] : send board maximum retry reach!")
            return (2, None)
        # _SendExitCode(socketPlayer[indexPlayer])
        if socketPlayer[indexPlayer] is not None:
            socketPlayer[indexPlayer].close()
            socketPlayer[indexPlayer] = None
        (flagSucess, socketClient) = _TryAccept(idPlayer[indexPlayer])
        if not flagSuccess:
            print("[Error] : send board fail and reconnect fail for team ",
                  idPlayer[indexPlayer])
            return 2, None

        socketPlayer[indexPlayer] = socketClient
        (flagSuccess, flagTimeout) = _SendAll(
            socketPlayer[indexPlayer], rbHeader)
        if not flagSuccess:
            socketPlayer[indexPlayer].close()
            socketPlayer[indexPlayer] = None
            print("[Error] : send board fail after reconnect, maybe target team ",
                  idPlayer[indexPlayer], "\'s exe is wrong")
            return 1 if flagTimeout else 2, None

    # receive feedback
    (rbHeader, flagTimeout) = _RecvUntil(socketPlayer[indexPlayer], structHeader.size)
    if flagTimeout:
        print("[Error] : recv init position info timeout for team ",
              idPlayer[indexPlayer])
        if socketPlayer[indexPlayer] is not None:
            socketPlayer[indexPlayer].close()
            socketPlayer[indexPlayer] = None
        return (1, None)
    if rbHeader is None:
        if cntRecursive > 3:
            print("[Error] : send map maximum retry reach!")
            return 2, None
        # _SendExitCode(socketPlayer[indexPlayer])
        socketPlayer[indexPlayer].close()
        socketPlayer[indexPlayer] = None
        (flagSucess, socketClient) = _TryAccept(idPlayer[indexPlayer])
        if not flagSucess:
            print(
                "[Error] : recv init position info fail and reconnect fail for team ", idPlayer[indexPlayer])
            return 2, None

        socketPlayer[indexPlayer] = socketClient
        return SendInitMap(indexPlayer, mapStat)

    (whatever, idPackageRecv) = structHeader.unpack(rbHeader)

    structStep = struct.Struct("ii")
    (rbStep, flagTimeout) = _RecvUntil(socketPlayer[indexPlayer], structStep.size)
    if flagTimeout:
        print("[Error] : recv steps timeout for team ",
              idPlayer[indexPlayer])
        if socketPlayer[indexPlayer] is not None:
            socketPlayer[indexPlayer].close()
            socketPlayer[indexPlayer] = None
        return (1, None)
    if rbStep is None:
        if cntRecursive > 3:
            print("[Error] : send board maximum retry reach!")
            return (2, None)
        # _SendExitCode(socketPlayer[indexPlayer])
        socketPlayer[indexPlayer].close()
        socketPlayer[indexPlayer] = None
        (flagSucess, socketClient) = _TryAccept(idPlayer[indexPlayer])
        if (not flagSucess):
            print(
                "[Error] : recv steps fail and reconnect fail for team ", idPlayer[indexPlayer])
            return (2, None)

        socketPlayer[indexPlayer] = socketClient
        return SendInitMap(indexPlayer, mapStat)

    if idPackageRecv == idPackage:
        upStep = structStep.unpack(rbStep)

        # step=select block, move sheep, move dir
        Step = (upStep[0], upStep[1])

        return 0, Step



'''
    indexPlayer : 輪到玩家1~4
    mapStat : 地盤狀態
    gameStat : 羊群狀態

    return (stateFunc, listStep)
    stateFunc : 函數是否執行成功 0 = 成功、1 = 超時、2 = 斷線
    Step : (r, c) 
'''


def SendBoard(indexPlayer, mapStat, gameStat, gameFlag=1, cntRecursive=0):
    global pathExe
    global idPlayer
    global socketPlayer
    global idPackage

    if socketPlayer[indexPlayer] is None:

        if cntRecursive > 3:
            print("[Error] : lose connection after timeout for team ",
                  idPlayer[indexPlayer])
            return 2, None

        (flagSuccess, socketClient) = _TryAccept(idPlayer[indexPlayer])
        if not flagSuccess:
            return SendBoard(indexPlayer, mapStat, gameStat, cntRecursive + 1)

        socketPlayer[indexPlayer] = socketClient

    idPackage += 1
    structHeader = struct.Struct("ii")
    structItem = struct.Struct("i")

    # gameFlag =1: keep going; =0: game over
    rbHeader = structHeader.pack(gameFlag, idPackage)
    if gameFlag == 0:
        #print(f'send endGameFlag to {indexPlayer + 1}')
        pass

    else:
        # pack map
        for i in range(12):
            for j in range(12):
                rbHeader += structItem.pack(mapStat[i][j])

        # pack game state
        for i in range(12):
            for j in range(12):
                rbHeader += structItem.pack(int(gameStat[i][j]))

    # only retry once
    (flagSuccess, flagTimeout) = _SendAll(socketPlayer[indexPlayer], rbHeader)
    if (flagTimeout):
        print("[Error] : send board timeout for team ", idPlayer[indexPlayer])
        if (socketPlayer[indexPlayer] != None):
            socketPlayer[indexPlayer].close()
            socketPlayer[indexPlayer] = None
        return (1, None)
    if (not flagSuccess):
        if cntRecursive > 3:
            print("[Error] : send board maximum retry reach!")
            return (2, None)
        # _SendExitCode(socketPlayer[indexPlayer])
        if socketPlayer[indexPlayer] is not None:
            socketPlayer[indexPlayer].close()
            socketPlayer[indexPlayer] = None
        (flagSucess, socketClient) = _TryAccept(idPlayer[indexPlayer])
        if not flagSuccess:
            print("[Error] : send board fail and reconnect fail for team ",
                  idPlayer[indexPlayer])
            return 2, None

        socketPlayer[indexPlayer] = socketClient
        (flagSuccess, flagTimeout) = _SendAll(
            socketPlayer[indexPlayer], rbHeader)
        if not flagSuccess:
            socketPlayer[indexPlayer].close()
            socketPlayer[indexPlayer] = None
            print("[Error] : send board fail after reconnect, maybe target team ",
                  idPlayer[indexPlayer], "\'s exe is wrong")
            return 1 if flagTimeout else 2, None

    # receive feedback
    while gameFlag == 1:
        (rbHeader, flagTimeout) = _RecvUntil(socketPlayer[indexPlayer], structHeader.size)
        if flagTimeout:
            print("[Error] : recv step info timeout for team ",
                  idPlayer[indexPlayer])
            if socketPlayer[indexPlayer] is not None:
                socketPlayer[indexPlayer].close()
                socketPlayer[indexPlayer] = None
            return (1, None)
        if rbHeader is None:
            if cntRecursive > 3:
                print("[Error] : send board maximum retry reach!")
                return 2, None
            # _SendExitCode(socketPlayer[indexPlayer])
            socketPlayer[indexPlayer].close()
            socketPlayer[indexPlayer] = None
            (flagSucess, socketClient) = _TryAccept(idPlayer[indexPlayer])
            if not flagSucess:
                print(
                    "[Error] : recv step info fail and reconnect fail for team ", idPlayer[indexPlayer])
                return 2, None

            socketPlayer[indexPlayer] = socketClient
            return SendBoard(indexPlayer, mapStat, gameStat, cntRecursive + 1)

        (whatever, idPackageRecv) = structHeader.unpack(rbHeader)

        structStep = struct.Struct("iiii")
        (rbStep, flagTimeout) = _RecvUntil(socketPlayer[indexPlayer], structStep.size)
        if flagTimeout:
            print("[Error] : recv steps timeout for team ",
                  idPlayer[indexPlayer])
            if socketPlayer[indexPlayer] is not None:
                socketPlayer[indexPlayer].close()
                socketPlayer[indexPlayer] = None
            return (1, None)
        if rbStep is None:
            if cntRecursive > 3:
                print("[Error] : send board maximum retry reach!")
                return (2, None)
            # _SendExitCode(socketPlayer[indexPlayer])
            socketPlayer[indexPlayer].close()
            socketPlayer[indexPlayer] = None
            (flagSucess, socketClient) = _TryAccept(idPlayer[indexPlayer])
            if (not flagSucess):
                print(
                    "[Error] : recv steps fail and reconnect fail for team ", idPlayer[indexPlayer])
                return (2, None)

            socketPlayer[indexPlayer] = socketClient
            return SendBoard(indexPlayer, mapStat, gameStat, cntRecursive + 1)

        if idPackageRecv == idPackage:
            upStep = structStep.unpack(rbStep)

            # step=select block, move sheep, move dir
            Step = ([upStep[0], upStep[1]], upStep[2], upStep[3])

            return 0, Step
