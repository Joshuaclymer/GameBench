from .agent import ReasoningViaPlanning

# To-do:
# * add support for openeded actions
# * add support for image observations
# * maybe caching results between calls to take_action? It's possible the agent
#   will accurately predict a future state, in which case it shouldn't
#   recalculate rewards and all.
# * maybe give unique prefix for each prompt that demonstrates how to answer
#   that specific prompt, rather than one prefix that tries to do it all.
