import os 
os.chdir(os.path.dirname(__file__))
from flask import Flask, render_template, request, redirect, url_for
from functions import add_1_ID, delete_player, Elo
import datetime
import pickle
import datetime
import argparse 

args = argparse.ArgumentParser()
args.add_argument("-remove", "--remove", help="Delete ladder // create new ladder", type=bool, default=False)
args.add_argument("-run", "--run", help="Run the website - in development server env.", type=bool, default=True)
args.add_argument("-rg", "--removegame", help="Remove a game by gameID", type=str, default = "none")
args = args.parse_args()


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

if args.remove:
    if os.path.exists("saved_ladders/elo_ladder.p"):
        os.remove("saved_ladders/elo_ladder.p")
    elo_ladder = Ladder()
else:
    try:
        elo_ladder = pickle.load(open("saved_ladders/elo_ladder.p", "rb"))
    except:
        elo_ladder = Ladder()
# delete_player("Bjarne", elo_ladder)



app = Flask(__name__)
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if 'add_player' in request.form:
            name = request.form.get('name')
            rating = int(request.form.get('rating', 1500))

            new_player = Player(name, rating)
            elo_ladder.add_player(new_player)
        elif 'play_game' in request.form:
            winner = request.form.get('winner')
            loser = request.form.get('loser')
            white = request.form.get('white') if 'white' in request.form else None
            time_control = request.form.get('time_control')
            date = request.form.get('Date')
            print(date)
            elo_ladder.play_game(winner=winner, loser=loser, white=white, time_control=time_control, date=date)
        return redirect(url_for('home'))
    else:
        return render_template('index.html', sortedRatingDict=elo_ladder.get_ladder(), players=elo_ladder.players)

@app.route('/add_player', methods=['GET', 'POST'])
def add_player():
    if request.method == 'POST':
        name = request.form['name']
        rating = request.form.get('rating', 1500)
        new_player = Player(name, int(rating))
        elo_ladder.add_player(new_player)
        pickle.dump(elo_ladder, open("saved_ladders/elo_ladder.p", "wb"))
        return redirect(url_for('home'))
    else:
        return render_template('add_player.html')

@app.route('/play_game', methods=['GET', 'POST'])
def play_game():
    if request.method == 'POST':
        winner = request.form['winner']
        loser = request.form['loser']
        white = request.form.get('white')
        time_control = request.form.get('time_control')
        elo_ladder.play_game(winner, loser, white, time_control)
        pickle.dump(elo_ladder, open("saved_ladders/elo_ladder.p", "wb"))
        return redirect(url_for('home'))
    else:
        players = [player.name for player in elo_ladder.players]
        return render_template('play_game.html', players=players)
    
@app.route('/player/<name>')
def player_details(name):
    # Find the player in the ladder
    player = next((p for p in elo_ladder.players if p.name == name), None)
    if player is not None:
        # Retrieve games played by this player
        games = [elo_ladder.gamesPlayed[game_id] for game_id in player.gamesPlayed_IDS]
        # Pass player and games to the template
        return render_template('player_details.html', player=player, games=games)
    else:
        return f"No player found with the name {name}", 404

if args.removegame is not "none":
    game_id_to_remove = args.removegame
    elo_ladder.remove_game(game_id_to_remove)
    # Save the updated ladder state
    pickle.dump(elo_ladder, open("saved_ladders/elo_ladder.p", "wb"))

if __name__ == '__main__' and args.run:
    app.run(debug=True)
