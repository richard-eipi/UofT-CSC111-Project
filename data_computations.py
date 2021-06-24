"""
CSC111 Winter 2021 Project: Video Game Recommendation System

This Python module contains functions that extract data from the datasets required and functions
that do computations on data.

Copyright and Usage Information
===============================
This file is provided solely for the personal and private use of the CSC111 course department
at the University of Toronto St. George campus. All forms of distribution of this code,
whether as given or with any changes, are strictly prohibited. For more information on
copyright for CSC111 project materials, please consult our Course Syllabus.

This file is Copyright (c) 2021 Yifan Li, Yixin Guo, Yige Xiong, Richard Soma.
"""
import csv
import urllib.request
import json
import random
from weighted_decision import Game, DecisionTree, WeightedGraph


# Keyword sets in mature content description, used for similarity scores
VIOLENCE_KEYWORDS = {'violence', 'violent', 'gore', 'blood', 'bloody', 'war', 'kill', 'killed',
                     'killing', 'die', 'death', 'dead', 'murder', 'murders', 'shoot', 'shooting',
                     'shooter', 'guns', 'weapons', 'sword', 'suicide', 'fighting', 'aggressive',
                     'bomb', 'battle', 'attack', 'destruction', 'destroy', 'assault', 'damage'}
ADDICTION_KEYWORDS = {'drugs', 'drug', 'alcohol', 'beer', 'wine', 'drink', 'tobacco', 'gambling'}
HORROR_KEYWORDS = {'horror', 'scary', 'shock', 'shocking', 'jumpscare', 'scares'}
SEX_KEYWORDS = {'sex', 'sexual', 'sexually', 'sexy', 'nude', 'nudity', 'naked', 'underwear',
                'bananas', 'suggestive', 'bikini', 'swimsuit', 'bath', 'sperm', 'unbuttoned',
                'clothes', 'erotic', 'girls', 'boobs', 'condoms', 'topless', 'anime'}
GENERAL_KEYWORDS = {'general', 'cursing', 'language', 'profanity', 'swearing', 'ages', 'trauma',
                    'mature', 'adult', 'sensitive', 'disturbing', 'uncomfortable', 'depression'}


def load_games(filename: str = 'data/final_games.csv')\
        -> tuple[dict[str, Game], DecisionTree, WeightedGraph]:
    """Return a tuple of three objects:
        1. A dictionary of games. Each key is a game id; each item is a game object.
        2. A decision tree classifying games in terms of genre.
        3. A weighted graph linking similar games together.
    """
    games = {}
    tree = DecisionTree(set())
    graph = WeightedGraph()
    with open(filename, errors='ignore') as csv_file:
        reader = csv.reader(csv_file)
        next(reader, None)
        for row in reader:
            game = Game(row[0], row[1], row[2], set(row[3].split(',')), set(row[4].split(',')),
                        set(row[5].split(',')), row[6], set(row[7].split(',')), float(row[8]),
                        float(row[9]), [x == 'True' for x in row[10].split(',')], 0.0)
            games[game.id_num] = game
            tree.insert_game(game.genre_bools, game.id_num)
            graph.add_vertex(game.id_num)
            neighbours, sim_scores = row[11].split(';'), row[12].split(',')
            for i in range(len(neighbours)):
                if neighbours[i] in games:
                    graph.add_edge(game.id_num, neighbours[i], float(sim_scores[i]))

    return (games, tree, graph)


def pop_score_computation(games: dict[str, Game], game_lst: list[str]) -> None:
    """Update the recommendation scores of the games in game_set based on their popularity scores.

    Preconditions:
        - len(game_lst) > 0
    """
    ranked_games = sorted(game_lst, key=lambda game: games[game].popularity_score)
    for i in range(1, len(ranked_games) + 1):
        games[ranked_games[i - 1]].recommendation_score += i / len(ranked_games)


def graph_computation(games: dict[str, Game], graph: WeightedGraph, user_data: dict[str: dict],
                      game_set: set[str]) -> None:
    """Extract the games that the user plays on their steam account identified by their user_id,
    and use this information to add new games to game_set and update their recommendation
    scores.

    The recommendation score is based on how long the user played on each of the games
    in their steam library and the similarity score between the games on the graph.

    Note that the games that the user already has in her/his library should not be recommended.
    """
    # a dict that maps game id to how long the user played the game across all devices
    played_games = {}
    for game in user_data['response']['games']:
        id_num, play_time = str(game['appid']), int(game['playtime_forever'])
        if id_num in games:
            played_games[id_num] = play_time

    for game in played_games:
        if game in game_set:  # remove the game from game_set if it's already been played
            game_set.remove(game)

        neighbours = graph.get_neighbours(game)  # a dict that maps neighbors to sim scores
        for neighbour in neighbours:
            # making sure the neighbour is not already a game in the user's steam library
            # though it may be already in game_set!
            if neighbour not in played_games:
                score = neighbours[neighbour] + played_games[game] / 1000
                games[neighbour].recommendation_score += score
                game_set.add(neighbour)


def tree_computation(games: dict[str, Game], tree: DecisionTree, answers: list[bool],
                     indices: list[int], game_set: set[str]) -> None:
    """Add new games to game_set based on user answers and the decision tree and update
    their recommendation scores.

    This function guarantees that there will be at least 9 games in game_set.

    Indices are a list of indexes where the user selected 'I don't care'. The more we have to
    change the user's answers in order to get more games, the less the recommendation scores will
    be for those extra games added.
    """
    new_games = tree.find_games_from_answers(answers)
    for game in new_games:
        games[game].recommendation_score += 5
    game_set.update(new_games)

    iter_times = 0
    while len(game_set) < 9:
        if len(indices) > 0:
            index, score = indices.pop(), 5 / (iter_times + 1)
        else:
            index, score = random.randint(0, 8), 2.5 / (iter_times + 1)
        answers[index] = not answers[index]
        new_games = tree.find_games_from_answers(answers)
        for game in new_games:
            if game not in game_set:
                games[game].recommendation_score += score
        game_set.update(new_games)
        iter_times += 1


def read_json_data(user_id: str) -> dict[str: dict]:
    """Get steam library json data from web. (In case website fails, use local file)

    Return a dictionary like {'response': {'game_count': int, 'games': List(dict)}}
    """
    url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/" \
          "?key=F4D77259D3E7B5E62801D809111A12CC&steamid=" + user_id + "=json"
    response = urllib.request.urlopen(url)
    data = json.loads(response.read())

    return data


def read_csv(input_name: str = 'data/sample_original_games.csv',
             output_name: str = 'data/sample_final_games.csv') -> None:
    """Read the input csv and write a clean csv that stores the attributes of Game and the
    neighbours + sim scores of the graph. Remove games with missing data in url, name, all reviews,
    popular tags, game details, and genre.
    """
    games = {}
    graph = WeightedGraph()
    with open(input_name, errors='ignore') as csv_file:
        reader = csv.reader(csv_file)
        next(reader, None)
        for row in reader:
            if check_tidiness(row):
                game = init_game_obj(row)
                games[game.id_num] = game
                graph.add_vertex(game.id_num)
                for id_num in games:
                    if id_num != game.id_num:
                        weight = compute_similarity(game, games[id_num])
                        if weight > 2:
                            graph.add_edge(id_num, game.id_num, weight)

    write_csv(output_name, games, graph)


def check_tidiness(row: list) -> bool:
    """Check if a row of the original csv is 'tidy'.

    For a 'tidy' row, it must have a valid url, a game name, all reviews, popular tags,
    game details, and genre.
    """
    if len(row[0]) < 46:
        return False
    if row[2] == '' or row[2] == 'NaN':
        return False
    if row[5] == '' or row[5] == 'NaN' or '%' not in row[5]:
        return False
    if row[9] == '' or row[9] == 'NaN':
        return False
    if row[10] == '' or row[10] == 'NaN':
        return False
    if row[13] == '' or row[13] == 'NaN':
        return False
    return True


def write_csv(filename: str, games: dict[str, Game], graph: WeightedGraph) -> None:
    """Write a dataset storing Game attributes, neighbours & sim scores directly.
    """
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["url",
                         "id_num",
                         "name",
                         "popular_tags",
                         "game_details",
                         "genre",
                         "game_description",
                         "mature_content",
                         "price",
                         "popularity_score",
                         "genre_bools",
                         "neighbours",
                         "similarity_scores"])
        for id_num in games:
            game = games[id_num]

            neighbours, similarity_scores = [], []
            d = graph.get_neighbours(id_num)
            for neighbour in d:
                neighbours.append(neighbour)
                similarity_scores.append(round(d[neighbour], 4))

            writer.writerow([game.url,
                             game.id_num,
                             game.name,
                             str(game.popular_tags)[1:-1].replace(' ', '').replace('\'', ''),
                             str(game.game_details)[1:-1].replace(' ', '').replace('\'', ''),
                             str(game.genre)[1:-1].replace(' ', '').replace('\'', ''),
                             game.game_description,
                             str(list(game.mature_content))[1:-1].replace(' ', '').replace('\'',
                                                                                           ''),
                             game.price,
                             game.popularity_score,
                             str(game.genre_bools)[1:-1].replace(' ', ''),
                             str(neighbours)[1:-1].replace(', ', ';').replace('\'', ''),
                             str(similarity_scores)[1:-1].replace(' ', '')])


def init_game_obj(row: list) -> Game:
    """Initialize a game object.
    """
    url = row[0]
    id_num = get_id_num(url)
    name = row[2]
    popular_tags = set(row[9].split(','))
    game_details = set(row[10].split(','))
    genre = set(row[13].split(','))
    game_description = row[14]

    if row[15] not in {'NaN', ''}:
        mature_content = get_mature_content(row[15])
    else:
        mature_content = set()

    price = 0.0
    if '$' in row[18]:
        price = float(row[18][1:])
    elif '$' in row[19]:
        price = float(row[19][1:])

    all_reviews = get_all_reviews(row[5])
    popularity_score = all_reviews[1] * all_reviews[0] / 100
    genre_bools = get_genre_bools(game_details, genre)

    game = Game(url, id_num, name, popular_tags, game_details, genre, game_description,
                mature_content, price, popularity_score, genre_bools, 0.0)
    return game


def get_id_num(url: str) -> str:
    """Find the id number of the game from the given url.

    Preconditions:
        - the url must contain the id.
    """
    id_num, digit = '', False
    for i in range(0, len(url)):
        if url[i].isdigit():
            digit = True
            id_num += url[i]
        elif url[i] == '/' and digit is True:
            break

    return id_num


def get_all_reviews(info: str) -> tuple[int, int]:
    """Get review information from the given string.

    Return the percentage of positive reviews and the total number of reviews.

    Preconditions:
        - '%' in info
    """
    index = info.index('%')
    percentage = int(info[index - 2:index])
    total_players = 0
    for i in range(index + 9, index + 16):
        if info[i] == ' ':
            break
        elif info[i].isdigit():
            total_players *= 10
            total_players += int(info[i])

    return (percentage, total_players)


def get_mature_content(description: str) -> set[str]:
    """Return a set of keywords from the given description of mature content.

    Preconditions:
        - description not in {'NaN', ''}:
    """
    set_so_far = set()
    lst = description.split()
    for i in range(10, len(lst)):
        word = lst[i].lower().strip('-,;.!\"\'')
        if word in VIOLENCE_KEYWORDS:
            set_so_far.add('violence')
        elif word in ADDICTION_KEYWORDS:
            set_so_far.add('addiction')
        elif word in HORROR_KEYWORDS:
            set_so_far.add('horror')
        elif word in SEX_KEYWORDS:
            set_so_far.add('sex')
        elif word in GENERAL_KEYWORDS:
            set_so_far.add('general')

    if set_so_far == set():
        set_so_far.add('other')
    return set_so_far


def get_genre_bools(game_details: set[str], genre: set[str]) -> list[bool]:
    """Return a list of booleans corresponding to the answers to 7 genre related questions:

    1. action
    2. adventure
    3. strategy
    4. rpg
    5. simulation
    6. casual
    7. indie
    8. sports
    9. single-player
    """
    lst_so_far = [False for _ in range(9)]
    for word in genre:
        if word == 'Action':
            lst_so_far[0] = True
        elif word == 'Adventure':
            lst_so_far[1] = True
        elif word == 'Strategy':
            lst_so_far[2] = True
        elif word == 'RPG':
            lst_so_far[3] = True
        elif word == 'Simulation':
            lst_so_far[4] = True
        elif word == 'Casual':
            lst_so_far[5] = True
        elif word == 'Indie':
            lst_so_far[6] = True
        elif word in {'Racing', 'Sports'}:
            lst_so_far[7] = True

    if 'Single-player' in game_details:
        lst_so_far[8] = True

    return lst_so_far


def compute_similarity(game1: Game, game2: Game) -> float:
    """Compute the similarity score between the two given games.

    The similarity score is based on popular_tags, game_details, genre, and mature_content.

    Preconditions:
        - game1 is not game2
    """
    if game1.popular_tags != set() and game2.popular_tags != set():
        w1 = len(game1.popular_tags.intersection(game2.popular_tags)) / len(
            game1.popular_tags.union(game2.popular_tags))
    else:
        w1 = 0.0

    if game1.game_details != set() and game2.game_details != set():
        w2 = len(game1.game_details.intersection(game2.game_details)) / len(
            game1.game_details.union(game2.game_details))
    else:
        w2 = 0.0

    if game1.genre != set() and game2.genre != set():
        w3 = len(game1.genre.intersection(game2.genre)) / len(game1.genre.union(game2.genre))
    else:
        w3 = 0.0

    if game1.mature_content != set() and game2.mature_content != set():
        w4 = max(0.5, len(game1.mature_content.intersection(game2.mature_content)))
    else:
        w4 = 0.0

    return w1 + w2 + w3 + w4


if __name__ == '__main__':
    import doctest

    doctest.testmod(verbose=True)

    import python_ta
    import python_ta.contracts

    python_ta.contracts.DEBUG_CONTRACTS = False
    python_ta.contracts.check_all_contracts()
    python_ta.check_all(config={
        'extra-imports': ['python_ta.contracts', 'csv', 'urllib.request', 'json', 'random',
                          'weighted_decision'],
        'allowed-io': ['load_games', 'filter_original_csv', 'read_filtered_csv', 'write_csv'],
        'max-line-length': 100,
        'disable': ['R1702']
    })
