"""
This is a daemon to control an Olevia television via a serial port. The model
I used when writing this was a 247T FHD. However, this model wasn't in the
documentation that I got. Any Olevia TV based on the MTK MDDi video processor
will probably work.

Also of note, when you power the TV up, separately from these commands, it has
a neat little command line that you can access, with command history and
everything. Pretty cool, eh?

When run, this will bind on a port and allow for commands to be sent to the TV.
The allowable commands are in the olevia_commands dictionary below.

TODO: Add functionality to read the status of the TV, etc.

There's a 10 second delay when you issue the poweron command, because of power
up time before I can send the initialization sequence. This might be a problem
if you need a non-blocking command. All other commands are quick, and therefore
aren't a problem.

References:
    1) Chad Schroeder's "Creating a daemon the Python way"
    2) Olevia's support web site, where I got the RS232 command list

Special requires:
    1) Twister
    2) Serial support
"""

__author__ = "Chris Moates <six@mox.net>"
__copyright__ = "Copyright (C) 2007 Chris Moates"
__revision__ = "$Id$"
__version__ = "0.1"

# Configuration directives
# Set these as needed for your system
telnet_port = 53535
serial_port = 0

# These are just shorthand to make the dictionary smaller
preamble25 = '\xbe\x05\x25'
preamble26 = '\xbe\x05\x26'
preamble27 = '\xbe\x05\x27'
preamble90 = '\xbe\x05\x90'
preambleresponse = '\x06\x05\x90'

# This is the list of commands that can be sent to the TV. Note that not all
# commands are supported by all TV's. Mine, for example, has only 1 tuner,
# so tuner2 does nothing. "Illegal" commands appear to be ignored, so it looks
# safe to send something that your TV doesn't support.
olevia_commands = {
'poweron': '\x00',
'init': '\x80\x80\x00\x00\x01\x00\x80\x80\x30\x0d\x30\x30\x30\x2e\x30\x65\x30\x74\x30\x0d',
'poweroff':      preamble27+'\x00\xea',
'mute':          preamble25+'\x09\xf1',
'one':           preamble25+'\x11\xf9',
'two':           preamble25+'\x12\xfa',
'three':         preamble25+'\x13\xfb',
'four':          preamble25+'\x14\xfc',
'five':          preamble25+'\x15\xfd',
'six':           preamble25+'\x16\xfe',
'seven':         preamble25+'\x17\xff',
'eight':         preamble25+'\x18\x00',
'nine':          preamble25+'\x19\x01',
'zero':          preamble25+'\x10\xf8',
'channelreturn': preamble25+'\x1a\x02',
'dash':          preamble25+'\x59\x41',
'mts':           preamble25+'\x40\x28',
'menu':          preamble25+'\x04\xec',
'enter':         preamble25+'\x1b\x03',
'up':            preamble25+'\x45\x2d',
'down':          preamble25+'\x4a\x32',
'right':         preamble25+'\x07\xef',
'left':          preamble25+'\x0a\xf2',
'favorite':      preamble25+'\x46\x2e',
'display':       preamble25+'\x1e\x06',
'volumeup':      preamble25+'\x02\xea',
'volumedown':    preamble25+'\x03\xeb',
'channelup':     preamble25+'\x00\xe8',
'channeldown':   preamble25+'\x01\xe9',
'source':        preamble25+'\x0b\xf3',
'view':          preamble25+'\x0e\xf6',
'swap':          preamble25+'\x0f\xf7',
'freeze':        preamble25+'\x55\x3d',
'closedcaption': preamble25+'\x48\x30',
'aspect':        preamble25+'\x56\x3e',
'vgaautosync':   preamble25+'\x50\x38',
'lighting':      preamble25+'\x20\x08',
'sleep':         preamble25+'\x22\x0a',
'info':          preamble25+'\x23\x0b',
'tuner1':        preamble26+'\x00\xe9',
'tuner2':        preamble26+'\x01\xea',
'composite1':    preamble26+'\x02\xeb',
'composite2':    preamble26+'\x03\xec',
'svideo1':       preamble26+'\x05\xee',
'svideo2':       preamble26+'\x06\xef',
'component1':    preamble26+'\x08\xf1',
'component2':    preamble26+'\x09\xf2',
'vga':           preamble26+'\x0a\xf3',
'vgacomponent':  preamble26+'\x0b\xf4',
'hdmi1':         preamble26+'\x0c\xf5',
'hdmi2':         preamble26+'\x0e\xf7'
}
# shortcuts to above commands
olevia_commands['1'] =  olevia_commands['one']
olevia_commands['2'] =  olevia_commands['two']
olevia_commands['3'] =  olevia_commands['three']
olevia_commands['4'] =  olevia_commands['four']
olevia_commands['5'] =  olevia_commands['five']
olevia_commands['6'] =  olevia_commands['six']
olevia_commands['7'] =  olevia_commands['seven']
olevia_commands['8'] =  olevia_commands['eight']
olevia_commands['9'] =  olevia_commands['nine']
olevia_commands['0'] =  olevia_commands['zero']
olevia_commands['previous'] =  olevia_commands['channelreturn']
olevia_commands['cc'] =  olevia_commands['closedcaption']

# These are commands which return something.
olevia_status_commands = {
'readpowerstatus': preamble90+'\x00\x53',
'readinputsource': preamble90+'\x01\x54',
'readmutestatus':  preamble90+'\x02\x55',
'readvolumevalue': preamble90+'\x03\x56'
}

olevia_status_replies = {
'readpowerstatus': {
         # There is no response for power off
         preambleresponse+'\x01\x9c': 'power on'
    },
'readinputsource': {
         preambleresponse+'\x00\x9b': 'Tuner 1',
         preambleresponse+'\x01\x9c': 'Tuner 2',
         preambleresponse+'\x02\x9d': 'Composite 1',
         preambleresponse+'\x03\x9e': 'Composite 2',
         preambleresponse+'\x05\xa0': 'S-Video 1',
         preambleresponse+'\x06\xa1': 'S-Video 2',
         preambleresponse+'\x08\xa3': 'Component 1',
         preambleresponse+'\x09\xa4': 'Component 2',
         preambleresponse+'\x0a\xa5': 'VGA',
         preambleresponse+'\x0b\xa6': 'VGA Component',
         preambleresponse+'\x0c\xa7': 'HDMI 1',
         preambleresponse+'\x0e\xa9': 'HDMI 2'
    },
'readmutestatus': {
         preambleresponse+'\x00\x9b': 'mute off',
         preambleresponse+'\x01\x9c': 'mute on'
    },
'readvolumevalue': {
         preambleresponse+'\x00\x9b': '0',
         preambleresponse+'\x01\x9c': '1',
         preambleresponse+'\x02\x9d': '2',
         preambleresponse+'\x03\x9e': '3',
         preambleresponse+'\x04\x9f': '4',
         preambleresponse+'\x05\xa0': '5',
         preambleresponse+'\x06\xa1': '6',
         preambleresponse+'\x07\xa2': '7',
         preambleresponse+'\x08\xa3': '8',
         preambleresponse+'\x09\xa4': '9',
         preambleresponse+'\x0a\xa5': '10',
         preambleresponse+'\x0b\xa6': '11',
         preambleresponse+'\x0c\xa7': '12',
         preambleresponse+'\x0d\xa8': '13',
         preambleresponse+'\x0e\xa9': '14',
         preambleresponse+'\x0f\xaa': '15',
         preambleresponse+'\x10\xab': '16',
         preambleresponse+'\x11\xac': '17',
         preambleresponse+'\x12\xad': '18',
         preambleresponse+'\x13\xae': '19',
         preambleresponse+'\x14\xaf': '20',
         preambleresponse+'\x15\xb0': '21',
         preambleresponse+'\x16\xb1': '22',
         preambleresponse+'\x17\xb2': '23',
         preambleresponse+'\x18\xb3': '24',
         preambleresponse+'\x19\xb4': '25',
         preambleresponse+'\x1a\xb5': '26',
         preambleresponse+'\x1b\xb6': '27',
         preambleresponse+'\x1c\xb7': '28',
         preambleresponse+'\x1d\xb8': '29',
         preambleresponse+'\x1e\xb9': '30',
         preambleresponse+'\x1f\xba': '31',
         preambleresponse+'\x20\xbb': '32',
         preambleresponse+'\x21\xbc': '33',
         preambleresponse+'\x22\xbd': '34',
         preambleresponse+'\x23\xbe': '35',
         preambleresponse+'\x24\xbf': '36',
         preambleresponse+'\x25\xc0': '37',
         preambleresponse+'\x26\xc1': '38',
         preambleresponse+'\x27\xc2': '39',
         preambleresponse+'\x28\xc3': '40',
         preambleresponse+'\x29\xc4': '41',
         preambleresponse+'\x2a\xc5': '42',
         preambleresponse+'\x2b\xc6': '43',
         preambleresponse+'\x2c\xc7': '44',
         preambleresponse+'\x2d\xc8': '45',
         preambleresponse+'\x2e\xc9': '46',
         preambleresponse+'\x2f\xca': '47',
         preambleresponse+'\x30\xcb': '48',
         preambleresponse+'\x31\xcc': '49',
         preambleresponse+'\x32\xcd': '50',
         preambleresponse+'\x33\xce': '51',
         preambleresponse+'\x34\xcf': '52',
         preambleresponse+'\x35\xd0': '53',
         preambleresponse+'\x36\xd1': '54',
         preambleresponse+'\x37\xd2': '55',
         preambleresponse+'\x38\xd3': '56',
         preambleresponse+'\x39\xd4': '57',
         preambleresponse+'\x3a\xd5': '58',
         preambleresponse+'\x3b\xd6': '59',
         preambleresponse+'\x3c\xd7': '60',
         preambleresponse+'\x3d\xd8': '61',
         preambleresponse+'\x3e\xd9': '62',
         preambleresponse+'\x3f\xda': '63',
         preambleresponse+'\x40\xdb': '64',
         preambleresponse+'\x41\xdc': '65',
         preambleresponse+'\x42\xdd': '66',
         preambleresponse+'\x43\xde': '67',
         preambleresponse+'\x44\xdf': '68',
         preambleresponse+'\x45\xe0': '69',
         preambleresponse+'\x46\xe1': '70',
         preambleresponse+'\x47\xe2': '71',
         preambleresponse+'\x48\xe3': '72',
         preambleresponse+'\x49\xe4': '73',
         preambleresponse+'\x4a\xe5': '74',
         preambleresponse+'\x4b\xe6': '75',
         preambleresponse+'\x4c\xe7': '76',
         preambleresponse+'\x4d\xe8': '77',
         preambleresponse+'\x4e\xe9': '78',
         preambleresponse+'\x4f\xea': '79',
         preambleresponse+'\x50\xeb': '80',
         preambleresponse+'\x51\xec': '81',
         preambleresponse+'\x52\xed': '82',
         preambleresponse+'\x53\xee': '83',
         preambleresponse+'\x54\xef': '84',
         preambleresponse+'\x55\xf0': '85',
         preambleresponse+'\x56\xf1': '86',
         preambleresponse+'\x57\xf2': '87',
         preambleresponse+'\x58\xf3': '88',
         preambleresponse+'\x59\xf4': '89',
         preambleresponse+'\x5a\xf5': '90',
         preambleresponse+'\x5b\xf6': '91'
    }
}
from twisted.internet import reactor, protocol
import os
import sys
import serial
import time
import binascii

class OleviaTelnetToSerial(protocol.Protocol):
    initialized = "false"
    power = "off"
    def dataReceived(self, data):
        command = data.strip()
        if command == "poweron":
            # baud rate must be 110 for the power on command, but 115200 for all other commands
            ser.baudrate=110
            ser.write('\x00');
            time.sleep(10) # We have to wait a second afterwards, to let it power up
            ser.baudrate=115200
            self.power = "on"
            ser.write(olevia_commands['init'])
            self.initialized = "true"
            self.transport.write("Power on sent, and TV initialized.\n");
        elif command == "poweroff":
            ser.write(olevia_commands['poweroff'])
            self.power = "off"
            self.initialized = "false"
            self.transport.write("Power off sent.\n");
        elif command == "init":
            ser.write(olevia_commands['init'])
            self.initialized = "true"
            self.transport.write("Initialization command sent.\n")
        elif command in olevia_status_commands:
            # These are commands which can return a status. 
            ser.write(olevia_status_commands[command])
            # We should only have to read 5 characters but I occasionally get
            # extra 0x06's for no apparent reason, and I can't predict when that will
            # occur. So instead, I read 100 bytes and then only take the last 5.
            response = ser.read(100);
            if(response == ''):
                parsed_response = "power off"
                self.power = "off"
                self.initialized = "false"
                self.transport.write("No response received. Power is off.\n")
            else:
                response=response[-5:]
                if response in olevia_status_replies[command]:
                    parsed_response = olevia_status_replies[command][response]
                    self.transport.write("%s: %s\n" % (command, parsed_response))
                else:
                    self.transport.write("%s: received %s but don't understand that reply.\n" % (command, binascii.hexlify(response)))
                if command == "readpowerstatus":
                    # in the case where we can read the power status,
                    # then we know it's initialized and powered up, so set
                    # that accordingly
                    self.power = "on"
                    self.initialized = "true"
        elif command in olevia_commands:
            if(self.power == "on"):
                ser.write(olevia_commands[command])
                self.transport.write("Command %s found and executed.\n" % (command))
            else:
                self.transport.write("Couldn't send %s command; power is off.\n" % command)
        elif command == "status":
            self.transport.write("TV Power: %s\n" % self.power)
            self.transport.write("Initialized: %s\n" % self.initialized)
            self.transport.write("Serial Info: %s\n" % ser)
        else:
            self.transport.write("Received unknown command: %s\n" % (command))
        if command == "quit":
            os._exit(0)
#end Class OleviaTelnetToSerial

UMASK = 0
WORKDIR = "/tmp"
MAXFD = 1024
ser = serial.Serial()

if(hasattr(os, 'devnull')):
    REDIRECT_TO = os.devnull
else:
    REDIRECT_TO = '/dev/null'

def createDaemon():
    try:
        pid = os.fork()
    except OSError, e:
        raise Exception, "%s [%d]" % (e.strerror, e.errno)
    
    if(pid==0): # The first child
        os.setsid()
        
        try:
            pid = os.fork()
        except OSError, e:
            raise Exception, "%s [%d]" % (e.strerror, e.errno)
    
        if(pid==0):
            os.chdir(WORKDIR)
            os.umask(UMASK)
        else:
            os._exit(0)
    else:
        os._exit(0)

    import resource
    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    if(maxfd==resource.RLIM_INFINITY):
        maxfd = MAXFD

    factory = protocol.ServerFactory()
    factory.protocol = OleviaTelnetToSerial
    ser.port = serial_port
    ser.baudrate = 115200
    ser.timeout = .25
    ser.open()
    reactor.listenTCP(telnet_port,factory)
    reactor.run()
    
    for fd in range(0,maxfd):
        try:
            os.close(fd)
        except OSError:
            pass
    
    os.open(REDIRECT_TO, os.O_RDWR)
    os.dup2(0,1)
    os.dup2(0,2)
    return(0)

if __name__ == "__main__":
    retCode = createDaemon()
    sys.exit(retCode)
