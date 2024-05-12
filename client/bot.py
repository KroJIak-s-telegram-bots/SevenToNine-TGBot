from traceback import format_exc
from fnmatch import fnmatch
import json
import logging
import random

import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ChatMemberStatus
from aiogram.filters.command import Command
from aiogram.client.default import DefaultBotProperties

from modules.objects.client import UserInfo
from utils.const import ConstPlenty
from utils.funcs import getConfigObject, joinPath, getLogFileName
from db.database import dbUsersWorker, dbCardsWorker, dbLocalWorker

# SETTINGS
const = ConstPlenty()
botConfig = getConfigObject(const.path.config)
const.addConstFromConfig(botConfig)
logging.basicConfig(level=logging.INFO)
# logging.basicConfig(level=logging.INFO, filename=joinPath(const.path.logs, getLogFileName()), filemode='w', format=const.logging.format)
dbUsers = dbUsersWorker(joinPath(const.path.db, const.data.usersDatabasePath))
dbCards = dbCardsWorker(joinPath(const.path.db, const.data.cardsDatabasePath))
dbLocal = dbLocalWorker()
bot = Bot(const.telegram.token, default=DefaultBotProperties(parse_mode=const.default.parseMode))
dp = Dispatcher()

def getTranslation(userId, key, inserts=[], lang=None):
    user = dbUsers.getUser(userId)
    try:
        if not lang: lang = user.lang
        with open(joinPath(const.path.lang, f'{lang}.json'), encoding='utf-8') as langFile:
            langJson = json.load(langFile)
        text = langJson[key]
        if not inserts: return text
        for ins in inserts: text = text.replace('%{}%', str(ins), 1)
        return text
    except Exception:
        if user.isAdmin(): return getTranslation(userId, 'error.message', [format_exc()])
        else: return getTranslation(userId, 'error.message', ['wwc...'])

def getUserInfo(message):
    userInfo = UserInfo(message)
    if not dbUsers.isUserExists(userInfo.userId):
        permissions = dbUsers.getPermissions()
        dbUsers.addNewUser(userInfo.userId, userInfo.username, userInfo.userFullName, const.data.defaultLang, permissions[0])
    if not dbLocal.users.isUserExists(userInfo.userId):
        dbLocal.users.addNewUser(userInfo.userId)
    if not dbLocal.chats.isChatExists(userInfo.chatId):
        dbLocal.chats.addNewChat(userInfo.chatId)
    userLogInfo = f'{userInfo} | {str(dbLocal.users.db[str(userInfo.userId)])}'
    logging.info(userLogInfo)
    # print(userLogInfo)
    return userInfo

def getMainKeyboard(userInfo):
    if isPrivateChat(userInfo): return None
    mainButtons = []
    mainButtons.append([types.KeyboardButton(text=getTranslation(userInfo.userId, 'button.game.start'))])
    mainKeyboard = types.ReplyKeyboardMarkup(keyboard=mainButtons, resize_keyboard=True)
    return mainKeyboard

def getDeckKeyboard(userId):
    userBuffer = dbLocal.users.getBuffer(userId)
    deckButtons = [[types.KeyboardButton(text=card.text)] for card in userBuffer]
    deckKeyboard = types.ReplyKeyboardMarkup(keyboard=deckButtons, resize_keyboard=True)
    return deckKeyboard

def isPrivateChat(userInfo):
    return userInfo.userId == userInfo.chatId

# COMMANDS
@dp.message(Command('start'))
async def startHandler(message: types.Message):
    userInfo = getUserInfo(message)
    dbLocal.users.setMode(userInfo.userId, 0)
    mainKeyboard = getMainKeyboard(userInfo)
    await message.answer(getTranslation(userInfo.userId, 'start.message', [userInfo.userFirstName]), reply_markup=mainKeyboard)
    if isPrivateChat(userInfo):
        await message.answer(getTranslation(userInfo.userId, 'warn.private.message'))

async def updateCurrentCard(userInfo, card):
    dbLocal.chats.setCurrentCard(userInfo.chatId, card)
    stickerMessage = await bot.send_sticker(userInfo.chatId, card.sticker)
    dbLocal.chats.setLastStickerMessageId(userInfo.chatId, stickerMessage.message_id)

def isStartGameCommand(userInfo):
    return userInfo.userText in ['/startgame', f'/startgame@{const.telegram.alias}', getTranslation(userInfo.userId, 'button.game.start')]

async def startGameHandler(userInfo, message):
    gameCards = dbCards.getCards()
    random.shuffle(gameCards)
    currentCard = gameCards.pop(0)
    await updateCurrentCard(userInfo, currentCard)
    countMembersInChat = await bot.get_chat_member_count(userInfo.chatId) - 1
    countActiveMembers = 0
    step = len(gameCards) // countMembersInChat
    for userId in dbUsers.getUserIds():
        if countActiveMembers == countMembersInChat: break
        member = await bot.get_chat_member(userInfo.chatId, int(userId))
        print(userId, member.status)
        if member.status == ChatMemberStatus.LEFT: continue
        if not dbLocal.users.isUserExists(userId):
            dbLocal.users.addNewUser(userId)
        dbLocal.users.setMode(userId, 2)
        dbLocal.users.setCards(userId, gameCards[step * countActiveMembers:step * (countActiveMembers + 1)])
        dbLocal.users.setBuffer(userId, [None] * const.game.maxPlayerCards)
        fillUserBuffer(userId, userInfo.chatId)
        countActiveMembers += 1
    print(countActiveMembers)
    print(dbLocal.users.db)
    print([card.text for card in list(dbLocal.users.db.values())[0]['cards']])
    print(len(list(dbLocal.users.db.values())[0]['cards']), len(list(dbLocal.users.db.values())[0]['buffer']))

def fillUserBuffer(userId, chatId):
    userCards = dbLocal.users.getCards(userId)
    userBuffer = dbLocal.users.getBuffer(userId)
    currentCard = dbLocal.chats.getCurrentCard(chatId)
    mayNextCards = getMayNextCards(currentCard)
    powerUserCards = [(id, 1) if card.number in mayNextCards else (id, 0) for id, card in enumerate(userCards)]
    random.shuffle(powerUserCards)
    powerUserCards = [x[0] for x in sorted(powerUserCards, key=lambda x: x[1])]
    weakBufferCards = [(id, 0) if card is None else (id, 1) for id, card in enumerate(userBuffer) if card is None or card.number not in mayNextCards]
    weakBufferCards = [x[0] for x in sorted(weakBufferCards, key=lambda x: x[1])]

    for bufferId in weakBufferCards:
        if not len(powerUserCards): break
        userCardId = powerUserCards.pop(0)
        userBuffer[bufferId] = userCards[userCardId]
        userCards[userCardId] = None
    userCards = [card for card in userCards if card is not None]
    userBuffer = [card for card in userBuffer if card is not None]
    dbLocal.users.setCards(userId, userCards)
    dbLocal.users.setBuffer(userId, userBuffer)

def isCardMessage(userInfo):
    userText = userInfo.userText
    print([userText])
    if not userText: return False
    condition = ((fnmatch(userText, '? + ?️⃣ - ?') or fnmatch(userText, '? + 🔟 - ?'))
                 and userText[0] == userText[-1]
                 and int(userText[0]) <= 3 and int(userText[-1]) <= 3)
    print(fnmatch(userText, '? + ?️⃣ - ?'), userText[0] == userText[-1], int(userText[0]) <= 3, int(userText[-1]) <= 3, condition)
    return condition

def getCardBufferId(userInfo):
    splitUserText = userInfo.userText.split()
    cardRange = int(splitUserText[0])
    cardNumber = int(splitUserText[2][0]) if len(splitUserText[2]) > 1 else 10
    userBuffer = dbLocal.users.getBuffer(userInfo.userId)
    for id, card in enumerate(userBuffer):
        print(cardNumber, card.number, cardRange, card.range)
        if card.number == cardNumber and card.range == cardRange:
            return id

async def cardMessageHandler(userInfo, message):
    cardBufferId = getCardBufferId(userInfo)
    userBuffer = dbLocal.users.getBuffer(userInfo.userId)
    userCard = userBuffer[cardBufferId]
    currentCard = dbLocal.chats.getCurrentCard(userInfo.chatId)
    mayNextCards = getMayNextCards(currentCard)
    print(cardBufferId, userCard, currentCard)
    print(userCard.number, mayNextCards)
    if userCard.number in mayNextCards:
        userBuffer[cardBufferId] = None
        dbLocal.users.setBuffer(userInfo.userId, userBuffer)
        fillUserBuffer(userInfo.userId, userInfo.chatId)
        print(dbLocal.users.getBuffer(userInfo.userId))
        gameCards = dbCards.getCards()
        cardId = (userCard.range - 1) * 10 + userCard.number - 1
        lastStickerMessageId = dbLocal.chats.getLastStickerMessageId(userInfo.chatId)
        await bot.delete_message(userInfo.chatId, lastStickerMessageId)
        await updateCurrentCard(userInfo, gameCards[cardId], message)
        await bot.delete_message(userInfo.chatId, userInfo.messageId)

def getMayNextCards(card):
    mayNextCardDown = card.number - card.range
    if card.number < card.range: mayNextCardDown += 10
    mayNextCardUp = card.number + card.range
    if mayNextCardUp > 10: mayNextCardUp %= 10
    return (mayNextCardDown, mayNextCardUp)

def isUnknownCommand(userInfo):
    return userInfo.userText and userInfo.userText[0] == '/'

async def unknownCommandHandler(userInfo, message):
    mainKeyboard = getMainKeyboard(userInfo)
    await message.answer(getTranslation(userInfo.userId, 'unknown.command.message'), reply_markup=mainKeyboard)

@dp.message()
async def mainHandler(message: types.Message):
    userInfo = getUserInfo(message)
    userMode = dbLocal.users.getMode(userInfo.userId)
    if isPrivateChat(userInfo):
        await message.answer(getTranslation(userInfo.userId, 'permissions.cancel'))
        return

    elif isStartGameCommand(userInfo):
        await startGameHandler(userInfo, message)
        return

    elif isUnknownCommand(userInfo):
        await message.answer(getTranslation(userInfo.userId, 'unknown.command.message'))
        return

    elif userMode > 0:
        match userMode:
            case 1: pass
            case 2:
                if isCardMessage(userInfo):
                    await cardMessageHandler(userInfo, message)
        return


async def mainTelegram():
    await dp.start_polling(bot)

def main():
    asyncio.run(mainTelegram())

if __name__ == '__main__':
    main()