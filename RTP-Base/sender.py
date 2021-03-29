###############################################################################
# sender.py
# Name: Nafis Abeer, Chase Maivald
# BU ID: U98285639, U18719879
###############################################################################

import sys
import socket
import time
from random import randint

from util import *

def formPacket(data, sequence_number):
    size_of_line = len(data)
    data_pkt_header_function = PacketHeader(type=2, seq_num=sequence_number, length=size_of_line)
    data_pkt_header_function.checksum = compute_checksum(data_pkt_header_function / data)
    data_pkt_function = data_pkt_header_function / data
    return data_pkt_function


def sender(receiver_ip, receiver_port, window_size):
    """TODO: Open socket and send message from sys.stdin"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("connecting to UDP receiver...")

    #address = (receiver_ip, receiver_port)

    random_start_seqnum = randint(0,20000) #randomize sequence number 

    start_pkt_header = PacketHeader(type=0, seq_num=random_start_seqnum, length=0)
    s.sendto(str(start_pkt_header), (receiver_ip, receiver_port)) #starting thing doesnt really need data

    print("waiting for receiver to initiate connection...")

    while True:
        #time.sleep(0.5) #wait a little before sending data
        pkt, address = s.recvfrom(PACKETSIZE)
        # extract header and payload
        pkt_header = PacketHeader(pkt[:16])
        if pkt_header.seq_num == random_start_seqnum + 1:
            #connection has been established we can break out of this loop and start sending the rest of the data
            print('start ack received')
            break
        else:  # something went wrong and we must restablish a connection
            start_pkt_header = PacketHeader(type=0, seq_num=0, length=0)
            s.sendto(str(start_pkt_header), (receiver_ip, receiver_port))

    ####### implement sliding window logic
    print("\nsending data...\n")
    
    seqnum = 0  # 0 as the initial sequence number for data packets, this will always be the sequence number of the first packet in buffer
    temp_seqnum = 0 # this will update seq nums sent for current set of packets
    done = 0  # if this is one we have successfully sent all the data
    done_reading = 0  # done reading the buffer, this will signify that the last packet has been created
    sending_buffer = [] # will store window of packet contents
    for i in range(window_size):  # initialize a starting window, we will later slide it as necessary 
        line = sys.stdin.read(READ_BUFSIZE)
        if line:
            sending_buffer.append(line)
        else:
            done_reading = 1

    
    #hold = 1

    while not done:
        #s.settimeout(0.5)
        #for_three = 0
        #print("\n beginning of outside loop \n")

        
        for data in sending_buffer:
            data_pkt = formPacket(data, temp_seqnum)
            #if not hold:
            s.sendto(str(data_pkt), (receiver_ip, receiver_port))
            # print("\n sent seqnum: ")
            # print(temp_seqnum)
            # print(" \n")
            temp_seqnum += 1
            # hold = 0

        #lets test out of order packets

        #recv instead of recvfrom
        receiving = 1
        s.settimeout(0.5)
        while receiving:
            #print("\nreceving\n")
            try:
                ack_pkt, address = s.recvfrom(1472)
                ack_pkt_header = PacketHeader(ack_pkt[:16])
                if ack_pkt_header.seq_num > seqnum: #first packet of window has been received so now do a few things:
                    #1. pop the correct amount from sending buffer to account for the fact that a new expected sequence number is received
                    #2. add the correct amount of lines to sending buffer 
                    #3. update sequence number of the first packet, along with temp_seqnum so the right sequence numbers could be assigned to new packets
                    #4. break back out of this while loop and send the new packets out

                    get_diff_in_seqnums = ack_pkt_header.seq_num - seqnum #how many packets ahead is it
                    #print("the difference in seuence numbers is: ")
                    #print(get_diff_in_seqnums)
                    #print("\n")
                    for i in range(get_diff_in_seqnums): #get rid of that many lines from sending buffer
                        sending_buffer.pop(0)
                    
                    # now read in new lines into the buffer
                    for i in range(get_diff_in_seqnums): #see the difference in sequence numbers will never exceed the window size, b/c the reiver window isnt bigger than the window size
                        line = sys.stdin.read(READ_BUFSIZE)
                        if line:
                            sending_buffer.append(line)
                        else:
                            done_reading = 1

                    #print("expected seqnum is: ")
                    #print(ack_pkt_header.seq_num)
                    #print("\n")

                    seqnum = ack_pkt_header.seq_num #update first seqnum to that of expected sequence number 
                    #print("\nSlideeeeeee ")
                    #print(sending_buffer)
                    #print("\n")
                    temp_seqnum = seqnum #update this jawn to be the number for the first packet too
                    receiving = 0
            except socket.timeout:
                temp_seqnum = seqnum #reset 
                print("\n timeout occured \n")
                s.settimeout(None)
                receiving = 0 
                continue

        size_of_sending_buffer = len(sending_buffer) #shall be empty if all data hath been sent out

        if(done_reading and size_of_sending_buffer == 0):  # if by some miracle we get to this point, we've both finished reading the buffer and finished sending it as well
            done = 1
        
    
    ####### end game

    print("completed sending data...")
    end_pkt_header = PacketHeader(type = 1, seq_num = 0, length=0)
    s.sendto(str(end_pkt_header),(receiver_ip, receiver_port))
    print("waiting for receiver to acknowledge end of connection...")
    while True:
        pkt, address = s.recvfrom(PACKETSIZE)
        # extract header and payload
        pkt_header = PacketHeader(pkt[:16])
        if pkt_header.seq_num == end_pkt_header.seq_num + 1:
            #connection has been established we can break out of this loop and end sending the rest of the data
            print('end ack received')
            break
        else:  # something went wrong and we must resend request to end connection
            time.sleep(0.5)
            end_pkt_header = PacketHeader(type=1, seq_num=0, length=0)
            s.sendto(str(end_pkt_header), (receiver_ip, receiver_port))

    #pkt_header = PacketHeader(type=2, seq_num=10, length=14)
    #pkt_header.checksum = compute_checksum(pkt_header / "Hello, world!\n")
    #pkt = pkt_header / "Hello, world!\n"
    #s.sendto(str(pkt), (receiver_ip, receiver_port))

def main():
    """Parse command-line arguments and call sender function """
    if len(sys.argv) != 4:
        sys.exit("Usage: python sender.py [Receiver IP] [Receiver Port] [Window Size] < [message]")
    receiver_ip = sys.argv[1]
    receiver_port = int(sys.argv[2])
    window_size = int(sys.argv[3])
    sender(receiver_ip, receiver_port, window_size)

if __name__ == "__main__":
    main()
