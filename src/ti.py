"""
ti.py
=====
"""

from random import shuffle, choice

games = {}
rooms = {}

# Game states
MAX_PLAYERS = 10
ERROR = -1
WAITING, PLAYING, VOTING, OVER = range(4)
CREATE, JOIN = range(2)
alphabet = [chr(x+97) for x in range(26)]

def create_or_join(session, username, code):
    # Join
    if code in games:
        if games[code]["state"] != WAITING:
            return ERROR
        if len(games[code]["players"]) >= MAX_PLAYERS:
            return ERROR
        if username not in games[code]["players"]:
            games[code]["players"].append(username)
        # TODO join game
        return JOIN
    # Create
    else:
        games[code] = {
            "leader": username,
            "players": [username],
            "imposter": [],
            "state": WAITING,
            "settings": {
                "words": 6,
                "mixup": 2
            },
            "phrases": {},
            "mixups": {},
            "votes": {},
            "winners": []
        }
        return CREATE

def user_in_game(username, code):
    if code in games:
        return (username in games[code]["players"])
    return False

def is_error(return_val):
    if isinstance(return_val, int):
        return return_val == ERROR
    return True

def get_game(room_code):
    return games.get(room_code, {})

def add_context(session, game_info):
    game_info["username"] = session["username"]
    game_info["room_code"] = session["room_code"]
    return game_info

def game_context(session, room_code):
    game_data = get_game(room_code)
    return add_context(session, game_data)

def is_submitting_words(room_code, username):
    if username not in games[room_code]["phrases"]:
        return True
    for i in games[room_code]["players"]:
        player = games[room_code]["players"][i]
        if len(games[room_code]["phrases"].get(player, [])) == i:
            return True
    return False

def submit_words(room_code, username, words, user):
    if user not in games[room_code]["phrases"]:
        games[room_code]["phrases"][user] = [words]
    else:
        games[room_code]["phrases"][user].append(words)
    return True
    """
    if username not in games[room_code]["phrases"]:
        games[room_code]["phrases"][username] = [words]
        return True
    for i in range(games[room_code]["players"]):
        player = games[room_code]["players"][i]
        if len(games[room_code]["phrases"].get(player, [])) == i:
            games[room_code]["phrases"][username].append(words)
            return True
    """
    return False

def mixup_words(user, room_code):
    sentence = games[room_code]["phrases"][user][-1].split(" ")
    shuffle(sentence)
    for i, word in enumerate(sentence):
        for j in range(games[room_code]["settings"]["mixup"]):
            word = list(word)
            word[choice(range(len(word)))] = choice(alphabet)
            word = "".join(word)
            sentence[i] = word
    games[room_code]["mixups"][user] = " ".join(sentence)
        
def calculate_phase(room_code):
    if games[room_code]["state"] == PLAYING:
        for user in games[room_code]["phrases"]:
            if len(games[room_code]["phrases"][user]) < len(games[room_code]["players"]):
                return False
        games[room_code]["state"] = VOTING
        return True
    elif games[room_code]["state"] == VOTING:
        if len(games[room_code]["votes"]) == len(games[room_code]["players"]):
            games[room_code]["state"] = OVER
            determine_winners(room_code)
            return True
        return False
    return False

def determine_winners(room_code):
    votes = {}
    for user, vote in games[room_code]["votes"].items():
        votes[vote] = votes.get(vote, 0) + 1
    max_count = max(votes.keys())
    killed = [vote for vote, count in votes.items() if count == max_count]
    if games[room_code]["imposter"] in killed:
        games[room_code]["winners"] = [player for player in games[room_code]["players"] if player not in killed]
    else:
        games[room_code]["winners"] = [games[room_code]["imposter"]]
    
def determine_imposter(room_code):
    if len(games[room_code]["players"]) >= 1:
        games[room_code]["imposter"] = choice(games[room_code]["players"])
    return True
