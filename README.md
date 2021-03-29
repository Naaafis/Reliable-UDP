# Reliable-UDP

This implements a sliding window with cumalitive ack checks in order to send reliable data over the "best effort" UDP protocol. The UTIL file provides a checksum function to ensure the data being received is correct. The Sender resends a window if the expected packet on the receiver side does has not yet been revceived. The receiver stores ahead of order packets in a receiver window until the expected packet is received then places the entire window into the output beffuer before clearing the receiving window. 

The second set of sender and receiver takes into account the fact that the receiver side has a window to store ahead of order packet, as it forces the sender to take those received packets out of the sending window before resending the window. 
