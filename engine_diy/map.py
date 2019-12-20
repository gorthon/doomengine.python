from enum import Enum

class Map(object):
    # used to identify if a node id has the sector bit on the end
    # 0x8000 in binary 1000000000000000
    # 0x8000 in decimal 32768
    SUBSECTORIDENTIFIER = 0x8000
    class Indices:
        NAME      = 0
        THINGS    = 1
        LINEDEFS  = 2
        SIDEDEFS  = 3
        VERTEXES  = 4
        SEGS      = 5
        SSECTORS  = 6
        NODES     = 7
        SECTORS   = 8
        REJECT    = 9
        BLOCKMAP  = 10
        COUNT     = 11
    def __init__(self):
        self.name = ""
        self.vertices = []
        self.linedefs = []
        self.things = []
        self.playerThing = None # a thing
        self.nodes = []
        self.subsectors = []
        self.segs = []
        self.minx = None
        self.maxx = None
        self.miny = None
        self.maxy = None
        self.width = None
        self.height = None
    # helper method to get min and
    # max values of the maps coords
    def createMetaData(self):
        for i, ld in enumerate(self.linedefs):
            start = self.vertices[ld.startVertexID]
            end = self.vertices[ld.endVertexID]

            if self.minx == None or self.minx > start.x:
                self.minx = start.x
            if self.maxx == None or self.maxx < start.x:
                self.maxx = start.x
            if self.minx == None or self.minx > end.x:
                self.minx = end.x
            if self.maxx == None or self.maxx < end.x:
                self.maxx = end.x

            if self.miny == None or self.miny > start.y:
                self.miny = start.y
            if self.maxy == None or self.maxy < start.y:
                self.maxy = start.y
            if self.miny == None or self.miny > end.y:
                self.miny = end.y
            if self.maxy == None or self.maxy < end.y:
                self.maxy = end.y
        self.width = self.maxx - self.minx
        self.height = self.maxy - self.miny
    def getRootNode(self):
        return self.nodes[len(self.nodes) - 1]
    # traverse the BSP tree
    def isOnBackSide(self, x, y, node):
        dx = x - node.xPartition
        dy = y - node.yPartition
        # use cross product to determine which direction
        cross = dx * node.yChangePartition - dy * node.xChangePartition
        return cross <= 0
    def getSubsector(self, x, y):
        nodeId = len(self.nodes) - 1
        return self.recurseFindSubsector(x, y, nodeId)
    def recurseFindSubsector(self, x, y, nodeId):
        # see if this is a subsector
        # they used the last bit of the nodeId to set if it was
        # a node that was a subsector (if last bit was 1)
        # x & y:
        # Does a "bitwise and". Each bit of the output is 1
        # if the corresponding bit of x AND of y is 1, otherwise it's 0
        inSubsector = nodeId & Map.SUBSECTORIDENTIFIER
        if inSubsector > 0:
            # ~ x:
            # Returns the complement of x - the number you get by
            # switching each 1 for a 0 and each 0 for a 1.
            # This is the same as -x - 1.
            subsectorId = nodeId & (~Map.SUBSECTORIDENTIFIER)
            return subsectorId

        node = self.nodes[nodeId]
        isOnBack = self.isOnBackSide(x, y, node)
        if isOnBack:
            return self.recurseFindSubsector(x, y, node.backChildID)
        else:
            return self.recurseFindSubsector(x, y, node.frontChildID)

class Vertex(object):
    def __init__(self):
        self.x = 0 # 2byte signed short
        self.y = 0 # 2byte signed short
    def sizeof():
        return 4
    def __str__(self):
        return "{},{}".format(self.x, self.y)

class Linedef(object):
    class Flags:
        BLOCKING      = 0,
        BLOCKMONSTERS = 1,
        TWOSIDED      = 2,
        DONTPEGTOP    = 4,
        DONTPEGBOTTOM = 8,
        SECRET        = 16,
        SOUNDBLOCK    = 32,
        DONTDRAW      = 64,
        DRAW          = 128

    def __init__(self):
        # all 2 bytes (14 bytes)
        self.startVertexID = 0 # uint16
        self.endVertexID = 0 # uint16
        self.flags = 0 # uint16
        self.lineType = 0 # uint16
        self.sectorTag = 0 # uint16
        self.frontSideDef = 0 # uint16
        self.backSideDef = 0 # uint16

    def sizeof():
        return 14

    def __str__(self):
        return "s.{},e.{} f.{} t.{} s.{} f.{} b.{}"\
                .format(self.startVertexID, self.endVertexID,\
                self.flags, self.lineType, self.sectorTag,\
                self.frontSideDef, self.backSideDef)

class Thing(object):
    # Types https://doomwiki.org/wiki/Thing_types
    class Types:
        # Other
        O_PLAYER1 = 1
        O_PLAYER2 = 2
        O_PLAYER3 = 3
        O_PLAYER4 = 4
        O_DEATHMATCH_START = 11
        O_TELEPORT_LANDING = 14

        # Keys
        K_BLUECARD = 5
        K_YELLOWCARD = 6
        K_REDCARD = 13
        K_REDSKULL = 38
        K_YELLOWSKULL = 39
        K_BLUESKULL = 40

        # Monsters
        M_SPIDERDEMON = 7
        M_SHOTGUNGUY = 9
        M_CYBERDEMON = 16
        M_SPECTRE = 58
        M_IMP = 3001
        M_DEMON = 3002
        M_BARON = 3003
        M_ZOMBIEMAN = 3004
        M_CACODEMON = 3005
        M_LOSTSOUL = 3006

        # Weapons
        W_SHOTGUN = 2001
        W_CHAINGUN = 2002
        W_ROCKETLAUNCHER = 2003
        W_PLASMAGUN = 2004
        W_CHAINSAW = 2005
        W_BFG9000 = 2006

        # Ammo
        A_ENERGY_CELL_PACK = 17
        A_CLIP = 2007
        A_SHOTGUN_SHELLS = 2008
        A_ROCKET = 2010
        A_ROCKET_BOX = 2046
        A_ENERGY_CELL = 2047
        A_BULLET_BOX = 2048
        A_SHOTGUN_BOX = 2049

        # Artifacts
        R_SUPERCHARGE = 2013
        R_HEALTHBONUS = 2014
        R_ARMORBONUS = 2015
        R_INVULNERABILITY = 2022
        R_BERSERK = 2023
        R_PARTIAL_INVISIBILITY = 2024
        R_COMPUTER_AREA_MAP = 2026
        R_LIGHT_AMP_VISOR = 2045

        # Powerups
        P_BACKPACK = 8
        P_STIMPACK = 2011
        P_MEDKIT = 2012
        P_ARMOR = 2018
        P_MEGAARMOR = 2019
        P_RADIATION_SUIT = 2025

        # Obstacles
        B_IMPALED_HUMAN = 25
        B_TWITCHING_IMPALED_HUMAN = 26
        B_SKULL_ON_POLE = 27
        B_FIVE_SKULLS = 28
        B_PILE_SKULLS = 29
        B_TALL_GREEN_PILLAR = 30
        B_SHORT_GREEN_PILLAR = 31
        B_TALL_RED_PILLAR = 32
        B_SHORT_RED_PILLAR = 33
        B_CANDELABRA = 35
        B_SHORT_GREEN_PILLAR_HEART = 36
        B_SHORT_RED_PILLAR_SKULL = 37
        B_EVIL_EYE = 41
        B_FLOATING_SKULL = 42
        B_BURNT_TREE = 43
        B_TALL_BLUE_FIRESTICK = 44
        B_TALL_GREEN_FIRESTICK = 45
        B_TALL_RED_FIRESTICK = 46
        B_BROWN_STUMP = 47
        B_TALL_TECHNO_COLUMN = 48
        B_HANGING_VICTIM_TWITCHING = 49
        B_HANGING_VICTIM_ARMS = 50
        B_HANGING_VICTIM_LEG = 51
        B_HANGING_PAIR_LEGS = 52
        B_HANGING_LEG = 53
        B_LARGE_BROWN_TREE = 54
        B_SHORT_BLUE_FIRESTICK = 55
        B_SHORT_GREEN_FIRESTICK = 56
        B_SHORT_RED_FIRESTICK = 57
        B_FLOOR_LAMP = 2028
        B_EXPLODING_BARREL = 2035

        # Decorations
        D_BLOODYMESS = 10
        D_BLOODYMESS2 = 12
        D_DEAD_PLAYER = 15
        D_DEAD_FORMER_HUMAN = 18
        D_DEAD_FORMER_SERGEANT = 19
        D_DEAD_IMP = 20
        D_DEAD_DEMON = 21
        D_DEAD_CACODEMON = 22
        D_DEAD_LOSTSOUL_INVIS = 23
        D_POOL_BLOOD_FLESH = 24
        D_CANDLE = 34
        D_HANGING_VICTIM_ARMS = 59
        D_HANGING_LEG = 62
        D_HANGING_VICTIM_TWITCHING = 63

    def __init__(self):
        self.x = 0 # int16
        self.y = 0 # int16
        self.angle = 0 # uint16
        self.type = 0 # uint16
        self.flags = 0 # uint16
    def sizeof():
        return 10
    def __str__(self):
        return "{},{} {} {} {}"\
                .format(self.x, self.y, self.angle, self.type, self.flags)

# BSP Node
class Node(object):
    def __init__(self):
        # coords of slitter
        self.xPartition = 0 # int16
        self.yPartition = 0 # int16
        # directional length to reach end of splitter
        self.xChangePartition = 0 # int16
        self.yChangePartition = 0 # int16
        # corners of front box
        self.frontBoxTop = 0 # int16
        self.frontBoxBottom = 0 # int16
        self.frontBoxLeft = 0 # int16
        self.frontBoxRight = 0 # int16
        # corners of back box
        self.backBoxTop = 0 # int16
        self.backBoxBottom = 0 # int16
        self.backBoxLeft = 0 # int16
        self.backBoxRight = 0 # int16
        # indexes of children + subsector indicator
        self.frontChildID = 0 # uint16
        self.backChildID = 0 # uint16
    def sizeof():
        return 28
    def __str__(self):
        return "{},{} {},{} FTB:{},{} FLR:{},{}"\
                .format(self.xPartition, self.yPartition,\
                self.xChangePartition, self.yChangePartition,\
                self.frontBoxTop, self.frontBoxBottom,\
                self.frontBoxLeft, self.frontBoxRight,\
                )

# Sub sector
# a smaller portion of a Sector
# comprised of segs, which are portions of lines
# added together the segs create a subsector
# segs are formed via BSP tree so subsectors
# are used to isolate a player within the map
class Subsector(object):
    def __init__(self):
        self.segCount = 0 # unit16
        self.firstSegID = 0 # unit16
    def sizeof():
        return 4
    def __str__(self):
        return "{} {}".format(self.segCount, self.firstSegID)

# Portion of a linedef, when combined with
# other segs form a sub sector
class Seg(object):
    def __init__(self):
        self.startVertexID = 0 # uint16
        self.endVertexID = 0 # uint16
        self.angle = 0 # uint16 (degrees)
        self.linedefID = 0 # uint16
        self.direction = 0 # uint16 (0=same as linedef, 1=opposite of linedef)
        self.offset = 0 # uint16 (distance along linedef to start of seg)
    def sizeof():
        return 12


