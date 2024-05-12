from utils.funcs import joinPath

class configCategoryObject():
    def __init__(self, config, nameCategory):
        self.config = config
        self.nameCategory = nameCategory

    def get(self, elm):
        return self.config.get(self.nameCategory, elm)

class Telegram(configCategoryObject):
    def __init__(self, config):
        super().__init__(config, 'Telegram')
        self.token = self.get('token')
        self.alias = self.get('alias')

class Data(configCategoryObject):
    def __init__(self, config):
        super().__init__(config, 'Data')
        self.usersDatabasePath = self.get('usersDatabasePath')
        self.cardsDatabasePath = self.get('cardsDatabasePath')
        self.availableLangs = self.get('availableLangs')
        self.availableLangs = self.availableLangs.split(', ')
        self.defaultLang = self.get('defaultLang')

class Logging():
    def __init__(self):
        self.format = '%(asctime)s %(levelname)s %(message)s'

class Path():
    def __init__(self):
        self.project = joinPath('/', *__file__.split('/')[:-2])
        self.client = joinPath(self.project, 'client')
        self.db = joinPath(self.project, 'db')
        self.config = joinPath(self.client, 'config', 'bot.ini')
        self.lang = joinPath(self.client, 'lang')
        self.logs = joinPath(self.client, 'logs')

class Default():
    def __init__(self):
        self.parseMode = 'HTML'

class Game():
    def __init__(self):
        self.maxPlayerCards = 6

class ConstPlenty():
    def __init__(self, config=None):
        if config: self.addConstFromConfig(config)
        self.path = Path()
        self.default = Default()
        self.logging = Logging()
        self.game = Game()

    def addConstFromConfig(self, config):
        self.telegram = Telegram(config)
        self.data = Data(config)