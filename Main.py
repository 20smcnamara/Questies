import math
import pygame


# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
SCREEN_CENTER_X = SCREEN_WIDTH / 2
SCREEN_CENTER_Y = SCREEN_HEIGHT / 2
TILE_SIZE = int(SCREEN_WIDTH / 24)
HALF_TILE = int(TILE_SIZE / 2)
TILES_X = SCREEN_WIDTH / TILE_SIZE
TILES_Y = SCREEN_HEIGHT / TILE_SIZE
OUTLINE_SIZE = int(TILE_SIZE / 25 + 1)
OUTLINE_COLOR = (20, 20, 20)
SELECTION_COLOR = (225, 220, 50)
BASE_MOVEMENT_COST = 5

INACTIVE = (240, 175, 100)
ACTIVE = (100, 255, 100)
DANGER = (240, 100, 100)

# Directions
LEFT = 0
UP = 1
RIGHT = 2
DOWN = 3

# Pygame
pygame.init()
screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
font = 'freesansbold.ttf'
pygame.display.set_caption("0.0")
clock = pygame.time.Clock()


# Pygame self-made functions
def fitTextSize(font, rect, text, inc=4):
    for i in range(8, 1024, inc):
        testFont = pygame.font.Font(font, i)
        if testFont.size(text)[0] > rect[2] or testFont.size(text)[1] > rect[3]:
            return pygame.font.Font(font, i - inc)
    return pygame.font.Font(font, inc)


# Assets and asset constants
class AssetManager:

    def __init__(self, file_name='Assets.txt', extensions=".png"):
        file = open(file_name, 'r')

        lines = file.read().split("\n")

        self.highlighted = {}
        self.assets = {}

        for line in lines:
            print(line)
            if len(line) > 2:
                contents = line.split("=")

                location = "Assets"
                if contents[0].__eq__("Item"):
                    location = "Assets/Items/"

                name = contents[1]
                asset_file = location + name + extensions
                highlighted_file = location + "highlighted/" + name + extensions

                width = int(eval(contents[2]) * TILE_SIZE)
                height = int(eval(contents[3]) * TILE_SIZE)

                image = pygame.transform.smoothscale(pygame.image.load(asset_file), (width, height))
                highlighted = pygame.transform.smoothscale(pygame.image.load(highlighted_file), (width, height))

                self.assets[name] = image.copy()
                self.highlighted[name] = highlighted.copy()

    def get(self, name):
        return self.assets[name]

    def getH(self, name):
        return self.highlighted[name]


ASSET_MANAGER = AssetManager()
PLAYER_IMAGE = pygame.transform.smoothscale(pygame.image.load("Player.png"),
                                            (int(TILE_SIZE * 0.55), int(TILE_SIZE * 0.75)))
PLAYER_WIDTH = PLAYER_IMAGE.get_width()
PLAYER_HEIGHT = PLAYER_IMAGE.get_height()
HIGHLIGHTED_TILE = pygame.Surface((TILE_SIZE, TILE_SIZE))
HIGHLIGHTED_TILE.fill((255, 125, 125))
HIGHLIGHTED_TILE.set_alpha(150)


class Terrain:

    def __init__(self, difficulty, color=()):
        self.difficulty = difficulty
        self.color = color

    def getColor(self):
        return self.color


GrassLand = Terrain(1, (100, 255, 150))
DirtRoad = Terrain(0.75, (115, 90, 75))


class Object:

    def __init__(self, Blocking=True):
        self.selected = False
        self.blocking = Blocking

    def isBlocking(self):
        return self.blocking

    # toggleSelect never runs because Tile has its own and that is the only one that will run
    def toggleSelect(self):
        global selected

        if selected is not None and selected is not self:
            selected.deselect()

        if self.selected:
            self.deselect()
        else:
            self.select()

        if not self.selected:
            selected = None
        else:
            selected = self

    def deselect(self):
        global selected

        if self.selected:
            selected = None

        self.selected = False

    def select(self):
        global selected

        self.selected = True
        selected = self

    def isSelected(self):
        return self.selected


class Item(Object):

    def __init__(self, type_name, wg, val, name=None):
        super().__init__(Blocking=False)

        if name is not None:
            self.name = name
        else:
            self.name = type_name + type_name + type_name

        self.type = type_name
        self.weight = wg
        self.value = val
        self.inInventory = False

    def getName(self):
        return self.name

    def pickUp(self):
        self.inInventory = True

    def place(self, x, y):
        global tiles

        self.inInventory = False

        tiles[x][y].addContent(self)

    def draw(self, x, y):
        if self.inInventory:
            return

        global screen

        x_adjust = int((TILE_SIZE - PLAYER_WIDTH) / 2)
        y_adjust = int((TILE_SIZE - PLAYER_HEIGHT) / 2)

        if self.selected:
            screen.blit(ASSET_MANAGER.getH(self.type), (x + x_adjust, y + y_adjust))
        else:
            screen.blit(ASSET_MANAGER.get(self.type), (x + x_adjust, y + y_adjust))


class SunGlasses(Item):

    def __init__(self):
        super().__init__("Sunglasses", 1, 2)


class Character(Object):

    def __init__(self, pos, mvmt=30):
        super().__init__()
        self.movement = mvmt + BASE_MOVEMENT_COST
        self.spellCaster = True
        self.x = pos[0]
        self.y = pos[1]
        self.items = []

    def isSpellCaster(self):
        return self.spellCaster

    def getItems(self):
        return self.items.copy()

    def pickUp(self, item):
        self.items.append(item)
        tiles[self.x][self.y].removeContent(item)
        item.pickUp()

    def pickUp(self, item, xCord, yCord):
        self.items.append(item)
        tiles[xCord][yCord].removeContent(item)
        item.pickUp()

    def get(self, item):
        self.items.append(item)
        item.pickUp()

    def drop(self, index):
        self.items[index].place(self.x, self.y)
        del self.items[index]

    def select(self):
        super().select()

    def deselect(self):
        super().deselect()

    def moveTo(self, tile):
        self.x = tile[0]
        self.y = tile[1]

    def highlight(self):
        pos = self.findTilesToMoveTo(self.x, self.y)
        for p in pos:
            tiles[p[0]][p[1]].highlight()

    def unHighlight(self):
        pos = self.findTilesToMoveTo(self.x, self.y)
        for p in pos:
            tiles[p[0]][p[1]].unHighlight()

    def findTilesToMoveTo(self, x, y):
        return self.isPossible(x, y, self.movement, [])

    def inPossibilityList(self, LOP, pos):
        # Add this square
        for p in LOP:
            if p[2] < pos[2]:
                continue
            elif p[0] == pos[0] and p[1] == pos[1]:
                return True

    def isPossible(self, x, y, speed, possibilities):
        global tiles

        if x == len(tiles):
            x = 0

        if y == len(tiles[0]):
            y = 0

        using = tiles[x][y].difficulty * BASE_MOVEMENT_COST

        if using > speed:
            return None

        # Add this square
        possibilities.append((x, y, speed - using))

        # Check other squares
        if not self.inPossibilityList(possibilities, (x - 1, y, speed - using)):
            np = self.isPossible(x - 1, y, speed - using, possibilities)
            if np is not None:
                possibilities = list(set(np).union(set(possibilities)))
        if not self.inPossibilityList(possibilities, (x + 1, y, speed - using)):
            np = self.isPossible(x + 1, y, speed - using, possibilities)
            if np is not None:
                possibilities = list(set(np).union(set(possibilities)))
        if not self.inPossibilityList(possibilities, (x, y - 1, speed - using)):
            np = self.isPossible(x, y - 1, speed - using, possibilities)
            if np is not None:
                possibilities = list(set(np).union(set(possibilities)))
        if not self.inPossibilityList(possibilities, (x, y + 1, speed - using)):
            np = self.isPossible(x, y + 1, speed - using, possibilities)
            if np is not None:
                possibilities = list(set(np).union(set(possibilities)))

        return possibilities

    def draw(self, x, y):
        global screen
        x_adjust = int((TILE_SIZE - PLAYER_WIDTH) / 2)
        y_adjust = int((TILE_SIZE - PLAYER_HEIGHT) / 2)

        screen.blit(PLAYER_IMAGE, (x + x_adjust, y + y_adjust))


class Tree(Object):

    def __init__(self, bc=(135, 75, 0), lc=(0, 135, 25)):
        super().__init__()
        self.baseColor = bc
        self.leavesColor = lc
        self.bWidth = int(TILE_SIZE / 8 + 2)
        self.bHeight = int(TILE_SIZE / 4 + 2)
        self.lWidth = int(TILE_SIZE / 4 + 2)
        self.lHeight = int(TILE_SIZE / 1.25 + 2)

    def draw(self, x, y):
        tileCenterX = x + HALF_TILE
        pygame.draw.rect(screen, self.baseColor, (int(tileCenterX - self.bWidth), y + int(TILE_SIZE * 0.8),
                                                  int(self.bWidth * 2), self.bHeight))
        pygame.draw.polygon(screen, self.leavesColor, ((tileCenterX, int(y + TILE_SIZE * 0.0375)),
                                                       (tileCenterX - self.lWidth, y + int(TILE_SIZE * 0.8)),
                                                       (tileCenterX + self.lWidth, y + int(TILE_SIZE * 0.8))))

        if self.selected:
            pygame.draw.rect(screen, self.baseColor, (int(tileCenterX - self.bWidth), y + int(TILE_SIZE * 0.8),
                                                      int(self.bWidth * 2), self.bHeight), OUTLINE_SIZE)
            pygame.draw.polygon(screen, SELECTION_COLOR, ((tileCenterX, y + TILE_SIZE * 0.0375),
                                                          (tileCenterX - self.lWidth, y + int(TILE_SIZE * 0.8)),
                                                          (tileCenterX + self.lWidth, y + int(TILE_SIZE * 0.8))),
                                OUTLINE_SIZE)


class Tile(Object):

    def __init__(self, x, y, terrain=GrassLand, outline=True):
        super().__init__()
        self.connections = [None, None, None, None]
        self.contents = []
        self.x = x
        self.y = y
        self.terrain = terrain
        self.color = terrain.color
        self.difficulty = terrain.difficulty
        self.cover = None
        self.outline = outline
        self.highlighted = False
        self.selectedItem = 0

    def addContent(self, obj):
        self.contents.append(obj)

    def removeContent(self, obj):
        self.contents.remove(obj)

    def containsBlocker(self):
        for content in self.contents:
            if content.isBlocking():
                return True
        return False

    def toggleSelect(self):
        global selected

        # Contents can be selected
        if len(self.contents) > 0:
            # Deselection

            # Already selected tile so deselect and move selection to first item
            if self.selected and self.selectedItem == len(self.contents):
                self.selected = False
                self.selectedItem = 0

            # Already selected item so move to next one
            if self.selectedItem < len(self.contents) and self.contents[self.selectedItem].isSelected():
                self.selectedItem += 1

            # Selection

            # Selection tile is the tile itself
            if self.selectedItem == len(self.contents):
                if selected is not None:
                    selected.deselect()
                self.selected = True
                selected = self

            # Selection is the contents of the tile
            if self.selectedItem < len(self.contents) and not self.contents[self.selectedItem].isSelected():
                if selected is not None:
                    selected.deselect()
                self.contents[self.selectedItem].select()

        # No contents to select
        else:
            self.selected = not self.selected

            if self.selected:
                if selected is not None:
                    selected.deselect()
                selected = self

            else:
                selected = None

    def connect(self, tile, direction):
        self.connections[direction] = tile

    def addConnections(self, tilesConnected):
        for index in range(4):
            self.connections[index] = tilesConnected[index]

    def highlight(self):
        self.highlighted = True

    def unHighlight(self):
        self.highlighted = False

    def isHighlighted(self):
        return self.highlighted

    def draw(self, x, y, direction_x, direction_y, outline=True):

        x_cords = int(SCREEN_CENTER_X - HALF_TILE - x * TILE_SIZE)
        y_cords = int(SCREEN_CENTER_Y - HALF_TILE - y * TILE_SIZE)

        pygame.draw.rect(screen, self.color, (x_cords, y_cords, TILE_SIZE, TILE_SIZE))

        if self.highlighted:
            screen.blit(HIGHLIGHTED_TILE, (x_cords, y_cords))

        if outline:
            if self.selected:
                pygame.draw.rect(screen, SELECTION_COLOR, (x_cords, y_cords, TILE_SIZE, TILE_SIZE), OUTLINE_SIZE)
            else:
                pygame.draw.rect(screen, OUTLINE_COLOR, (x_cords, y_cords, TILE_SIZE, TILE_SIZE), OUTLINE_SIZE)

        for content in self.contents:
            content.draw(x_cords, y_cords)

        if x == 0 and y == 0:
            if self.connections[LEFT]:
                self.connections[LEFT].draw(x - 1, y, -1, 0)
            if self.connections[RIGHT]:
                self.connections[RIGHT].draw(x + 1, y, 1, 0)
            if self.connections[UP]:
                self.connections[UP].draw(x, y - 1, 0, -1)
            if self.connections[DOWN]:
                self.connections[DOWN].draw(x, y + 1, 0, 1)
        elif y == 0:
            if self.connections[UP]:
                self.connections[UP].draw(x, y - 1, 0, -1)
            if self.connections[DOWN]:
                self.connections[DOWN].draw(x, y + 1, 0, 1)
            if direction_x == -1 and math.fabs(x) < TILES_X / 2:
                if self.connections[LEFT]:
                    self.connections[LEFT].draw(x - 1, y, -1, 0)
            if direction_x == 1 and x < TILES_X / 2:
                if self.connections[RIGHT]:
                    self.connections[RIGHT].draw(x + 1, y, 1, 0)
                else:
                    self.highlighted = True
        else:
            if direction_y == -1 and math.fabs(y) < TILES_Y / 2:
                if self.connections[UP]:
                    self.connections[UP].draw(x, y - 1, 0, -1)
            if direction_y == 1 and y < TILES_Y / 2:
                if self.connections[DOWN]:
                    self.connections[DOWN].draw(x, y + 1, 0, 1)


class Button:

    def __init__(self, rct, txt, color, txt_color, font_to_use):
        self.labelPos = (int(rct[0] + rct[2] / 2 - font_to_use.size(txt)[0] / 2),
                         int(rct[1] + rct[3] / 2 - font_to_use.size(txt)[1] / 2))
        self.labelText = pygame.font.Font.render(font_to_use, txt, True, txt_color)
        self.txt = txt

        self.color = color
        self.rect = rct
        self.hidden = False

    def draw(self):
        if self.hidden:
            return

        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, OUTLINE_COLOR, self.rect, OUTLINE_SIZE)

        if self.txt != "":
            screen.blit(self.labelText, self.labelPos)

    def handleClick(self, pressed, location):
        if self.rect[0] < location[0] < self.rect[0] + self.rect[2] and \
                self.rect[1] < location[1] < self.rect[1] + self.rect[3]:
            return True
        return False

    def updateTxtColor(self, color, font):
        self.labelText = pygame.font.Font.render(font, self.txt, True, color)


class Slider:

    def __init__(self, pointA, pointB, color, size, pos=0.0, colorPoint=(0, 0, 0)):
        self.a = pointA
        self.b = pointB
        self.xDiff = (pointB[0] - pointA[0])
        self.yDiff = (pointB[1] - pointA[1])
        self.c = math.sqrt(self.xDiff ** 2 + self.yDiff ** 2)
        self.size = int(size)
        self.barSize = int(size * 0.8)
        self.color = color
        self.pos = pos
        self.colorPos = colorPoint

    def getPos(self):
        return self.pos

    def draw(self):
        #  Draw Bar
        pygame.draw.line(screen, self.color, self.a, self.b, self.barSize)

        #  Draw Picker
        p_cords = [int(self.a[0] + self.xDiff * self.pos), int(self.a[1] + self.yDiff * self.pos)]
        pygame.draw.circle(screen, self.colorPos, p_cords, self.size)

    def handle_mouse(self, mouse):
        distance = math.fabs((self.xDiff * (self.b[1] - mouse[1])) - (self.yDiff * (self.b[0] - mouse[0]))) / self.c

        if distance < self.size:
            pos = ((mouse[0] - self.a[0]) ** 2 + (mouse[1] - self.a[1]) ** 2) ** 0.5 / self.c

            if pos > 1:
                self.pos = 1
            else:
                self.pos = pos

        return distance < self.size


class ListDisplay:

    def __init__(self, LOI, rct=(int(SCREEN_WIDTH / 20), int(SCREEN_HEIGHT / 20),
                                 int(SCREEN_WIDTH / 3), int(SCREEN_HEIGHT / 20 * 18)),
                 txt="", txt_color=(75, 75, 75), target=None):
        self.items = selected.getItems()

        self.LOI = LOI
        self.rect = rct

        labelRect = (rct[0] + rct[2] * 0.1, rct[1] + rct[3] * 0.01, rct[2] * 0.8, rct[3] * 0.08)
        labelFont = fitTextSize(font, labelRect, txt)
        self.labelPos = (int(labelRect[0] + labelRect[2] / 2 - labelFont.size(txt)[0] / 2),
                         int(labelRect[1] + labelRect[3] / 2 - labelFont.size(txt)[1] / 2))
        self.labelText = pygame.font.Font.render(labelFont, txt, True, txt_color)
        self.txt_color = txt_color

        self.lineOne = (int(rct[0]), int(rct[1] + rct[3] * 0.1))
        self.lineTwo = (int(rct[0] + rct[2]), int(rct[1] + rct[3] * 0.1))

        self.slider = Slider((int(rct[0] + rct[2] * 0.97), int(rct[1] + rct[3] * 0.2)), (int(rct[0] + rct[2] * 0.97), int(rct[1] + rct[3] * 0.8)),
                             (200, 200, 200), int(rct[2] * 0.03), colorPoint=(225, 225, 225))

        self.amountOfItemsToDisplay = 15
        self.itemsTop = int(rct[1] + rct[3] * 0.1)
        self.itemsIncY = int(rct[3] * 0.9 / self.amountOfItemsToDisplay)
        self.itemsX = int(rct[0] + rct[2] * 0.1)
        self.itemsWidth = int(rct[2] * 0.8)

        self.characterLimit = 10

        self.font = fitTextSize(font, (self.itemsX, self.itemsTop, self.itemsWidth, self.itemsIncY * 0.8), "G")
        self.page = 0

        self.equipped = []

        self.buttons = []
        for x in range(self.amountOfItemsToDisplay):
            self.buttons.append((Button((self.itemsX + self.itemsWidth * 0.59, self.itemsTop + self.itemsIncY * x, self.itemsWidth / 5, self.itemsIncY), "Use", (25, 25, 25), INACTIVE, self.font),
                                 Button((self.itemsX + self.itemsWidth * 0.6 + self.itemsWidth / 5, self.itemsTop + self.itemsIncY * x, self.itemsWidth / 4,  self.itemsIncY), "Drop", (25, 25, 25), DANGER, self.font)))

    def draw(self):
        pygame.draw.rect(screen, (150, 150, 150), self.rect)
        pygame.draw.rect(screen, OUTLINE_COLOR, self.rect, OUTLINE_SIZE)
        screen.blit(self.labelText, self.labelPos)
        pygame.draw.line(screen, OUTLINE_COLOR, self.lineOne, self.lineTwo, OUTLINE_SIZE)

        pages = int(len(self.items) / self.amountOfItemsToDisplay + 1)

        self.page = math.floor(self.slider.getPos() / (1 / pages))
        if self.page == pages:
            self.page = pages - 1

        for count in range(self.amountOfItemsToDisplay):
            self.buttons[count][0].draw()
            self.buttons[count][1].draw()

            pygame.draw.line(screen, OUTLINE_COLOR, (self.itemsX, self.itemsTop + self.itemsIncY * count),
                             (self.itemsX + self.itemsWidth, self.itemsTop + self.itemsIncY * count), OUTLINE_SIZE)

            textPos = (int(self.itemsX - self.font.size(str(count + self.page * self.amountOfItemsToDisplay + 1))[0]),
                       int(self.itemsTop + self.itemsIncY * count + self.itemsIncY / 2 - self.font.size("A")[1] / 2))
            text = pygame.font.Font.render(self.font, str(count + self.page * self.amountOfItemsToDisplay + 1), True,
                                           [int(self.txt_color[0] * 0.8), int(self.txt_color[1] * 0.8), int(self.txt_color[2] * 0.8)])
            screen.blit(text, textPos)

            if self.page * self.amountOfItemsToDisplay + count >= len(self.items):
                continue

            textPos = (int(self.itemsX),
                       int(self.itemsTop + self.itemsIncY * count + self.itemsIncY / 2 - self.font.size("A")[1] / 2))
            text = pygame.font.Font.render(self.font, self.items[self.page * self.amountOfItemsToDisplay + count].getName()[:self.characterLimit], True,
                                           self.txt_color)
            screen.blit(text, textPos)

        self.slider.draw()

    def handleMouse(self, loc, pressed):
        yBool = (self.rect[1] < loc[1] < self.rect[1] + self.rect[3])
        xBool = (self.rect[0] < loc[0] < self.rect[0] + self.rect[2])

        if not xBool or not yBool:
            return 0
        else:
            if self.slider.handle_mouse(loc):
                return 2

            for num in range(self.amountOfItemsToDisplay):
                if self.buttons[num][0].handleClick(pressed, loc):
                    itemNum = self.amountOfItemsToDisplay * self.page + num
                    if itemNum < len(self.items):
                        tempItem = self.items[itemNum]
                        if self.equipped.__contains__(tempItem):
                            self.equipped.remove(tempItem)
                            self.buttons[num][0].updateTxtColor(ACTIVE, self.font)
                        else:
                            self.equipped.append(tempItem)
                            self.buttons[num][0].updateTxtColor(INACTIVE, self.font)
                        return 2
                if self.buttons[num][1].handleClick(pressed, loc):
                    itemNum = self.amountOfItemsToDisplay * self.page + num
                    if itemNum < len(self.items):
                        selected.drop(itemNum)
                        self.items = selected.getItems()
                    return 2

            return 1


# Collections
tiles = []
showCharacterButtons = False
characterButtons = []


def generateTiles():
    global tiles

    xRange = int(TILES_X)
    yRange = int(TILES_Y)

    for col in range(yRange):
        newRow = []
        for row in range(xRange):
            if col == yRange / 2 - 1 or col == yRange / 2 or col == yRange / 2 + 1:
                newRow.append(Tile(row, col, terrain=DirtRoad))
            else:
                newRow.append(Tile(row, col))
        tiles.append(newRow.copy())

    for col in range(yRange):
        for row in range(xRange):

            if col > 0:
                tiles[col - 1][row].connect(tiles[col][row], UP)
                tiles[col][row].connect(tiles[col - 1][row], DOWN)
            else:
                tiles[len(tiles) - 1][row].connect(tiles[col][row], UP)
                tiles[col][row].connect(tiles[len(tiles) - 1][row], DOWN)

            if col < len(tiles) - 1:
                tiles[col + 1][row].connect(tiles[col][row], DOWN)
                tiles[col][row].connect(tiles[col + 1][row], UP)
            else:
                tiles[0][row].connect(tiles[col][row], DOWN)
                tiles[col][row].connect(tiles[0][row], UP)

            if row > 0:
                tiles[col][row - 1].connect(tiles[col][row], LEFT)
                tiles[col][row].connect(tiles[col][row - 1], RIGHT)
            else:
                tiles[col][len(tiles[0]) - 1].connect(tiles[col][row], LEFT)
                tiles[col][row].connect(tiles[col][len(tiles[0]) - 1], RIGHT)

            if row < len(tiles) - 1:
                tiles[col][row + 1].connect(tiles[col][row], RIGHT)
                tiles[col][row].connect(tiles[col][row + 1], LEFT)
            else:
                tiles[col][0].connect(tiles[col][row], RIGHT)
                tiles[col][row].connect(tiles[col][0], LEFT)


generateTiles()
tiles[int(len(tiles) / 2)][int(len(tiles[0]) / 2)].addContent(Tree())
camera = [int(len(tiles) / 2), int(len(tiles[0]) / 2)]

# Initial setup
LD = None
update = [(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)]

MainCharacter = Character((camera[0], camera[1] + 1))
MainCharacter.get(SunGlasses())
MainCharacter.get(SunGlasses())

tiles[camera[0]][camera[1] + 1].addContent(MainCharacter)
tiles[camera[0]][camera[1]].draw(0, 0, 0, 0)


# Button setup variables
ButtonNames = ["Spells", "Items", "Movement", "Retrieve"]

ButtonCount = len(ButtonNames)
ButtonWidth = int(SCREEN_WIDTH / (ButtonCount + 1))
ButtonZeroX = int(ButtonWidth / (ButtonCount + 1))
ButtonIncX = int(ButtonWidth + ButtonZeroX)

ButtonY = int(SCREEN_HEIGHT / 8 * 6)
ButtonHeight = int(SCREEN_HEIGHT / 8)

ButtonColor = (45, 45, 90)
ButtonTextColor = (0, 230, 100)

longestWord = 0
for x in range(1, ButtonCount):
    if len(ButtonNames[x]) > len(ButtonNames[longestWord]):
        longestWord = x

ButtonFont = fitTextSize(font, (0, 0, ButtonWidth, ButtonHeight), ButtonNames[longestWord] + "XX")

# Button setup
for buttonID in range(ButtonCount):
    characterButtons.append(Button((ButtonZeroX + buttonID * ButtonIncX, ButtonY, ButtonWidth, ButtonHeight),
                                   ButtonNames[buttonID], ButtonColor, ButtonTextColor, ButtonFont))

# Loop constants
NORMAL = 0
SELECTING = 1
MOVING = 2
GRABBING = 3

# Loop variables
mouseDown = [0, 0, 0]
DEBUGGING = False
state = NORMAL
selected = None
actor = None

while True:
    mapUpdateNeeded = False

    #  Handle Mouse
    mouseLocation = pygame.mouse.get_pos()
    mousePressed = pygame.mouse.get_pressed()

    if mousePressed != mouseDown:
        if mousePressed[0] != mouseDown[0] and mousePressed[0] == 1:
            # Check for button presses
            if showCharacterButtons:
                for index, button in enumerate(characterButtons):
                    result = button.handleClick(mousePressed, mouseLocation)
                    if result:
                        if index == 1:
                            LD = ListDisplay(selected.items, txt="Items")
                            state = SELECTING
                        if index == 2:
                            selected.highlight()
                            state = MOVING
                        if index == 3:
                            state = GRABBING
                            actor = selected
                        showCharacterButtons = False

            elif state == SELECTING:
                LD_result = LD.handleMouse(mouseLocation, mousePressed)
                if LD_result == 0:
                    actor = None
                    state = NORMAL
                    selected.deselect()
                    LD = None
                    mapUpdateNeeded = True
                elif LD_result == 2:
                    mapUpdateNeeded = True
            # Check for tile stuff
            else:
                tile_x = int(camera[1] - (SCREEN_CENTER_X - HALF_TILE - mouseLocation[0]) / TILE_SIZE)
                tile_y = int(camera[0] - (SCREEN_CENTER_Y - HALF_TILE - mouseLocation[1]) / TILE_SIZE)

                if tile_y >= len(tiles):
                    tile_y %= len(tiles)
                if tile_x >= len(tiles[0]):
                    tile_x %= len(tiles[0])

                if DEBUGGING:
                    t = tiles[tile_y][tile_x]
                    print(tile_x, tile_y, t.x, t.y)

                if selected is not None and type(selected) == Character and state == MOVING:
                    s_tile = tiles[tile_y][tile_x]
                    if s_tile.isHighlighted() and not s_tile.containsBlocker():
                        selected.unHighlight()
                        oldX = selected.x
                        oldY = selected.y
                        tiles[oldX][oldY].contents.remove(selected)
                        tiles[tile_y][tile_x].addContent(selected)
                        selected.moveTo((tile_y, tile_x))
                        selected.deselect()
                    else:
                        selected.unHighlight()
                        selected.deselect()
                else:
                    tiles[tile_y][tile_x].toggleSelect()

                if type(selected) == Character:
                    showCharacterButtons = True

                if state != NORMAL:
                    if state == GRABBING and issubclass(type(selected), Item):
                        actor.pickUp(selected, tile_y, tile_x)

                    actor = None
                    state = NORMAL

            mapUpdateNeeded = True
        if mousePressed[1] != mouseDown[1]:
            pass
        if mousePressed[2] != mouseDown[2]:
            pass

        mouseDown = mousePressed

    #  Handle Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit(0)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                camera[1] += 1
                if camera[1] >= len(tiles[0]):
                    camera[1] = 0
                mapUpdateNeeded = True
            if event.key == pygame.K_RIGHT:
                camera[1] -= 1
                if camera[1] < 0:
                    camera[1] = len(tiles[0]) - 1
                mapUpdateNeeded = True
            if event.key == pygame.K_UP:
                camera[0] += 1
                if camera[0] >= len(tiles):
                    camera[0] = 0
                mapUpdateNeeded = True
            if event.key == pygame.K_DOWN:
                camera[0] -= 1
                if camera[0] < 0:
                    camera[0] = len(tiles) - 1
                mapUpdateNeeded = True

            if event.key == pygame.K_m:
                DEBUGGING = not DEBUGGING

    if mapUpdateNeeded:
        update = [(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)]
        tiles[camera[0]][camera[1]].draw(0, 0, 0, 0)
        counter = 0

    if LD is not None:
        if selected is not None and type(selected) == Character:
            LD.draw()
        else:
            LD = None

    if showCharacterButtons:
        for index, button in enumerate(characterButtons):
            button.draw()

    pygame.display.update(update)
    screen.fill((0, 0, 0))
    update = []
    clock.tick(60)
    if DEBUGGING:
        speed = clock.get_fps()
        if speed < 55:
            print(speed)
