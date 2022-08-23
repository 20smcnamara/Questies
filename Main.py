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

    def __init__(self, args={"Blocking": True}):
        self.selected = False
        self.blocking = args["Blocking"]

    def isBlocking(self):
        return self.blocking

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

    def __init__(self, wg):
        super().__init__()
        self.weight = wg


class Character(Object):

    def __init__(self, pos, mvmt=30):
        super().__init__()
        self.movement = mvmt + BASE_MOVEMENT_COST
        self.spellCaster = False
        self.tile = pos
        self.items = []

    def isSpellCaster(self):
        return self.spellCaster

    def select(self):
        super().select()

    def deselect(self):
        super().deselect()

    def moveTo(self, tile):
        self.tile = tile

    def highlight(self):
        pos = self.findTilesToMoveTo(self.tile[0], self.tile[1])
        for p in pos:
            tiles[p[0]][p[1]].highlight()

    def unHighlight(self):
        pos = self.findTilesToMoveTo(self.tile[0], self.tile[1])
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
            if self.selected and self.selectedItem == 0:
                self.selected = False
                self.selectedItem = 1

            # Already selected item so move to next one
            if self.contents[self.selectedItem - 1].isSelected():
                self.selectedItem += 1
                if self.selectedItem > len(self.contents):
                    self.selectedItem = 0

            # Selection

            # Selection tile is the tile itself
            if self.selectedItem == 0:
                if selected is not None:
                    selected.deselect()
                self.selected = True
                selected = self

            # Selection is the contents of the tile
            if self.selectedItem > 0 and not self.contents[self.selectedItem - 1].isSelected():
                if selected is not None:
                    selected.deselect()
                self.contents[self.selectedItem - 1].select()

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


class ListDisplay:

    def __init__(self, LOI, rct=(int(SCREEN_WIDTH / 20), int(SCREEN_HEIGHT / 20),
                                 int(SCREEN_WIDTH / 3), int(SCREEN_HEIGHT / 20 * 18)),
                 txt="", txt_color=(75, 75, 75)):
        self.LOI = LOI
        self.rect = rct

        labelRect = (rct[0] + rct[2] * 0.1, rct[1] + rct[3] * 0.01, rct[2] * 0.8, rct[3] * 0.08)
        labelFont = fitTextSize(font, labelRect, txt)
        self.labelPos = (int(labelRect[0] + labelRect[2] / 2 - labelFont.size(txt)[0] / 2),
                         int(labelRect[1] + labelRect[3] / 2 - labelFont.size(txt)[1] / 2))
        self.labelText = pygame.font.Font.render(labelFont, txt, True, txt_color)

        self.lineOne = (int(rct[0]), int(rct[1] + rct[3] * 0.1))
        self.lineTwo = (int(rct[0] + rct[2]), int(rct[1] + rct[3] * 0.1))

    def draw(self):
        pygame.draw.rect(screen, (150, 150, 150), self.rect)
        pygame.draw.rect(screen, OUTLINE_COLOR, self.rect, OUTLINE_SIZE)
        screen.blit(self.labelText, self.labelPos)
        pygame.draw.line(screen, OUTLINE_COLOR, self.lineOne, self.lineTwo, OUTLINE_SIZE)


class Button:

    def __init__(self, rct, txt, color, txt_color):
        labelRect = rct
        labelFont = fitTextSize(font, labelRect, txt)
        self.labelPos = (int(labelRect[0] + labelRect[2] / 2 - labelFont.size(txt)[0] / 2),
                         int(labelRect[1] + labelRect[3] / 2 - labelFont.size(txt)[1] / 2))
        self.labelText = pygame.font.Font.render(labelFont, txt, True, txt_color)
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
                newRow.append(Tile(col, row, terrain=DirtRoad))
            else:
                newRow.append(Tile(col, row))
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

tiles[camera[0]][camera[1] + 1].addContent(Character((camera[0], camera[1] + 1)))
tiles[camera[0]][camera[1]].draw(0, 0, 0, 0)

characterButtons.append(Button((int(SCREEN_WIDTH / 6), int(SCREEN_HEIGHT / 8 * 6), int(SCREEN_WIDTH / 6),
                                int(SCREEN_HEIGHT / 8)), "Items", (45, 45, 90), (0, 230, 100)))
characterButtons.append(Button((int(SCREEN_WIDTH / 12 * 5), int(SCREEN_HEIGHT / 8 * 6), int(SCREEN_WIDTH / 6),
                                int(SCREEN_HEIGHT / 8)), "Spells", (45, 45, 90), (0, 230, 100)))
characterButtons.append(Button((int(SCREEN_WIDTH / 6 * 4), int(SCREEN_HEIGHT / 8 * 6), int(SCREEN_WIDTH / 6),
                                int(SCREEN_HEIGHT / 8)), "Movement", (45, 45, 90), (0, 230, 100)))

# Loop variables
mouseDown = [0, 0, 0]
DEBUGGING = True
selected = None

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
                        if index == 0:
                            LD = ListDisplay(selected.items, txt="Items")
                        if index == 2:
                            selected.highlight()
                        showCharacterButtons = False

            # Check for tile stuff
            else:
                tile_x = int(camera[1] - (SCREEN_CENTER_X - HALF_TILE - mouseLocation[0]) / TILE_SIZE)
                tile_y = int(camera[0] - (SCREEN_CENTER_Y - HALF_TILE - mouseLocation[1]) / TILE_SIZE)

                if DEBUGGING:
                    print(tile_x, tile_y)

                if tile_y >= len(tiles):
                    tile_y %= len(tiles)
                if tile_x >= len(tiles[0]):
                    tile_x %= len(tiles[0])

                if selected is not None and type(selected) == Character:
                    s_tile = tiles[tile_y][tile_x]
                    if s_tile.isHighlighted() and not s_tile.containsBlocker():
                        selected.unHighlight()
                        oldPosition = selected.tile
                        tiles[oldPosition[0]][oldPosition[1]].contents.remove(selected)
                        tiles[tile_y][tile_x].addContent(selected)
                        selected.moveTo((tile_y, tile_x))
                        selected.deselect()
                    else:
                        selected.deselect()
                else:
                    tiles[tile_y][tile_x].toggleSelect()

                if type(selected) == Character:
                    showCharacterButtons = True

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
            if index != 1:
                button.draw()
            if selected.isSpellCaster():
                button.draw()

    pygame.display.update(update)
    screen.fill((0, 0, 0))
    update = []
    clock.tick(60)
    # print(clock.get_fps())
