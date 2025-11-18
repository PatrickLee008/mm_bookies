import random
from typing import List


class DataKits:
    # 可用字符集合（数字+大小写字母）
    CHARACTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

    @staticmethod
    def generate(prefix: str, middle_numbers: str, random_length: int = 4) -> str:
        """
        生成唯一ID

        :param prefix: ID前缀(如"x")
        :param middle_numbers: 中间固定数字部分(如"1288511")
        :param random_length: 随机部分长度(默认为4)
        :return: 生成的唯一ID
        :raises ValueError: 如果middle_numbers不是纯数字
        """
        # 验证中间数字部分
        if not middle_numbers.isdigit():
            raise ValueError("中间部分必须为数字")

        # 生成随机部分
        random_chars = ''.join(random.choices(DataKits.CHARACTERS, k=random_length))

        return f"{prefix}{middle_numbers}{random_chars}"

    @staticmethod
    def batch_generate(prefix: str, middle_numbers: str, random_length: int = 4,
                       count: int = 1) -> List[str]:
        """
        批量生成唯一ID

        :param prefix: ID前缀
        :param middle_numbers: 中间固定数字部分
        :param random_length: 随机部分长度(默认为4)
        :param count: 要生成的ID数量
        :return: 生成的ID列表
        :raises ValueError: 如果middle_numbers不是纯数字或count不是正整数
        """
        if not isinstance(count, int) or count <= 0:
            raise ValueError("count必须是正整数")

        ids = []
        generated = set()  # 用于检测重复

        for _ in range(count):
            while True:
                new_id = DataKits.generate(prefix, middle_numbers, random_length)
                if new_id not in generated:
                    generated.add(new_id)
                    ids.append(new_id)
                    break

        return ids


# 使用示例
if __name__ == "__main__":
    try:
        # 生成单个ID
        id1 = DataKits.generate("x", "1288511", 5)
        print(f"生成的ID: {id1}")

        # 批量生成10个ID
        ids = DataKits.batch_generate("o", "20240603", 6, 10)
        print("批量生成的ID:")
        for id in ids:
            print(id)

        # 测试异常情况
        # invalid_id = UniqueIdGenerator.generate("x", "12a34")  # 会抛出ValueError

    except ValueError as e:
        print(f"错误: {e}")