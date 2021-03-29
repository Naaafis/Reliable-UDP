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
    sending_buffer = [None] * window_size # will store window of packet contents, this now has new logic
    first_acked = 0  # if this is one we will slide the window

    for i in range(window_size):  # initialize a starting window, we will later slide it as necessary 
        line = sys.stdin.read(READ_BUFSIZE)
        if line:
            sending_buffer[i] = line
        else:
            done_reading = 1

    hold = 1
    while not done:
        if first_acked: #that means first packet, and possibly subsequent packs were received, so just slide the window in here
            #Todo:
            #1. copy contents of first none "None" packet to the end in sending buffer into a new array
            #2. Update sending buffer
            first_encounter = 0
            temp_buffer = []
            for i in range(window_size):
                temp_data = sending_buffer[i]
                if temp_data:
                    first_encounter = 1
                if first_encounter:
                    temp_buffer.append(temp_data)
                if first_encounter == 0:
                    seqnum += 1 #increment the sequence number here now because we are no longer relying on expected sequence number to update it 

            #the new amount of lines to be read in is window-size - sizeof(temp_buffer)

            temp_size = len(temp_buffer) #if the temporary buffer was empty then the sending buffer was empty and we will read an entire new window in
            upper_bound = window_size #just to set the upper bound how many new lines we read in
            sending_buffer = [None] * window_size
            for indx in range(temp_size):
                sending_buffer[indx] = temp_buffer[indx]
            for k in range (temp_size, window_size):
                line = sys.stdin.read(READ_BUFSIZE)
                if line:
                    sending_buffer[k] = line
                else:
                    done_reading = 1
                    sending_buffer[k] = None  #gotta set empty buffers now because we will use it to determine if the whole thing is empty and we can leave the outermost loop

            #while we are in here, might as well update the first temp number we send out
            temp_seqnum = seqnum 
            first_acked = 0 #new scenario where the first packet of the current window has still not been received          

        for data in sending_buffer:
            if data:
                data_pkt = formPacket(data, temp_seqnum)
                if not hold:
                    s.sendto(str(data_pkt), (receiver_ip, receiver_port))

                temp_seqnum += 1
                hold = 0
            else: #increment temp_seqnum anyways to avoid sending packets out of order
                temp_seqnum += 1

        #lets test out of order packets

        #recv instead of recvfrom
        receiving = 1
        s.settimeout(0.5)
        while receiving:
            #print("\nreceving\n")
            try:
                ack_pkt, address = s.recvfrom(1472)
                ack_pkt_header = PacketHeader(ack_pkt[:16])
                if ack_pkt_header.seq_num > seqnum: #packet inside of window has been received so now do a few things:
                    #1. find out which packet it is 
                    #2. get rid of that packet from the sending buffer
                    #3. continue looping until the first packet is received, or timeout occurs

                    get_diff_in_seqnums = ack_pkt_header.seq_num - seqnum #how many packets ahead is it
                  
                    sending_buffer[get_diff_in_seqnums] = None #drop that packet contents, dont have to resend it
                   
                if ack_pkt_header.seq_num == seqnum:
                    #correct sequence number is received and we can soon leave this loop
                    sending_buffer[0] = None #first packet of sending buffer has been received 
                    first_acked = 1 
                    receiving = 0
                    
            except socket.timeout:
                temp_seqnum = seqnum #reset 
                print("\n timeout occured \n")
                s.settimeout(None)
                receiving = 0 #breaks out of while loop
                continue

        #size_of_sending_buffer = len(sending_buffer) #shall be empty if all data hath been sent out

        good_to_end = 1
        for index in range(window_size):
            dtg = sending_buffer[index]
            if dtg: #if there is still stuff to send in sending buffer
                good_to_end = 0  #don't end the loop

        if(done_reading and good_to_end):  # if by some miracle we get to this point, we've both finished reading the buffer and finished sending it as well
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
