from service.match_service import MatchVisitTemplate
from service.match_service import MatchManager
from datatype.enums import DartMultiplier, MatchStatus

CHECKOUTS = {
    170: "T20 T20 Bull",
    167: "T20 T19 Bull",
    164: "T20 T18 Bull",
    161: "T20 T17 Bull",
    160: "T20 T20 D20",

    158: "T20 T20 D19",
    157: "T20 T19 D20",
    156: "T20 T20 D18",
    155: "T20 T19 D19",
    154: "T20 T18 D20",

    136: "T20 T20 D8",

    130: "T20 T20 D5",
    129: "T19 T16 D12",
    128: "T18 T14 D16",
    127: "T20 T17 D8",
    126: "T19 T19 D6",
    125: "25 T20 D20",
    124: "T20 T16 D8",
    123: "T19 T16 D9",
    122: "T18 T20 D4",
    121: "T17 T10 D20",
    120: "T20 20 D20",

    70: "T10 D20",
    69: "T15 D12",
    68: "T20 D4",
    67: "T17 D8",
    66: "T10 D18",
    65: "T19 D4",
    64: "T16 D8",
    63: "T13 D12",
    62: "T10 D16",
    61: "T15 D8",
    60: "20 D20",

    36: "D18"
}


class X01Match(MatchManager, MatchVisitTemplate):

    def __init__(self, starting_total):
        super().__init__()
        self.scores = []  # list of scores remaining parallel to players
        self.averages = []  # single-dart average (x 3 for 3-dart average)
        self.first9 = []  # average for first 9 darts
        self.STARTING_TOTAL = starting_total

    # This has the potential to be buggy if the match is set first and players registered after
    def post_init(self):
        for i in range(0, len(self.match.players)):
            self.scores.append(self.STARTING_TOTAL)  # Might want to parameterize the starting total
            self.first9.append(None)
            self.averages.append(None)
        self.match.status = MatchStatus.IN_PROGRESS

    def validate_visit(self, player_index, visit):
        if self.match.last_player_index is player_index:
            # Note: this won't work properly for 3 players...
            return False, "Player " + str(player_index + 1) + " is not in the correct sequence. Visit ignored."

        if self.match.status is not MatchStatus.IN_PROGRESS:
            return False, "Game is not in progress."
            # print(str(self.match.last_player_index) + "-" + str(player_index))
        self.match.last_player_index = player_index
        return True, None

    def check_winning_condition(self, player_index, visit):
        """returns 1, 2 or 3 for when a dart closes the game / leg (i.e. finishing double) or 0 if not closed out

        :param player_index: position of player details in various lists
        :param visit: a list of 3 Darts (each containing multiplier and segment)
        :return: 0, 1, 2 or 3
        """
        i = 0
        for dart in visit.darts:
            i = i + 1
            if dart.multiplier == DartMultiplier.DOUBLE and self.scores[player_index] - dart.get_score() == 0:
                # game, shot!
                self.scores[player_index] = 0
                self.match.status = MatchStatus.FINISHED
                return i
            else:
                print("deducting for " + str(player_index))
                self.scores[player_index] -= dart.get_score()

        return 0

    def record_statistics(self, player_index, visit, result):
        """Store stats both for in-memory immediate use and on disk for later recall

        :return:
        """
        if result is not 0:
            visit.remove_trailing_darts(result)  # a double finished the game, so ignore any subsequent darts

        self.match.visits[player_index].append(visit)

        # Calculate first 9 if, and only if, this is the 3rd visit
        if len(self.match.visits[player_index]) == 3:
            self.first9[player_index] = (self.STARTING_TOTAL - self.scores[player_index]) / 3

        # Calculate single-dart average taking account of a double being hit with dart 1 or 2 when checking out
        num_darts_thrown = (len(self.match.visits[player_index]) - 1) * 3
        num_darts_thrown += 3 if result is 0 else result

        if result is not 0:
            self.match.winning_num_darts = num_darts_thrown
            self.match.winning_player_index = player_index

        self.averages[player_index] = (self.STARTING_TOTAL - self.scores[player_index]) / num_darts_thrown

    def format_summary(self, player_index, visit):
        # Include suggested checkout if remaining score can be checked out in 3 darts
        summary = "Last visit was by " + self.match.players[player_index] + " with " + visit.to_string() + "\n"

        if self.match.winning_player_index is not -1:
            summary += self.match.players[self.match.winning_player_index] + " wins in " \
                       + str(self.match.winning_num_darts) + " darts\n"

        i = 0
        for player in self.match.players:
            summary = summary + player + ": " + str(self.scores[i]) + " Remaining"
            if self.scores[i] in CHECKOUTS.keys():
                summary += " (" + CHECKOUTS.get(self.scores[i]) + ")"
            if self.first9[i]:
                summary += "\n - [First 9 Avg: " + '{0:.2f}'.format(self.first9[i]) + "] "
            if self.averages[i]:
                summary += "\n - [3-dart Avg: " + '{0:.2f}'.format(self.averages[i] * 3) + "] "
            i = i + 1
            summary += "\n"
        return summary


class X01MatchBuilder:
    """
    This could be extended to include dynamic key-value pair parameters (see object_factory.py),
    or make it a singleton, etc.
    """

    def __init__(self):
        pass

    def __call__(self, starting_total=501):
        return X01Match(starting_total)
