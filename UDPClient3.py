#Python 3
#Usage: python3 UDPClient3.py localhost 12000
#coding: utf-8
from socket import *
import sys,json,time,os
import datetime as dt

#Server would be running on the same host as Client
serverName = sys.argv[1]
serverPort = int(sys.argv[2])
clientSocket = socket(AF_INET, SOCK_DGRAM)
check = 0
receivedBytes = 0
datatran = 0
#first-way handshake
date_time = dt.datetime.now().strftime("%d/%m/%Y, %H:%M:%S.%f")
message2 = {"SYNbit":1, "Seq":1000, "time":date_time, "data":0, "Ack":0}
message = json.dumps(message2)
clientSocket.sendto(message.encode(), (serverName, serverPort))
print("clientsnd   " + str(date_time) + "    S     " + str(message2["Seq"]) + "   "+ str(message2["data"]) + "      " + str(message2["Ack"]))

#second-way handshake
receivedMessage, serverAddress = clientSocket.recvfrom(2048)
receivedMessage = json.loads(receivedMessage.decode())
fullData = []
if (receivedMessage["SYNbit"] == 1 and receivedMessage["ACKbit"] == 1 and receivedMessage["Seq"] == 5000 and receivedMessage["Ack"] == message2["Seq"]+1):
    print("serverrcv   " + str(receivedMessage["time"]) + "    SA    " + str(receivedMessage["Seq"]) + "   " + str(receivedMessage["data"]) + "      " + str(receivedMessage["Ack"]))
    #time.sleep(1)
    #third-way handshake
    date_time = dt.datetime.now().strftime("%d/%m/%Y, %H:%M:%S.%f")
    message2 = {"ACKbit": 1, "Seq":receivedMessage["Ack"], "time":date_time, "data":0, "Ack":receivedMessage["Seq"]+1}
    message = json.dumps(message2)
    clientSocket.sendto(message.encode(), (serverName, serverPort))
    print("clientsnd   " +  str(date_time) + "    A     " + str(message2["Seq"]) + "   " + str(message2["data"]) + "      " + str(message2["Ack"]))
    receivedMessage, serverAddress = clientSocket.recvfrom(2048)
    data2 = receivedMessage.decode().split('/')
    if (data2[0] == "3-way handshake success"):
        datatran = int(data2[3]) #(MSW/MSS)
        message = input("3-way Connection has been made, please type Subscribe\n")
        clientSocket.sendto(message.encode(),(serverName, serverPort))
        #wait for the reply from the server
        receivedMessage, serverAddress = clientSocket.recvfrom(2048)
    if (receivedMessage.decode()=='Subscription successfull'):
        #Wait for 10 back to back messages from server
        for i in range((int(data2[1])+int(data2[2]))*2): #data[1]is packet number in string format
            receivedMessage, serverAddress = clientSocket.recvfrom(datatran+500)
            data = receivedMessage.decode()
            if (i % 2 == 1):
                data = data.split('/')
                if (len(data) == 4):#reply duplicate ACKs
                    check = data[0]
                    print('check is ', check)
                    seqNum = int(data[2])
                    ACKnum = int(data[1]) + datatran
                    print('seqNum is ', seqNum, ' ACKnum is ', ACKnum)
                    makepacket = "%s/%d/%d/" % (check, seqNum, ACKnum)
                    clientSocket.sendto(makepacket.encode(), (serverName, serverPort))
                elif (len(data) == 5):
                    fullData.append(data[2])
                    check = data[0]
                    print('check is ', check)
                    seqNum = int(data[3])
                    ACKnum = int(data[1]) + datatran
                    print('seqNum is ', seqNum, ' ACKnum is ', ACKnum)
                    makepacket = "%s/%d/%d/" % (check, seqNum, ACKnum)
                    #Data Received (in bytes) increments – do not include retransmitted data
                    receivedBytes += len(check)+4+4
                    clientSocket.sendto(makepacket.encode(), (serverName, serverPort))
                else:
                    end = time.time()
                    duration = end - float(data[4])
                    print('duration is ', duration)
                    fullData.append(data[2])
                    check = data[0]
                    print('check is ', check)
                    seqNum = int(data[3])
                    ACKnum = int(data[1]) + datatran
                    print('seqNum is ', seqNum, ' ACKnum is ', ACKnum)
                    makepacket = "%s/%d/%d/%s/" % (check, seqNum, ACKnum, duration)
                    # Data Received (in bytes) increments – do not include retransmitted data
                    receivedBytes += len(check)+4+4+4
                    clientSocket.sendto(makepacket.encode(), (serverName, serverPort))

            else:
                print(receivedMessage.decode())
        #generate new txt file in the same directory
        with open('New Sample Text File.txt', 'w') as file:
            for line in fullData:
                file.write(line)
        #first-way wave
        receivedMessage, serverAddress = clientSocket.recvfrom(2048)
        receivedMessage = json.loads(receivedMessage.decode())
        print("serversnd   " + str(receivedMessage["time"]) + "    F     " + str(receivedMessage["Seq"]) + "   " + str(receivedMessage["data"]) + "      " + str(receivedMessage["Ack"]))
        #second-third-way waves
        date_time = dt.datetime.now().strftime("%d/%m/%Y, %H:%M:%S.%f")
        message2 = {"FINbit":1, "ACKbit":1, "Seq":receivedMessage["Ack"], "Ack":receivedMessage["Seq"]+1, "time":date_time, "data":0 , "receivedBytes":receivedBytes}
        print("clientrcv   " + str(message2["time"]) + "    FA    " + str(message2["Seq"]) + "    " + str(message2["data"]) + "      " + str(message2["Ack"]))
        message = json.dumps(message2)
        clientSocket.sendto(message.encode(), (serverName, serverPort))
        #fourth-way wave
        receivedMessage, serverAddress = clientSocket.recvfrom(2048)
        receivedMessage = json.loads(receivedMessage.decode())
        print("serversnd   " + str(receivedMessage["time"]) + "    A     " + str(receivedMessage["Seq"]) + "   " + str(receivedMessage["data"]) + "      " + str(receivedMessage["Ack"]))
        # prepare to exit. Send Unsubscribe message to server
        if (receivedMessage["ACKbit"] == 1 and receivedMessage["Ack"] == message2["Seq"]+1):
            print('4-way Termination has been made, Connection close')
            message = 'Unsubscribe'
            clientSocket.sendto(message.encode(), (serverName, serverPort))
            receivedMessage, serverAddress = clientSocket.recvfrom(2048)
            print(receivedMessage.decode())
            # Close the socket
            clientSocket.close()
    else:
        # Close the socket
        clientSocket.close()
else:
    # Close the socket
    clientSocket.close()



