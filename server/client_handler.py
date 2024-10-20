import json
# 用于封装客户端的 socket 交互功能。
class ClientHandler:
    def __init__(self, socket):
        self.socket = socket

    def send_message(self, message):
        """发送消息给客户端"""
        msg = {
            'status': 200,
            'Operation': 'message',
            'message': message
        }
        self.socket.sendall(json.dumps(msg).encode('utf-8'))

    def receive_message(self):
        """接收客户端消息"""
        return self.socket.recv(1024).decode('utf-8')

    def close(self):
        """关闭客户端连接"""
        self.socket.close()
