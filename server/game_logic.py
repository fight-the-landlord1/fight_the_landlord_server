import random
import threading
import socket
from server.client_handler import ClientHandler
from server.config import HOST, PORT, MAX_PLAYERS, TOTAL_CARDS, PLAYER_CARDS

# 包含游戏的核心逻辑：发牌、抢地主、出牌流程等。
# 创建服务器类以封装逻辑
class GameServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 创建 socket 对象
        self.server_socket.bind((HOST, PORT))  # 绑定主机和端口
        self.server_socket.listen(MAX_PLAYERS)  # 最大连接数为 4 个玩家
        self.clients = []  # 存储玩家的 socket
        self.player_cards = [[] for _ in range(MAX_PLAYERS)]  # 存储每个玩家的牌
        self.base_cards = []  # 地主的底牌
        self.current_turn = 0  # 当前出牌玩家编号
        self.lock = threading.Lock()  # 线程锁，用于控制共享资源
        self.start_game()  # 初始化游戏

    def start_game(self):
        print("等待 4 位玩家连接...")
        # 连接 4 位玩家
        while len(self.clients) < MAX_PLAYERS:
            client_socket, addr = self.server_socket.accept()
            print(f"玩家 {len(self.clients) + 1} 连接成功：{addr}")
            client_handler = ClientHandler(client_socket)
            self.clients.append(client_handler)
            client_handler.send_message("连接成功，等待其他玩家...")

        print("所有玩家已连接，开始游戏。")
        self.send_all("所有玩家已连接，开始游戏。")

        # 发牌
        self.deal_cards()
        self.send_all("发牌完毕，等待抢地主...")
        self.ask_for_landlord()

    def deal_cards(self):
        """发牌：每位玩家 25 张，剩余 8 张作为地主的底牌"""
        all_cards = list(range(1, TOTAL_CARDS + 1))  # 1 到 108 张牌
        random.shuffle(all_cards)  # 洗牌

        # 每个玩家分 25 张牌
        for i in range(MAX_PLAYERS):
            self.player_cards[i] = all_cards[i * PLAYER_CARDS: (i + 1) * PLAYER_CARDS]
            self.clients[i].send_message(f"你的牌是：{sorted(self.player_cards[i])}")

        # 剩下的 8 张牌作为底牌
        self.base_cards = all_cards[MAX_PLAYERS * PLAYER_CARDS:]
        print(f"地主底牌：{sorted(self.base_cards)}")

    def ask_for_landlord(self):
        """询问所有玩家是否抢地主"""
        for i, client in enumerate(self.clients):
            client.send_message(f"玩家 {i + 1}，你要抢地主吗？（输入Y/N）")

        landlord_found = False
        while not landlord_found:
            for i, client in enumerate(self.clients):
                response = client.receive_message().strip().upper()
                if response == 'Y':
                    landlord_found = True
                    self.assign_landlord(i)
                    break

    def assign_landlord(self, landlord_idx):
        """确定地主并发放底牌"""
        print(f"玩家 {landlord_idx + 1} 成为地主！")
        self.send_all(f"玩家 {landlord_idx + 1} 成为地主！")

        # 给地主发底牌
        self.player_cards[landlord_idx].extend(self.base_cards)
        self.clients[landlord_idx].send_message(f"你的底牌是：{sorted(self.base_cards)}")

        # 开始游戏，地主先出牌
        self.current_turn = landlord_idx
        self.start_turn()

    def start_turn(self):
        """游戏回合：从地主开始，依次轮流出牌"""
        while True:
            client = self.clients[self.current_turn]
            client.send_message("轮到你出牌，请输入你的牌（空格分隔）或输入 '跳过'")
            received = client.receive_message().strip()

            if received.lower() == '跳过':
                client.send_message("你选择跳过")
            else:
                # 假设这里简单处理出牌逻辑，可以扩展为牌型验证
                try:
                    played_cards = list(map(int, received.split()))
                    if all(card in self.player_cards[self.current_turn] for card in played_cards):
                        # 从玩家牌中移除
                        for card in played_cards:
                            self.player_cards[self.current_turn].remove(card)
                        self.send_all(f"玩家 {self.current_turn + 1} 出牌：{sorted(played_cards)}")
                    else:
                        client.send_message("你的牌不合法，请重新出牌。")
                        continue  # 重新让该玩家出牌
                except ValueError:
                    client.send_message("输入有误，请重新输入牌的序号。")
                    continue  # 重新让该玩家出牌

            # 检查是否游戏结束
            if not self.player_cards[self.current_turn]:
                self.send_all(f"玩家 {self.current_turn + 1} 赢得了游戏！")
                break

            # 轮到下一位玩家
            self.current_turn = (self.current_turn + 1) % MAX_PLAYERS

    def send_all(self, message):
        """给所有玩家发送消息"""
        for client in self.clients:
            client.send_message(message)
