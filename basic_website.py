# https://github.com/ddm7018/Elo
from flask import Flask, render_template, request, redirect, url_for
from elosports.elo import Elo
from functions import add_1_ID
import datetime

class Ladder:
    def __init__(self, k=20, g=1):
        self.eloLeague = Elo(k, g)
        self.players = []
        self.gamesPlayed = {}  # Store details of all games played
        self.game_id = "0000"
    
    def add_player(self, player):
        self.players.append(player)
        player.add_to_elo_ladder(self)

    def play_game(self, winner, loser, white=None, time_control=None,):
        if winner == loser:
            print("Same person picked for winner and loser - restarting")
            return

        # Calculate old ratings
        winner_old_rating = self.eloLeague.ratingDict.get(winner, 1500)
        loser_old_rating = self.eloLeague.ratingDict.get(loser, 1500)

        # Update Elo ratings
        self.eloLeague.gameOver(winner=winner, loser=loser, winnerHome=None)
        d = datetime.date.today().strftime("%d/%m/%Y")
        # Save game details in the ladder
        self.gamesPlayed[self.game_id] = {
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

        # Update players' game IDs
        for player in self.players:
            if player.name in [winner, loser]:
                player.gamesPlayed_IDS.append(self.game_id)

        self.game_id = add_1_ID(self.game_id)
        
        winner_player = next((player for player in self.players if player.name == winner), None)
        loser_player = next((player for player in self.players if player.name == loser), None)
        if winner_player:
            winner_player.rating = int(round(self.eloLeague.ratingDict[winner]))
        if loser_player:
            loser_player.rating = int(round(self.eloLeague.ratingDict[loser]))        
        

    def get_ladder(self):
        sortedRating = sorted(self.eloLeague.ratingDict.items(), key=lambda x: x[1], reverse=True)
        return [(name, int(round(rating))) for name, rating in sortedRating]

class Player:
    def __init__(self, name, rating=1500):
        self.name = name
        self.rating = rating
        self.gamesPlayed_IDS = []  
        rating_rounded = int(round(rating))

    def add_to_elo_ladder(self, ladder):
        ladder.eloLeague.addPlayer(self.name, rating=self.rating)


app = Flask(__name__)

# Initialize the ladder instance
elo_ladder = Ladder()
x1 = Player("Jakob")
x2 = Player("Thomas")
x3 = Player("Bjarne")
elo_ladder.add_player(x1)
elo_ladder.add_player(x2)
elo_ladder.add_player(x3)
elo_ladder.play_game("Jakob", "Thomas", "Jakob", "5+5")
print(elo_ladder.gamesPlayed[elo_ladder.players[0].gamesPlayed_IDS[0]])
print(elo_ladder.get_ladder())
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

if __name__ == '__main__':
    app.run(debug=True)