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
            self.BYTE_ORDER = 'little'
            # define memory table
            #-------EPROM(read only)--------
            self.SMS_STS_MODEL                = 0x03
            self.MEM_ADDR_ID                  = 0x05

            #-------EPROM(read & write)--------
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
            self.BYTE_ORDER = 'big'
            # define memory table
            #-------EPROM(read only)--------
            self.SMS_STS_MODEL                = 0x03

            #-------EPROM(read & write)--------
            self.MEM_ADDR_ID                  = 0x05
            self.MEM_ADDR_BAUD_RATE           = 0x06

            #-------SRAM(read & write)--------
            self.MEM_ADDR_TORQUE_ENABLE       = 0x28
            self.MEM_ADDR_GOAL_POSITION       = 0x2A
            self.MEM_ADDR_GOAL_SPEED          = 0x2E
            self.MEM_ADDR_EPROM_LOCK          = 0x30

            #-------SRAM(read only)--------
            self.MEM_ADDR_PRESENT_POSITION    = 0x38
            self.MEM_ADDR_PRESENT_SPEED       = 0x3A
            self.MEM_ADDR_PRESENT_LOAD        = 0x3C
            self.MEM_ADDR_PRESENT_VOLTAGE     = 0x3E
            self.MEM_ADDR_PRESENT_TEMPERATURE = 0x3F
            self.MEM_ADDR_MOVING              = 0x42

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
        _id       = int.from_bytes(self.ser.read(   1   ), byteorder=self.BYTE_ORDER)
        _length   = int.from_bytes(self.ser.read(   1   ), byteorder=self.BYTE_ORDER)
        _data     =                self.ser.read(_length)
        data      = list(_data)
        error     = data[0   ]
        _params   = data[1:-1]
        _checksum = data[  -1]
        try:
            assert id == _id
        except AssertionError:
            print(f'[AssertionError] sender id: {id}, receiver id: {_id}')
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
            else:
                byte_arr = list(int.to_bytes(length=2, byteorder=self.BYTE_ORDER, signed=False))
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
        params = [byte_addr, len(byte_arr[0])] + [j for id, byte in zip(id_arr, byte_arr) for j in [id] + byte]
        packet = self.__make_packet__(id, instruction, params)
        if debug: print('packet', [hex(i) for i in packet])
        self.ser.write(packet)
        return None

    def sync_read(self, id_arr, byte_addr, byte_len, debug=False): # id, byte_addr,
        if self.model == 'SCS': 
            print('Sync Read is not avaiable for SCS Servo')
            raise
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
            step = list(step.to_bytes(length=2, byteorder=self.BYTE_ORDER, signed=False))
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
        corr = int.from_bytes(_params, byteorder=self.BYTE_ORDER)
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
        mode = int.from_bytes(_params, byteorder=self.BYTE_ORDER)
        return ['posi', 'wheel', 'pwm', 'step'][mode]

    def set_acc(self, id_arr=[1], acc_arr=[1]):
        self.sync_write(id_arr, self.MEM_ADDR_ACC, acc_arr)

    def get_acc(self, id_arr=[1]):
        self.sync_read(id_arr, self.MEM_ADDR_ACC, 1)

    def move2Posi(self, id_arr=[1], posi_arr=[0], velo_arr=[80]):
        # 每个servo一个goal posi
        byte_arr = []
        for posi, velo in zip(posi_arr, velo_arr):
            posi = list(posi.to_bytes(length=2, byteorder=self.BYTE_ORDER, signed=False))
            velo = list(velo.to_bytes(length=2, byteorder=self.BYTE_ORDER, signed=False))
            byte_arr.append(posi + [0x00, 0x00] + velo)
        self.sync_write(id_arr, self.MEM_ADDR_GOAL_POSITION, byte_arr)

    def readPosi(self, id_arr=[1], debug=False):
        old_dict = self.sync_read(id_arr, self.MEM_ADDR_PRESENT_POSITION, 6, debug=debug)
        new_dict = {}
        for _id in id_arr:
            if old_dict[_id]['status'] == 0:
                new_dict[_id] = {}
                posi = int.from_bytes(old_dict[_id]['params'][0:2], byteorder=self.BYTE_ORDER)
                #print(posi)
                if posi >> 15:
                    new_dict[_id]['posi'] = -1 * (posi & 0x7FFF)
                else: 
                    new_dict[_id]['posi'] = posi & 0xFFF
                new_dict[_id]['velo'] = int.from_bytes(old_dict[_id]['params'][2:4], byteorder=self.BYTE_ORDER)
                new_dict[_id]['load'] = int.from_bytes(old_dict[_id]['params'][4:6], byteorder=self.BYTE_ORDER)
            else:
                print('[ERROR]', _id, old_dict[_id])
        return new_dict

class EncoderUnwrapper:
    def __init__(self, curr_posi=0, abs_max_posi=4095):
        self.last_raw     = None           # 上一次原始读数
        self.posi         = curr_posi      # 累计位置（单位：步）
        self.total_step = abs_max_posi + 1 # 编码器（0~4095）一圈共4096步

    def update(self, raw_value):
        """
        输入编码器原始读数 (0 ~ 4095)，返回连续的累积位置（可正可负）
        """
        if self.last_raw:
            # 计算相对变化量
            delta = raw_value - self.last_raw

            # 处理跳变：如果跨过了0点（顺时针4095->0 或 逆时针0->4095）
            if  delta  >  self.total_step // 2:  # 逆向跳变
                # 假设逆时针转，跳变前100，跳变后4000，delta为正3900，显著大于最大步数的一半
                delta -=  self.total_step
            elif delta < -self.total_step // 2:  # 顺向跳变
                # 假设顺时针转，跳变前4000，跳变后100，delta为负
                delta +=  self.total_step

            # 累加
            self.posi += delta
            self.last_raw = raw_value
            return None

        else:
            # 第一次调用，初始化
            self.last_raw = raw_value
            return None

    def get_degrees(self):
        """返回累计角度，单位：度"""
        return self.posi * (360.0 / self.total_step)

# ==== 使用示例 ====
if __name__ == "__main__":
    encoder = EncoderUnwrapper(curr_posi=10000)

    # 模拟原始读数变化（顺时针转过一圈多一些）
    raw_values = [1, 1000, 2500, 4000, 4090, 4092, 4095, 2, 10, 100, 500, 1000, 2000, 3000, 1]
    raw_values = raw_values[::-1]
    for raw in raw_values:
        encoder.update(raw)
        deg = encoder.get_degrees()
        print(f"raw={raw:4d},  posi={encoder.posi:6d},  deg={deg:8.2f}")

class Calibrator(ST3215):
    def __init__(self, port='COM17', id_arr=[1, 2, 3, 4, 5, 6], abs_max_posi=4095, __set_posi_corr__=True):
        super().__init__(port)
        self.total_step = abs_max_posi + 1
        for _id in id_arr:
            self.__set_torque_mode__(dev_id=_id, mode='free')
            if __set_posi_corr__:
                self.__set_posi_corr__(dev_id=_id, step=0, save=False)
        posi_raw = self.readPosi(id_arr=id_arr)
        encoder = {_id: EncoderUnwrapper(curr_posi=posi_raw[_id]["posi"], abs_max_posi=abs_max_posi)
                    for _id in id_arr}
        for _id in id_arr:
            encoder[_id].min_step = abs_max_posi
            encoder[_id].max_step = 0
            encoder[_id].posi_raw = 0
        self.encoder = encoder
        self.id_arr  = id_arr
        print('initialized')

    def update(self):
        print(f' id |  min |  max |  len | curr |  raw')
        posi_raw = self.readPosi(id_arr=self.id_arr)
        for _id in self.id_arr:
            _posi_raw = posi_raw[_id]["posi"]
            self.encoder[_id].posi_raw = _posi_raw
            self.encoder[_id].update(_posi_raw)
            min_step = self.encoder[_id].min_step
            max_step = self.encoder[_id].max_step
            posi     = self.encoder[_id].posi
            if posi < min_step:
                self.encoder[_id].min_step = posi
            elif posi > max_step:
                self.encoder[_id].max_step = posi
            print(f'{_id:3d} |{min_step: 5d} |{max_step: 5d} |{max_step-min_step: 5d}|{posi: 5d}|{_posi_raw: 5d}')

    def config(self):
        conf = {}
        print(f' id |  min  | range | corr')
        MARGIN = 100
        for _id in self.id_arr:
            min  = self.encoder[_id].min_step
            max  = self.encoder[_id].max_step
            if   min < -2047:
                corr = 4096 + min
            elif min >  2047:
                corr = min - 4096
            else:
                corr = min
            corr -= MARGIN
            if   corr >  2047:
                corr  =  2047
            elif corr < -2047:
                corr  = -2047
            print(f'{_id:3d} | {min: 5d} | {max-min: 5d} | {corr: 5d}')
            conf[_id] = {'min':min, 'range':max-min, 'corr':corr}
        return conf
        '''
        if max - min < 2047:
            if min > 2047:           # min:3500 raw:3500 corr:min-4096
                corr = min - 4096
            elif min > 0:
                corr = min
            elif min < 0:            # min:-500 raw:3500 corr:-500=min
                corr = min
            else:
                raise
        else: # max - min > 2047     #   min    raw   corr
            if   min > 2047:         #  3500   3500   -500=min-4000
                corr = min - 4096
            elif min > 0:            #   500    500    500=min
                corr = min
            elif min < -2047:        # -3500    500    500=4000+min
                corr = 4096 + min
            elif min < 0:            #  -500   3500   -500=min
                corr = min
            else:
                raise
        '''