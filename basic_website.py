import os 
os.chdir(os.path.dirname(__file__))
from flask import Flask, render_template, request, redirect, url_for
from functions import add_1_ID, delete_player, Elo, is_correct_answer, Ladder, Player
import datetime
import pickle
import argparse 

args = argparse.ArgumentParser()
args.add_argument("-re", "--remove", help="Delete ladder // create new ladder", type=bool, default=False)
args.add_argument("-r", "--run", help="Run the website - in development server env.", type=bool, default=True)
args.add_argument("-rg", "--removegame", help="Remove a game by gameID", type=str, default = "none")
args = args.parse_args()

if args.remove:
    if os.path.exists("saved_ladders/elo_ladder.p"):
        os.remove("saved_ladders/elo_ladder.p")
    elo_ladder = Ladder()
else:
    try:
        elo_ladder = pickle.load(open("saved_ladders/elo_ladder.p", "rb"))
    except:
        elo_ladder = Ladder()

# loading the variantions from the pickle file
try:
    with open("variations.pkl", "rb") as f:
        variations_correct = pickle.load(f)
    correct_answer = variations_correct[0]
    variantions = variations_correct[1]
except:
    print("No variations file found => The purpose of this is to ask for a password when using the website. "
            "If you don't want to use this feature, you can ignore this message.")
    variations_correct = "None"

app = Flask(__name__)
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Handle form submissions such as adding a player or recording a game
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
            draw = 'draw' in request.form  # Check if the draw option was selected
            elo_ladder.play_game(winner=winner, loser=loser, white=white, time_control=time_control, date=date, draw=draw)
        return redirect(url_for('home'))
    else:
        # Prepare last 10 games
        last_10_games = sorted(elo_ladder.gamesPlayed.items(), key=lambda x: x[0], reverse=True)[:len(elo_ladder.players)]
        # Convert tuples back to dictionary for easier template processing
        last_10_games_dict = {game_id: details for game_id, details in last_10_games}
        # Render the template, passing both the sorted rating dictionary and the last 10 games
        return render_template('index.html', sortedRatingDict=elo_ladder.get_ladder(), players=elo_ladder.players, last_10_games=last_10_games_dict)

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
    # Assuming 'elo_ladder', 'variantions', and 'correct_answer' are defined correctly elsewhere

    if request.method == 'POST':
        if is_correct_answer(user_input=request.form.get('password'), variations=variantions, correct_answer=correct_answer, threshold=50):
            winner = request.form['winner']
            loser = request.form['loser']
            white = request.form.get('white', '')
            time_control = request.form.get('time_control', '')
            draw = 'draw' in request.form  # Check if the draw option was selected
            # Assuming 'elo_ladder' is a previously defined object with a play_game method
            elo_ladder.play_game(winner, loser, white, time_control, draw=draw)
            pickle.dump(elo_ladder, open("saved_ladders/elo_ladder.p", "wb"))
            return redirect(url_for('home'))
        else:
            players = [player.name for player in elo_ladder.players]
            error_message = "The password is incorrect. Hint: The guy who sends emails out."
            return render_template('play_game.html', players=players, error_message=error_message)
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
