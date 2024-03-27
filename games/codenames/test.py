


# use 4 HumanAgents to play a game of codenames
from .game import CodenamesGame as Game
from build.lib.agents.human_agent import HumanAgent
from agents.gpt import OpenAITextAgent
from api.classes import Agent
from .config import GameConfig

# create a game config
config = GameConfig()

# create a list of agents
#agents = [HumanAgent(agent_id=1, team_id=1, agent_type_id="agent"), HumanAgent(team_id=1, agent_id=2, agent_type_id="agent"), HumanAgent(team_id=2, agent_id=3, agent_type_id="agent"), HumanAgent(team_id=2, agent_id=4, agent_type_id="agent")]
#agents = [OpenAITextAgent(openai_model="gpt-4-1106-preview",agent_id=1, team_id=1, agent_type_id="agent"), HumanAgent(team_id=1, agent_id=2, agent_type_id="agent"), OpenAITextAgent(openai_model="gpt-4-1106-preview",agent_id=3, team_id=2, agent_type_id="agent"), OpenAITextAgent(openai_model="gpt-4-1106-preview",agent_id=4,team_id=2, agent_type_id="agent")]
agents = [OpenAITextAgent(openai_model="gpt-4-1106-preview",agent_id=1, team_id=1, agent_type_id="agent"), OpenAITextAgent(openai_model="gpt-4-1106-preview",agent_id=2, team_id=1, agent_type_id="agent"), OpenAITextAgent(openai_model="gpt-4-1106-preview",agent_id=3, team_id=2, agent_type_id="agent"), OpenAITextAgent(openai_model="gpt-4-1106-preview",agent_id=4,team_id=2, agent_type_id="agent")]
# create a game

# play the game

for i in range(1):
    game = Game(config=config, agents=agents)
    print(game.play())
