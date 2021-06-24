"""
CSC111 Winter 2021 Project: Video Game Recommendation System

This Python module contains the data types used to represent our problem domain.

Copyright and Usage Information
===============================
This file is provided solely for the personal and private use of the CSC111 course department
at the University of Toronto St. George campus. All forms of distribution of this code,
whether as given or with any changes, are strictly prohibited. For more information on
copyright for CSC111 project materials, please consult our Course Syllabus.

This file is Copyright (c) 2021 Yifan Li, Yixin Guo, Yige Xiong, Richard Soma.
"""
from __future__ import annotations
from typing import Optional, Union
from dataclasses import dataclass


@dataclass
class Game:
    """
    Game class
    Instance Attributes:
        - url: url of store page, https://store.steampowered.com/app/477160/Human_Fall_Flat/
        - id_num: id of the game, '477160'
        - name: name of the game
        - popular_tags: {'Funny','Multiplayer','Co-op','Puzzle'}
        - game_details: {'Multi-player','Online Multi-Player','Stats'}
        - genre: genre of the game, {'Adventure','Indie'}
        - game_description: long description of the game (for results)
        - mature_content: {'violence', 'addiction'}
        - price: price of the game; if free, 0.0

        - popularity_score: number of reviewers * proportion of positive reviews
        - genre_bools: a list of booleans indicating genre; used for decision tree
        - recommendation_score: a float representing how much we recommend this game
    """
    url: str
    id_num: str
    name: str
    popular_tags: set[str]
    game_details: set[str]
    genre: set[str]
    game_description: str
    mature_content: set[str]
    price: float

    popularity_score: float
    genre_bools: list[bool]
    recommendation_score: float


class DecisionTree:
    """A decision tree used to classify games in terms of genre.

    Representation Invariants:
        - len(self._subtrees) <= 2
    """
    # Private Instance Attributes:
    #   - _root: the item stored at this tree's root
    #   - _subtrees: the list of subtrees of this tree
    _root: Union[bool, set[str]]
    _subtrees: list[DecisionTree]

    def __init__(self, root: Union[bool, set[str]]) -> None:
        """Initialize a new DecisionTree."""
        self._root = root
        self._subtrees = []

    def insert_game(self, items: list[bool], final: str, index: int = 0) -> None:
        """Insert all items from <items> into this tree after and including <index>,
         without creating duplicates at the same depth.

        The final item will be added to a set of game ids if the entire path already exists.
        Otherwise, create a new set and add <final> to the set.

        Preconditions:
            - 0 <= index <= len(items) == 9
        """
        if index == len(items):
            if self._subtrees == []:
                self._subtrees.append(DecisionTree({final}))
            else:
                self._subtrees[0]._root.add(final)
        else:
            item = items[index]

            next_tree = None
            for subtree in self._subtrees:
                if subtree._root == item:
                    next_tree = subtree
                    break

            if next_tree is None:
                next_tree = DecisionTree(item)
                self._subtrees.append(next_tree)

            next_tree.insert_game(items, final, index + 1)

    def find_games_from_answers(self, answers: list[bool]) -> set[str]:
        """Return a list of game ids based on <answers>."""
        curr = self
        for answer in answers:
            curr = curr._find_subtree(answer)
            if curr == set():
                return curr

        return curr._find_subtree()

    def _find_subtree(self, answer: Optional[bool] = None) -> Union[DecisionTree, set[str]]:
        """Return the subtree whose root is <answer>.

        If <answer> is None, then return the root of the subtree.

        Preconditions:
            - any(subtree._root is answer for subtree in self._subtrees)
            - If answer is None, then the only subtree is a set of game ids
        """
        if answer is None:
            return self._subtrees[0]._root
        else:
            for subtree in self._subtrees:
                if subtree._root is answer:
                    return subtree

            return set()


class _Vertex:
    """A weighted vertex in a weighted game graph, used to represent a game.

    Instance Attributes:
        - game: data stored in this vertex; represents a game id
        - neighbours: a dictionary mapping each adjacent vertex to an edge weight

    Representation Invariants:
        - self not in self.neighbours
        - all(self in u.neighbours for u in self.neighbours)
        - all(self.neighbours[u] >= 2 for u in self.neighbours)
    """
    game: str
    neighbours: dict[_Vertex, float]

    def __init__(self, game: str) -> None:
        """Initialize a new vertex with the given game id.
        """
        self.game = game
        self.neighbours = {}


class WeightedGraph:
    """A weighted graph used to represent a network of games.
    """
    # Private Instance Attributes:
    #     - _vertices:
    #         A collection of the vertices contained in this graph.
    #         Maps game id to _Vertex object.
    _vertices: dict[str, _Vertex]

    def __init__(self) -> None:
        """Initialize an empty graph (no vertices or edges).
        """
        self._vertices = {}

    def add_vertex(self, game: str) -> None:
        """Add a vertex with the given game id to this graph.
        """
        self._vertices[game] = _Vertex(game)

    def add_edge(self, game1: str, game2: str, weight: float) -> None:
        """Add an edge with the given weight between the two games.

        Preconditions:
            - game1 in self._Vertices and game2 in self._Vertices
            - weight >= 2
        """
        v1, v2 = self._vertices[game1], self._vertices[game2]
        v1.neighbours[v2], v2.neighbours[v1] = weight, weight

    def get_neighbours(self, game: str) -> dict[str, float]:
        """Return a dictionary mapping neighbours to similarity scores.

        Preconditions:
            - game in self._Vertices
        """
        v1 = self._vertices[game]
        return {v2.game: v1.neighbours[v2] for v2 in v1.neighbours}


if __name__ == '__main__':
    import doctest

    doctest.testmod(verbose=True)

    import python_ta
    import python_ta.contracts

    python_ta.contracts.DEBUG_CONTRACTS = False
    python_ta.contracts.check_all_contracts()
    python_ta.check_all(config={
        'extra-imports': ['python_ta.contracts', 'typing', 'dataclasses'],
        'allowed-io': [],
        'max-line-length': 100,
        'disable': ['R0902', 'E1136']
    })
