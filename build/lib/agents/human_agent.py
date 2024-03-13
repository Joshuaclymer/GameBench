from api.classes import Agent, AvailableActions, Action

class HumanAgent(Agent):
    agent_type_id = "human"
    def take_action(self, rules, observation, available_actions: AvailableActions):
        print(observation.text)
        if observation.image:
            observation.image.show()
        print(available_actions.predefined)
        #print(available_actions.openended)
        action = input("Enter action: ") 
        openended_list = available_actions.openended
        predefined_list = available_actions.predefined
        if predefined_list and action in [a.action_id for a in predefined_list]:
            return Action(action_id=action)
        elif openended_list and action in [a.action_id for a in openended_list]:
            return Action(action_id=action, openended_response=input("Enter open-ended response: "))
        