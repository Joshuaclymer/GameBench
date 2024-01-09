from api.classes import Agent, AvailableActions, Action

class HumanAgent(Agent):
    agent_type_id = "human"
    def take_action(self, observation, available_actions: AvailableActions):
        print(observation.text)
        print(available_actions.predefined)
        print(available_actions.openended)
        action = input("Enter action: ")
        openended_list = list(available_actions.openended.keys())
        predefined_list = list(available_actions.predefined.keys())

        if action in predefined_list:
            return Action(action_id=available_actions.predefined[action].action_id)
        elif action in openended_list:
            return Action(action_id=available_actions.openended[action].action_id, openended_response=[input("Enter open-ended response: ")])
        
        print("NOT IN EITHER LIST")