import json
import os
import shutil

from utils.funcs import joinPath
from modules.objects.db import Card, User

class dbWorker():
    def __init__(self, databasePath, defaultDBFileName='default.json'):
        folderPath = databasePath.split('/')
        self.fileName = folderPath.pop(-1)
        self.folderPath = '/'.join(folderPath)
        if not self.isExists():
            shutil.copyfile(joinPath(self.folderPath, defaultDBFileName),
                            joinPath(self.folderPath, self.fileName))

    def isExists(self):
        files = os.listdir(self.folderPath)
        return self.fileName in files

    def get(self):
        with open(joinPath(self.folderPath, self.fileName)) as file:
            dbData = json.load(file)
        return dbData

    def save(self, dbData):
        with open(joinPath(self.folderPath, self.fileName), 'w', encoding='utf-8') as file:
            json.dump(dbData, file, indent=4, ensure_ascii=False)

class dbLocalWorker():
    def __init__(self):
        self.users = dbLocalUsersWorker()
        self.chats = dbLocalChatsWorker()

class dbLocalUsersWorker():
    def __init__(self):
        self.db = {}

    def isUserExists(self, userId):
        return str(userId) in self.db

    def addNewUser(self, userId):
        self.db[str(userId)] = dict(mode=0,
                                    cards=[],
                                    buffer=[])

    def setMode(self, userId, mode):
        self.db[str(userId)]['mode'] = mode

    def getMode(self, userId):
        return self.db[str(userId)]['mode']

    def setCards(self, userId, cards):
        self.db[str(userId)]['cards'] = cards

    def getCards(self, userId):
        return self.db[str(userId)]['cards']

    def clearCards(self, userId):
        self.db[str(userId)]['cards'] = []

    def setBuffer(self, userId, buffer):
        self.db[str(userId)]['buffer'] = buffer

    def getBuffer(self, userId):
        return self.db[str(userId)]['buffer']

class dbLocalChatsWorker():
    def __init__(self):
        self.db = {}

    def isChatExists(self, chatId):
        return str(chatId) in self.db

    def addNewChat(self, chatId):
        self.db[str(chatId)] = dict()

    def setCurrentCard(self, chatId, card):
        self.db[str(chatId)]['currentCard'] = card

    def getCurrentCard(self, chatId):
        return self.db[str(chatId)]['currentCard']

    def setLastStickerMessageId(self, chatId, messageId):
        self.db[str(chatId)]['lastStickerMessageId'] = messageId

    def getLastStickerMessageId(self, chatId):
        return self.db[str(chatId)]['lastStickerMessageId']

class dbUsersWorker(dbWorker):
    def getUserIds(self):
        dbData = self.get()
        userIds = tuple(dbData['users'].keys())
        return userIds

    def getPermissions(self):
        dbData = self.get()
        permissions = tuple(dbData['permissions'].values())
        return permissions

    def isUserExists(self, userId):
        dbData = self.get()
        return str(userId) in dbData['users']

    def addNewUser(self, userId, login, fullname, lang, permission='default'):
        dbData = self.get()
        newUser = dict(login=login,
                       fullname=fullname,
                       lang=lang,
                       permission=permission)
        dbData['users'][str(userId)] = newUser
        self.save(dbData)

    def getUser(self, userId):
        dbData = self.get()
        dictUser = dbData['users'][str(userId)]
        user = User(str(userId), dictUser)
        return user

    def setInUser(self, userId, key, value):
        dbData = self.get()
        dbData['users'][str(userId)][str(key)] = value
        self.save(dbData)

class dbCardsWorker(dbWorker):
    def getCards(self):
        dbData = self.get()
        gameCards = [Card(int(cardId), dictCard) for cardId, dictCard in dbData.items()]
        return gameCards