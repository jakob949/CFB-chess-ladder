def add_1_ID(s_id):
    return str(int(s_id) + 1).zfill(len(s_id))

def delete_player(player_to_remove, ladder):
    player_to_remove = next((player for player in ladder.players if player.name == player_to_remove), None)
    if player_to_remove is not None:
        ladder.remove_player(player_to_remove)

class Elo:
    def __init__(self, k, g=1, homefield=100):
        self.ratingDict = {}
        self.k = k
        self.g = g
        self.homefield = homefield

    def addPlayer(self, name, rating=1500):
        self.ratingDict[name] = rating

    def gameOver(self, winner, loser, winnerHome=None):
        if winnerHome is None:
            winnerHome = False  # Assuming no home advantage if not specified
        if winnerHome:
            result = self.expectResult(self.ratingDict[winner] + self.homefield, self.ratingDict[loser])
        else:
            result = self.expectResult(self.ratingDict[winner], self.ratingDict[loser] + self.homefield)

        self.ratingDict[winner] = self.ratingDict[winner] + (self.k * self.g) * (1 - result)
        self.ratingDict[loser] = self.ratingDict[loser] + (self.k * self.g) * (0 - (1 - result))

    def expectResult(self, p1, p2):
        exp = (p2 - p1) / 400.0
        return 1 / ((10.0 ** (exp)) + 1)

    def removePlayer(self, name):
        if name in self.ratingDict:
            del self.ratingDict[name]