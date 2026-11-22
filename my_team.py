# my_team.py
# ---------------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html

import importlib
import importlib.util
import os
import sys
import zlib

from contest.capture_agents import CaptureAgent


###############################
# Loading the shared package  #
###############################

_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
_SHARED_DIR = os.path.join(_AGENT_DIR, 'shared')
_FOLDER_HASH = zlib.crc32(_SHARED_DIR.encode('utf-8')) & 0xFFFFFFFF
_SHARED_PACKAGE = 'setup1_shared_%08x' % _FOLDER_HASH


def _load_component(module_name):
    """Import one component module of ./shared under a package name unique to this folder."""
    if _SHARED_PACKAGE not in sys.modules:
        init_file = os.path.join(_SHARED_DIR, '__init__.py')
        spec = importlib.util.spec_from_file_location(
            _SHARED_PACKAGE, init_file, submodule_search_locations=[_SHARED_DIR])
        package = importlib.util.module_from_spec(spec)
        sys.modules[_SHARED_PACKAGE] = package
        spec.loader.exec_module(package)
    full_name = _SHARED_PACKAGE + '.' + module_name
    return importlib.import_module(full_name)


match_start = _load_component('c1_match_start')
startup = _load_component('c3_startup')
observation = _load_component('c4_observation')
team_memory = _load_component('c5_team_memory')
mode_rules = _load_component('c6_mode_rules')
action_picker = _load_component('c9_action_picker')


#################
# Team creation #
#################

def create_team(first_index, second_index, is_red,
                first='AttackerAgent', second='DefenderAgent', num_training=0,
                params_path=None, debug=None, **unused_options):
    """Match start: load the params and both agents."""
    team = match_start.create_team_context(first_index, second_index, is_red, params_path, debug)
    first_class = AGENT_CLASSES[first]
    second_class = AGENT_CLASSES[second]
    first_agent = first_class(first_index, team)
    second_agent = second_class(second_index, team)
    return [first_agent, second_agent]


##########
# Agents #
##########

class Setup1Agent(CaptureAgent):
    """Reflex agent: scores every legal move with the weights of its current mode."""

    role = mode_rules.ATTACKER  # which mode rules the agent follows: attacker or defender

    def __init__(self, index, team, time_for_computing=.1):
        super().__init__(index, time_for_computing)
        self.team = team        # state shared with the teammate: params, map facts and memory (TeamContext)

    # Startup: once per game.
    def register_initial_state(self, game_state):
        super().register_initial_state(game_state)
        team = self.team
        is_first_agent = self.index == min(team.indices)
        if is_first_agent or team.map_info is None:
            try:
                team.map_info = startup.build_map_info(game_state, self.red, self.get_maze_distance)
                team.memory = team_memory.TeamMemory()
            except Exception:
                if team.debug:
                    raise
                team.map_info = None
                team.memory = None

    # Per-turn loop: observation -> team memory -> mode rules -> features, scorer, picker.
    def choose_action(self, game_state):
        team = self.team
        try:
            turn = observation.observe_turn(self, game_state, team)
            team_memory.update_team_memory(team.memory, turn, team.map_info, self.get_maze_distance)
            mode = mode_rules.choose_mode(self.role, turn, team.memory, team.params)
            action = action_picker.pick_action(self, game_state, mode, turn, team)
            return action
        except Exception:
            if team.debug:
                raise
            return action_picker.fallback_action(game_state, self.index)


class AttackerAgent(Setup1Agent):
    """Eats enemy food and banks it. Defends when conditions are met."""

    role = mode_rules.ATTACKER


class DefenderAgent(Setup1Agent):
    """Guards our side. Attacks when conditions are met."""

    role = mode_rules.DEFENDER


AGENT_CLASSES = {'AttackerAgent': AttackerAgent, 'DefenderAgent': DefenderAgent}
