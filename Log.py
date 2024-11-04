import configparser
import os
import pickle

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


def generate_key_iv():
    # 生成安全的随机密钥和IV
    key = os.urandom(16)  # AES-128 位密钥
    iv = os.urandom(16)  # AES 块大小
    return key, iv


def write_config(key, iv, config_file='config.ini'):
    # 将密钥和IV转换为十六进制字符串
    key_hex = key.hex()
    iv_hex = iv.hex()

    # 创建配置文件并写入密钥和IV
    config = configparser.ConfigParser()
    config['Encryption'] = {
        'key': key_hex,
        'iv': iv_hex
    }
    with open(config_file, 'w') as file:
        config.write(file)


def read_config(config_file='config.ini'):
    # 读取配置文件
    config = configparser.ConfigParser()
    if not config.read(config_file):
        print("配置文件不存在，将生成新的配置文件。")
        return None
    return config


class Log:
    def __init__(self, user=None, password=None, config_file='config.ini', credentials_file='credentials.pkl'):
        self.config = read_config(config_file)
        if self.config is None:
            # 生成密钥和IV
            key, iv = generate_key_iv()
            # 写入配置文件
            write_config(key, iv, config_file)
        else:
            # 获取十六进制格式的密钥和IV
            key_hex = self.config['Encryption']['key']
            iv_hex = self.config['Encryption']['iv']
            # 将十六进制字符串转换回字节
            key = bytes.fromhex(key_hex)
            iv = bytes.fromhex(iv_hex)
        self.key = key
        self.iv = iv
        self.credentials_file = credentials_file
        self.credentials = self.load_credentials()
        if user and password:
            self.save_credentials(user, password)

    def _encrypt(self, data):
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        padded_data = pad(data.encode(), AES.block_size)
        return cipher.encrypt(padded_data)

    def _decrypt(self, data):
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        decrypted_padded_data = cipher.decrypt(data)
        return unpad(decrypted_padded_data, AES.block_size).decode()

    def save_credentials(self, username, password):
        self.credentials[username] = (self._encrypt(username), self._encrypt(password))
        with open(self.credentials_file, 'wb') as file:
            pickle.dump(self.credentials, file)

    def load_credentials(self):
        if os.path.exists(self.credentials_file):
            with open(self.credentials_file, 'rb') as file:
                return pickle.load(file)
        else:
            return {}

    def get_decrypted_user(self, username):
        if username in self.credentials:
            user_encrypted, _ = self.credentials[username]
            return self._decrypt(user_encrypted)
        return None

    def get_decrypted_password(self, username):
        if username in self.credentials:
            _, password_encrypted = self.credentials[username]
            return self._decrypt(password_encrypted)
        return None

    def get_credentials(self):
        return self.credentials

    def remove_credentials(self, username):
        # 从存储中删除指定的账号信息
        if username in self.credentials:
            del self.credentials[username]
            with open(self.credentials_file, 'wb') as file:
                pickle.dump(self.credentials, file)  # 保存更新后的凭证
            return True
        return False
