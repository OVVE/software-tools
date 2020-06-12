import matplotlib.pyplot as plt
import numpy as np
import time
import sys
from time import sleep
from datetime import datetime
import struct
import crc16
import os
from struct import *
from collections import namedtuple
from pprint import pprint 

#


#plot configuration

#just add plotX variables containing a list of variables you want to plot in one figure. 
#It is a 2-dim array, so you may define multiple plots per figure which are synchronized in the X-axis 
#Also add a label per figure and then add the figureX variable to figures. Everything else is done by the script below
figure1=[['currentFlow','targetAirFlow','controlI','currentPressure'],['controlOutputFiltered'],['controlLimitHit','controlForceHome','control_state']]
figure2=[['respiratory_rate_set','respiratory_rate_measured'],['tidal_volume_set','volume_in_measured'],['ie_ratio_set','ie_ratio_measured']]
figure3=[['pressure_measured','peep_value_measured','peak_pressure_measured','plateau_value_measurement']]
figure4=[['inhalationTrajectoryStartFlow','inhalationTrajectoryEndFlow','inhalationTrajectoryInitialFlow','inhalationTrajectoryPhaseShiftEstimate']]
figure5=[['pressure_measured','flow_measured','volume_out_measured']]
#figureX=...
figureLabels=['Controller','Settings','Pressures','Trajectory','Debug']
figures=[figure1,figure2,figure3,figure4,figure5]


#global vars
seqNum=0
msgType=0
crcCalc=0
rxCnt=0
packetLen=0
recCrc=0
rxData=bytearray()
rxState=0
statPacketRxCntCrcFail=0
statPacketRxCntOk=0
statPacketRxCntHeaderFail=0
xarray=[]
xarray2=[]
xarray3=[]
yarray=[]
yarray2=[]
yarray3=[]
lastTime=0
timeOffset=0
oldProtocol=0
lastTimeUserPacket=0


#prefill the plot data structure
plotDataX=[[[]]]
plotDataY=[[[]]]
for i in range(len(figures)):
    plotDataX.append([])
    plotDataY.append([])
    for j in range(len(figures[i])):
        plotDataX[i].append([])
        plotDataY[i].append([])
        for z in range(len(figures[i][j])):
            plotDataX[i][j].append([])
            plotDataY[i][j].append([])



def updt(total, progress):
    """
    Displays or updates a console progress bar.

    Original source: https://stackoverflow.com/a/15860757/1391441
    """
    barLength, status = 20, ""
    progress = float(progress) / float(total)
    if progress >= 1.:
        progress, status = 1, ""
    block = int(round(barLength * progress))
    text = "\r[{}] {:.0f}% {}".format(
        "#" * block + "-" * (barLength - block), round(progress * 100, 0),
        status)
    sys.stdout.write(text)
    sys.stdout.flush()


def handleRxByte(byte) -> None:
    global rxState
    global seqNum
    global msgType
    global crcCalc
    global rxCnt
    global packetLen
    global recCrc
    global rxData
    global statPacketRxCntHeaderFail
    global statPacketRxCntOk
    global statPacketRxCntCrcFail
    global oldProtocol

    if rxState == 0:
        if byte== 0x26: #check for first sync byte
            rxState=1
    elif rxState == 1:
        if byte== 0x56: #check for 2nd sync byte
            rxState=2
        elif byte!= 0x26: #make sure to catch S1S1S2S3 sync byte combination
            rxState=0
            statPacketRxCntHeaderFail+=1
    elif rxState == 2:
        if byte== 0x7E: #check for 3rd sync byte
            rxState=3
        else:
            rxState=0
            statPacketRxCntHeaderFail+=1
    elif rxState==3:
        crcCalc = crc16.crc16xmodem(byte.to_bytes(1, 'little'), 0xffff) #init CRC with 0xffff
        seqNum=byte    #lower byte of seq no
        rxState=4
    elif rxState==4:
        crcCalc = crc16.crc16xmodem(byte.to_bytes(1, 'little'), crcCalc)
        seqNum+=byte<<8 #high byte of seq no
        rxState=5
    elif rxState==5:
        crcCalc = crc16.crc16xmodem(byte.to_bytes(1, 'little'), crcCalc)
        if byte!=4: #check protocol version
            rxState=0
        else:
            rxState=6
    elif rxState==6:
        crcCalc = crc16.crc16xmodem(byte.to_bytes(1, 'little'), crcCalc)
        msgType=byte #store packetType
        rxState=7
        rxCnt=0
        rxData=bytearray()
    elif rxState==7:
        crcCalc = crc16.crc16xmodem(byte.to_bytes(1, 'little'), crcCalc)
        packetLen=byte #store length
        if (packetLen<128): #128 is max
            rxState=8
        else:
            statPacketRxCntLenFail+=1
            rxState=0
    elif rxState==8:
        crcCalc = crc16.crc16xmodem(byte.to_bytes(1, 'little'), crcCalc)
        rxData.append(byte) #save data
        rxCnt+=1
        if rxCnt==packetLen:
            rxState=9
    elif rxState==9:
        recCrc=byte #low byte crc
        rxState=10
    elif rxState==10:
        recCrc|=byte<<8 #high byte crc
        if recCrc==crcCalc: #check crc
            statPacketRxCntOk+=1
            processPacket(rxData,msgType,seqNum)
        else:
            statPacketRxCntCrcFail+=1
        rxState=0 #restart state machine
        
def processPacket(byteData, packetType, sequenceNo):

# old protocol (before alarms):
#typedef struct __attribute__((packed)) {
#  uint8_t mode_value;                 // byte 3      - rpi unsigned char
#  uint32_t respiratory_rate_measured; // bytes 4 - 7 - rpi unsigned int
#  uint32_t respiratory_rate_set;      // bytes 8 - 11
#  int32_t tidal_volume_measured;      // bytes 12 - 15
#  int32_t tidal_volume_set;           // bytes 16 - 19
#  uint32_t ie_ratio_measured;         // bytes 20 - 23
#  uint32_t ie_ratio_set;              // bytes 24 - 27
#  int32_t peep_value_measured;        // bytes 28 - 31
#  int32_t peak_pressure_measured;     // bytes 32 - 35
#  int32_t plateau_value_measurement;  // bytes 36 - 39
#  int32_t pressure_measured;          // bytes 40 - 43
#  int32_t flow_measured;              // bytes 44 - 47
#  int32_t volume_in_measured;         // bytes 48 - 51
#  int32_t volume_out_measured;        // bytes 52 - 55
#  int32_t volume_rate_measured;       // bytes 56 - 59
#  uint8_t control_state;              // byte 60       - rpi unsigned char
#  uint8_t battery_level;              // byte 61
#  uint16_t reserved;                  // bytes 62 - 63 - rpi unsigned int
#  uint32_t alarm_bits;                // bytes 64 - 67
#} data_packet_def;

#
# typedef struct __attribute__((packed)) {
#   uint8_t mode_value;                        // byte 4
#   uint8_t control_state;                     // byte 5
#   uint8_t battery_status;                    // byte 6
#   uint8_t reserved;                          // byte 7
#   uint16_t respiratory_rate_set;             // bytes 8 - 9  
#   uint16_t respiratory_rate_measured;        // bytes 10 - 11
#   int16_t tidal_volume_set;                  // bytes 12 - 13
#   int16_t tidal_volume_measured;             // bytes 14 - 15
#   uint16_t ie_ratio_set;                     // bytes 16 - 17
#   uint16_t ie_ratio_measured;                // bytes 18 - 19
#   int16_t peep_value_measured;               // bytes 20- 21
#   int16_t peak_pressure_measured;            // bytes 22 - 23
#   int16_t plateau_value_measurement;         // bytes 24 - 25
#   int16_t pressure_set;                      // bytes 26 - 27
#   int16_t pressure_measured;                 // bytes 28 - 29
#   int16_t flow_measured;                     // bytes 30 - 31
#   int16_t volume_in_measured;                // bytes 32 - 33
#   int16_t volume_out_measured;               // bytes 34 - 35
#   int16_t volume_rate_measured;              // bytes 36 - 37
#   int16_t high_pressure_limit_set;           // bytes 38 - 39
#   int16_t low_pressure_limit_set;            // bytes 40 - 41
#   int16_t high_volume_limit_set;             // bytes 42 - 43
#   int16_t low_volume_limit_set;              // bytes 44 - 45
#   int16_t high_respiratory_rate_limit_set;   // bytes 46 - 47
#   int16_t low_respiratory_rate_limit_set;    // bytes 48 - 49
#   uint32_t alarm_bits;                       // bytes 50 - 53
# } data_packet_def;

    global lastTime
    global plotDataX
    global plotDataY
    global timeOffset
    global lastTimeUserPacket
    if packetType==0x01:
        if oldProtocol==1:
            packet = namedtuple('packet','mode_value repiratory_rate_measured respiratory_rate_set tidal_volume_measured tidal_volume_set ie_ratio_measured ie_ratio_set peep_value_measured peak_pressure_measured plateau_value_measurement pressure_measured flow_measured volume_in_measured volume_out_measured volume_rate_measured control_state battery_level reserved alarm_bits')
            currentPacket = packet(*unpack('<BIIiiIIiiiiiiiiBBHI', byteData))
        else:
            packet = namedtuple('packet','mode_value control_state battery_status reserved respiratory_rate_set respiratory_rate_measured tidal_volume_set tidal_volume_measured ie_ratio_set ie_ratio_measured peep_value_measured peak_pressure_measured plateau_value_measurement pressure_set pressure_measured flow_measured volume_in_measured volume_out_measured volume_rate_measured high_pressure_limit_set low_pressure_limit_set high_volume_limit_set low_volume_limit_set high_respiratory_rate_limit_set low_respiratory_rate_limit_set alarm_bits')
            currentPacket = packet(*unpack('<BBBBHHhhHHhhhhhhhhhhhhhhhI', byteData))
        
        if lastTimeUserPacket==lastTime:
            lastTime+=100

        for figure in figures:
            for plot in figure:
                for element in plot:
                    value=getattr(currentPacket,element,'none')
                    if value!='none':

                        #do some value specific data scaling
                        if element=='pressure_measured':
                            value/=100.0
                        if element=='peep_value_measured':
                            value/=100.0
                        if element=='peak_pressure_measured':
                            value/=100.0
                        if element=='plateau_value_measurement':
                            value/=100.0
                        if element=='ie_ratio_measured':
                            value/=256.0
                        if element=='ie_ratio_set':
                            value/=256.0

                        plotDataY[figures.index(figure)][figure.index(plot)][plot.index(element)].append(value)
                        plotDataX[figures.index(figure)][figure.index(plot)][plot.index(element)].append(lastTime/1000)
        lastTimeUserPacket=lastTime


#typedef struct __attribute__((packed)){
#  long time; //millis
#  uint32_t targetInhalationTime;
#  uint32_t targetHoldTime;
#  uint32_t targetExhalationTime;
#  float targetAirFlow;
#  float controlI;
#  float controlOutputFiltered;
#  float inhalationTrajectoryStartFlow; //modified start flow
#  float inhalationTrajectoryEndFlow; //modified end flow
#  float inhalationTrajectoryInitialFlow; //flow calculation based on square form
#  int32_t inhalationTrajectoryPhaseShiftEstimate; //compressing the air in the bag causes a delay of flow and we therefore need to estimate the phase shift in timing to allow enough inhale time
#  int32_t currentFlow;
#  int32_t currentPressure;
#  uint8_t controlForceHome;
#  uint8_t inhalationTrajectoryInitialCycleCnt;
#  uint8_t controlLimitHit;
#} CONTROL_LOG_DATA;

    elif packetType==0x81:
        packet = namedtuple('packet','time targetInhalationTime targetHoldTime targetExhalationTime targetAirFlow controlI controlOutputFiltered inhalationTrajectoryStartFlow inhalationTrajectoryEndFlow inhalationTrajectoryInitialFlow inhalationTrajectoryPhaseShiftEstimate currentFlow currentPressure controlForceHome inhalationTrajectoryInitialCycleCnt controlLimitHit')
        currentPacket = packet(*unpack('<iIIIffffffiiiBBB', byteData))
        
        if currentPacket.time+timeOffset>lastTime:
            lastTime=currentPacket.time+timeOffset
        else:
            timeOffset=lastTime
            lastTime=timeOffset+currentPacket.time

        for figure in figures:
            for plot in figure:
                for element in plot:
                    value=getattr(currentPacket,element,'none')


                    if value!='none':
                        #do some value specific data scaling
                        if element=='currentPressure':
                            value/=100.0
                        plotDataY[figures.index(figure)][figure.index(plot)][plot.index(element)].append(value)
                        plotDataX[figures.index(figure)][figure.index(plot)][plot.index(element)].append(lastTime/1000)
                        
#main code

if len(sys.argv)>1:
    
    if (sys.argv[1]=="-1"):
        print('Usage: python3 playlog filname\n   Options: -1: older format before May 28th')
    else:
    
        #open log and process all packets
        print('Reading logfile: '+str(sys.argv[1]))

        fileLen=os.path.getsize(sys.argv[1])
        if len(sys.argv)>2:
            if (sys.argv[2]=="-1"):
                oldProtocol=1
        bytesRead=0
        with open(str(sys.argv[1]),"rb") as f:
            byteData = f.read(1024*64)
            bytesRead+=len(byteData)
            while len(byteData) != 0:
                # Do stuff with byte.
                updt(fileLen,bytesRead+1)
                for byte in byteData:
                    handleRxByte(byte)
                byteData = f.read(1024*64)
                bytesRead+=len(byteData)
                
        print('\nReading file...Done')
        print('Decoded: '+str(statPacketRxCntOk)+' packets and couldnt decode: '+str(statPacketRxCntCrcFail+statPacketRxCntHeaderFail))

        if statPacketRxCntOk==0:
            print('Aborting due to no decoded packets')
        else:
            #create figures and plots
            visibleFigures=[]
            visiblePlots=[]
            for figure in figures:
                fig=plt.figure()
                visibleFigures.append(fig)
                for plot in figure:
                    if figure.index(plot)>0:
                        subplt=fig.add_subplot(len(figures),1,figure.index(plot)+1,sharex=visiblePlots[len(visiblePlots)-figure.index(plot)])
                    else:
                        subplt=fig.add_subplot(len(figures),1,figure.index(plot)+1)
                    visiblePlots.append(subplt)
                    label=''
                    for element in plot:
                        subplt.plot(plotDataX[figures.index(figure)][figure.index(plot)][plot.index(element)],plotDataY[figures.index(figure)][figure.index(plot)][plot.index(element)],label=element)
                        if figure.index(plot)>0:
                            subplt.set(xlabel='time (s)', ylabel='data')
                        else:
                            subplt.set(xlabel='time (s)', ylabel='data',title=figureLabels[figures.index(figure)])
                    subplt.legend(loc='upper right', shadow=True)
                    subplt.grid()
            
            #show everything
            plt.show()

else:
    #usage
    print('Usage: python3 playlog filname\n   Options: -1: older format before May 28th')
