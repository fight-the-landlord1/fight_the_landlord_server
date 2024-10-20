import socket
import json


class CardClient:
    def __init__(self, host='localhost', port=12345):
        """初始化客户端并连接到服务器"""
        self.s = self.connect_to_server(host, port)
        self.cards = []  # 当前玩家的手牌
        self.CURRENT = []  # 当前出牌情况
        self.POKERS = self.initialize_pokers()  # 初始化牌映射表

    def connect_to_server(self, host, port):
        """连接服务器"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            print("连接服务器成功")
            return s
        except ConnectionError as e:
            print(f"无法连接到服务器: {e}")
            exit(1)

    def initialize_pokers(self):
        """初始化一副牌的映射表"""
        A = ['红桃', '黑桃', '方片', '梅花']
        B = ['3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2']
        pokers = []
        for i in A:
            for j in B:
                pokers.append(f"{i}{j}")
        pokers += ['小王', '大王']
        return pokers

    def map_card(self, card_num):
        """将编号映射为牌名"""
        return self.POKERS[card_num - 1] if card_num > 0 else None

    def show_cards(self, cards):
        """显示当前玩家的手牌"""
        print("你现在的牌是:", list(filter(None, map(self.map_card, sorted(cards)))))

    def send_message(self, msg):
        """发送 JSON 格式的消息到服务器"""
        try:
            self.s.sendall(json.dumps(msg).encode('utf-8'))
        except Exception as e:
            print(f"发送消息失败: {e}")

    def receive_message(self):
        """接收并处理服务器的消息"""
        try:
            while True:
                receive = self.s.recv(1024).decode('utf-8')
                if receive.strip():
                    self.json_parse(receive)
        except (ConnectionResetError, ConnectionAbortedError):
            print("与服务器的连接断开")
        except Exception as e:
            print(f"接收消息时出错: {e}")

    def json_parse(self, js):
        """解析服务器发送的 JSON 消息"""
        try:
            recjs = json.loads(js)
        except json.JSONDecodeError:
            print("收到非法 JSON 格式的消息")
            return

        operations = {
            'message': self.handle_message,
            'init': self.handle_init,
            'AskS': self.select_landlord,
            'Add': self.handle_add,
            'SetTurn': self.play_card,
            'Announce': self.handle_announce,
        }

        operation = recjs.get('Operation')
        handler = operations.get(operation)
        if handler:
            handler(recjs)
        else:
            print('未知的 JSON 操作')

    def handle_message(self, recjs):
        """处理普通的服务器消息"""
        print(recjs['message'])

    def handle_init(self, recjs):
        """接收服务器的发牌并展示"""
        self.cards = recjs['message']
        self.show_cards(self.cards)

    def handle_add(self, recjs):
        """接收底牌并更新手牌"""
        self.cards += recjs['message']
        print('你获得了底牌:')
        self.show_cards(recjs['message'])

    def handle_announce(self, recjs):
        """展示上家出牌信息"""
        if recjs['message']:
            print("上家打出了:", list(map(self.map_card, sorted(recjs['message']))))
        else:
            print("上家选择跳过")

    def select_landlord(self):
        """玩家抢地主的选择"""
        msg = {
            'Status': 200,
            'Operation': 'AnsS',
            'message': self.ask_yes_no("你要抢地主吗？（Y/N）")
        }
        self.send_message(msg)

    def play_card(self, recjs):
        """玩家出牌逻辑"""
        print(f"当前牌型: {recjs['type']}, 牌值: {recjs['value']}")
        while True:
            cards = input("请输入你要出的牌序号（空格分隔），或输入0表示跳过: ").strip()
            if self.is_valid_card_input(cards):
                msg = {
                    'Status': 200,
                    'Operation': 'AnsTurn',
                    'message': list(map(int, cards.split())) if cards != "0" else [],
                }
                self.send_message(msg)
                break
            else:
                print("输入不合法，请重新输入")

    def ask_yes_no(self, prompt):
        """询问用户 Y/N 问题"""
        while True:
            choice = input(prompt).strip().upper()
            if choice in ['Y', 'N']:
                return 1 if choice == 'Y' else 0
            print("无效输入，请输入 Y 或 N")

    def is_valid_card_input(self, cards):
        """验证输入的出牌是否合法（仅做格式检查，具体牌型由服务器判断）"""
        if cards == "0":
            return True
        try:
            return all(1 <= int(c) <= 108 for c in cards.split())
        except ValueError:
            return False

    def close_connection(self):
        """关闭连接"""
        self.s.close()


# 启动客户端
if __name__ == "__main__":
    client = CardClient()  # 创建客户端实例
    client.receive_message()  # 监听并处理服务器消息
    client.close_connection()  # 关闭连接
