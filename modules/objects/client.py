
class UserInfo():
    def __init__(self, message):
        self.chatId = message.chat.id
        self.userId = message.from_user.id
        self.username = message.from_user.username
        self.userFirstName = message.from_user.first_name
        self.userFullName = message.from_user.full_name
        self.messageId = message.message_id
        self.userText = message.text

    def __str__(self):
        resultStr = ' | '.join(list(map(str, (self.chatId, self.userId, self.username, self.userFirstName,
                     self.userFullName, self.messageId, self.userText))))
        return resultStr