import os
import sys
import time
import pygame
from pygame.locals import MOUSEBUTTONDOWN, QUIT
import torch

from gymenv import MancalaEnv, InvalidCoordinatesError
from deepq import MancalaAgentModel

state = 0

model_fn = sys.argv[1] if len(sys.argv) > 1 else os.path.join("save", "policy")
MODEL_SAVE_DIR = 'save'

if torch.cuda.is_available():

    # GPU Config

    device = torch.device('cuda')

else:
    # CPU Config

    device = torch.device('cpu')


os.environ['SDL_VIDEO_WINDOW_POS'] = '%i,%i' % (30, 100)
os.environ['SDL_VIDEO_CENTERED'] = '0'

''' 
TODO: Load the trained policy net
policy_net = torch.load(os.path.join(os.getcwd(), model_fn), map_location='cpu')
policy_net.eval()
'''

policy_net = MancalaAgentModel()

env = MancalaEnv(has_screen=True)


state = env.reset()

done = False

reward_earned = 0

env = MancalaEnv(has_screen=True)

state = env.reset()

clock = pygame.time.Clock()


def debug_print(player, initial_state, env, action, reward):

    format_state = lambda s: "[{}] {} [{}] {}".format(s[0], s[1:7], s[7], s[8:14])

    print("{} action: {}\nState before:{}\nState after: {}\nReward: {}\n".format(
        player,
        action,
        format_state(initial_state),
        format_state(env.state),
        reward
    ))


def handle_game_end():
    if done:
        print("Game has ended!\nFinal scores: P1 {}, P2 {}".format(
            env.get_player_score(1),
            env.get_player_score(2)
              ))
        env.reset()


action_mask = torch.ones(6, dtype=torch.float).unsqueeze(0)

while 1:

    env.render()

    if env.get_active_player() == 2:  # AI

        # Create action mask

        action_mask = torch.empty(6, dtype=torch.float).fill_(float("inf"),)
        valid_actions = env.get_valid_actions()
        action_mask[tuple(valid_actions)] = 0.
        action_mask = action_mask.unsqueeze(0)

        input_t = torch.FloatTensor(state[2]).unsqueeze(0).to(device)

        values = policy_net(input_t, action_mask).to(device)

        action = torch.argmax(values)

        time.sleep(0.25)
        env.indicate_action_on_screen(action)
        time.sleep(0.75)

        initial_state = env.state.copy()
        state, reward, done, info = env.step(action)

        debug_print("AI", initial_state, env, action, reward)

        if done:
            handle_game_end()

    else:
        for event in pygame.event.get():

            if event.type == QUIT:
                pygame.quit()
            elif event.type == MOUSEBUTTONDOWN:

                try:
                    action = env.get_action_from_coords(event.pos)
                except InvalidCoordinatesError:
                    continue

                valid_actions = env.get_valid_actions()

                if action in valid_actions[0]:
                    initial_state = env.state.copy()
                    state, reward, done, info = env.step(action)
                    debug_print("Human", initial_state, env, action, reward)

                if done:
                    handle_game_end()

