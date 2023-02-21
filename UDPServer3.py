# Sample code for Multi-Threaded Server
#Python 3
# Usage: python3 UDPserver3.py
#coding: utf-8
import os
from socket import *
import threading
import sys,json,time,random
import datetime as dt

#Server will run on this port
serverPort = int(sys.argv[1])
t_lock=threading.Condition()
#will store clients info in this list
clients=[]
# would communicate with clients after every second
UPDATE_INTERVAL= 1
timeout=False
#reflact client to server ACKnum(data[0])
check = 0
seqNum = 0
Receiver_log = []
Sender_log = []

pdrop = 0.2
SenderBytes = 0
datatran = 8192 #(MSW/MSS)

#client to server
def recv_handler():
    global t_lock
    global clients
    global clientSocket
    global serverSocket
    global check
    global seqNum
    global ACKnum
    global pdrop
    global SenderBytes
    global datatran
    message, clientAddress = serverSocket.recvfrom(2048)
    message = json.loads(message)
    message2 = "clientsnd   " + str(message["time"]) + "    S     " + str(message["Seq"]) + "    " + str(message["data"]) + "      " + str(message["Ack"]) + "\n"
    # generate Receiver_log.txt
    f2 = open("Receiver_log.txt", "a")
    f2.write(message2)
    f2.close()

    filename = './' + sys.argv[2]
    filesize = os.path.getsize(filename)
    pktNum = int(round(filesize / datatran,0))
    droppedPktIndex = []
    for i in range(pktNum):
        if i % int(round(1/pdrop, 0)) == 0:
            droppedPktIndex.append(i + 1)
    if (message["SYNbit"] == 1 and message["Seq"] == 1000):
        date_time = dt.datetime.now().strftime("%d/%m/%Y, %H:%M:%S.%f")
        serverMessage = {"SYNbit":1, "ACKbit":1, "Seq":5000, "Ack":message["Seq"]+1, "time":date_time, "data":0}
        message2 = "serverrcv   " + str(serverMessage["time"]) + "    SA    " + str(serverMessage["Seq"]) + "     " + str(serverMessage["data"]) + "      " + str(serverMessage["Ack"]) + "\n"
        # generate Sender_log.txt
        f = open("Sender_log.txt", "a")
        f.write(message2)
        f.close()
        #print(message2)
        serverMessage = json.dumps(serverMessage)
        serverSocket.sendto(serverMessage.encode(), clientAddress)
        message, clientAddress = serverSocket.recvfrom(2048)
        message = json.loads(message)
        serverMessage = json.loads(serverMessage)
        if(message["ACKbit"] == 1 and message["Ack"] == serverMessage["Seq"]+1):
            message2 = "clientsnd   " + str(message["time"]) + "    A     " + str(message["Seq"]) + "    " + str(message["data"]) + "      " + str(message["Ack"]) + "\n"
            # generate Receiver_log.txt
            f2 = open("Receiver_log.txt", "a")
            f2.write(message2)
            f2.close()
            #print(message2)
            serverMessage = "3-way handshake success/" + str(pktNum) + '/' + str(len(droppedPktIndex)) + '/' + str(datatran) + '/'
            seqNum = message["Ack"]
            ACKnum = message["Seq"] + 1
            serverSocket.sendto(serverMessage.encode(), clientAddress)
            print('Server is ready for service')
        else:
            serverSocket.close()
    while(1):
        message, clientAddress = serverSocket.recvfrom(2048)
        #received data from the client, now we know who we are talking with
        message = message.decode()
        #get lock as we might me accessing some shared data structures
        with t_lock:
            currtime = dt.datetime.now()
            date_time = currtime.strftime("%d/%m/%Y, %H:%M:%S.%f")
            print('Received request from', clientAddress[0], 'listening at', clientAddress[1], ':', message, 'at time ', date_time)
            print()
            if (message[0].isnumeric() == False):
                if(message == 'Subscribe'):
                    #store client information (IP and Port No) in list
                    clients.append(clientAddress)
                    serverMessage="Subscription successfull"

                elif(message=='Unsubscribe'):
                    #check if client already subscribed or not
                    if(clientAddress in clients):
                        clients.remove(clientAddress)
                        serverMessage="Subscription removed"
                    else:
                        serverMessage="You are not currently subscribed"

                else:
                    if (message[0] == '{'):
                        message = json.loads(message)
                        message2 = "clientrcv   " + str(message["time"]) + "    FA    " + str(message["Seq"]) + "    " + str(message["data"]) + "      " + str(message["Ack"]) + "\n"
                        receivedBytes = message["receivedBytes"]
                        # generate Receiver_log.txt
                        f2 = open("Receiver_log.txt", "a")
                        f2.write(message2)
                        f2.close()
                        date_time = dt.datetime.now().strftime("%d/%m/%Y, %H:%M:%S.%f")
                        serverMessage = {"ACKbit": 1, "Seq":message["Ack"], "time":date_time, "data":0, "Ack":message["Seq"]+1}
                        message2 = "serversnd   " + str(serverMessage["time"]) + "    A     " + str(serverMessage["Seq"]) + "    " + str(serverMessage["data"]) + "      " + str(serverMessage["Ack"]) + "\n"
                        # generate Sender_log.txt
                        f = open("Sender_log.txt", "a")
                        f.write(message2)
                        f.close()
                        serverMessage = json.dumps(serverMessage)

                        #Receiver statistics:
                        message4 = '\n\n\n\nAmount of (original) Data Received (in bytes) – do not include retransmitted data: ' + str(receivedBytes) + ' bytes' +\
                                   '\nNumber of (original) Data Segments Received: ' + str(pktNum+len(droppedPktIndex)) +\
                                   '\nNumber of duplicate segments received (if any): ' + str(len(droppedPktIndex))
                        f2 = open("Receiver_log.txt", "a")
                        f2.write(message4)
                        f2.close()

                        #Sender statistic
                        message5 = '\n\n\n\nAmount of (original) Data Transferred (in bytes): ' + str(SenderBytes) + ' bytes'+\
                                   '\nNumber of Data Segments Sent (excluding retransmissions): ' + str(pktNum) + \
                                   '\nNumber of (all) Packets Dropped (by the PL module): ' + str(len(droppedPktIndex)) + \
                                   '\nNumber of Retransmitted Segments: ' + str(len(droppedPktIndex)) +\
                                   '\nNumber of Duplicate Acknowledgements received: ' + str(len(droppedPktIndex))

                        f = open("Sender_log.txt", "a")
                        f.write(message5)
                        f.close()


                    else:
                        serverMessage="Unknown command, send Subscribe or Unsubscribe only"
                serverSocket.sendto(serverMessage.encode(), clientAddress)
            #send message to the client
            #serverSocket.sendto(serverMessage.encode(), clientAddress)
            else:
                message = message.split('/')
                if (len(message) == 5):
                    duration = message[3]
                    print('duration is ',duration)
                #calculate new seqNum, ACKnum for server Sender
                check = int(message[0])
                seqNum = int(message[2])
                ACKnum = int(message[1])
                if (check < pktNum):
                    message2 = "serverrcv   " + str(date_time) + "    A     " + message[1] + "    0      " + message[2] + "\n"
                    # generate Receiver_log.txt
                    f2 = open("Receiver_log.txt", "a")
                    f2.write(message2)
                    f2.close()
                else:
                    message2 = "serverrcv   " + str(date_time) + "    A     " + message[1] + "    0      " + message[2] + "\n"
                    # generate Receiver_log.txt
                    f2 = open("Receiver_log.txt", "a")
                    f2.write(message2)
                    f2.close()
                    date_time = dt.datetime.now().strftime("%d/%m/%Y, %H:%M:%S.%f")
                    serverMessage = {"FINbit":1, "Seq":seqNum, "time":date_time, "data":0, "Ack":ACKnum}
                    message2 = "serversnd   " + str(serverMessage["time"]) + "    F     " + str(serverMessage["Seq"]) + "    " + str(serverMessage["data"]) + "      " + str(serverMessage["Ack"]) + "\n"
                    # generate Sender_log.txt
                    f = open("Sender_log.txt", "a")
                    f.write(message2)
                    f.close()
                    serverMessage = json.dumps(serverMessage)
                    serverSocket.sendto(serverMessage.encode(), clientAddress)
            #notify the thread waiting
            t_lock.notify()



#server to client
def send_handler():
    global t_lock
    global clients
    global clientSocket
    global serverSocket
    global timeout
    global check
    global seqNum
    global ACKnum
    global pdrop
    global SenderBytes
    global datatran

    #go through the list of the subscribed clients and send them the current time after every 1 second
    filename = './' + sys.argv[2]
    print('Your file is:' + filename)
    filesize = os.path.getsize(filename)
    file = open(filename)
    pktNum = int(round(filesize/datatran,0))
    #print(pktNum)
    count = 1
    pdrop = 0.2
    random.seed(100)
    NUM = random.random()
    droppedPktIndex = []
    #base on pdrop rate, take out all dropped packets index into droppedPktIndex[], I use averagely dropping strategy
    for i in range(pktNum):
        if i % int(round(1/pdrop, 0)) == 0:
            droppedPktIndex.append(i + 1)
    while(1):
        #get lock
        with t_lock:
            for i in clients:
                data = file.read(datatran)
                #stop and wait protocol
                if (count <= pktNum and check == count - 1):
                    #PL Module
                    if count in droppedPktIndex and NUM <= pdrop:#retransmit (random number is not larger than pdrop, then drop)
                        if (count == 1):
                            date_time = dt.datetime.now().strftime("%d/%m/%Y, %H:%M:%S.%f")
                            message = 'Current time is ' + date_time
                            clientSocket.sendto(message.encode(), i)
                            print('Sending time to', i[0], 'listening at', i[1], 'at time ', date_time)
                            makepacket = "%d/%d/%d/" % (count, seqNum, ACKnum)
                            clientSocket.sendto(makepacket.encode(), i)
                            message3 = "serversnd   " + str(date_time) + "    D     " + str(seqNum) + "     " + str(datatran) + "   " + str(ACKnum) + "\n"
                            f = open("Sender_log.txt", "a")
                            f.write(message3)
                            f.close()
                            time.sleep(0.1)

                            date_time = dt.datetime.now().strftime("%d/%m/%Y, %H:%M:%S.%f")
                            message3 = "packetdrop  " + str(date_time) + "    D     " + str(seqNum+8192) + "    " + str(datatran) + "   " + str(ACKnum) + "\n"
                            f = open("Sender_log.txt", "a")
                            f.write(message3)
                            f.close()

                            #retransmit
                            date_time = dt.datetime.now().strftime("%d/%m/%Y, %H:%M:%S.%f")
                            message = 'Current time is ' + date_time
                            clientSocket.sendto(message.encode(), i)
                            print('Sending time to', i[0], 'listening at', i[1], 'at time ', date_time)
                            makepacket = "%d/%d/%s/%d/" % (count, seqNum+datatran, data, ACKnum)
                            SenderBytes += 3 * 4 + 8192
                            clientSocket.sendto(makepacket.encode(), i)
                            date_time = dt.datetime.now().strftime("%d/%m/%Y, %H:%M:%S.%f")
                            message2 = "serversnd   " + str(date_time) + "    D     " + str(seqNum+datatran) + "    " + str(datatran) + "   " + str(ACKnum) + "\n"
                        else:
                            date_time = dt.datetime.now().strftime("%d/%m/%Y, %H:%M:%S.%f")
                            message = 'Current time is ' + date_time
                            clientSocket.sendto(message.encode(), i)
                            print('Sending time to', i[0], 'listening at', i[1], 'at time ', date_time)
                            makepacket = "%d/%d/%d/" % (count, seqNum, ACKnum)
                            clientSocket.sendto(makepacket.encode(), i)
                            message3 = "serversnd   " + str(date_time) + "    D     " + str(seqNum) + "    " + str(datatran) + "   " + str(ACKnum) + "\n"
                            f = open("Sender_log.txt", "a")
                            f.write(message3)
                            f.close()
                            time.sleep(0.1)

                            date_time = dt.datetime.now().strftime("%d/%m/%Y, %H:%M:%S.%f")
                            message3 = "packetdrop  " + str(date_time) + "    D     " + str(seqNum+datatran) + "    " + str(datatran) + "   " + str(ACKnum) + "\n"
                            f = open("Sender_log.txt", "a")
                            f.write(message3)
                            f.close()

                            #retransmit
                        
                            date_time = dt.datetime.now().strftime("%d/%m/%Y, %H:%M:%S.%f")
                            message = 'Current time is ' + date_time
                            clientSocket.sendto(message.encode(), i)
                            print('Sending time to', i[0], 'listening at', i[1], 'at time ', date_time)
                            makepacket = "%d/%d/%s/%d/" % (count, seqNum+datatran, data, ACKnum)
                            SenderBytes += 3 * 4 + datatran
                            clientSocket.sendto(makepacket.encode(), i)
                            date_time = dt.datetime.now().strftime("%d/%m/%Y, %H:%M:%S.%f")
                            message2 = "serversnd   " + str(date_time) + "    D     " + str(seqNum+datatran) + "    " + str(datatran) + "   " + str(ACKnum) + "\n"
                    else:#normal transmit
                        start = time.time()
                        date_time = dt.datetime.now().strftime("%d/%m/%Y, %H:%M:%S.%f")
                        message = 'Current time is ' + date_time
                        clientSocket.sendto(message.encode(), i)
                        print('Sending time to', i[0], 'listening at', i[1], 'at time ', date_time)
                        makepacket = "%d/%d/%s/%d/%f/" % (count, seqNum, data, ACKnum, start)
                        SenderBytes += 4*4+datatran
                        clientSocket.sendto(makepacket.encode(), i)
                        if(count == 1):
                            message2 = "serversnd   " + str(date_time) + "    D     " + str(seqNum) + "     " + str(datatran) + "   " + str(ACKnum) + "\n"
                        else:
                            message2 = "serversnd   " + str(date_time) + "    D     " + str(seqNum) + "    " + str(datatran) + "   " + str(ACKnum) + "\n"
                    # generate Sender_log.txt
                    f = open("Sender_log.txt", "a")
                    f.write(message2)
                    f.close()
                    count += 1


            #notify other thread
            t_lock.notify()
        #sleep for UPDATE_INTERVAL
        time.sleep(UPDATE_INTERVAL)


#we will use two sockets, one for sending and one for receiving
clientSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(('localhost', serverPort))

recv_thread=threading.Thread(name="RecvHandler", target=recv_handler)
recv_thread.daemon=True
recv_thread.start()



send_thread=threading.Thread(name="SendHandler",target=send_handler)
send_thread.daemon=True
send_thread.start()


#this is the main thread
while True:
    time.sleep(0.1)


s