"""
CSC111 Winter 2021 Project: Video Game Recommendation System

This Python module contains data types and functions for an interactive system on Pygame.

Copyright and Usage Information
===============================
This file is provided solely for the personal and private use of the CSC111 course department
at the University of Toronto St. George campus. All forms of distribution of this code,
whether as given or with any changes, are strictly prohibited. For more information on
copyright for CSC111 project materials, please consult our Course Syllabus.

This file is Copyright (c) 2021 Yifan Li, Yixin Guo, Yige Xiong, Richard Soma.
"""
from __future__ import annotations
from typing import Optional
import random
import urllib.error
import webbrowser
import pygame
from pygame.colordict import THECOLORS
from data_computations import pop_score_computation, graph_computation, tree_computation, \
    read_json_data
from weighted_decision import Game, DecisionTree, WeightedGraph

SCREEN_SIZE = (800, 800)
BACKGROUND_TEXT_SIZE = 45
BACKGROUND_TEXT_POS = (400, 100)

BUTTON_POS = (750, 750)
BUTTON_SIZE = (50, 30)
SMALL_BUTTON_SIZE = (20, 20)
BUTTON_TEXT_SIZE = 20
NUM_BOX_SIZE = (30, 30)
COLOURS = {'navy': (3, 43, 67), 'light_blue': (184, 208, 232), 'green': (157, 196, 181),
           'yellow': (237, 174, 73), 'url_blue': (26, 13, 170)}
STANDARD_BUTTON_COLORS = (COLOURS['light_blue'], COLOURS['yellow'])

TABLE_SIZE = (703, 509)
TABLE_TEXT_SIZE = 15
TABLE_ORIGIN = (50, 200)
COLUMN_WIDTH = 175
ROW_LENGTH = 50
BOUNDARIES_WIDTH = 1

RESTART_BUTTON_SIZE = (70, 30)
DESC_SIZE = (750, 580)
DESC_ORIGIN = (25, 130)
WARNIING_POS = (20, 750)
URL_BUTTON_SIZE = (680, 15)
URL_POS = (360, 750)

FONT_HEADER = "data/game_font.TTF"
FONT_BODY = "data/body_font.TTF"


def main_loop(system_objects: tuple[dict[str, Game], DecisionTree, WeightedGraph]) -> None:
    """The main loop of Pygame.
    """
    game_set = set()  # The set of games to recommend

    screen = initialize_screen()
    all_groups = initialize_groups()
    initialize_sprites(all_groups)
    background = initialize_background()
    screen.blit(background, (0, 0))

    clicked_sprite, curr_num_box = None, None
    group, running = 'main', True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check what is being clicked (before the user releases the mouse!)
                for sprite in all_groups[group]:
                    if sprite.rect.collidepoint(pygame.mouse.get_pos()):  # check if touching mouse
                        clicked_sprite = sprite
            elif event.type == pygame.MOUSEBUTTONUP and event.dict['button'] == 1 \
                    and clicked_sprite is not None and isinstance(clicked_sprite, Button) \
                    and clicked_sprite.rect.collidepoint(pygame.mouse.get_pos()):
                # Call sprite.clicked() after the user releases the left button of the mouse
                output = mouse_click(clicked_sprite, system_objects, game_set)
                if output[0] is not None:
                    group, background, curr_num_box = output
                    screen.blit(background, (0, 0))
                clicked_sprite = None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif group == 'graph':
                    curr_num_box = keyboard_entry(event, curr_num_box)

        all_groups[group].clear(screen, background)
        all_groups[group].update()
        all_groups[group].draw(screen)
        pygame.display.update()

    pygame.display.quit()
    pygame.quit()


class Button(pygame.sprite.Sprite):
    """An abstract class representing a button in Pygame.

    Instance Attributes:
        - color1: default color of the button
        - color2: color to change to when mouse hovers on top
        - image: this button's corresponding pygame surface
        - rect: the rectangle of this button's image (surface), stored as pygame.Rect
        - text: the text on the button
    """
    color1: tuple
    color2: tuple
    image: pygame.Surface
    rect: pygame.Rect
    text: str

    def __init__(self, colors: tuple[tuple, tuple], center: tuple[int, int], button_text: str,
                 size: tuple[int, int] = BUTTON_SIZE) -> None:
        pygame.sprite.Sprite.__init__(self)
        self.color1 = colors[0]
        self.color2 = colors[1]
        self.image = pygame.Surface(size)
        self.image.fill(colors[0])
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.text = button_text
        center_text(self.image, button_text, BUTTON_TEXT_SIZE, THECOLORS['black'])

    def update(self) -> None:
        """Update the color of this button when mouse is hovering/not hovering on top.
        """
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            self.image.fill(self.color2)
            center_text(self.image, self.text, BUTTON_TEXT_SIZE + 2, THECOLORS['black'])
        else:
            self.image.fill(self.color1)
            center_text(self.image, self.text, BUTTON_TEXT_SIZE, THECOLORS['black'])

    def clicked(self) -> Optional[tuple[str, pygame.Surface]]:
        """Do something when this button is clicked (change background...).
        """
        raise NotImplementedError


class StartButton(Button):
    """A button that starts the system.
    """

    def clicked(self) -> tuple[str, pygame.Surface]:
        """Initialize the second page (Q & A with decision tree).

        Draw a big table of 9 rows (each representing a question) and 4 columns
        (first column is questions, the rest are 'Yes', 'Don't care', 'No thanks').
        """
        new_background = pygame.Surface(SCREEN_SIZE)
        new_background.fill(COLOURS['navy'])
        my_text = text('Please check the boxes to indicate your preferences of genre',
                       BACKGROUND_TEXT_SIZE - 15, COLOURS['light_blue'], FONT_BODY)
        my_text2 = text("For more accurate recommendations, try avoid selecting 'I don't care",
                        BACKGROUND_TEXT_SIZE - 20, COLOURS['light_blue'], FONT_BODY)
        text_rect = my_text.get_rect(center=BACKGROUND_TEXT_POS)
        text2_rect = my_text.get_rect(center=(460, 150))

        new_background.blit(my_text, text_rect)
        new_background.blit(my_text2, text2_rect)

        table_section = pygame.Surface(TABLE_SIZE)
        bol_lst = ['', 'YES', 'DON\'T CARE', 'NO']
        genre_lst = ['ACTION', 'ADVENTURE', 'STRATEGY', 'RPG', 'SIMULATION', 'CASUAL', 'INDIE',
                     'SPORTS', 'SINGLE-PLAYER']

        # the first row (including the top-left corner)
        for i in range(len(bol_lst)):
            table_cell(table_section, (COLUMN_WIDTH, ROW_LENGTH),
                       (i * (COLUMN_WIDTH + BOUNDARIES_WIDTH), 0), bol_lst[i])

        # the rest of the rows
        for i in range(1, 10):
            for j in range(4):
                pos = (j * (COLUMN_WIDTH + BOUNDARIES_WIDTH), i * (ROW_LENGTH + BOUNDARIES_WIDTH))
                if j == 0:
                    table_text = genre_lst[i - 1]
                else:
                    table_text = ''
                table_cell(table_section, (COLUMN_WIDTH, ROW_LENGTH), pos, table_text)

        new_background.blit(table_section, TABLE_ORIGIN)

        return ('tree', new_background)


class NextButton(Button):
    """A button that ends the Q & A section and starts the steam account section.

    Instance Attributes:
        - small_buttons: a nested list of SmallButtons on this page
        - num_boxes: a list of num_boxes on the next page (to be used in mouse_click)
    """
    small_buttons: list[list[SmallButton]]
    num_boxes: list[NumBox]

    def __init__(self, small_buttons: list[list[SmallButton]], num_boxes: list[NumBox]) -> None:
        Button.__init__(self, STANDARD_BUTTON_COLORS, BUTTON_POS, 'Next')
        self.small_buttons = small_buttons
        self.num_boxes = num_boxes

    def clicked(self) -> tuple[str, pygame.Surface]:
        """Initialize the third page (steam account).
        """
        new_background = pygame.Surface(SCREEN_SIZE)
        new_background.fill(COLOURS['navy'])
        my_text = text('Please enter your Steam ID', BACKGROUND_TEXT_SIZE,
                       COLOURS['light_blue'], FONT_HEADER)
        text_rect = my_text.get_rect(center=BACKGROUND_TEXT_POS)
        new_background.blit(my_text, text_rect)

        msg = ['Your Steam ID is a sequence of 17 numbers unique to each Steam user',
               'To find your Steam ID:',
               '1. Log into your Steam Account',
               '2. Click on the username in the top right corner => "View Profile"',
               '3. Your Steam ID should be at the very top, shown in a link',
               'e.g. if the link is http://steamcommunity.com/profiles/12345678987654321',
               'the steam id will be: 12345678987654321']
        curr_pos = 260
        for i in range(0, len(msg)):
            body_text = text(msg[i], 20, COLOURS['light_blue'], FONT_BODY)
            body_rect = body_text.get_rect(center=(SCREEN_SIZE[0] // 2, curr_pos))
            new_background.blit(body_text, body_rect)
            curr_pos += 30

        return ('graph', new_background)

    def get_games(self, game_set: set[str],
                  system_objects: tuple[dict[str, Game], DecisionTree, WeightedGraph]) -> None:
        """Add new games to game_set based on user answers and the tree.
        """
        answers, indices = self._get_answers()
        games, tree = system_objects[0], system_objects[1]
        tree_computation(games, tree, answers, indices, game_set)

    def _get_answers(self) -> tuple[list[bool], list[int]]:
        """Return a list of booleans representing the user's answers and
         a list of indices where the answer could change.

        If the user didn't select an answer or selected 'I don't care', select a random answer.
        """
        answers, indices, index = [], [], 0
        for question in self.small_buttons:
            if question[0].selected is True:
                answers.append(True)
            elif question[2].selected is True:
                answers.append(False)
            else:
                answers.append(random.choice([True, False]))
                indices.append(index)
            index += 1

        return (answers, indices)


class SmallButton(Button):
    """A button that represents a user answer/selection in the Q & A session.

    Instance Attributes:
        - neighbours: the other two buttons in the same row
        - selected: whether the current button is ticked by the user
    """
    neighbours: list[SmallButton]
    selected: bool

    def __init__(self, center: tuple[int, int]) -> None:
        Button.__init__(self, (THECOLORS['white'], THECOLORS['grey']), center, '',
                        SMALL_BUTTON_SIZE)
        self.neighbours = []
        self.selected = False

    def clicked(self) -> None:
        """Change self.selected to True and change neighbours' corresponding attributes to False.

        Also change the colors.
        """
        self.selected = True
        self.color1 = COLOURS['yellow']
        for neighbour in self.neighbours:
            neighbour.selected = False
            neighbour.color1 = THECOLORS['white']


class OKButton(Button):
    """A button that ends the steam account section and starts the results section.

    Instance Attributes:
        - num_boxes: a list of NumBoxes on this page
        - background: the background for the next page (results)
        - table: the table for the next page (results)
        - user_data: output from API
        - valid_steam_id: a boolean indicating whether the user has entered a valid steam id
        - read_buttons: a list of ReadButtons on the next page
        - back_button: the BackButton for the description stage (which stores the same background)
    """
    num_boxes: list[NumBox]
    background: pygame.Surface
    table: pygame.Surface
    user_data: dict
    valid_steam_id: bool
    read_buttons: list[ReadButton]
    back_button: BackButton

    def __init__(self, num_boxes: list[NumBox], read_buttons: list[ReadButton],
                 back_button: BackButton) -> None:
        Button.__init__(self, STANDARD_BUTTON_COLORS, BUTTON_POS, 'OK')
        self.num_boxes = num_boxes
        self.background = pygame.Surface(SCREEN_SIZE)
        self.table = pygame.Surface(TABLE_SIZE)
        self.user_data = {}
        self.valid_steam_id = False
        self.read_buttons = read_buttons
        self.back_button = back_button

    def clicked(self) -> tuple[str, pygame.Surface]:
        """Initialize the third page (steam account) if there is nothing wrong with user id.
        """
        self.background.fill(COLOURS['navy'])

        try:
            self.user_data = read_json_data(self._get_id())
            self.valid_steam_id = True
        except urllib.error.HTTPError:
            my_text = text('You did not enter a valid Steam ID. '
                           'The results are based on the Q & A session only.',
                           TABLE_TEXT_SIZE, COLOURS['yellow'], FONT_BODY)
            self.background.blit(my_text, WARNIING_POS)

        my_text = text('Here are the top 9 games recommended for you!', BACKGROUND_TEXT_SIZE - 10,
                       COLOURS['light_blue'], FONT_HEADER)
        text_rect = my_text.get_rect(center=BACKGROUND_TEXT_POS)
        self.background.blit(my_text, text_rect)

        col_lst = ['NAME', 'GENRE', 'PRICE (USD)', 'DESCRIPTION']  # info to display for each game

        # column names (including the top-left corner):
        for i in range(len(col_lst)):
            table_cell(self.table, (COLUMN_WIDTH, ROW_LENGTH),
                       (i * (COLUMN_WIDTH + BOUNDARIES_WIDTH), 0), col_lst[i])

        self.background.blit(self.table, TABLE_ORIGIN)

        return ('results', self.background)

    def get_games(self, game_set: set[str],
                  system_objects: tuple[dict[str, Game], DecisionTree, WeightedGraph]) -> None:
        """Add new games to game_set based on user's steam id and the graph.

        Eliminate the games that the user already played in their steam account.

        Mutate self.read_buttons and self.back_button so that they have the descriptions, urls,
        and the background.
        """
        games, graph = system_objects[0], system_objects[2]
        if self.valid_steam_id:
            graph_computation(games, graph, self.user_data, game_set)

        game_lst = list(game_set)
        pop_score_computation(games, game_lst)
        # sort the games in terms of recommendation score, keep the top 9
        selected_games = sorted(game_lst, key=lambda game: games[game].recommendation_score,
                                reverse=True)[:9]

        # mutate self.table, display game info
        for i in range(9):
            content_lst = [games[selected_games[i]].name,
                           str(games[selected_games[i]].genre)[1:-1].replace('\'', ''),
                           str(games[selected_games[i]].price), '']
            self.read_buttons[i].desc = games[selected_games[i]].game_description
            self.read_buttons[i].url = games[selected_games[i]].url

            for j in range(4):
                table_text = content_lst[j]
                pos = (j * (COLUMN_WIDTH + BOUNDARIES_WIDTH),
                       (i + 1) * (ROW_LENGTH + BOUNDARIES_WIDTH))
                table_cell(self.table, (COLUMN_WIDTH, ROW_LENGTH), pos, table_text)

        self.background.blit(self.table, TABLE_ORIGIN)
        self.back_button.background = self.background

    def _get_id(self) -> str:
        """Return a string representing user id based on what the user entered into num_boxes.
        """
        str_so_far = ''
        for num_box in self.num_boxes:
            str_so_far += num_box.text
        return str_so_far


class NumBox(Button):
    """A button that represents a box that stores a number from the user's steam id...

    Instance Attributes:
        - prev: the previous box that stores a number
        - next: the next box that stores a number
    """
    prev: Optional[NumBox]
    next: Optional[NumBox]

    def __init__(self, center: tuple[int, int], prev: Optional[NumBox]) -> None:
        Button.__init__(self, (COLOURS['light_blue'], COLOURS['light_blue']), center, '',
                        NUM_BOX_SIZE)
        self.prev = prev
        self.next = None

    def clicked(self) -> None:
        """Do nothing when clicked."""
        return None


class ReadButton(Button):
    """A button that lets the user read the description of a game recommended.

    On the last page of the output, where the system displays the top 9 games
    recommended to the user, each game has its own ReadButton. By clicking
    this button, a full description of the game can be displayed to
    the user.

    Instance Attributes:
        - desc: a description for the game
        - url: a string representing the steam website of the game
        - url_button: a URL button that can be clicked on
    """
    desc: str
    url: str
    url_button: UrlButton

    def __init__(self, center: tuple[int, int], url_button: UrlButton) -> None:
        Button.__init__(self, (COLOURS['yellow'], THECOLORS['grey']), center, 'Read')
        self.desc = ''
        self.url = ''
        self.url_button = url_button

    def clicked(self) -> tuple[str, pygame.Surface]:
        """Displays description and url.
        """
        new_background = pygame.Surface(SCREEN_SIZE)
        new_background.fill(COLOURS['light_blue'])
        desc_title = text('Game Description', BACKGROUND_TEXT_SIZE + 10,
                          COLOURS['navy'], FONT_HEADER)
        desc_text_rect = desc_title.get_rect(center=BACKGROUND_TEXT_POS)
        new_background.blit(desc_title, desc_text_rect)
        self.url_button.text = self.url

        desc_background = pygame.Surface(DESC_SIZE)
        desc_background.fill(COLOURS['navy'])
        center_paragraph(desc_background, self.desc, TABLE_TEXT_SIZE, THECOLORS['white'])
        new_background.blit(desc_background, DESC_ORIGIN)

        return ('desc', new_background)


class UrlButton(Button):
    """A button that opens a webpage when clicked on.

    Instance Attributes:
        - color: color of the button
        - image: this button's corresponding pygame surface
        - rect: the rectangle of this button's image (surface), stored as pygame.Rect
        - text: the text on the button
    """

    def __init__(self) -> None:
        pygame.sprite.Sprite.__init__(self)
        self.color = COLOURS['light_blue']
        self.image = pygame.Surface(URL_BUTTON_SIZE)
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.rect.center = URL_POS
        self.text = ''

    def update(self) -> None:
        """Update the color of this button when mouse is hovering/not hovering on top.
        """
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            self.image.fill(self.color)
            center_text(self.image, 'Game url: ' + self.text, TABLE_TEXT_SIZE, COLOURS['url_blue'])
        else:
            self.image.fill(self.color)
            center_text(self.image, 'Game url: ' + self.text, TABLE_TEXT_SIZE, COLOURS['navy'])

    def clicked(self) -> None:
        """Open the webpage.
        """
        webbrowser.open(self.text)


class RestartButton(Button):
    """A button that restarts the whole system in the results page.

    After the top 9 games recommended to the user have been displayed,
    the RestartButton will appear in the bottom right corner that allows
    the user to start the whole recommendation system again.

    Instance Attributes:
        - all_groups: a dict mapping stage names to sprite groups.
    """
    all_groups: dict[str, pygame.sprite.Group]

    def __init__(self, all_groups: dict[str, pygame.sprite.Group]) -> None:
        Button.__init__(self, STANDARD_BUTTON_COLORS, BUTTON_POS, 'Restart', RESTART_BUTTON_SIZE)
        self.all_groups = all_groups

    def clicked(self) -> tuple[str, pygame.Surface]:
        """Restart the system.
        """
        background = initialize_background()
        initialize_sprites(self.all_groups)

        return ('main', background)


class BackButton(Button):
    """A button that lets the user go back to the results page after reading description.

    On the results page, the user can click ReadButton to read about the description of the game
    they choose. This BackButton allows the user to return from the description page to the
    results page to see the game recommendation table.

    Instance Attributes:
        - background: the background for the results page.
    """
    background: Optional[pygame.Surface]

    def __init__(self) -> None:
        Button.__init__(self, (THECOLORS['grey'], COLOURS['yellow']), BUTTON_POS, 'Back')
        self.background = None

    def clicked(self) -> tuple[str, pygame.Surface]:
        """Go back to the results page.
        """
        return ('results', self.background)


def initialize_screen() -> pygame.Surface:
    """Initialize pygame and the display window.
    """
    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode(SCREEN_SIZE)
    screen.fill(COLOURS['light_blue'])
    pygame.display.flip()
    pygame.event.clear()

    return screen


def initialize_groups() -> dict[str, pygame.sprite.Group]:
    """Initialize sprite groups and return a dictionary mapping the four stages to their groups.

    They can be treated as lists of sprite objects.
    """
    main_group = pygame.sprite.Group()
    tree_group = pygame.sprite.Group()
    graph_group = pygame.sprite.Group()
    results_group = pygame.sprite.Group()
    desc_group = pygame.sprite.Group()

    return {'main': main_group, 'tree': tree_group, 'graph': graph_group, 'results': results_group,
            'desc': desc_group}


def initialize_sprites(all_groups: dict[str, pygame.sprite.Group]) -> None:
    """Initialize all sprites, add them to groups.
    """
    for group in all_groups:
        all_groups[group].empty()

    start_button = StartButton(STANDARD_BUTTON_COLORS, BUTTON_POS, 'Start')
    start_button.add(all_groups['main'])  # it's the other way around: Sprite.add(Group)

    url_button = UrlButton()
    url_button.add(all_groups['desc'])

    small_buttons = _init_small_buttons(all_groups)
    num_boxes = _init_num_boxes(all_groups)
    read_buttons = _init_read_buttons(all_groups, url_button)

    next_button = NextButton(small_buttons, num_boxes)
    next_button.add(all_groups['tree'])

    back_button = BackButton()
    back_button.add(all_groups['desc'])

    ok_button = OKButton(num_boxes, read_buttons, back_button)
    ok_button.add(all_groups['graph'])

    restart_button = RestartButton(all_groups)
    restart_button.add(all_groups['results'])


def initialize_background() -> pygame.Surface:
    """Initialize the background of the main page.
    """
    background = pygame.Surface(SCREEN_SIZE)
    background.fill(COLOURS['navy'])
    title_text = text('Video Game Recommendation System', BACKGROUND_TEXT_SIZE,
                      COLOURS['light_blue'], FONT_HEADER)
    title_rect = title_text.get_rect(center=(SCREEN_SIZE[0] // 2, SCREEN_SIZE[1] // 8))
    background.blit(title_text, title_rect)

    msg = ['Hi, welcome to the CSC111 Video Game Recommendation System!',
           'This system sorts out 9 games from a database containing over 20 thousand',
           'games collected on Steam, based on your answers to the following questionnaire.', '',
           'For a more personalized system, please enter your steam account id',
           'in the second half of the questionnaire, and recommendations will be',
           'made based on the games you currently have in your Steam Library.', '', 'Enjoy!']
    curr_pos = 200
    for i in range(len(msg)):
        body_text = text(msg[i], 25, COLOURS['light_blue'], FONT_BODY)
        body_rect = body_text.get_rect(center=(SCREEN_SIZE[0] // 2, curr_pos))
        background.blit(body_text, body_rect)
        curr_pos += 30

    image = pygame.image.load('data/steam.jpeg')
    image = pygame.transform.scale(image, (440, 250))

    background.blit(image, (185, 480))

    return background


def _init_small_buttons(all_groups: dict[str, pygame.sprite.Group]) -> list[list[SmallButton]]:
    """Initialize small buttons.
    """
    small_buttons = [[] for _ in range(9)]
    for i in range(9):
        for j in range(3):
            x = TABLE_ORIGIN[0] + COLUMN_WIDTH // 2 + (j + 1) * COLUMN_WIDTH + j * BOUNDARIES_WIDTH
            y = TABLE_ORIGIN[1] + ROW_LENGTH // 2 + (i + 1) * ROW_LENGTH + i * BOUNDARIES_WIDTH
            small_button = SmallButton((x, y))
            small_buttons[i].append(small_button)
            small_button.add(all_groups['tree'])
        for k in range(3):
            small_buttons[i][k].neighbours = [small_buttons[i][k - 1], small_buttons[i][k - 2]]

    return small_buttons


def _init_num_boxes(all_groups: dict[str, pygame.sprite.Group]) -> list[NumBox]:
    """Initialize num boxes.
    """
    num_boxes = []
    curr_num_box = None
    gap = (SCREEN_SIZE[0] - NUM_BOX_SIZE[0] * 17) // 18
    for i in range(17):
        num_box = NumBox((gap + NUM_BOX_SIZE[0] // 2 + i * (gap + NUM_BOX_SIZE[0]),
                          SCREEN_SIZE[1] // 4), curr_num_box)
        num_box.add(all_groups['graph'])
        num_boxes.append(num_box)
        if curr_num_box is not None:
            curr_num_box.next = num_box
        curr_num_box = num_box

    return num_boxes


def _init_read_buttons(all_groups: dict[str, pygame.sprite.Group],
                       url_button: UrlButton) -> list[ReadButton]:
    """Initialize read buttons.
    """
    read_buttons = []
    for i in range(9):
        x = TABLE_ORIGIN[0] + COLUMN_WIDTH // 2 + 3 * COLUMN_WIDTH + 3 * BOUNDARIES_WIDTH
        y = TABLE_ORIGIN[1] + ROW_LENGTH // 2 + (i + 1) * (ROW_LENGTH + BOUNDARIES_WIDTH)
        read_button = (ReadButton((x, y), url_button))
        read_buttons.append(read_button)
        read_button.add(all_groups['results'])

    return read_buttons


def mouse_click(clicked_sprite: Button, system_objects: tuple, game_set: set[str]) -> \
        tuple[Optional[str], Optional[pygame.Surface], Optional[NumBox]]:
    """Deal with a user mouseclick.

    Return the new group and background (if any); also return the current NumBox to be filled
    with input text.
    """
    group, background, curr_num_box = None, None, None
    output = clicked_sprite.clicked()
    if output is not None:
        # Switch to another page and background
        group, background = output
        if isinstance(clicked_sprite, NextButton):
            clicked_sprite.get_games(game_set, system_objects)
            curr_num_box = clicked_sprite.num_boxes[0]
        elif isinstance(clicked_sprite, OKButton):
            clicked_sprite.get_games(game_set, system_objects)
        elif isinstance(clicked_sprite, RestartButton):
            reset_recommendation_scores(system_objects[0])

    return (group, background, curr_num_box)


def keyboard_entry(event: pygame.event.Event, curr_num_box: NumBox) -> NumBox:
    """Deal with user keyboard entry. Return the next NumBox to be filled with input text.

    Preconditions:
        - event.type == pygame.KEYDOWN
    """
    if pygame.K_0 <= event.key <= pygame.K_9:
        curr_num_box.text = str(chr(event.key))
        if curr_num_box.next is not None:
            curr_num_box = curr_num_box.next
    elif event.key == pygame.K_BACKSPACE:
        if curr_num_box.next is None and curr_num_box.text != '':
            curr_num_box.text = ''
        elif curr_num_box.prev is not None:
            curr_num_box = curr_num_box.prev
            curr_num_box.text = ''

    return curr_num_box


def table_cell(table: pygame.Surface, dim: tuple[int, int],
               pos: tuple[int, int], table_text: str) -> None:
    """Blit one cell with the given dimensions, position, and text onto the table.
    """
    cell = pygame.Surface(dim)
    cell.fill(COLOURS['light_blue'])
    center_text(cell, table_text, TABLE_TEXT_SIZE, COLOURS['navy'], True)
    table.blit(cell, pos)


def center_text(surface: pygame.surface, message: str, size: int, color: tuple,
                sensitive: bool = False) -> None:
    """Put the text at the center of the given surface.
    """
    if sensitive and len(message) > 0 and size > 2 * surface.get_width() // len(message):
        center_paragraph(surface, message, round(size / 1.2), color, gap=0)
    else:
        my_text = text(message, size, color, FONT_BODY)
        center_x, center_y = surface.get_width() / 2, surface.get_height() / 2
        text_rect = my_text.get_rect(center=(center_x, center_y))
        surface.blit(my_text, text_rect)


def center_paragraph(surface: pygame.surface, message: str, size: int, color: tuple,
                     gap: int = 5) -> None:
    """Put the paragraph at the center of the given surface.
    """
    width, height = surface.get_width(), surface.get_height()
    max_length = height // (size + gap) - 1
    paragraph_lst, line_so_far = [], ''

    for word in message.split():
        if (len(line_so_far) + len(word)) * size / 2 < (width - 2 * size):
            line_so_far += word + ' '
        else:
            if len(paragraph_lst) + 1 == max_length:
                line_so_far += '...'
            paragraph_lst.append(text(line_so_far, size, color, FONT_BODY))
            line_so_far = word + ' '
    paragraph_lst.append(text(line_so_far, size, color, FONT_BODY))

    num_lines = min(max_length, len(paragraph_lst))
    for i in range(num_lines):
        yi = round((height - (size + gap) * num_lines) / 2 + ((size + gap) * (i + 0.5)))
        text_rect = paragraph_lst[i].get_rect(center=(width // 2, yi))
        surface.blit(paragraph_lst[i], text_rect)


def text(message: str, size: int, color: tuple, font: str) -> pygame.Surface:
    """Render a line of text in Pygame.
    """
    my_text = pygame.font.Font(font, size).render(message, True, color)
    return my_text


def reset_recommendation_scores(games: dict[str, Game]) -> None:
    """Reset the recommendation scores of all games.
    """
    for game in games:
        games[game].recommendation_score = 0.0


if __name__ == '__main__':
    import doctest

    doctest.testmod(verbose=True)

    import python_ta
    import python_ta.contracts

    python_ta.contracts.DEBUG_CONTRACTS = False
    python_ta.contracts.check_all_contracts()
    python_ta.check_all(config={
        'extra-imports': ['python_ta.contracts', 'typing', 'random', 'urllib.error', 'webbrowser',
                          'pygame', 'pygame.colordict', 'data_computations', 'weighted_decision'],
        'allowed-io': [],
        'max-line-length': 100,
        'disable': ['R1702', 'E1136'],
        'generated-members': ['pygame.*']
    })
