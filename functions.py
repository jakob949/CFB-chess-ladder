from fuzzywuzzy import fuzz
import datetime

# delete_player("Bjarne", elo_ladder)

def add_1_ID(s_id):
    return str(int(s_id) + 1).zfill(len(s_id))

def delete_player(player_to_remove, ladder):
    player_to_remove = next((player for player in ladder.players if player.name == player_to_remove), None)
    if player_to_remove is not None:
        ladder.remove_player(player_to_remove)

def is_correct_answer(user_input, correct_answer="None", variations="None", threshold=70):
    if correct_answer == "None" or variations == "None":
        return False
    user_input = user_input.lower().strip()
    correct_answer = correct_answer.lower().strip()

    for key in variations:
        temp_fuzz = fuzz.ratio(user_input, variations[key])
        if temp_fuzz >= threshold:
            user_input = variations[key]  
            print("fuzz score match, for the variation: ", key, temp_fuzz, user_input, variations[key])
            break
    print("\n", user_input, correct_answer)
    score = fuzz.ratio(user_input, correct_answer)

    return score >= threshold

# all credits for the Elo class go to ddm7018
# https://github.com/ddm7018/Elo
class Ladder:
    def __init__(self, k=20, g=1):
        self.eloLeague = Elo(k, g)
        self.players = []
        self.gamesPlayed = {}
        self.game_id = "0000"

    def add_player(self, player):
        self.players.append(player)
        player.add_to_elo_ladder(self)

    def play_game(self, winner, loser, white=None, time_control=None):
        if winner == loser:
            print("Same person picked for winner and loser - restarting")
            return

        # Ensure both winner and loser are part of the ladder
        if winner not in [player.name for player in self.players] or loser not in [player.name for player in self.players]:
            print("One or both players not found in the ladder")
            return

        # Calculate old ratings
        winner_old_rating = self.eloLeague.ratingDict.get(winner, 1500)
        loser_old_rating = self.eloLeague.ratingDict.get(loser, 1500)

        # Update Elo ratings
        self.eloLeague.gameOver(winner=winner, loser=loser, winnerHome=None)
        d = datetime.datetime.today().strftime("%d/%m/%Y")

        # Save game details in the ladder
        self.game_id = str(int(self.game_id) + 1).zfill(4)
        game_details = {
            'game_id': self.game_id,
            'Date': str(d),
            'winner': winner,
            'loser': loser,
            'white': white,
            'winner_old_elo': winner_old_rating,
            'winner_new_elo': self.eloLeague.ratingDict[winner],
            'loser_old_elo': loser_old_rating,
            'loser_new_elo': self.eloLeague.ratingDict[loser],
            'time_control': time_control,
        }
        self.gamesPlayed[self.game_id] = game_details

        # Update player ratings and game history
        for player in self.players:
            if player.name == winner or player.name == loser:
                player.rating = self.eloLeague.ratingDict[player.name]
                player.gamesPlayed_IDS.append(self.game_id)
    
    def remove_game(self, game_id):
        # Check if the game exists
        if game_id not in self.gamesPlayed:
            print("Game ID not found.")
            return

        game_details = self.gamesPlayed[game_id]

        # Restore player ratings
        winner, loser = game_details['winner'], game_details['loser']
        self.eloLeague.ratingDict[winner] = game_details['winner_old_elo']
        self.eloLeague.ratingDict[loser] = game_details['loser_old_elo']

        # Update players' games played list
        for player in self.players:
            if game_id in player.gamesPlayed_IDS:
                player.gamesPlayed_IDS.remove(game_id)
                player.rating = self.eloLeague.ratingDict[player.name]

        # Remove the game from the ladder
        del self.gamesPlayed[game_id]
    
    def get_ladder(self):
        sortedRating = sorted(self.eloLeague.ratingDict.items(), key=lambda x: x[1], reverse=True)
        return [(name, int(round(rating))) for name, rating in sortedRating]

    def remove_player(self, player):
        player.remove_from_elo_ladder(self)
        self.players.remove(player)

class Player:
    def __init__(self, name, rating=1500):
        self.name = name
        self.rating = rating
        self.gamesPlayed_IDS = []

    def add_to_elo_ladder(self, ladder):
        ladder.eloLeague.addPlayer(self.name, self.rating)

    def remove_from_elo_ladder(self, ladder):
        ladder.eloLeague.removePlayer(self.name)

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