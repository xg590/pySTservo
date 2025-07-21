### Servo and Driver Board
<table>
    <tr>
        <td>
            <a href='https://www.waveshare.net/wiki/SC09_Servo'>SC09</a>
        </td>
        <td>
            <a href='https://www.waveshare.net/wiki/ST3215_Servo'>ST3215</a>
        </td>
    </tr>
    <tr>
        <td><img src='./misc/Servo_SC09.jpg'   height="100"></img></td>
        <td><img src='./misc/Servo_ST3215.jpg' height="100"></img></td>
    </tr>
    <tr>
        <td><a href='https://www.waveshare.net/wiki/Bus_Servo_Adapter_(A)'>Bus Servo Adapter (A)</a></td>
        <td><a href='https://www.waveshare.net/wiki/Servo_Driver_with_ESP32'>Servo Driver with ESP32</a></td>
    </tr>
    <tr>
        <td><img src='./misc/Adapter_A.jpg'   height="100"></img></td>
        <td><img src='./misc/Driver_with_ESP32.jpg' height="100"></img></td>
    </tr>
</table>

### Driver Board Spec
* 输入电压：< 12.6V（输入电压需要与舵机电压匹配）
* 通信接口：UART
* 供电接口：5.5*2.1mm DC
* 产品尺寸：42mm x 33mm
* 固定孔通径：2.5mm 
* 适用舵机：多达253个ST/SC系列总线舵机
### 接线方式
* UART: <b style='color:red'>Tx-Tx, Rx-Rx</b>
### SDK
* Waveshare provides two python SDKs [STServo_Python.zip](https://www.waveshare.net/wiki/%E6%96%87%E4%BB%B6:STServo_Python.zip) and [SCServo_Python.zip](https://www.waveshare.net/wiki/%E6%96%87%E4%BB%B6:SCServo_Python.zip), but only SCServo Python is needed. 
```sh
unzip SCServo_Python.zip scservo_sdk/*
```
### Usage
* Instantiation
```py
import sys, time
sys.path.append("/home/pi/scservo_sdk")
from scservo_sdk.port_handler import PortHandler # Uses STServo SDK library
from scservo_sdk.sms_sts      import sms_sts
from scservo_sdk.scservo_def  import *
class serialBusServo:
    def __init__(self, 
                 DEVICENAME='/dev/ttyACM0', # Check which port is being used on your controller for DEVICENAME, eg) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"
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
        REG_LOCK = 0x37 # you can find the register addr in misc/Comm_Proto_ST3215/磁编码sts-内存表解析_220714_v3.xlsx
        self.packetHandler.write1ByteTxRx(original_addr, REG_LOCK,        0) # unlock EPROM
        self.packetHandler.write1ByteTxRx(original_addr, REG_ID  , new_addr) # set new ID
        self.packetHandler.write1ByteTxRx(new_addr     , REG_LOCK,        1) # lock EPROM

servo = serialBusServo()
```
* Don't forget change <b style="color: red"> scs_end </b> because different servo has different endianness.
* Spin ST3215 servo
```py
servo.packetHandler.scs_end = 0 # {'SC09': 1, 'ST3215': 0}
addr = 2
posi = 4000
speed = 400
acc = 1
servo.packetHandler.WritePosEx(addr, posi, speed, acc)
for i in range(15):
    print(servo.packetHandler.ReadPosSpeed(addr))
    time.sleep(1)
posi = 0
speed = 2400
acc = 0
servo.packetHandler.WritePosEx(addr, posi, speed, acc)
```
* Spin SC09 servo.
```py
servo.packetHandler.scs_end = 1
addr = 1
posi = 1000
speed = 150
acc = 0
servo.packetHandler.WritePosEx(addr, posi, speed, acc)
for i in range(10):
    print(servo.packetHandler.ReadPosSpeed(addr))
    time.sleep(1)
posi = 0
speed = 2400
servo.packetHandler.WritePosEx(addr, posi, speed, acc)
```
* note for myself
```py
def moveSC09ByPosi(addr=1, posi=0, speed=1):
    if posi > 1023: posi = 1023
    REG_POSI = 42 # acceleration does not apply to SC09
    txpacket = [__hibyte__(posi) , __lobyte__(posi), 0, 0,
                __hibyte__(speed), __lobyte__(speed)]
    comm_result, error = packetHandler.writeTxRx(addr, REG_POSI, len(txpacket), txpacket) 
    return None

def moveST3215ByPosi(addr=2, acc=0, posi=0, speed=1):
    if posi > 4095: posi = 4095
    REG_ACC  = 41
    txpacket = [acc,
                __lobyte__(posi) , __hibyte__(posi), 0, 0,
                __lobyte__(speed), __hibyte__(speed)]
    comm_result, error = packetHandler.writeTxRx(addr, REG_ACC, len(txpacket), txpacket) 
    return None
```