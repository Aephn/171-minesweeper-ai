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
import math

# offsets for
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

        # Tiles we have already proven safe but haven't uncovered yet.
        self.safe_queue = deque()

        # Tiles provably mines:
        self.mines = set()

        # Tiles that we have seen (or are already queued to be seen)
        self.queued = set()

        # Uncovered tiles whose number > 0
        self.frontier = set()

        # Track where flags are
        self.flagged = set()
        self._last_action = None

        self.last_x = startX
        self.last_y = startY
        self.queued.add((startX, startY))

    ########################################################################
    # YOUR CODE ENDS						   #
    ########################################################################

    #
    # Helpers added for full-frontier CSP and globally weighted guessing
    #

    def getAction(self, number: int) -> Action:
        if number == -1:
            # If the last action was a flag/unflag, add/remove the tile to the flagged set
            if self._last_action == AI.Action.FLAG:
                self.flagged.add((self.last_x, self.last_y))
            elif self._last_action == AI.Action.UNFLAG:
                self.flagged.discard((self.last_x, self.last_y))
        else:
            # Record last move on board
            self.board[self.last_x][self.last_y] = number

            # If tile is 0 it is def safe
            if number == 0:
                for dx, dy in POSITIONS:
                    nx, ny = self.last_x + dx, self.last_y + dy
                    if (
                        0 <= nx < self.colDimension
                        and 0 <= ny < self.rowDimension
                        and (nx, ny) not in self.queued
                    ):
                        self.safe_queue.append((nx, ny))
                        self.queued.add((nx, ny))
            else:
                # tile is a non-zero frontier tile (we are unsure right now)
                self.frontier.add((self.last_x, self.last_y))

        # Clear all guaranteed safe tiles (to get to the full frontier)
        while self.safe_queue:
            x, y = self.safe_queue.popleft()

            res = self.uncover_tile(x, y)
            # if tile is already uncovered, skip it
            if not res:
                continue
            return res

        # flag all provably mines
        if self.mines:
            x, y = self.mines.pop()
            self.store_action(x, y, AI.Action.FLAG)
            return Action(AI.Action.FLAG, x, y)

        # continue code for locality semantics (iterate a copy: loop may discard from frontier)
        for fx, fy in list(self.frontier):
            res, flags = self.check_position(fx, fy)

            # if all empty spots are mines...
            num_empty = len(res)
            mine_total = self.board[fx][fy]

            # if there are no empty spots, remove from frontier (since we can't do anything with it)
            if num_empty == 0:
                self.frontier.discard((fx, fy))

            mines_among_unknown = mine_total - flags
            # all free positions are guaranteed to be free (mines among unknowns = 0)
            if res and mines_among_unknown == 0:
                for pos_tup in res:
                    self.safe_queue.append(pos_tup)

                # technically could be unsafe..?
                x, y = self.safe_queue.popleft()
                return self.uncover_tile(x, y)

            # all unknown positions are mines
            if res and num_empty == mines_among_unknown:
                for pos_tup in res:
                    self.mines.add(pos_tup)

                # technically could be unsafe..?
                x, y = res[0]
                self.mines.discard((x, y))
                self.store_action(x, y, AI.Action.FLAG)
                return Action(AI.Action.FLAG, x, y)

        # If we have flagged all mines, all remaining tiles can be assumed to be safe
        if len(self.flagged) == self.totalMines:
            for x in range(self.colDimension):
                for y in range(self.rowDimension):
                    if self.board[x][y] == -1 and (x, y) not in self.flagged:
                        self.safe_queue.append((x, y))

        return Action(AI.Action.LEAVE)

    def store_action(self, x, y, action):
        self.last_x = x
        self.last_y = y
        self._last_action = action

    def check_position(self, x, y) -> list[list[tuple[int, int]], int]:
        # single check function:
        # Return positions of all free
        result = []
        flags = 0
        for dx, dy in POSITIONS:
            t_x = x + dx
            t_y = y + dy

            if (t_x, t_y) in self.flagged:
                flags += 1

            elif (
                0 <= t_x < self.colDimension
                and 0 <= t_y < self.rowDimension
                and self.board[t_x][t_y] == -1
            ):
                result.append((t_x, t_y))

        return [result, flags]

    def uncover_tile(self, x, y) -> Action | None:
        if self.board[x][y] != -1:
            return None
        self.store_action(x, y, AI.Action.UNCOVER)
        return Action(AI.Action.UNCOVER, x, y)

    ########################################################################
    # YOUR CODE ENDS							   #
    ########################################################################
