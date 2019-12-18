import sys, engine_diy, pygame
from engine_diy.wad import WAD
from engine_diy.game2d import Game2D
from engine_diy.map import *
from engine_diy.player import Player

class Plot(object):
    def __init__(self, map, game):
        # calculate map scale to fit screen minus padding
        self.pad = pad = 10
        gw = (game.width - self.pad*2)
        gh = (game.height - self.pad*2)
        self.scale = scale = min(gw/map.width, gh/map.height)

        # center the map on the screen
        self.xoff = (game.width - (map.width * scale))/2 - (map.minx * scale)
        self.yoff = (game.height - (map.height *scale))/2 + (map.maxy * scale)
    def ot(self, x, y):
        # flip cartesian, scale and translate
        x = x * self.scale + self.xoff
        y = -y * self.scale + self.yoff
        return x, y

# helper method to draw map nodes
def drawNode(game, node):
    ## draw front box
    rgba = (0, 1, 0, .5)
    fl, ft = pl.ot(node.frontBoxLeft, node.frontBoxTop)
    fr, fb = pl.ot(node.frontBoxRight, node.frontBoxBottom)
    game.drawBox([fl, ft], [fr, ft], [fr, fb], [fl, fb], rgba, 2)

    ## draw back box
    rgba = (1, 0, 0, .5)
    bl, bt = pl.ot(node.backBoxLeft, node.backBoxTop)
    br, bb = pl.ot(node.backBoxRight, node.backBoxBottom)
    game.drawBox([bl, bt], [br, bt], [br, bb], [bl, bb], rgba, 2)

    ## draw the node seg splitterd
    rgba = (1, 1, 0, 1)
    xp, yp = pl.ot(node.xPartition, node.yPartition)
    xc, yc = pl.ot(node.xPartition + node.xChangePartition, node.yPartition + node.yChangePartition)
    game.drawLine([xp, yp], [xc, yc], (0,0,1,1), 3)

def drawSubsector(subsectorId):
    global game
    print("DRAW SUBSECTOR", subsectorId)

# path to wad
if len(sys.argv) > 1:
    path = sys.argv[1]
else:
    path = "wads/DOOM.WAD"
# map name
if len(sys.argv) > 2:
    mapname = sys.argv[2]
else:
    mapname = "E1M1"

# load WAD
wad = WAD(path)

# choose a map
map = wad.loadMap(mapname)
if map == None:
    print("ERROR: invalid map {}".format(mapname))
    quit()

# build player
player = Player()
player.id = 1
player.x = map.playerThing.x
player.y = map.playerThing.y
player.angle = map.playerThing.angle

# setup game
game = Game2D()
game.setupWindow(1600, 1200)

pl = Plot(map, game)

# render helpers
mode = 0
max_modes = 5
def mode_up():
    global mode
    mode = (mode + 1) % max_modes
game.onKeyUp(pygame.K_UP, mode_up)
def mode_down():
    global mode
    mode = (mode - 1) % max_modes
game.onKeyUp(pygame.K_DOWN, mode_down)

while True:

    game.events()
    if game.over:
        break;

    # update

    # draw
    game.drawStart()

    # loop over linedefs
    for i, ld in enumerate(map.linedefs):
        start = map.vertices[ld.startVertex]
        end = map.vertices[ld.endVertex]
        # map is in cartesian, flip to screen y
        sx, sy = pl.ot(start.x, start.y)
        ex, ey = pl.ot(end.x, end.y)
        # draw the line
        game.drawLine([sx, sy], [ex, ey], (1,1,1,1), 1)

    # render things as dots (things list does not contain player thing)
    if mode == 1:
        for i, thing in enumerate(map.things):
            x, y = pl.ot(thing.x, thing.y)
            game.drawRectangle([x-2,y-2], 4, 4, (1,0,0,1))

        ## render player
        px, py = pl.ot(player.x, player.y)
        game.drawRectangle([px-2,py-2], 4, 4, (0,1,0,1))

    ## render last sector node
    if mode == 2:
        drawNode(game, map.getRootNode())
    if mode == 3:
        for i, n in enumerate(map.nodes):
            drawNode(game, n)
    if mode == 4:
        map.renderBspNodes(player.x, player.y, drawSubsector)

    game.drawEnd()


    # dinky gameloop
    game.sleep()

