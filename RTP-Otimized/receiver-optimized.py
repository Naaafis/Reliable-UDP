###############################################################################
# receiver.py
# Name: Nafis Abeer, Chase Maivald
# BU ID: U98285639, U18719879
###############################################################################

import sys
import socket

from util import *

#send ack function for start and end messages
def send_start_end_ack(sock, seqno, address): 
    pkt_header = PacketHeader(type=3, seq_num=seqno + 1, length=0)
    #pkt_header.checksum = compute_checksum(pkt_header / "")
    #pkt = pkt_header / ""
    sock.sendto(str(pkt_header), address)


# sending acks for data messages 
def send_data_ack(sock, seqno, address): #the seqnum to be sent will be auto updated to what it should be
    pkt_header = PacketHeader(type=3, seq_num=seqno, length=0)
    #pkt_header.checksum = compute_checksum(pkt_header / "")
    #pkt = pkt_header / ""
    sock.sendto(str(pkt_header), address)

def receiver(receiver_port, window_size):
    """ TODO: Listen on socket and print received message to sys.stdout """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('127.0.0.1', receiver_port))

    # start flag to indicate that we can start receiving data
    start_flag = 1 # when 0, we can receive data

    expected_seqnum = 0 # the first expected sequence number of the data packets is 0
                        # increment expected_seqnum by 1 if the packet received is the next packet
                        # don't increment expected_seqnum if the next packet_received is subsequent packets, just place it in the window
    
    if (window_size <= 1):
        recv_buffer_size = window_size
    else:
        recv_buffer_size = window_size - 1
    
    receive_buffer = [None] * recv_buffer_size # stored messages of ahead of order packets (first packet of buffer would just be printed directly)
    

    while True:
        # receive packet
        pkt, address = s.recvfrom(PACKETSIZE)

        # extract header and payload
        pkt_header = PacketHeader(pkt[:16])
        msg = pkt[16:16+pkt_header.length]

        if pkt_header.type == 0 and start_flag == 1:
           # print("received start information... \n")
            #pkt_checksum = pkt_header.checksum
            #pkt_header.checksum = 0
            #computed_checksum = compute_checksum(pkt_header / msg)
            #if pkt_checksum == computed_checksum:
           # sys.stdout.write("connection established \n")
            sys.stdout.flush()
            send_start_end_ack(s, pkt_header.seq_num, address)
            start_flag = 0

        if pkt_header.type == 1 and start_flag == 0:
           # print("received end information... \n")
            #pkt_checksum = pkt_header.checksum
            #pkt_header.checksum = 0
            #computed_checksum = compute_checksum(pkt_header / msg)
            #if pkt_checksum == computed_checksum:
            #   send_ack(s, pkt_header.seq_num, address)
           # sys.stdout.write("connection terminated \n")
            sys.stdout.flush()
            send_start_end_ack(s, pkt_header.seq_num, address)
            start_flag = 1
            expected_seqnum = 0 #so now it waits for data to have a sequence number of 0

        if pkt_header.type == 2 and start_flag == 0:
            # implement receiver sliding window
            # take the first piece of actual data we receive and ack it
            # set the expected seq_num to one more than current seq_num
            # only except subsequent data if the seq_num of that data matches the expected data
            # only store buffer into actual output file if seq_num == first_seq_num + windowsize, cuz that means we're done receiving 
            # previous window

            working_seqnum = pkt_header.seq_num
            #three cases with wokring_seqnum
            #if working_seqnum is expected_seqnum, increment expected_seqnum and place msg into output file directly
            #also check buffer and until an empty position of buffer is reached 
            pkt_checksum = pkt_header.checksum
            pkt_header.checksum = 0
            computed_checksum = compute_checksum(pkt_header / msg)

            in_receiver_window = expected_seqnum + window_size #needed so if working window size is less than this, its going into receiver buffer

            if working_seqnum == expected_seqnum and pkt_checksum == computed_checksum: #if expected packet it received
                sys.stdout.write(msg) #just place packet content directly into output buffer
                sys.stdout.flush() #dk what it does but it works
                expected_seqnum = expected_seqnum + 1 #now expecting packet with the next sequence number
                loop_until = 1; #this will be used to loop through receive buffer and add its contents to output buffer
                index = 0;
                while loop_until: #this will not slide, only empty buffer indices that get placed into output buffer and increment expected seq_num
                    if index < window_size - 1:
                        if receive_buffer[index]: #put buffer into output one by one
                            message = receive_buffer[index]
                            sys.stdout.write(message) 
                            sys.stdout.flush()  # dk what it does but it works
                            expected_seqnum = expected_seqnum + 1 #placing packets in order so we increment what we are expecting
                            receive_buffer[index] = None #empty that index of the buffer because we will eventually have to move the first none value up
                            index = index + 1 #move on to next 
                        else:
                            loop_until = 0
                    else:
                        loop_until = 0

                #aight now we slideeeeeeee
                first_encounter = 0
                temp_buffer = []
                for i in range(window_size - 1):
                    message2 = receive_buffer[i]
                    if message2: #see if the receive buffer has something in the first spot this function basically accomplishes nothing
                        first_encounter = 1
                    if first_encounter:
                        temp_buffer.append(message2) #slideeeeee so now first index is first available element
                
                if first_encounter: #basically updates receive_buffer if it wasn't empty in the first place
                    receive_buffer = [None] * window_size - 1 #empty receive buffer, its contents are in temp_buffer, just slid up
                    size_of_temp_buffer = len(temp_buffer)
                    # for j in range(size_of_temp_buffer):
                    #     receive_buffer[j] = temp_buffer[j] # copy contents
                    upper_bound = window_size - 1
                    receive_buffer = temp_buffer[:]
                    for k in range (size_of_temp_buffer, upper_bound):
                        receive_buffer[k] = None     

            elif working_seqnum > expected_seqnum and working_seqnum < in_receiver_window and pkt_checksum == computed_checksum: 
                #if not expected number but still less than windowsize from current expected number

                #say the expected sequence number is 2 but we get 3, and window size is 3
                #where would we place 3 based on logic provided?
                #see the receive buffer in this scenario should hold 2 numbers, because the the third number (seqnum 2) is going 
                #   directly to output buffer if it shows up
                #with that said, the receive buffer has a size of window_size - 1
                #the 0 index of the receive buffer holds any packets thats 1 ahead out of order
                #that means if we get 3 it should be in index 0
                #if we get 4 it should go to index 1
                how_many_ahead = working_seqnum - expected_seqnum
                index2 = how_many_ahead - 1 #because index 0 is actually the 1 ahead case and 1 is the 2 ahead case and so on
                receive_buffer[index2] = msg
                # print("\nHave seqnum: ") 
                # print(working_seqnum) 
                # print(" in buffer, its contents are: ") 
                # print(msg) 
                # print("\n")
            
            #else:
            #    continue #dont do nothing if the working sequence number is out of range or if packet messed up checksum by corrupting data

            send_data_ack(s, working_seqnum, address) #send that ack babbyyy
            # print("\nexpected sequence number is: ")
            # print(expected_seqnum)
            # print("\n")

            # expected_seqnum = pkt_header.seq_num + 1
            # next_window_seq_num = expected_seqnum + window_size
            # pkt_checksum = pkt_header.checksum
            # pkt_header.checksum = 0
            # computed_checksum = compute_checksum(pkt_header / msg)
            # if pkt_checksum == computed_checksum:
            #     message_buffer.append(msg)
            #     send_ack(s, pkt_header.seq_num, address)
            # else we will keep waiting for first valid data entry, which will eventually 
            # be sent because sender did not yet receive ack for first packet sent
            # for i in range()


        # verify checksum
        # pkt_checksum = pkt_header.checksum
        # pkt_header.checksum = 0
        # computed_checksum = compute_checksum(pkt_header / msg)
        # if pkt_checksum != computed_checksum:
        #     print ("checksums not match")

        # print payload
        # print (msg)

def main():
    """Parse command-line argument and call receiver function """
    if len(sys.argv) != 3:
        sys.exit("Usage: python receiver.py [Receiver Port] [Window Size]")
    receiver_port = int(sys.argv[1])
    window_size = int(sys.argv[2])
    receiver(receiver_port, window_size)

if __name__ == "__main__":
    main()
