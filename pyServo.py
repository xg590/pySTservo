import sys
sys.path.append("/home/pi/scservo_sdk")
from scservo_sdk.port_handler import PortHandler
from scservo_sdk.sms_sts      import sms_sts

class serialBusServo:
    def __init__(self, 
                 DEVICENAME='/dev/ttyACM0', # Check which port is being used on your controller for DEVICENAME, 
                                            # eg) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"
                 BAUDRATE  =1000000):       # STServo default baudrate : 1000000
        self.portHandler = PortHandler(DEVICENAME) # Initialize PortHandler instance
        if self.portHandler.openPort():
            print("Succeeded to open the port")
        else:
            print("Failed to open the port")
            raise
        if self.portHandler.setBaudRate(BAUDRATE): # Set port baudrate
            print("Succeeded to change the baudrate")
        else:
            print("Failed to change the baudrate")
            raise
        self.packetHandler = sms_sts(self.portHandler) # Initialize PacketHandler instance
        return None

    def __change_addr__(self, original_addr, new_addr):
        REG_ID   = 0x05
        REG_LOCK = 0x37
        self.packetHandler.write1ByteTxRx(original_addr, REG_LOCK,        0) # unlock EPROM
        self.packetHandler.write1ByteTxRx(original_addr, REG_ID  , new_addr) # set new ID
        self.packetHandler.write1ByteTxRx(new_addr     , REG_LOCK,        1) # lock EPROM

    def __set_posi_corr__(self, addr=1, step=0):
        if step > 2047 : raise
        REG_CORR = 0x1F # position correction in step
        REG_LOCK = 0x37 # eprom lock
        self.packetHandler.write1ByteTxRx(addr, REG_LOCK,    0) # unlock EPROM
        self.packetHandler.write2ByteTxRx(addr, REG_CORR, step)
        self.packetHandler.write1ByteTxRx(addr, REG_LOCK,    1) # lock EPROM
        
    def __get_posi_corr__(self, addr=1):
        REG_CORR = 0x1F # position correction in step 
        step, result, error = self.packetHandler.read2ByteTxRx(addr, REG_CORR)
        return step, result, error
    
    def __set_torque_mode__(self, addr=1, mode='free'):
        REG_TORQUE = 0x28
        mode = {'free': 0, 'torque': 1, 'damped': 2}[mode]
        self.packetHandler.write1ByteTxRx(addr, REG_TORQUE, mode)

    def get_mode(self, addr=1):
        REG_MODE = 0x21
        mode, result, error = servo.packetHandler.read1ByteTxRx(addr, REG_MODE)
        return ['posi', 'wheel', 'pwm', 'step'][mode]

    def set_mode(self, addr=1, mode='posi'):
        REG_MODE = 0x21
        mode = ['posi', 'wheel', 'pwm', 'step'].index(mode)
        result, error = servo.packetHandler.write1ByteTxRx(addr, REG_MODE, mode)
        return result, error
    
    def move2Pos(self, addr=1, posi=0, speed=800, acc=100):
        self.packetHandler.WritePosEx(addr, posi, speed, acc)