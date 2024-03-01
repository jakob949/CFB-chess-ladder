def add_1_ID(s_id):
    return str(int(s_id) + 1).zfill(len(s_id))

def delete_player(player_to_remove, ladder):
    player_to_remove = next((player for player in ladder.players if player.name == player_to_remove), None)
    if player_to_remove is not None:
        ladder.remove_player(player_to_remove)
