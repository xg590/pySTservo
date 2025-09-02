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
