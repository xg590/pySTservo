#!/usr/bin/env python
import serial, time

# define baud rate 
BAUD_RATE = {'1M':0,'500K':1,'250K':2,'128K':3,'115200':4,'76800':5,'57600':6,'38400':7}

class ST3215:
    def __init__(self, port='COM7', baudrate = 1_000_000):
        # eg) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"
        self.ser = serial.Serial(port=port, baudrate=baudrate, bytesize=serial.EIGHTBITS, timeout=0)
        self.model = 'STS'
        self.ser.timeout = 3
        return None

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, value):
        if value == 'STS': # {'ST3215': 0, 'SC09': 1}
            self.MEM_ADDR_EPROM_LOCK = 0x37

            # define memory table
            #-------EPROM(read only)--------
            SMS_STS_MODEL                = 0x03
            
            #-------EPROM(read & write)--------
            self.MEM_ADDR_ID                  = 0x05
            self.MEM_ADDR_BAUD_RATE           = 0x06
            self.MEM_ADDR_STEP_CORR           = 0x1F
            self.MEM_ADDR_MODE                = 0x21
            
            #-------SRAM(read & write)--------
            self.MEM_ADDR_TORQUE_ENABLE       = 0x28
            self.MEM_ADDR_ACC                 = 0x29
            self.MEM_ADDR_GOAL_POSITION       = 0x2A
            self.MEM_ADDR_GOAL_TIME           = 0x2C
            self.MEM_ADDR_GOAL_SPEED          = 0x2E
            self.MEM_ADDR_EPROM_LOCK          = 0x37
            
            #-------SRAM(read only)--------
            self.MEM_ADDR_PRESENT_POSITION    = 0x38
            self.MEM_ADDR_PRESENT_SPEED       = 0x3A
            self.MEM_ADDR_PRESENT_LOAD        = 0x3C
            self.MEM_ADDR_PRESENT_VOLTAGE     = 0x3E
            self.MEM_ADDR_PRESENT_TEMPERATURE = 0x3F
            self.MEM_ADDR_MOVING              = 0x42
            self.MEM_ADDR_PRESENT_CURRENT     = 0x45

        elif value == 'SCS':
            self.MEM_ADDR_EPROM_LOCK = 0x30
        else:
            raise
        self._model = value

    def __make_packet__(self, id, instruction, params):
        length = len(params) + 2
        checksum = 255 - (id + length + instruction + sum(params)) & 0xFF
        packet = [0xFF, 0xFF, id, length, instruction] + params + [checksum]
        return bytearray(packet)
    
    def __recv_packet__(self, id, params_in_bytes=False):
        # 0xFF 0xFF id length error params checksum
        TIMEOUT = 3 # raise an Error in case no response while one is expected
        _t = time.time()
        while True:
            header = self.ser.read(2)
            if b'\xff\xff' == header:
                break
            if time.time() - _t > TIMEOUT:
                print(f'[Error] [ID: {id}] Timeout for __recv_packet__]')
                print(f'[Debug] [ID: {id}] Response: {header}')
                raise TimeoutError
        _id       = int.from_bytes(self.ser.read(   1   ))
        _length   = int.from_bytes(self.ser.read(   1   ))
        _data     =                self.ser.read(_length)
        data      = list(_data)
        error     = data[0   ]
        _params   = data[1:-1]
        _checksum = data[  -1]
        try:
            assert id == _id
        except AssertionError:
            print(f'sender id: {id}, receiver id: {_id}')
        assert _checksum == 255 - (_id + _length + error + sum(_params)) & 0xFF
        if params_in_bytes:
            return error, _data[1:-1]
        else:
            return error, _params
        
    def ping(self, id):
        params = []
        instruction = 0x01
        packet = self.__make_packet__(id, instruction, params)
        self.ser.write(packet)
        try: 
            status, _params = self.__recv_packet__(id)
            return status, _params
        except TimeoutError:
            return None

    def read(self, id, byte_addr, byte_len):
        params = [byte_addr, byte_len]
        instruction = 0x02
        packet = self.__make_packet__(id, instruction, params)
        self.ser.write(packet)
        status, _params = self.__recv_packet__(id, params_in_bytes=True)
        return status, _params

    def write(self, id, byte_addr, byte_arr):
        # 输入的数据byte_arr应当是一个list，但如果是数字，也帮忙转换成list。
        if isinstance(byte_arr, list):
            pass
        elif isinstance(byte_arr, int):
            if byte_arr < 256:
                byte_arr = [byte_arr]
            elif byte_arr < 65536:
                byte_arr = [byte_arr , byte_arr>>8]
            else:
                raise
        else:
            raise
        params = [byte_addr] + byte_arr
        instruction = 0x03
        packet = self.__make_packet__(id, instruction, params)
        self.ser.write(packet)
        status, _params = self.__recv_packet__(id)
        return status, _params

    def reg_write(self, id, byte_addr, byte_arr):
        # 两次发信完成同步，第一次发信给每个舵机，要改什么，每个舵机可改的东西不一样。
        params = [byte_addr] + byte_arr
        instruction = 0x04
        packet = self.__make_packet__(id, instruction, params)
        self.ser.write(packet)
        status, _params = self.__recv_packet__(id)
        return status, _params

    def action(self):
        # 广播消息，无返回。
        self.ser.write(b'\xFF\xFF\xFE\x02\x05\xFA')
        return None

    def sync_write(self, id_arr, byte_addr, byte_arr, debug=False):
        # 广播消息，无返回。
        # 一次发信同步完成，但每个舵机被改的地址都一样，比如都是改速度。
        id = 0xFE
        instruction = 0X83
        if not isinstance(id_arr, list): raise
        if     isinstance(byte_arr[0], int ): params = [byte_addr, len(byte_arr   )] + [j for id       in     id_arr            for j in [id] + byte_arr]
        elif   isinstance(byte_arr[0], list): params = [byte_addr, len(byte_arr[0])] + [j for id, byte in zip(id_arr, byte_arr) for j in [id] + byte    ]
        else: raise
        packet = self.__make_packet__(id, instruction, params)
        if debug: print('packet', [hex(i) for i in packet])
        self.ser.write(packet)
        return None
        
    def sync_read(self, id_arr, byte_addr, byte_len, debug=False): # id, byte_addr, 
        # 一次发信同步完成，但每个舵机被改的地址都一样，比如都是改速度。
        id = 0xFE
        instruction = 0X82
        params = [byte_addr, byte_len] + id_arr
        packet = self.__make_packet__(id, instruction, params)
        self.ser.write(packet)
        _dict = {}
        for _id in id_arr:
            status, _params = self.__recv_packet__(_id, params_in_bytes=True)
            _dict[_id] = {'status': status, 'params': _params}
        return _dict

    def __change_addr__(self, original_dev_id, new_dev_id):
        self.write(original_dev_id, self.MEM_ADDR_EPROM_LOCK,          0) # unlock EPROM
        self.write(original_dev_id, self.MEM_ADDR_ID        , new_dev_id) # set new ID
        self.write(new_dev_id     , self.MEM_ADDR_EPROM_LOCK,          1) # lock EPROM

    def __set_posi_corr__(self, dev_id=1, step=0, save=False):
        if step > 2047 or step < -2047 :
            raise
        elif step >= 0:
            step = [ step & 0xFF, step >> 8]
        else: # negative number
            step *= -1
            step += 0x800
            step = [ step & 0xFF, step >> 8]
        if self.model == 'SCS': raise # There is no position correction for SCS servo
        if save: self.write(dev_id, self.MEM_ADDR_EPROM_LOCK,   0) # unlock EPROM
        self.write(dev_id, self.MEM_ADDR_STEP_CORR, step)
        if save: self.write(dev_id, self.MEM_ADDR_EPROM_LOCK,   1) # lock EPROM
        
    def __get_posi_corr__(self, dev_id=1):
        if self.model == 'SCS': raise # There is no position correction for SCS servo
        status, _params = self.read(dev_id, self.MEM_ADDR_STEP_CORR, 2)
        corr = int.from_bytes(_params, byteorder='little')
        if corr > 0x800:
            corr -= 0x800
            corr *= -1
        return status, corr

    def __set_torque_mode__(self, dev_id=1, mode='free'):
        if self.model not in ['STS', 'SCS']: raise
        mode = {'free': 0, 'torque': 1, 'damped': 2}[mode]
        self.write(dev_id, self.MEM_ADDR_TORQUE_ENABLE, mode)

    def set_mode(self, dev_id=1, mode='posi'):
        if self.model == 'SCS': raise
        mode = ['posi', 'wheel', 'pwm', 'step'].index(mode)
        result, error = self.write(dev_id, self.MEM_ADDR_MODE, mode)
        return result, error

    def get_mode(self, dev_id=1):
        if self.model == 'SCS': raise # There is only one mode for SCS servo
        status, _params = self.read(dev_id, self.MEM_ADDR_MODE, )
        mode = int.from_bytes(_params)
        return ['posi', 'wheel', 'pwm', 'step'][mode]

    def move2Posi(self, dev_id=1, posi=0, velo=800, acc=100):
        if acc > 254 or acc < 0: raise
        if velo > 0xFFFF      : raise
        if isinstance(posi, list): # 每个servo一个goal posi
            byte_arr = []
            for s in posi:
                if s > 0x0FFF : raise
                byte_arr.append([acc, s & 0xFF, s >> 8, 0x00, 0x00, velo & 0xFF, velo >> 8])
            self.sync_write(dev_id, self.MEM_ADDR_ACC, byte_arr)
    
    def readPosi(self, dev_id=1, debug=False):
        if   isinstance(dev_id, int): dev_id = [dev_id]
        elif isinstance(dev_id, list): pass
        else: raise
        old_dict = self.sync_read(dev_id, self.MEM_ADDR_PRESENT_POSITION, 6, debug=debug)
        new_dict = {}
        for _id in dev_id:
            if old_dict[_id]['status'] == 0:
                new_dict[_id] = {}
                new_dict[_id]['posi'] = int.from_bytes(old_dict[_id]['params'][0:2], byteorder='little')
                new_dict[_id]['velo'] = int.from_bytes(old_dict[_id]['params'][2:4], byteorder='little')
                new_dict[_id]['load'] = int.from_bytes(old_dict[_id]['params'][4:6], byteorder='little')
            else:
                print('[ERROR]', _id, old_dict[_id])
        return new_dict
