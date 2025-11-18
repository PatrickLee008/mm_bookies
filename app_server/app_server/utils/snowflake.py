import time
import threading
from datetime import datetime


# 雪花算法生成ID
class SnowflakeIdGenerator:
    def __init__(self, worker_id=0, datacenter_id=0):
        self.lock = threading.Lock()
        # 起始时间戳（可自定义）
        self.twepoch = 1288834974657  # Twitter的初始时间(2010-11-04 09:42:54 UTC)

        # 位数分配
        self.worker_id_bits = 5
        self.datacenter_id_bits = 5
        self.max_worker_id = -1 ^ (-1 << self.worker_id_bits)
        self.max_datacenter_id = -1 ^ (-1 << self.datacenter_id_bits)
        self.sequence_bits = 12

        # 位移
        self.worker_id_shift = self.sequence_bits
        self.datacenter_id_shift = self.sequence_bits + self.worker_id_bits
        self.timestamp_left_shift = self.sequence_bits + self.worker_id_bits + self.datacenter_id_bits
        self.sequence_mask = -1 ^ (-1 << self.sequence_bits)

        # 参数检查
        if worker_id > self.max_worker_id or worker_id < 0:
            raise ValueError(f"worker id can't be greater than {self.max_worker_id} or less than 0")
        if datacenter_id > self.max_datacenter_id or datacenter_id < 0:
            raise ValueError(f"datacenter id can't be greater than {self.max_datacenter_id} or less than 0")

        self.worker_id = worker_id
        self.datacenter_id = datacenter_id
        self.sequence = 0
        self.last_timestamp = -1


    def _gen_timestamp(self):
        return int(time.time() * 1000)

    def generate_id(self):
        with self.lock:
            timestamp = self._gen_timestamp()

            # 时钟回拨处理
            if timestamp < self.last_timestamp:
                raise Exception(
                    f"Clock moved backwards. Refusing to generate id for {self.last_timestamp - timestamp} milliseconds")

            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.sequence_mask
                if self.sequence == 0:
                    timestamp = self._til_next_millis(self.last_timestamp)
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            return ((timestamp - self.twepoch) << self.timestamp_left_shift) | \
                (self.datacenter_id << self.datacenter_id_shift) | \
                (self.worker_id << self.worker_id_shift) | \
                self.sequence

    def _til_next_millis(self, last_timestamp):
        timestamp = self._gen_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self._gen_timestamp()
        return timestamp

if __name__ == '__main__':
    # 使用示例
    generator = SnowflakeIdGenerator(worker_id=1, datacenter_id=1)
    # 生成10个ID
    for i in range(10):
        print(generator.generate_id())  # 输出64位整数ID