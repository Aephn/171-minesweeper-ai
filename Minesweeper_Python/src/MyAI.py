# ==============================CS-199==================================
# FILE:			MyAI.py
#
# AUTHOR: 		Justin Chung
#
# DESCRIPTION:	This file contains the MyAI class. You will implement your
# agent in this file. You will write the 'getAction' function,
# the constructor, and any additional helper functions.
#
# NOTES: 		- MyAI inherits from the abstract AI class in AI.py.
#
# - DO NOT MAKE CHANGES TO THIS FILE.
# ==============================CS-199==================================

# not needed for macos, but needed for windows
# from msvcrt import open_osfhandle
from AI import AI
from Action import Action
from collections import deque

# offsets for checking neighbors
POSITIONS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]


class MyAI(AI):
    def __init__(self, rowDimension, colDimension, totalMines, startX, startY):
        ########################################################################
        # YOUR CODE BEGINS						   #
        ########################################################################
        self.rowDimension = rowDimension
        self.colDimension = colDimension
        self.totalMines = totalMines

        # -1 to store unknown
        self.board = [[-1 for _ in range(rowDimension)] for _ in range(colDimension)]

        # Tiles proven to be mines
        self.known_mines = set()

        # Tiles already queued as safe
        self.safe_set = set()

        # Tiles that we have seen (or are already queued to be seen)
        self.safe_queue = deque()

        # Uncovered tiles whose number > 0
        self.frontier = set()

        self.last_x = startX
        self.last_y = startY

        # Track last action sent to game
        self.last_action = AI.Action.UNCOVER

        # Count safe tiles that were uncovered
        self.uncovered_count = 0

    ########################################################################
    # YOUR CODE ENDS						   #
    ########################################################################
    
    def getAction(self, number: int) -> Action:
        self.update_after_uncover(number)

        self.apply_basic_rules()
        self.apply_global_rules()
        
        action = self.pop_safe_action()
        if action is not None:
            return action

        total_safe = self.rowDimension * self.colDimension - self.totalMines
        if self.uncovered_count >= total_safe:
            return Action(AI.Action.LEAVE)

        # Guess if no guaranteed move exists
        action = self.guess_tile()
        if action is not None:
            return action

        return Action(AI.Action.LEAVE)

        
    def update_after_uncover(self, number):
        if number == -1:
            return
        
        if self.board[self.last_x][self.last_y] == -1:
            self.board[self.last_x][self.last_y] = number
            self.uncovered_count += 1

        if number == 0:
            for nx, ny in self.neighbors(self.last_x, self.last_y):
                self.add_safe(nx, ny)
        else:
            self.frontier.add((self.last_x, self.last_y))

    def apply_basic_rules(self):
        changed = True

        while changed:
            changed = False

            for x, y in list(self.frontier):
                if self.board[x][y] <= 0:
                    self.frontier.discard((x, y))
                    continue

                unknowns = []
                known_mine_count = 0

                # Count unknown neighbors and known mines
                for nx, ny in self.neighbors(x, y):
                    if (nx, ny) in self.known_mines:
                        known_mine_count += 1
                    elif self.board[nx][ny] == -1:
                        unknowns.append((nx, ny))

                if not unknowns:
                    self.frontier.discard((x, y))
                    continue

                remaining_mines = self.board[x][y] - known_mine_count

                # If all mines are found, rest are safe
                if remaining_mines <= 0:
                    for x, y in unknowns:
                        if self.add_safe(x, y):
                            changed = True

                # If all unknowns must be mines, mark them
                elif remaining_mines == len(unknowns):
                    for tile in unknowns:
                        if tile not in self.known_mines:
                            self.known_mines.add(tile)
                            self.safe_set.discard(tile)
                            changed = True


    def apply_global_rules(self):
        unknowns = self.all_unknown_tiles()
        remaining_mines = self.totalMines - len(self.known_mines)

        # If all mines are known, everything else is safe
        if remaining_mines <= 0:
            for x, y in unknowns:
                self.add_safe(x, y)

        # If every unknown tile is a mine, mark them
        elif remaining_mines == len(unknowns):
            for tile in unknowns:
                self.known_mines.add(tile)
                self.safe_set.discard(tile)


    def guess_tile(self):
        unknowns = self.all_unknown_tiles()

        if not unknowns:
            return None

        remaining_mines = max(0, self.totalMines - len(self.known_mines))
        global_risk = float(remaining_mines) / float(len(unknowns))

        best_tile = None
        best_risk = 2.0

        for x, y in unknowns:
            risks = [global_risk]

            # Check nearby clues to estimate risk
            for nx, ny in self.neighbors(x, y):
                clue = self.board[nx][ny]

                if clue <= 0:
                    continue

                unknown_neighbors = []
                known_mine_count = 0

                for ax, ay in self.neighbors(nx, ny):
                    if (ax, ay) in self.known_mines:
                        known_mine_count += 1
                    elif self.board[ax][ay] == -1:
                        unknown_neighbors.append((ax, ay))

                remaining = clue - known_mine_count

                if unknown_neighbors and remaining >= 0:
                    risks.append(float(remaining) / float(len(unknown_neighbors)))

            risk = max(risks)

            # Small preference for edges/corners
            if x == 0 or x == self.colDimension - 1:
                risk -= 0.0001

            if y == 0 or y == self.rowDimension - 1:
                risk -= 0.0001

            if risk < best_risk:
                best_risk = risk
                best_tile = (x, y)

        if best_tile is None:
            return None

        return self.uncover_tile(best_tile[0], best_tile[1])


    def pop_safe_action(self):
        while self.safe_queue:
            x, y = self.safe_queue.popleft()
            self.safe_set.discard((x, y))

            if self.board[x][y] == -1 and (x, y) not in self.known_mines:
                return self.uncover_tile(x, y)

        return None


    def add_safe(self, x, y):
        if not self.in_bounds(x, y):
            return False

        tile = (x, y)

        if self.board[x][y] != -1:
            return False

        if tile in self.known_mines:
            return False

        if tile in self.safe_set:
            return False

        self.safe_set.add(tile)
        self.safe_queue.append(tile)

        return True


    def all_unknown_tiles(self):
        result = []

        for x in range(self.colDimension):
            for y in range(self.rowDimension):
                if self.board[x][y] == -1 and (x, y) not in self.known_mines:
                    result.append((x, y))

        return result


    def neighbors(self, x, y):
        result = []

        for dx, dy in POSITIONS:
            nx = x + dx
            ny = y + dy

            if self.in_bounds(nx, ny):
                result.append((nx, ny))

        return result


    def in_bounds(self, x, y):
        return 0 <= x < self.colDimension and 0 <= y < self.rowDimension


    def store_action(self, x, y, action):
        self.last_x = x
        self.last_y = y
        self.last_action = action


    def uncover_tile(self, x, y):
        if not self.in_bounds(x, y):
            return None

        if self.board[x][y] != -1:
            return None

        if (x, y) in self.known_mines:
            return None

        self.store_action(x, y, AI.Action.UNCOVER)

        return Action(AI.Action.UNCOVER, x, y)

    ########################################################################
    # YOUR CODE ENDS							   #
    ########################################################################
