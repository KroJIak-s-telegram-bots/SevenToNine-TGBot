
class Card():
    def __init__(self, cardId, dictCard):
        self.cardId = cardId
        self.number = dictCard['number']
        self.range = dictCard['range']
        self.sticker = dictCard['sticker']
        self.text = f'<b>{self.range} +</b> {self.number}\uFE0F⃣ <b>- {self.range}</b>'

    def __str__(self):
        return self.text

class User():
    def __init__(self, userId, dictUser):
        self.userId = userId
        self.login = dictUser['login']
        self.fullname = dictUser['fullname']
        self.lang = dictUser['lang']
        self.permission = dictUser['permission']

    def isDefault(self):
        return self.permission == 'default'

    def isAdmin(self):
        return self.permission == 'admin'