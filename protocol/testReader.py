import serial
import sys
from time import sleep
import binascii
import crc16
import codecs
import struct

BAUD = 38400
PORT = "/dev/ttyUSB0"
SER_TIMEOUT = 0.065
SER_WRITE_TIMEOUT = 0.03


#Global Variables
ser = 0
dicA = {'ver': '', 'seq': '' }

#Function to Initialize the Serial Port
def init_serial():
    
    global ser          #Must be declared in Each Function
    ser = serial.Serial()
    ser.baudrate = BAUD
    ser.port = PORT 
    #a little less than polling spped from arduino
    ser.timeout = SER_TIMEOUT
    #ser.write_timeout = SER_WRITE_TIMEOUT
    ser.open()          #Opens SerialPort

    # print port open or closed
    if ser.isOpen():
        print ('Open: ' + ser.portstr)
    #sleep(1)    
#Function Ends Here
        

#Call the Serial Initilization Function, Main Program Starts from here
init_serial()
sleep(1)

def crccitt(hex_string):
    byte_seq = binascii.unhexlify(hex_string)
    crc = crc16.crc16xmodem(byte_seq, 0xffff)
    return '{:04X}'.format(crc & 0xffff)

def read_all(port, chunk_size=200):
    """Read all characters on the serial port and return them."""
    
    if not port.isOpen():
        raise SerialException('Serial is diconnected')  
    if not port.timeout:
        raise TypeError('Port needs to have a timeout set!')

    read_buffer = b''

    while True:
        # Read in chunks. Each chunk will wait as long as specified by
        # timeout. Increase chunk_size to fail quicker
        byte_chunk = port.read(size=chunk_size)
        read_buffer += byte_chunk
        if not len(byte_chunk) == chunk_size:
            break
    port.reset_input_buffer()
    return read_buffer

#ser.flush()
count = 0

global in_pkt

in_pkt={'sequence_count': 0,            # bytes  0- 1 - rpi unsigned short int
            'packet_version': 0,             # byte 2      - rpi unsigned char
            'mode_value': 0,                 # byte 3      - rpi unsigned char
            'respiratory_rate_measured': 0, # bytes 4 - 7 - rpi unsigned int
            'respiratory_rate_set': 0,      # bytes 8 - 11
            'tidal_volume_measured': 0,     # bytes 12 - 15
            'tidal_volume_set': 0,          # bytes 16 - 19
            'ie_ratio_measured': 0,         # bytes 20 - 23
            'ie_ratio_set': 0,              # bytes 24 - 27
            'peep_value_measured': 0,       # bytes 28 - 31
            'peak_pressure_measured': 0,    # bytes 32 - 35
            'plateau_value_measured': 0,    # bytes 36 - 39
            'pressure_measured': 0,         # bytes 40 - 43
            'flow_measured': 0,             # bytes 44 - 47
            'volume_in_measured': 0,        # bytes 48 - 51
            'volume_out_measured': 0,       # bytes 52 - 55
            'volume_rate_measured': 0,      # bytes 56 - 59
            'control_state': 0,              # byte 60       - rpi unsigned char
            'battery_level': 0,              # byte 61
            'reserved': 0,                  # bytes 62 - 63 - rpi unsigned int
            'alarm_bits': 0,                # bytes 64 - 67
            'crc': 0 }                      # bytes 68 - 69 

global cmd_pkt

cmd_pkt = {'sequence_count': 0,               # bytes 1 - 2 - rpi unsigned short int
                'packet_version': 0,                         # byte 3      - rpi unsigned char
                'mode_value': 0,                             # byte 4      - rpi unsigned char
                'respiratory_rate_set': 0, # bytes 5 - 8 - rpi unsigned int
                'tidal_volume_set':  0,         # bytes 9 - 12
                'ie_ratio_set':  0,             # bytes 13 - 16
                'alarm_bits':   0,              # bytes 17 - 20
                'crc':   0 }                    # bytes 21 - 22 - rpi unsigned short int  
    
def process_in_serial():
    global ser
    global in_pkt
    global cmd_pkt        
    #ser.reset_input_buffer()
    error_count = 0
    prevByte = 0
    #sleep(1)
    byteData = b''
    ValidPkt = 0
    prevSeq = -1
    while True:
        print('begin:')
        byteData = read_all(ser, 70)
        if len(bytearray(byteData)) != 70:
            #byteData = b''
            print('reread')
            byteData = read_all(ser, 70)
        # else:
        #     ValidPkt += ValidPkt
            
        #byteData = ser.read(70)
        #2 ways to print
        # print (byteData)  #raw will show ascii if can be decoded
        #hex only -- byte order is reversed
        print(''.join(r'\x'+hex(letter)[2:] for letter in byteData))
        if byteData[0:2] == b'\x00\x00':
            prevSeq = -1 
            currentSeq = int.from_bytes(byteData[0:2], byteorder='little')
        else:
            prevSeq = (int.from_bytes(byteData[0:2], byteorder='little') - 1)
            currentSeq = int.from_bytes(byteData[0:2], byteorder='little')
            
            #TO DO -- Map all packets to parameter structs
                
        if  currentSeq !=  ( prevSeq + 1) :
            print ("There appears to be Sequence Error")
            print (currentSeq)
            print (prevSeq)
        
        #if (int.from_bytes(byteData[0:2], byteorder='little') - PrevSeq ) == 1 :
        in_pkt['sequence_count']=int.from_bytes(byteData[0:2], byteorder='little')
        in_pkt['packet_version']=int.from_bytes(byteData[2:3], byteorder='little')
        in_pkt['mode_value']=int.from_bytes(byteData[3:4], byteorder='little')
        in_pkt['crc']=int.from_bytes(byteData[68:70], byteorder='little')
        
        print ('Received SEQ and CRC:')
        print (in_pkt['sequence_count'])
        print (in_pkt['crc'])
        calcRcvCRC = crccitt(byteData[0:68].hex())
        print("Calculated CRC:")
        print (int(calcRcvCRC, 16))
        if in_pkt['crc'] != int(calcRcvCRC,16):
            print ("Mismatch")
            error_count = error_count + 1
            ValidPkt += ValidPkt
            print ('Dropped packets count ' + str(error_count))
            print ('Valid packets count ' + str(ValidPkt))
            
        else:    
            cmd_pkt['sequence_count'] = in_pkt['sequence_count']
            sendPkts(cmd_pkt['sequence_count'], in_pkt['crc'])
        
    
        # error_count = error_count + 1
        # print ('Dropped packets count ' + str(error_count))
        # print ('Valid packets count ' + str(ValidPkt))
        

def sendPkts(seq_cnt, crc):
    global ser
    global in_pkt
    global cmd_pkt
    byteData = b''
    #prevByte = (int.from_bytes(byteData[1:3], byteorder='little') - 1)
    endian = "little"
    cmd_byteData = b''
    start_byte = 0xFF
    packet_version = 1

    cmd_byteData += bytes(seq_cnt.to_bytes(2, endian))
    cmd_byteData += bytes(in_pkt['packet_version'].to_bytes(1, endian))
    cmd_byteData += bytes(cmd_pkt['mode_value'].to_bytes(1, endian))
    cmd_byteData += bytes(cmd_pkt['respiratory_rate_set'].to_bytes(4, endian))
    cmd_byteData += bytes(cmd_pkt['tidal_volume_set'].to_bytes(4, endian))
    cmd_byteData += bytes(cmd_pkt['ie_ratio_set'].to_bytes(4, endian))
    cmd_byteData += bytes(cmd_pkt['alarm_bits'].to_bytes(4, endian))
    #Get CRC
    calcCRC = crccitt(cmd_byteData.hex())
    print ('CALC CRC HEX and byte: ')
    # flip the bits
    CRCtoSend = struct.pack('<Q', int(calcCRC, base=16))
    print(calcCRC)
    print (CRCtoSend)
    cmd_byteData += CRCtoSend[0:2]
    cmd_pkt['crc']  = bytes.fromhex(calcCRC)
    
    if (len(bytearray(cmd_byteData))) == 22:
        i = 0
        try:
            for i in range(len(cmd_byteData)):
                ser.write(cmd_byteData[i:i+1])
                #self.ser.write(cmd_byteData)
                #self.ser.reset_output_buffer()
        except serial.SerialException:
            print('Serial write error')
    else:
        print ('Data packet too long')
    print('length wrote CRC Length CRC Array:')
    print (len(bytearray(cmd_byteData)))
    #print (len(CRCtoSend))
    #print (bytearray(CRCtoSend))
    CRCtoSend = None        
    #print(bytearray(cmd_byteData))
    
    print("Sent back SEQ and CRC: ")
    # print(''.join(r'\x'+hex(letter)[2:] for letter in cmd_byteData))
    print (int.from_bytes(cmd_byteData[0:2], byteorder='little'))
    print (int.from_bytes(cmd_byteData[20:], byteorder='little'))
    byteData = b'\x00'
    
if __name__ == '__main__':
    process_in_serial()



