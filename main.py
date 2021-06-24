"""
CSC111 Winter 2021 Project: Video Game Recommendation System

This Python module is the main module where the program is run.

Copyright and Usage Information
===============================
This file is provided solely for the personal and private use of the CSC111 course department
at the University of Toronto St. George campus. All forms of distribution of this code,
whether as given or with any changes, are strictly prohibited. For more information on
copyright for CSC111 project materials, please consult our Course Syllabus.

This file is Copyright (c) 2021 Yifan Li, Yixin Guo, Yige Xiong, Richard Soma.
"""
from data_computations import load_games
from recommendation_system import main_loop


def run() -> None:
    """Run the program"""
    games, tree, graph = load_games()
    main_loop((games, tree, graph))


if __name__ == '__main__':
    import doctest

    doctest.testmod(verbose=True)

    import python_ta
    import python_ta.contracts

    python_ta.contracts.DEBUG_CONTRACTS = False
    python_ta.contracts.check_all_contracts()
    python_ta.check_all(config={
        'extra-imports': ['python_ta.contracts', 'data_computations', 'recommendation_system'],
        'allowed-io': [],
        'max-line-length': 100,
        'disable': [],
    })
