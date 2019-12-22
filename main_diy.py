import sys, engine_diy, pygame, random, math
from engine_diy.wad import WAD
from engine_diy.game2d import Game2D
from engine_diy.map import *
from engine_diy.player import Player
from engine_diy.angle import Angle
from engine_diy.segment_range import *

class Plot(object):
    def __init__(self, map, surfWidth, surfHeight):
        # calculate map scale to fit screen minus padding
        self.pad = pad = 10
        gw = (surfWidth - self.pad*2)
        gh = (surfHeight - self.pad*2)
        self.scale = scale = min(gw/map.width, gh/map.height)

        # center the map on the screen
        self.xoff = (surfWidth - (map.width * scale))/2 - (map.minx * scale)
        self.yoff = (surfHeight - (map.height *scale))/2 + (map.maxy * scale)
    def ot(self, x, y):
        # flip cartesian, scale and translate
        x = x * self.scale + self.xoff
        y = -y * self.scale + self.yoff
        return x, y

def angleToScreen(angle, fov, screenWidth):
    ix = 0
    halfWidth = (int)(screenWidth/2)
    if angle.gtF(fov):
        # left side
        angle.isubF(fov)
        ix = halfWidth - round(math.tan(angle.toRadians()) * halfWidth)
    else:
        # right side
        angle = Angle(fov - angle.deg)
        ix = round(math.tan(angle.toRadians()) * halfWidth)
        ix += halfWidth
    return ix


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

def drawSubsector(subsectorId, rgba=None):
    global game, map, pl
    subsector = map.subsectors[subsectorId]
    if rgba is None:
        rgba = (random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1), 1)
    for i in range(0, subsector.segCount):
        seg = map.segs[subsector.firstSegID + i]
        startVertex = map.vertices[seg.startVertexID]
        endVertex = map.vertices[seg.endVertexID]
        sx, sy = pl.ot(startVertex.x, startVertex.y)
        ex, ey = pl.ot(endVertex.x, endVertex.y)
        game.drawLine([sx,sy], [ex,ey], rgba, 2)

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
player.setPosition(map.playerThing.x, map.playerThing.y)
player.setAngle(map.playerThing.angle)


# setup game
game = Game2D()
game.setupWindow(1600, 1200)

# main screen plot
pl = Plot(map, game.width, game.height)

# render helpers
mode = 0
max_modes = 10
def mode_up():
    global mode
    mode = (mode + 1) % max_modes
game.onKeyUp(pygame.K_UP, mode_up)
def mode_down():
    global mode
    mode = (mode - 1) % max_modes
game.onKeyUp(pygame.K_DOWN, mode_down)
def on_left():
    global player
    player.angle.iaddF(2) # rotate left
game.onKeyHold(pygame.K_LEFT, on_left)
def on_right():
    global player
    player.angle.isubF(2) # rotate right
game.onKeyHold(pygame.K_RIGHT, on_right)
def on_w():
    global player
    player.y += 5 # move "up"/"forward" (positive y in game world)
game.onKeyHold(pygame.K_w, on_w)
def on_s():
    global player
    player.y -= 5 # move "down"/"backward" (negative y in game world)
game.onKeyHold(pygame.K_s, on_s)
def on_a():
    global player
    player.x -= 5 # move "left"
game.onKeyHold(pygame.K_a, on_a)
def on_d():
    global player
    player.x += 5 # move "left"
game.onKeyHold(pygame.K_d, on_d)


# takes screen projected wall and builds
# updates the segList to render
def clipWall(segList, wallStart, wallEnd):
    node = segList
    while node != None and node.range.xEnd < wallStart - 1:
        node = node.next
    # should always have a node since we cap our ends with
    # "infinity"
    if wallStart < node.range.xStart:
        # found a position in the node list
        # are they overlapping?
        if wallEnd < node.range.xStart - 1:
            # all of the wall is visible to insert it
            p = node.insertPrevious(wallStart, wallEnd)
            # go to next wall
            print(p, " vs ", segList, " vs ", node)
            return
        # if not overlapping, end is already included
        # so just update the start
        node.setRange(wallStart, node.range.xStart - 1)
    # this part is already occupied
    if wallEnd <= node.range.xEnd:
        return # go to next wall

    #
    nextNode = node
    while nextNode.range.xEnd >= nextNode.next.range.xStart - 1:
        # this wall partially clipped by other walls
        # so store each fragment
        # StoreWallRange(seg, NextWall->XEnd + 1, next(NextWall, 1)->XStart - 1);
        nextNode = nextNode.next
        if wallEnd <= nextNode.range.xEnd:
            node.xEnd = nextNode.range.xEnd
            if nextNode != node:
                # delete range of walls
                node = node.next
                nextNode = nextNode.next
                # garbage collector erase
                # m_SolidWallRanges.erase(FoundClipWall, NextWall);
            return
    return
def clipWall2(segList, wallStart, wallEnd):
    segRange = None
    segIndex = None
    # skip all segments that end before this wall starts
    i=0
    while (i < len(segList) and segList[i].xEnd < wallStart - 1):
        i += 1
    segIndex = i
    segRange = segList[segIndex]
    # should always have a node since we cap our ends with
    # "infinity"
    # START to OVERLAP
    if wallStart < segRange.xStart:
        # found a position in the node list
        # are they overlapping?
        if wallEnd < segRange.xStart - 1:
            # all of the wall is visible to insert it
            # STOREWALL
            # StoreWallRange(seg, CurrentWall.XStart, CurrentWall.XEnd);
            segList.insert(segIndex, SolidSegmentRange(wallStart, wallEnd))
            # go to next wall
            return
        # if not overlapping, end is already included
        # so just update the start
        # STOREWALL
        # StoreWallRange(seg, CurrentWall.XStart, FoundClipWall->XStart - 1);
        segRange.xStart = wallStart
    # FULL OVERLAPPED
    # this part is already occupied
    if wallEnd <= segRange.xEnd:
        return # go to next wall

    # CHOP AND MERGE
    # start by looking at the next entry in the list
    # is the next entry within the current wall range?
    nextSegIndex = segIndex
    nextSegRange = segRange
    while wallEnd >= segList[nextSegIndex + 1].xStart - 1:
        nextSegIndex += 1
        nextSegRange = segList[nextSegIndex]
        # partially clipped by other walls, store each fragment
        # STOREWALL
        # StoreWallRange(seg, NextWall->XEnd + 1, next(NextWall, 1)->XStart - 1);
        if wallEnd <= nextSegRange.xEnd:
            segRange.xEnd = nextSegRange.xEnd
            if nextSegIndex != segIndex:
                segIndex += 1
                nextSegIndex += 1
                del segList[segIndex:nextSegIndex]
            return

    # wall precedes all known segments
    # STOREWALL
    # StoreWallRange(seg, NextWall->XEnd + 1, CurrentWall.XEnd);
    segRange.xEnd = wallEnd
    if (nextSegIndex != segIndex):
        segIndex += 1
        nextSegIndex += 1
        del segList[segIndex:nextSegIndex]

    return
def printSegList(segList):
    for i,r in enumerate(segList):
        if i+1 < len(segList):
            print("{} > ".format(r), end='')
        else:
            print(r, end='')
    print('')

# python DIY linked lists are a nightmare
# because of the pass-object-by-reference
# nature of variables
# when I change next and prev values on a
# node it changes it for that copy of the
# variable, and not for the underlying reference

# test with straight lists
segList = [SolidSegmentRange(-100000, -1)]
segList.append(SolidSegmentRange(320, 100000))
printSegList(segList)

# new wall
clipWall2(segList, 68, 80) # -i 68,80 +i
printSegList(segList)

# free start, overlap end
clipWall2(segList, 46, 69) # -i 46,80 +i
printSegList(segList)

# completely overlapped
clipWall2(segList, 70, 75) # -i 46,80 +i
printSegList(segList)

# add some segments that will partially overlap
clipWall2(segList, 107, 195)
clipWall2(segList, 198, 210)
clipWall2(segList, 223, 291)
# -100000,-1 > 46,80 > 107,195 > 198,210 > 223,291 > 320,100000
printSegList(segList)

# chopped and merged
clipWall2(segList, 76, 107)
# -100000,-1 > 46,195 > 198,210 > 223,291 > 320,100000
printSegList(segList)
clipWall2(segList, 2, 316)
# -100000,-1 > 2,316 > 320,100000
printSegList(segList)

# not in list at all yet
segList = [SolidSegmentRange(-100000, -1)]
segList.append(SolidSegmentRange(46,210))
segList.append(SolidSegmentRange(223,291))
segList.append(SolidSegmentRange(320,100000))
printSegList(segList)
clipWall2(segList, 0, 42)
printSegList(segList)

quit()

# test wall clipping
segList = SegmentNode()
segList.setRange(-100000, -1)
segList.insertNext(320, 100000)
print(segList)
clipWall(segList, 68,80)
#segList = clipWall(segList, 68,80)
print(segList)
#clipWall(segList, 46,80)
#print(segList)


quit()


modeSSrenderIndex = 0
modeAngleIndex = 0
while True:

    game.events()
    if game.over:
        break;

    # update

    # draw
    game.drawStart()

    # loop over linedefs
    for i, ld in enumerate(map.linedefs):
        start = map.vertices[ld.startVertexID]
        end = map.vertices[ld.endVertexID]
        # map is in cartesian, flip to screen y
        sx, sy = pl.ot(start.x, start.y)
        ex, ey = pl.ot(end.x, end.y)
        # draw the line
        game.drawLine([sx, sy], [ex, ey], (1,1,1,1), 1)

    fov = 90
    fpsWinWidth = 320
    fpsWinHeight = 200
    fpsWinOffX = 20
    fpsWinOffY = 20
    game.setFPS(60)
    # render things as dots (things list does not contain player thing)
    if mode == 1:
        for i, thing in enumerate(map.things):
            x, y = pl.ot(thing.x, thing.y)
            game.drawRectangle([x-2,y-2], 4, 4, (1,0,0,1))

        ## render player
        px, py = pl.ot(player.x, player.y)
        game.drawRectangle([px-2,py-2], 4, 4, (0,1,0,1))
    if mode == 2:
        drawNode(game, map.getRootNode())
    if mode == 3:
        for i, n in enumerate(map.nodes):
            drawNode(game, n)
    if mode == 4:
        game.setFPS(10)
        modeSSrenderIndex = ( modeSSrenderIndex + 1 ) % len(map.subsectors)
        drawSubsector(modeSSrenderIndex, (1, 0, 0, 1))
    if mode == 5:
        # render player
        px, py = pl.ot(player.x, player.y)
        game.drawRectangle([px-2,py-2], 4, 4, (0,1,0,1))
        # render player subsector
        ssId = map.getSubsector(player.x, player.y)
        drawSubsector(ssId)
    if mode == 6:
        game.setFPS(10)
        modeAngleIndex = (modeAngleIndex + 1) % len(map.vertices)
        # render player
        px, py = pl.ot(player.x, player.y)
        game.drawRectangle([px-2,py-2], 4, 4, (0,1,0,1))
        # render target vertex
        vertex = map.vertices[modeAngleIndex]
        vx, vy = pl.ot(vertex.x, vertex.y)
        game.drawRectangle([vx-3,vy-3], 6, 6, (1,0,0,1))
        # test angle
        a = player.angleToVertex(vertex)
        dirx, diry = a.toVector()
        # render angle
        endx, endy = pl.ot(player.x + dirx*50, player.y + diry*50)
        game.drawLine([px, py], [endx, endy], (0,1,1,1), 2)
    if mode == 7 or mode == 8:
        # test segs that are in 90deg FOV of player
        # render player
        px, py = pl.ot(player.x, player.y)
        game.drawRectangle([px-2,py-2], 4, 4, (0,1,0,1))
        # iterate all of the segs and test them, if they have angles render seg
        for i, seg in enumerate(map.segs):
            linedef = map.linedefs[seg.linedefID]
            # if in mode 8 only render solid walls
            if mode == 8:
                if linedef.isSolid() is False:
                    continue

            v1 = map.vertices[seg.startVertexID]
            v2 = map.vertices[seg.endVertexID]
            angles = player.clipVerticesToFov(v1, v2, fov)
            if angles is not None:
                # render the seg
                v1x, v1y = pl.ot(v1.x, v1.y)
                v2x, v2y = pl.ot(v2.x, v2.y)
                game.drawLine([v1x,v1y], [v2x,v2y], (1,0,0,1), 2)
                # render fps window for all walls
                v1xScreen = angleToScreen(angles[0], fov, fpsWinWidth)
                v2xScreen = angleToScreen(angles[1], fov, fpsWinWidth)
                fpsStart = [v1xScreen + fpsWinOffX, fpsWinOffY]
                fpsEnd = [v1xScreen + fpsWinOffX, fpsWinHeight + fpsWinOffY]
                game.drawLine(fpsStart, fpsEnd, (1,1,0,1), 1)
                fpsStart = [v2xScreen + fpsWinOffX, fpsWinOffY]
                fpsEnd = [v2xScreen + fpsWinOffX, fpsWinHeight + fpsWinOffY]
                game.drawLine(fpsStart, fpsEnd, (1,0,1,1), 1)
    if mode == 9:
        # render player
        px, py = pl.ot(player.x, player.y)
        game.drawRectangle([px-2,py-2], 4, 4, (0,1,0,1))
        # test rendering segs with wall culling
        # start with the linked list ends being "infinity"
        segListNode = SegmentNode()
        segListNode.setRange(-10000, -1)
        segListNode.setNext(fpsWinWidth, 10000)
        print(segListNode, flush=True);
        # iterate the valid walls
        # TODO, optimize the map by having a list of
        # only solid wall linedefs and segs
        for i, seg in enumerate(map.segs):
            linedef = map.linedefs[seg.linedefID]
            if linedef.isSolid() is False:
                continue
            v1 = map.vertices[seg.startVertexID]
            v2 = map.vertices[seg.endVertexID]
            angles = player.clipVerticesToFov(v1, v2, fov)
            if angles is not None:
                # render the seg (helper)
                v1x, v1y = pl.ot(v1.x, v1.y)
                v2x, v2y = pl.ot(v2.x, v2.y)
                game.drawLine([v1x,v1y], [v2x,v2y], (1,0,0,1), 2)
                # get screen projection Xs
                v1xScreen = angleToScreen(angles[0], fov, fpsWinWidth)
                v2xScreen = angleToScreen(angles[1], fov, fpsWinWidth)
                # see if what section of this wall should be culled
                clipWall(segListNode, v1xScreen, v2xScreen)

    game.drawEnd()


    # dinky gameloop
    game.sleep()

