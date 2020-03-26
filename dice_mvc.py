# coding: utf-8

import random
import math
import pandas as pd
import xlwt
from openpyxl import Workbook

# ----------------------< Game rules constants  >-----------------------------------------------------------------------

# Number of dices by default in the set
DEFAULT_DICES_NB = 5
# Target total score to win by default
DEFAULT_TARGET_SCORE = 2000
# Number of side of the dices used in the game
NB_DICE_SIDE = 6

# List of dice value scoring
LIST_SCORING_DICE_VALUE = [1, 5]
# List of associated score for scoring dice values
LIST_SCORING_MULTIPLIER = [100, 50]

# Trigger for multiple bonus
TRIGGER_OCCURRENCE_FOR_BONUS = 3
# Special bonus multiplier for multiple ace bonus
BONUS_VALUE_FOR_ACE_BONUS = 1000
# Standard multiplier for multiple dices value bonus
BONUS_VALUE_FOR_NORMAL_BONUS = 100


# ----------------------< Class handling roll statistics by individual turn >-------------------------------------------
# constructor parameters :                  None
#
# getters :
#
#   turn_nb_roll()                          Number of rolls during the turns
#   turn_nb_full_roll()                     Number of times all the dices set was used during the roll
#   turn_nb_bonus()                         Number of multiple dices bonus got during the roll
#
# public methods :
#
#   increment_turn_nb_roll()                Increment the number of roll during the turn
#   increment_turn_nb_full_roll()           Increment the number of full roll during the turn
#   add_to_turn_nb_bonus()                  Accumulate the number of bonus during the turn
#
#   reset_statistics()
# ----------------------------------------------------------------------------------------------------------------------
class DiceTurnStatistics:
    def __init__(self):
        self._turn_nb_roll = 0
        self._turn_nb_full_roll = 0
        self._turn_nb_bonus = 0

    def __repr__(self):
        return str([self._turn_nb_roll, self._turn_nb_full_roll, self._turn_nb_bonus])

    def __str__(self):
        output_str = 'turn nb roll : ' + str(self._turn_nb_roll)
        output_str += ', turn nb full roll : ' + str(self._turn_nb_full_roll)
        output_str += ', turn nb bonus : ' + str(self._turn_nb_bonus) + '\n'
        return output_str

    @property
    def turn_nb_roll(self):
        return self._turn_nb_roll

    @property
    def turn_nb_full_roll(self):
        return self._turn_nb_full_roll

    @property
    def turn_nb_bonus(self):
        return self._turn_nb_bonus

    def increment_turn_nb_roll(self):
        self._turn_nb_roll += 1

    def increment_turn_nb_full_roll(self):
        self._turn_nb_full_roll += 1

    def add_to_turn_nb_bonus(self, nb_bonus):
        self._turn_nb_bonus += nb_bonus

    def reset_statistics(self):
        self._turn_nb_roll = 0
        self._turn_nb_full_roll = 0
        self._turn_nb_bonus = 0


# ----------------------< Class handling full games statistics >--------------------------------------------------------
# constructor parameters :                  None
#
# getters :
#
#   max_turn_scoring()                      Maximum scoring done in a turn during the game and performer player index
#                                               -->  {'player_index': , 'value': }
#   longest_turn()                          Longest turn done during the game and performer player index
#                                               -->  {'player_index': , 'value': }
#   max_turn_loss()                         Maximum turn score lost in a turn during the game and performer player index
#                                               -->  {'player_index': , 'value': }
#
#   nb_scoring_turn()                       Number of scoring turn during the game
#   nb_non_scoring_turn()                   Number of non scoring turn during the game
#   mean_scoring_turn()                     Mean score of the scoring turns during the game
#   mean_non_scoring_turn()                 Mean lost score of the non scoring turns during the game
#
# public methods :
#
#   update_game_statistics                  Update the statistics regarding scoring/non scoring status
#       ( player_index, dice_set)
#
#   reset_statistics()
# ----------------------------------------------------------------------------------------------------------------------
class DiceGameStatistics:
    def __init__(self):
        self._max_turn_scoring = 0
        self._max_turn_scoring_player_index = 0
        self._max_turn_loss = 0
        self._max_turn_loss_player_index = 0
        self._longest_turn = 0
        self._longest_turn_player_index = 0

        self._nb_scoring_turn = 0
        self._nb_non_scoring_turn = 0
        self._sigma_scoring = 0
        self._sigma_non_scoring = 0

    def __repr__(self):
        return str([self._max_turn_scoring,
                    self._max_turn_scoring_player_index,
                    self._max_turn_loss,
                    self._max_turn_loss_player_index,
                    self._longest_turn,
                    self._longest_turn_player_index,
                    self._nb_scoring_turn,
                    self._nb_non_scoring_turn,
                    self._sigma_scoring,
                    self._sigma_non_scoring])

    def __str__(self):
        output_str = 'player #' + str(self._max_turn_scoring_player_index)
        output_str += ' has max turn scoring : ' + str(self._max_turn_scoring) + '\n'
        output_str += 'player #' + str(self._max_turn_loss_player_index)
        output_str += ' has max turn loss : ' + str(self._max_turn_loss) + '\n'
        output_str += 'player #' + str(self._longest_turn_player_index)
        output_str += ' has the longest turn  : ' + str(self._longest_turn) + '\n'
        output_str += str(self._nb_scoring_turn) + ' scoring turns, '
        output_str += str(self._nb_non_scoring_turn) + ' non scoring turns\n'
        output_str += str(self._sigma_scoring) + ' accumulated scored points, '
        output_str += str(self._sigma_non_scoring) + ' accumulated non-scored points\n'
        return output_str

    @property
    def max_turn_scoring(self):
        """Get maximum score done in one turn and player """
        return {'player_index': self._max_turn_scoring_player_index, 'value': self._max_turn_scoring}

    @property
    def longest_turn(self):
        return {'player_index': self._longest_turn_player_index, 'value': self._longest_turn}

    @property
    def max_turn_loss(self):
        return {'player_index': self._max_turn_loss_player_index, 'value': self._max_turn_loss}

    @property
    def nb_scoring_turn(self):
        return self._nb_scoring_turn

    @property
    def nb_non_scoring_turn(self):
        return self._nb_non_scoring_turn

    @property
    def mean_scoring_turn(self):
        if self._nb_scoring_turn == 0:
            return 0
        return self._sigma_scoring / self._nb_scoring_turn

    @property
    def mean_non_scoring_turn(self):
        if self._nb_non_scoring_turn == 0:
            mean_for_non_scoring = 0
        else:
            mean_for_non_scoring = self._sigma_non_scoring / self._nb_non_scoring_turn

        return mean_for_non_scoring

    def update_game_statistics(self, player_index, dice_set):

        def update_scoring_turn_statistics():

            def update_max_turn_scoring(score):
                if score > self._max_turn_scoring:
                    self._max_turn_scoring = score
                    self._max_turn_scoring_player_index = player_index

            def update_longest_turn(nb_roll):
                if nb_roll > self._longest_turn:
                    self._longest_turn = nb_roll
                    self._longest_turn_player_index = player_index

            def sum_scoring_turn(score):
                self._sigma_scoring += score

            # ----<Update the game statistics for scoring turns>--------------------------------------------------------
            self._nb_scoring_turn += 1

            update_max_turn_scoring(dice_set.turn_score)
            update_longest_turn(dice_set.turn_statistics.turn_nb_roll)
            sum_scoring_turn(dice_set.turn_score)

        def update_non_scoring_turn_statistics():

            def update_max_loss(loss_score):
                if loss_score > self._max_turn_loss:
                    self._max_turn_loss = loss_score
                    self._max_turn_loss_player_index = player_index

            def sum_non_scoring_turn(score):
                self._sigma_non_scoring += score

            # ----<Update the game statistics for non scoring turns>----------------------------------------------------
            self._nb_non_scoring_turn += 1

            update_max_loss(dice_set.turn_lost_score)
            sum_non_scoring_turn(dice_set.turn_lost_score)

        # ----<update game level statistics for lost or win turn>-------------------------------------------------------
        if dice_set.its_lost_roll:
            update_non_scoring_turn_statistics()
        else:
            update_scoring_turn_statistics()

    def reset_statistics(self):
        self._max_turn_scoring = 0
        self._max_turn_scoring_player_index = 0
        self._max_turn_loss = 0
        self._max_turn_loss_player_index = 0
        self._longest_turn = 0
        self._longest_turn_player_index = 0

        self._nb_scoring_turn = 0
        self._nb_non_scoring_turn = 0
        self._sigma_scoring = 0
        self._sigma_non_scoring = 0


# ----------------------< Class handling game dice turns >--------------------------------------------------------------
# constructor parameters :
#   nb_dices                                Total number of dices in the game set (default->DEFAULT_DICES_NB)
#
# getters :
#
#   nb_dices_to_roll()                      Number of dices to roll for next throw
#   scoring_dices_list()                    List of tuple (# of occurrence, value) for all the scoring dices
#   nb_scoring_dices()                      Number of non scoring dices after last throw
#   non_scoring_dices_list()                List of tuple (# of occurrence, value) for all the non scoring dices
#   nb_non_scoring_dices()                  Number of scoring dices after last throw
#   roll_score()                            Score done after last throw
#   turn_score()                            Total score done during the turn
#   turn_lost_score()                       Total score lost during the turn
#   turn_statistics()                       roll statistics for the current turn
#   its_lost_roll()                         Status after the last throw, True for a lost turn
#
# public methods :
#
#   roll_dices_and_count_roll_score()       Roll the dices and count the score done
#
#   prepare_for_next_turn()                 Prepare for a new turn
# ----------------------------------------------------------------------------------------------------------------------
class DiceGameTurn:
    # Class constants defining the game rules parameters for all instances
    _nb_side = NB_DICE_SIDE
    _list_scoring_dice_value = LIST_SCORING_DICE_VALUE
    _list_scoring_multiplier = LIST_SCORING_MULTIPLIER

    _trigger_occurrence_for_bonus = TRIGGER_OCCURRENCE_FOR_BONUS
    _bonus_value_for_ace_bonus = BONUS_VALUE_FOR_ACE_BONUS
    _bonus_value_for_normal_bonus = BONUS_VALUE_FOR_NORMAL_BONUS

    def __init__(self, nb_dices=DEFAULT_DICES_NB):
        self._nb_dices = nb_dices

        self._turn_statistics = DiceTurnStatistics()
        self._non_scoring_occurrence_list = [0] * self._nb_side
        self._scoring_occurrence_list = [0] * self._nb_side
        self._its_lost_roll = False

        self._roll_score = 0
        self._turn_score = 0
        self._turn_lost_score = 0

    def __str__(self):
        output_str = str(self.nb_non_scoring_dices)
        output_str += ' dices non scoring ' + str(self.non_scoring_dices_list)
        output_str += ', ' + str(self.nb_scoring_dices)
        output_str += ' dices scoring ' + str(self.scoring_dices_list)
        output_str += ' for ' + str(self.roll_score) + ", total=" + str(self.turn_score)
        output_str += ', ' + str(self.nb_dices_to_roll) + ' dices to roll\n'
        output_str += str(self.turn_statistics)
        return output_str

    @property
    def nb_dices_to_roll(self):
        if self._its_lost_roll:
            # If it's a lost roll -> no remaining dice to roll
            return 0

        if self._turn_score == 0 or self.nb_non_scoring_dices == 0:
            # If first roll of a turn or if all dices scored -> all dices should be rolled
            return self._nb_dices

        # Last turn was a scoring one -> Next roll will use the remaining non scoring dices
        return self.nb_non_scoring_dices

    @property
    def scoring_dices_list(self):
        # Create a list of tuple (# of value occurrence, value) for all the scoring dices
        return [(Occurrence, Index + 1,) for Index, Occurrence in
                enumerate(self._scoring_occurrence_list) if Occurrence > 0]

    @property
    def non_scoring_dices_list(self):
        # Create a list of tuple (# of value occurrence, value) for all the non scoring dices
        return [(Occurrence, Index + 1,) for Index, Occurrence in
                enumerate(self._non_scoring_occurrence_list) if Occurrence > 0]

    @property
    def nb_scoring_dices(self):
        # nb of dices by categories it's the sum of the dices value occurrence
        # e.g. for this occurrence [ 0, 1, 1, 0, 0, 2] -> 4 dices
        return sum(self._scoring_occurrence_list)

    @property
    def nb_non_scoring_dices(self):
        # nb of dices by categories it's the sum of the dices value occurrence
        # e.g. for this occurrence [ 0, 1, 1, 0, 0, 2] -> 4 dices
        return sum(self._non_scoring_occurrence_list)

    @property
    def roll_score(self):
        return self._roll_score

    @property
    def turn_score(self):
        return self._turn_score

    @property
    def turn_lost_score(self):
        return self._turn_lost_score

    @property
    def turn_statistics(self):
        return self._turn_statistics

    @property
    def its_lost_roll(self):
        return self._its_lost_roll

    def roll_dices_and_count_roll_score(self):
        def roll_dices():
            def random_roll_generator():
                # generator of nb_dice_roll random values in interval [0..nb_side[
                dice_index = 0
                while dice_index < self.nb_dices_to_roll:
                    yield random.randint(0, self._nb_side - 1)
                    dice_index += 1

            # ----<Update the list of dices values occurrence by rolling all the dices who should be rolled>------------
            # dices_value_occurrence_list is in the scope of all this set of helper functions
            for random_side_index in random_roll_generator():
                dices_value_occurrence_list[random_side_index] += 1

            self._turn_statistics.increment_turn_nb_roll()

        def count_roll_score():
            def count_bonus_roll_score():
                # Compute score from bonus based on the multiple detection trigger level
                # dices_value_occurrence_list is in the scope of all this set of helper functions

                bonus_occurrence_trigger = self._trigger_occurrence_for_bonus

                # Test all the occurrences to detect bonus trigger values
                for side_index, dices_occurrence in enumerate(dices_value_occurrence_list):

                    nb_bonus = dices_occurrence // bonus_occurrence_trigger
                    if nb_bonus > 0:
                        # if there is a bonus

                        #  select bonus multiplier for ace or other dice value
                        bonus_multiplier = self._bonus_value_for_ace_bonus if side_index == 0 \
                            else self._bonus_value_for_normal_bonus

                        # Update roll score (index 0 reflect occurrence for value 1 ...)
                        self._roll_score += nb_bonus * bonus_multiplier * (side_index + 1)

                        # Update potential remainder (7 occurrences with trigger at 3 -> 1 occurrence)
                        dices_value_occurrence_list[side_index] %= bonus_occurrence_trigger

                        # Update scoring and non scoring dices occurrence list
                        self._non_scoring_occurrence_list[side_index] = dices_value_occurrence_list[side_index]
                        self._scoring_occurrence_list[side_index] = nb_bonus * bonus_occurrence_trigger

                        # Update turn statistics
                        self._turn_statistics.add_to_turn_nb_bonus(nb_bonus)
                    else:
                        # Update scoring and non scoring dices occurrence list for no bonus case
                        self._scoring_occurrence_list[side_index] = 0
                        self._non_scoring_occurrence_list[side_index] = dices_occurrence

            def count_non_bonus_roll_score():
                # For all the potential scoring values and multiplier from the rules in class constants
                # dices_value_occurrence_list is in the scope of all this set of helper functions

                for scoring_dice_value, scoring_multiplier in zip(self._list_scoring_dice_value,
                                                                  self._list_scoring_multiplier):

                    scoring_dice_index = scoring_dice_value - 1  # index 0 reflect occurrence for value 1 ...
                    dice_occurrence_to_test = dices_value_occurrence_list[scoring_dice_index]

                    if dice_occurrence_to_test > 0:
                        # if there is a scoring dice occurrence

                        # Update roll score
                        self._roll_score += dice_occurrence_to_test * scoring_multiplier

                        # Update scoring and non scoring dices occurrence list
                        self._non_scoring_occurrence_list[scoring_dice_index] = 0
                        self._scoring_occurrence_list[scoring_dice_index] += dice_occurrence_to_test

            # ----<Count roll score>------------------------------------------------------------------------------------
            self._roll_score = 0
            count_bonus_roll_score()
            count_non_bonus_roll_score()

        def update_roll_status():
            # Scoring or non scoring roll status
            self._its_lost_roll = (self._roll_score == 0)

            if self._its_lost_roll:
                # Non scoring roll
                self._turn_lost_score = self._turn_score
                self._turn_score = 0
            else:
                # Scoring roll
                self._turn_score += self._roll_score

            # If all dices set rolled successfully -> update turn statistics for full roll counter
            if self.nb_dices_to_roll == self._nb_dices:
                self._turn_statistics.increment_turn_nb_full_roll()

        # ----<Roll dices, count roll score and update roll status>-----------------------------------------------------

        # dices_value_occurrence_list is in the scope of all this set of helper functions
        dices_value_occurrence_list = [0] * self._nb_side

        roll_dices()
        count_roll_score()
        update_roll_status()

    def prepare_for_next_turn(self):
        # reset status for next turn
        self._turn_score = 0
        self._turn_lost_score = 0
        self._turn_statistics.reset_statistics()
        self._its_lost_roll = False


# ----------------------< Class handling players status a statistics >--------------------------------------------------
# constructor parameters :
#   players_names_list                      List of players name
#
# getters :
#
#   best_score()                            Current best total score
#   player_rank()                           Current player rank
#   index_of_player_with_best_score()       Index of the player with best total score (rank 1)
#
# public methods :
#
#   player_name(player_index)               Player name
#   player_score(player_index)              Player total score
#   player_total_nb_roll(player_index)      Player total number of roll
#   player_total_nb_full_roll(player_index) Player total number of full roll
#   player_total_lost_score(player_index)   Player total score lost
#   player_total_nb_bonus(player_index)     Player total number of bonus for multiple dices
#
#   update_player_statistics                Update players statistics at the end of the turn
#       (self, player_index, dice_set)
#
#   sort_player_index_by_score()            Produce a list of player index sorted by players total score
#
#   player_status(player_index)             Player index -->    { 'rank': , 'score': , 'nb_roll': ,
#                                                                 'nb_full_roll': , 'total_lost_score': ,
#                                                                 'nb_bonus': }
#
#   leader_status()                         Rank 1 player -->   { 'rank': , 'score': , 'nb_roll': ,
#                                                                 'nb_full_roll': , 'total_lost_score': ,
#                                                                 'nb_bonus': }
#   reset_status()
# ----------------------------------------------------------------------------------------------------------------------
class DiceGamePlayers:
    def __init__(self, players_names_list):
        self._nb_players = len(players_names_list)

        self._players_names_list = players_names_list
        self._players_score_list = [0] * self._nb_players
        self._player_total_nb_roll = [0] * self._nb_players

        self._player_total_nb_full_roll = [0] * self._nb_players
        self._player_total_lost_score = [0] * self._nb_players
        self._player_total_nb_bonus = [0] * self._nb_players

    def __str__(self):
        output_str = str(self._nb_players) + ' players :\n'
        for player_index in self.sort_player_index_by_score():
            output_str += self._players_names_list[player_index]
            output_str += ' scoring ' + str(self._players_score_list[player_index])
            output_str += ' in ' + str(self._player_total_nb_roll[player_index]) + ' roll'
            output_str += ' with ' + str(self._player_total_nb_full_roll[player_index]) + ' full roll,'
            output_str += ' ' + str(self._player_total_nb_bonus[player_index]) + ' bonus'
            output_str += ' and ' + str(self._player_total_lost_score[player_index]) + ' potential points lost\n'

        return output_str

    def __len__(self):
        return self._nb_players

    def player_name(self, player_index):
        return self._players_names_list[player_index]

    def player_score(self, player_index):
        return self._players_score_list[player_index]

    def player_total_nb_roll(self, player_index):
        return self._player_total_nb_roll[player_index]

    def player_total_nb_full_roll(self, player_index):
        return self._player_total_nb_full_roll[player_index]

    def player_total_lost_score(self, player_index):
        return self._player_total_lost_score[player_index]

    def player_total_nb_bonus(self, player_index):
        return self._player_total_nb_bonus[player_index]

    def player_status(self, player_index):
        return {'rank': self.sort_player_index_by_score().index(player_index) + 1,
                'score': self._players_score_list[player_index],
                'nb_roll': self._player_total_nb_roll[player_index],
                'nb_full_roll': self._player_total_nb_full_roll[player_index],
                'total_lost_score': self._player_total_lost_score[player_index],
                'nb_bonus': self._player_total_nb_bonus[player_index]}

    def player_rank(self, player_index):
        return self.sort_player_index_by_score().index(player_index) + 1

    @property
    def index_of_player_with_best_score(self):
        return self._players_score_list.index(self.best_score)

    @property
    def best_score(self):
        return max(self._players_score_list)

    @property
    def leader_status(self):
        return self._players_names_list[self.index_of_player_with_best_score]

    def update_player_statistics(self, player_index, dice_set):
        # End of a turn : update player statistics from turn statistics

        dice_turn_statistics = dice_set.turn_statistics
        self._player_total_nb_roll[player_index] += dice_turn_statistics.turn_nb_roll
        self._player_total_nb_full_roll[player_index] += dice_turn_statistics.turn_nb_full_roll
        self._player_total_nb_bonus[player_index] += dice_turn_statistics.turn_nb_bonus

        # End of a turn : update total score or total lost regarding the turn status (lost/win)
        if dice_set.its_lost_roll:
            # It's a lost turn -> update total player lost score
            self._player_total_lost_score[player_index] += dice_set.turn_lost_score
        else:
            # It's a win turn -> update total player score
            self._players_score_list[player_index] += dice_set.turn_score

    def sort_player_index_by_score(self):
        # Generate a sorted by score list of player index [rank 1 player index, Rank 2 player index ... ]
        return sorted(range(len(self)), key=lambda n: self._players_score_list[n], reverse=True)

    def reset_status(self):
        def shuffle_players_order():
            random.shuffle(self._players_names_list)

        # ----<Reset players statistics and shuffle player name list >--------------------------------------------------
        self._players_score_list = [0] * self._nb_players
        self._player_total_nb_roll = [0] * self._nb_players
        self._player_total_nb_full_roll = [0] * self._nb_players
        self._player_total_lost_score = [0] * self._nb_players
        self._player_total_nb_bonus = [0] * self._nb_players

        shuffle_players_order()


# ----------------------< Class handling player level turn >------------------------------------------------------------
# constructor parameters :
#   players_names_list                      List of players name
#   nb_dices                                Total number of dices in the game set (default->DEFAULT_DICES_NB)
#   target_score                            Target score to win (default->DEFAULT_TARGET_SCORE)
#
# getters :
#
#   turn_player_name()                      Current player name
#   turn_player_score()                     Current player total score
#   turn_player_rank()                      Current player rank
#
#   turn_score()                            Current turn score
#   turn_index()                            Current turn index
#
#   there_is_a_winner()                     True if the last roll produced a wining total score
#   can_we_roll_again()                     True if dices to roll remains and last roll scored
#
#   players()                               Players 
#   game_statistics()                       Game statistics 
#   dices_set()                             Dice set 
#
# public methods :
#
#   start_new_turn()                        Initialise for new turn
#   prepare_for_next_player_turn()          Prepare for next turn
#
#   update_status_and_game_statistics()      Update current player global statistics from the result of the turn
#
#   reset_game()
# ----------------------------------------------------------------------------------------------------------------------
class DiceGameModel:
    def __init__(self, players_names_list, nb_dices=DEFAULT_DICES_NB, target_score=DEFAULT_TARGET_SCORE):
        self._players = DiceGamePlayers(players_names_list)
        self._dice_set = DiceGameTurn(nb_dices)
        self._game_statistics = DiceGameStatistics()

        self._target_score = target_score
        self._there_is_a_winner = False

        self._current_player_index = 0
        self._turn_index = 0

    def __str__(self):
        output_str = 'target score: ' + str(self._target_score)
        output_str += ', current turn #' + str(self._turn_index)
        output_str += ', there is a winner : ' + str(self._there_is_a_winner)
        output_str += ', current player #' + str(self._current_player_index) + '\n'
        output_str += 'dices status :\n' + str(self._dice_set)
        output_str += 'players status :\n' + str(self._players)
        output_str += 'game statistics :\n' + str(self._game_statistics)
        return output_str

    @property
    def turn_player_name(self):
        return self._players.player_name(self._current_player_index)

    @property
    def turn_player_score(self):
        return self._players.player_score(self._current_player_index)

    @property
    def turn_player_rank(self):
        return self._players.player_rank(self._current_player_index)

    @property
    def turn_score(self):
        return self._dice_set.turn_score

    @property
    def turn_index(self):
        return self._turn_index

    @property
    def players(self):
        return self._players

    @property
    def game_statistics(self):
        return self._game_statistics

    @property
    def dices_set(self):
        return self._dice_set

    @property
    def there_is_a_winner(self):
        return self._there_is_a_winner

    @property
    def can_we_roll_again(self):
        # if it's a fail roll -> finish player turn
        if self._dice_set.its_lost_roll:
            return False

        # if it's a game winning roll -> finish game
        if (self.turn_player_score + self.turn_score) >= self._target_score:
            self._there_is_a_winner = True
            return False

        # It's not the end of the game or of the turn -> player can choose to continue turn or to mark
        return True

    def start_new_turn(self):
        if self._current_player_index == 0:
            self._turn_index += 1

    def update_status_and_game_statistics(self):
        # ----<End of a player turn :  statistics update>---------------------------------------------------------------
        self._players.update_player_statistics(self._current_player_index, self._dice_set)
        self._game_statistics.update_game_statistics(self._current_player_index, self._dice_set)

    def prepare_for_next_player_turn(self):
        self._dice_set.prepare_for_next_turn()

        self._current_player_index += 1
        self._current_player_index %= len(self._players)

    def reset_game(self):
        self._players.reset_status()
        self._game_statistics.reset_statistics()
        self._current_player_index = 0
        self._turn_index = 0
        self._there_is_a_winner = False


# ----------------------< Class handling dice game view >---------------------------------------------------------------
# static methods :
#   print_turn_start_status                 View turn level player status
#       (dice_game_model, verbose)
#   print_roll_status                       View last roll status (Score, dices ...)
#       (dice_game_model, verbose)
#   print_lost_turn_message                 Message for lost turn
#       (dice_game_model, verbose)
#   print_win_turn_message                  Message for win turn
#       (dice_game_model, verbose)
#   print_turn_final_players_status         Message at the end of a player turn
#       (dice_game_model, verbose)
#   print_final_status                      View the global status of all the players at the end of the game
#       (dice_game_model, verbose)
#
# verbose is a boolean parameter to turn of display if False
# ----------------------------------------------------------------------------------------------------------------------
class DiceGameView:
    @staticmethod
    def print_turn_start_status(dice_game_model, verbose):
        if verbose:
            output_str = '\nturn #' + str(dice_game_model.turn_index)
            output_str += '--> ' + str(dice_game_model.turn_player_name)
            output_str += ' rank #' + str(dice_game_model.turn_player_rank)
            output_str += ', score ' + str(dice_game_model.turn_player_score)
            print(output_str)

    @staticmethod
    def print_roll_status(dice_game_model, verbose):
        if verbose:
            dice_turn = dice_game_model.dices_set
            output_str = 'roll #' + str(dice_turn.turn_statistics.turn_nb_roll) + ' : '
            output_str += str(dice_turn.nb_scoring_dices) + ' scoring dices '
            output_str += str(dice_turn.scoring_dices_list) + ' '
            output_str += 'scoring ' + str(dice_turn.roll_score) + ', '
            output_str += 'potential total turn score ' + str(dice_turn.turn_score) + ', '
            output_str += 'remaining dice to roll : ' + str(dice_turn.nb_dices_to_roll)
            print(output_str)

    @staticmethod
    def print_lost_turn_message(dice_game_model, verbose):
        if verbose:
            dice_turn = dice_game_model.dices_set
            output_str = 'you lose this turn and a potential to score '
            output_str += str(dice_turn.turn_lost_score) + ' pts'
            print(output_str)

    @staticmethod
    def print_win_turn_message(dice_game_model, verbose):
        if verbose:
            dice_turn = dice_game_model.dices_set
            output_str = 'you win this turn, scoring '
            output_str += str(dice_turn.turn_score) + ' pts'
            print(output_str)

    @staticmethod
    def print_turn_final_players_status(dice_game_model, verbose):
        if verbose:
            player = dice_game_model.players
            output_str = '\ntotal score : '
            for player_index in player.sort_player_index_by_score():
                output_str += str(player.player_name(player_index)) + '--> '
                output_str += str(player.player_score(player_index)) + ' '
            print(output_str, '\n')

    @staticmethod
    def print_final_status(dice_game_model, verbose):
        if verbose:
            players = dice_game_model.players
            statistics = dice_game_model.game_statistics

            print('Game in', dice_game_model.turn_index, 'turns')
            for player_index in players.sort_player_index_by_score():

                output_str = players.player_name(player_index)

                if player_index == players.index_of_player_with_best_score:
                    output_str += ' win ! '
                else:
                    output_str += ' lose ! '

                best_score = players.player_status(player_index)
                output_str += ' scoring ' + str(best_score['score'])
                output_str += ' in ' + str(best_score['nb_roll']) + ' roll'
                output_str += ' with ' + str(best_score['nb_full_roll']) + ' full roll,'
                output_str += ' ' + str(best_score['nb_bonus']) + ' bonus'
                output_str += ' and ' + str(best_score['total_lost_score']) + ' potential points lost'
                print(output_str)

            output_str = '\nMax turn scoring : '
            output_str += players.player_name(statistics.max_turn_scoring['player_index'])
            output_str += ' with ' + str(statistics.max_turn_scoring['value'])
            output_str += '\nLongest turn : '
            output_str += players.player_name(statistics.longest_turn['player_index'])
            output_str += ' with ' + str(statistics.longest_turn['value']) + ' roll'
            output_str += '\nMax turn loss : '
            output_str += players.player_name(statistics.max_turn_loss['player_index'])
            output_str += ' with ' + str(statistics.max_turn_loss['value']) + '\n'
            output_str += '\nMean scoring turn : ' + '{:.2f}'.format(statistics.mean_scoring_turn)
            output_str += ' (' + str(statistics.nb_scoring_turn) + ' turns)'
            output_str += '\nMean non scoring turn : ' + '{:.2f}'.format(statistics.mean_non_scoring_turn)
            output_str += ' (' + str(statistics.nb_non_scoring_turn) + ' turns)'

            print(output_str)


# ----------------------< Class handling full dice game >---------------------------------------------------------------
# constructor parameters :
#   players_names_list                      List of players name
#   nb_dices                                Total number of dices in the game set (default->DEFAULT_DICES_NB)
#   target_score                            Target score to win (default->DEFAULT_TARGET_SCORE)
#
#   verbose                                 Verbose mode if parameters is True (default->True)
#   interactive                                 - User choose to mark interactively if True
#                                               - Algorithmic choice to mark if False
#
#   choice_critter_value                    For non-interactive game (default->0):
#                                              - if == 0 : random 50/50 choice to mark or not
#                                              - if > 0  : mark if turn score >= choice_critter_value
#                                              - if < 0  : mark if number of dice to roll < abs(choice_critter_value)
#
# public methods :
#   run_full_game()                          Run a full dice game
# ----------------------------------------------------------------------------------------------------------------------
class DiceGameController:
    def __init__(self, players_names_list, nb_dices=DEFAULT_DICES_NB, target_score=DEFAULT_TARGET_SCORE, verbose=True,
                 interactive=True, choice_critter_value=0):

        self._dice_game_view = DiceGameView()
        self._dice_game_model = DiceGameModel(players_names_list, nb_dices, target_score)
        self._verbose = verbose

        self._interactive = interactive
        self._choice_critter_value = choice_critter_value

    def __str__(self):
        output_str = 'verbose mode : ' + str(self._verbose)
        output_str += ', interactive mode : ' + str(self._interactive)
        output_str += ', turn target score : ' + str(self._choice_critter_value) + '\n'
        output_str += str(self._dice_game_model)
        return output_str

    @property
    def get_model(self):
        return self._dice_game_model

    def run_full_game(self):

        def manage_player_turn():
            def player_choose_to_mark():
                # For scoring roll : choice to mark or to roll again
                #   if interactive mode : ask the player to choice.
                #   if non interactive mode, 3 algorithms :
                #       - Random (50/50) choice             (_choice_critter_value == 0)
                #       - Turn score threshold              (_choice_critter_value > 0)
                #       - Remaining dice to roll threshold  (_choice_critter_value < 0)

                if self._interactive:
                    # Interactive : player make the choice
                    return input('roll dices ? [y/n] ') == 'n'
                elif self._choice_critter_value == 0:
                    # Random choice (50/50)
                    return random.randint(1, 1000) % 2 == 0
                elif self._choice_critter_value > 0:
                    # Choice based on the turn score level threshold
                    turn_score = self._dice_game_model.turn_score
                    return turn_score >= self._choice_critter_value
                else:
                    # Choice based on the remaining dice to roll threshold
                    nb_dices_to_roll = self._dice_game_model.dices_set.nb_dices_to_roll
                    return nb_dices_to_roll < abs(self._choice_critter_value)

            # ----<Player turn>-----------------------------------------------------------------------------------------

            model = self._dice_game_model
            view = self._dice_game_view

            model.start_new_turn()
            view.print_turn_start_status(model, self._verbose)

            # Until : roll fail | game winning roll | player choice to mark
            roll_again = True
            while roll_again:
                # Roll remaining dices and count score
                model.dices_set.roll_dices_and_count_roll_score()
                view.print_roll_status(model, self._verbose)

                if model.can_we_roll_again:
                    # If no fail and no game wining -> we can roll again
                    if player_choose_to_mark():
                        # it's a scoring roll -> end turn
                        view.print_win_turn_message(model, self._verbose)
                        roll_again = False
                elif model.there_is_a_winner:
                    # it's a game winning roll -> end turn
                    roll_again = False
                else:
                    # it's a lost roll -> end turn
                    view.print_lost_turn_message(model, self._verbose)
                    roll_again = False

            # End of a turn management
            model.update_status_and_game_statistics()
            view.print_turn_final_players_status(model, self._verbose)
            model.prepare_for_next_player_turn()

        # ----<Handle full game>----------------------------------------------------------------------------------------
        model = self._dice_game_model
        view = self._dice_game_view

        model.reset_game()
        while not model.there_is_a_winner:
            manage_player_turn()

        view.print_final_status(self._dice_game_model, self._verbose)


# ----------------------< Class handling game stats >---------------------------------------------------------------
# constructor parameters :
#   nb_dice                                     List of players name
#   nb_turn                                     Total number of dices in the game set (default->DEFAULT_DICES_NB)
#   interval                                    Target score to win (default->DEFAULT_TARGET_SCORE)
#
# public methods :
#
#   launch_analyse()                             Launch nb_turn turn and update the stats
#   print_occurrence_distribution()              Print the occurrence dict
# ----------------------------------------------------------------------------------------------------------------------
class DiceGameStatisticsAnalyse:
    def __init__(self, nb_turn, interval, nb_dice=DEFAULT_DICES_NB):
        self._nb_dice = nb_dice
        self._nb_turn = nb_turn
        self._interval = interval

        self._dice_game_turn = DiceGameTurn(nb_dice)

        self._max_turn_scoring = 0
        self._mean_scoring = 0
        self._max_nb_roll = 0
        self._max_bonus = 0
        self._score_distribution = OccurrenceDistribution(interval)

    def __str__(self):
        output_str = 'Score max : ' + str(self._max_turn_scoring)
        output_str += '\nScore moyen : ' + str(self._mean_scoring)
        output_str += '\nPlus grand nombre de lancer : ' + str(self._max_nb_roll)
        output_str += '\nPlus grand nombre de bonus : ' + str(self._max_bonus)
        self.pretty_print_occurrence_distribution()
        return output_str

    def launch_analyse(self):
        def play_until_fail():
            self._dice_game_turn.roll_dices_and_count_roll_score()
            while self._dice_game_turn.roll_score != 0:
                self._dice_game_turn.roll_dices_and_count_roll_score()

        turn_index = 0
        while turn_index < self._nb_turn:

            play_until_fail()

            turn_score = self._dice_game_turn.turn_lost_score

            # Update our attributes depending on the score and bonus number made
            if turn_score > self._max_turn_scoring:
                self._max_turn_scoring = turn_score

            if self._dice_game_turn.turn_statistics.turn_nb_roll > self._max_nb_roll:
                self._max_nb_roll = self._dice_game_turn.turn_statistics.turn_nb_roll

            if self._dice_game_turn.turn_statistics.turn_nb_bonus > self._max_bonus:
                self._max_bonus = self._dice_game_turn.turn_statistics.turn_nb_bonus

            self._mean_scoring += turn_score
            self._score_distribution.push(turn_score)

            turn_index += 1

            # Reset all the turn's parameters to 0
            self._dice_game_turn.prepare_for_next_turn()

        self._mean_scoring /= self._nb_turn

    def pretty_print_occurrence_distribution(self):
        pretty_occurrence_distribution = dict(sorted(self._score_distribution._occurrence_distribution.items()))

        print('Tableau d\'occurences : ')
        for key in pretty_occurrence_distribution:
            if key == 0:
                print('{0 :', end='')
            else:
                interval_from = (key - 1) * self._score_distribution.interval + 1
                interval_to = key * self._score_distribution.interval
                print('{', interval_from, '->', interval_to, " :", end='')

            print(' ', pretty_occurrence_distribution[key] / self._nb_turn, '},', end='')

        print('\n')


# ----------------------< Class handling game stats >---------------------------------------------------------------
# constructor parameters :
#   nb_dice                                     List of players name
#   nb_turn                                     Total number of dices in the game set (default->DEFAULT_DICES_NB)
#   interval                                    Target score to win (default->DEFAULT_TARGET_SCORE)
#
# public methods :
#
#   launch_analyse()                             Launch nb_turn turn and update the stats
#   print_occurrence_distribution()              Print the occurrence dict
# ----------------------------------------------------------------------------------------------------------------------
class DiceGameDistributionAnalyse:
    def __init__(self, nb_turn, interval, nb_dice=DEFAULT_DICES_NB):
        self._nb_dice = nb_dice
        self._nb_turn = nb_turn
        self._interval = interval

        self._dice_game_turn = DiceGameTurn(nb_dice)

        self._roll_score_distribution = OccurrenceDistribution(interval)
        self._turn_score_distribution = OccurrenceDistribution(interval)
        self._turn_nb_roll_distribution = OccurrenceDistribution(1)
        self._turn_nb_full_roll_distribution = OccurrenceDistribution(1)
        self._turn_nb_bonus_distribution = OccurrenceDistribution(1)
        self._turn_nb_dices_fail_distribution = OccurrenceDistribution(1)
        self._turn_nb_dice_to_roll_distribution = OccurrenceDistribution(1)

    @property
    def nb_turn(self):
        return self._nb_turn

    @property
    def roll_score_distribution(self):
        return self._roll_score_distribution

    @property
    def turn_score_distribution(self):
        return self._turn_score_distribution

    @property
    def turn_nb_roll_distribution(self):
        return self._turn_nb_roll_distribution

    @property
    def turn_nb_full_roll_distribution(self):
        return self._turn_nb_full_roll_distribution

    @property
    def turn_nb_bonus_distribution(self):
        return self._turn_nb_bonus_distribution

    @property
    def turn_nb_dices_fail_distribution(self):
        return self._turn_nb_dices_fail_distribution

    @property
    def turn_nb_dice_to_roll_distribution(self):
        return self._turn_nb_dice_to_roll_distribution

    def launch_analyse(self):
        def play_until_fail():
            nb_dice_to_roll = self._dice_game_turn.nb_dices_to_roll
            self._turn_nb_dice_to_roll_distribution.push(nb_dice_to_roll)

            self._dice_game_turn.roll_dices_and_count_roll_score()

            roll_score = self._dice_game_turn.roll_score
            self._roll_score_distribution.push(roll_score)

            while self._dice_game_turn.roll_score != 0:
                nb_dice_to_roll = self._dice_game_turn.nb_dices_to_roll
                self._turn_nb_dice_to_roll_distribution.push(nb_dice_to_roll)

                self._dice_game_turn.roll_dices_and_count_roll_score()

                # Case it's a lost roll, we push the nb_dice of this roll
                if self._dice_game_turn.roll_score == 0:
                    self._turn_nb_dices_fail_distribution.push(nb_dice_to_roll)

                roll_score = self._dice_game_turn.roll_score
                self._roll_score_distribution.push(roll_score)

        turn_index = 0
        while turn_index < self._nb_turn:
            play_until_fail()

            turn_score = self._dice_game_turn.turn_lost_score
            turn_nb_roll = self._dice_game_turn.turn_statistics.turn_nb_roll
            turn_nb_full_roll = 0
            turn_nb_bonus = self._dice_game_turn.turn_statistics.turn_nb_bonus

            self._turn_score_distribution.push(turn_score)
            self._turn_nb_roll_distribution.push(turn_nb_roll)
            self._turn_nb_full_roll_distribution.push(turn_nb_full_roll)
            self._turn_nb_bonus_distribution.push(turn_nb_bonus)

            turn_index += 1

            # Reset all the turn's parameters to 0
            self._dice_game_turn.prepare_for_next_turn()


# ----------------------< Class generating excel file >---------------------------------------------------------------
# constructor parameters :
#   statistics                                   DiceGameDistributionAnalyse instance
#
# public methods :
#
#   export_excel()                               Create an excel with all the game stats
# ----------------------------------------------------------------------------------------------------------------------
class ExcelStatsGenerator:
    def __init__(self, distribution_statistics):
        self._distribution_statistics = distribution_statistics

    def export_excel(self):
        statistics = pd.DataFrame(
            {
                '': ['Nb Turns',
                     'Roll Score',
                     'Turn Score',
                     'Turn Nb Roll',
                     'Turn Nb Full Roll',
                     'Turn Nb Bonus',
                     'Roll Nb Dice Fail Roll',
                     'Roll Nb Dice To Roll'],

                'Max': [self._distribution_statistics.nb_turn,
                        self._distribution_statistics.roll_score_distribution.get_max(),
                        self._distribution_statistics.turn_score_distribution.get_max(),
                        self._distribution_statistics.turn_nb_roll_distribution.get_max(),
                        self._distribution_statistics.turn_nb_full_roll_distribution.get_max(),
                        self._distribution_statistics.turn_nb_bonus_distribution.get_max(),
                        self._distribution_statistics.turn_nb_dices_fail_distribution.get_max(),
                        self._distribution_statistics.turn_nb_dice_to_roll_distribution.get_max()],

                'Mean': ['',
                         self._distribution_statistics.roll_score_distribution.get_mean(),
                         self._distribution_statistics.turn_score_distribution.get_mean(),
                         self._distribution_statistics.turn_nb_roll_distribution.get_mean(),
                         self._distribution_statistics.turn_nb_full_roll_distribution.get_mean(),
                         self._distribution_statistics.turn_nb_bonus_distribution.get_mean(),
                         self._distribution_statistics.turn_nb_dices_fail_distribution.get_mean(),
                         self._distribution_statistics.turn_nb_dice_to_roll_distribution.get_mean()],
            })

        df = pd.DataFrame(statistics, columns=['', 'Max', 'Mean'])

        df.to_excel(r'C:\Users\thoma\Desktop\export_dataframe.xlsx', index=False, header=True)


# ----------------------< Class defining a new struct  >---------------------------------------------------------------
# constructor parameters :
#   interval                                     Interval of the distribution
#   occurrence_distribution                      The dictionary used to store the score occurrence
#
# getters :
#
#   occurrence_distribution()                    Occurrence Distribution
#   interval()                                   Interval
#
# public methods :
#
#   push()                                      Push a new element in the dict
# ----------------------------------------------------------------------------------------------------------------------
class OccurrenceDistribution:
    def __init__(self, interval):
        self._interval = interval
        self._occurrence_distribution = dict()

    def __str__(self):
        return str(self._occurrence_distribution)

    @property
    def occurrence_distribution(self):
        return self._occurrence_distribution

    @property
    def interval(self):
        return self._interval

    def push(self, value):
        value_occurrence_index = math.ceil(value / self._interval)

        if value_occurrence_index in self._occurrence_distribution:
            self._occurrence_distribution[value_occurrence_index] += 1
        else:
            self._occurrence_distribution[value_occurrence_index] = 1

    def get_max(self):
        sorted_occurrence_distribution = dict(sorted(self._occurrence_distribution.items()))
        if len(sorted_occurrence_distribution.keys()) > 0:
            max_key = list(sorted_occurrence_distribution.keys())[-1]
            max_key_occurrence = sorted_occurrence_distribution.get(max_key)
            return max_key * self._interval
        else:
            return 0

    def get_mean(self):
        occurrence_value_sum = 0
        occurrence_count = 0
        for occurrence in self._occurrence_distribution:
            occurrence_value_sum += self._occurrence_distribution[occurrence] * self._interval * occurrence
            occurrence_count += self._occurrence_distribution[occurrence]

        if occurrence_value_sum != 0 and occurrence_count != 0:
            return occurrence_value_sum / occurrence_count
        else:
            return 0


game_target_score = 5000
game_players_names_list = ['Stéphane', 'Romain', 'François', 'Isabelle', 'Christophe', 'Laurent', "Sylvie"]

#       - Random (50/50) choice             (_choice_critter_value == 0)
#       - Turn score threshold              (_choice_critter_value > 0)
#       - Remaining dice to roll threshold  (_choice_critter_value < 0)
game_choice_critter_value = 0

# dice_controller = DiceGameController(
#   game_players_names_list,
#   nb_dices=5,
#   target_score=game_target_score,
#   verbose=True, interactive=False,
#   choice_critter_value=game_choice_critter_value)

# dice_controller.run_full_game()

nb_turn = 10000000
dice_distribution_statistics = DiceGameDistributionAnalyse(nb_turn, 50, 5)

dice_distribution_statistics.launch_analyse()

excel = ExcelStatsGenerator(dice_distribution_statistics)
excel.export_excel()
