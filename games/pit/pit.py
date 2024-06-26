from dataclasses import dataclass, field
from typing import List, Tuple, Dict
import random
import uuid
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules


@dataclass
class Commodity:
    name: str
    value: float


@dataclass
class TradeProposal:
    proposer_id: int
    offered_commodities: Dict[str, int]
    status: str = "pending"
    trade_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class PitGame(Game):
    rules: Rules = Rules(
        title="Pit",
        summary="""Pit is a commodity trading game where players engage in trading to accumulate points and emerge as the winner.
        The game involves commodity cards representing various goods, with each card holding a specific point value.
        Players shout out their trade offers, attempting to negotiate deals with others to acquire valuable commodities.
        Additionally, Bull and Bear cards periodically influence the market conditions, either boosting or decreasing commodity values.
        The game continues with trading phases, market fluctuations, and scoring until a player or team reaches the agreed-upon point total,
        declaring them the victor in the spirited world of commodity trading.""",
        additional_details=None,
    )
    id: str = "pit"
    agent_virtual_players: Dict[int, List[int]] = field(default_factory=dict)
    virtual_player_hands: Dict[int, Dict[str, int]] = field(default_factory=dict)
    virtual_player_scores: Dict[int, float] = field(default_factory=dict)
    agents: List[Agent] = field(default_factory=list)
    pending_trades: List[TradeProposal] = field(default_factory=list)
    last_trade_outcome: str = ""

    def __post_init__(self):
        self.commodities = [
            Commodity("Barley", 85.0),
            Commodity("Corn", 75.0),
            Commodity("Soyabeans", 55.0),
            Commodity("Wheat", 100.0),
            Commodity("Bull", 0.0),
            Commodity("Bear", 0.0),
        ]
        self.scores = []
        self.round_number = 0
        self.pending_trades = []
        self.max_possible = 6  # actual value: 9
        self.winning_score = 500  # actual value: 500

    def setup_virtual_players(self):
        virtual_player_id = 0
        for agent in self.agents:
            self.agent_virtual_players[agent.agent_id] = [
                virtual_player_id,
                virtual_player_id + 1,
            ]
            for vp_id in self.agent_virtual_players[agent.agent_id]:
                self.virtual_player_scores[vp_id] = 0.0
                self.virtual_player_hands[vp_id] = {
                    commodity.name: 0 for commodity in self.commodities
                }
            virtual_player_id += 2

    def shuffle_cards(self):
        deck = [
            commodity.name for commodity in self.commodities[:-2] for _ in range(9)
        ] + ["Bull", "Bear"]

        random.shuffle(deck)

        for vp_id in self.virtual_player_hands.keys():
            self.virtual_player_hands[vp_id] = {
                commodity.name: 0 for commodity in self.commodities
            }

        vp_ids = list(self.virtual_player_hands.keys())
        for card in deck:
            vp_id = vp_ids.pop(0)
            self.virtual_player_hands[vp_id][card] += 1
            vp_ids.append(vp_id)

    def init_game(
        self,
        agent_1_cls: Agent,
        agent_2_cls: Agent,
    ):
        agent_1 = agent_1_cls(
            team_id=0,
            agent_id=1,
            agent_type_id=agent_1_cls.agent_type_id,
            **self.agent_1_kwargs,
        )
        agent_2 = agent_2_cls(
            team_id=1,
            agent_id=2,
            agent_type_id=agent_2_cls.agent_type_id,
            **self.agent_2_kwargs,
        )
        self.agents = [agent_1, agent_2]
        self.scores = [0.0] * len(self.agents)
        self.setup_virtual_players()

    def propose_trade(self, proposer_id, offered_commodities):
        proposer_hand = self.virtual_player_hands[
            self.agent_virtual_players[proposer_id][0]
        ]

        if all(
            proposer_hand[commodity] >= quantity
            for commodity, quantity in offered_commodities.items()
        ):
            if self.show_state:
                print(
                    f"Proposer (Agent {proposer_id}) Hand before trade:", proposer_hand
                )
            self.pending_trades = [
                proposal
                for proposal in self.pending_trades
                if proposal.proposer_id != proposer_id
            ]
            proposal = TradeProposal(proposer_id, offered_commodities)
            self.pending_trades.append(proposal)
            trade_details = " + ".join(
                f"{quantity} {commodity}"
                for commodity, quantity in offered_commodities.items()
            )
            if self.show_state:
                print(f"Agent {proposer_id} proposed a trade offering {trade_details}.")
        else:
            if self.show_state:
                print(f"Agent {proposer_id} does not have enough commodities to trade.")

    def respond_to_trade(self, responder_id, trade_id, accept, response_commodities):
        proposal = next(
            (p for p in self.pending_trades if p.trade_id == trade_id), None
        )

        if proposal and accept:
            responder_hand = self.virtual_player_hands[
                self.agent_virtual_players[responder_id][0]
            ]

            has_enough_of_each_commodity = all(
                responder_hand.get(commodity, 0) >= quantity
                for commodity, quantity in response_commodities.items()
            )

            if has_enough_of_each_commodity:
                proposal.status = "accepted"
                self.execute_trade(proposal, responder_id, response_commodities)
            else:
                if self.show_state:
                    print(
                        f"Agent {responder_id} does not have enough commodities to respond to the trade."
                    )

            self.pending_trades = [
                p for p in self.pending_trades if p.trade_id != trade_id
            ]
        elif proposal:
            if self.show_state:
                print(f"Agent {responder_id} rejects trade proposal {trade_id}.")
            self.pending_trades = [
                p for p in self.pending_trades if p.trade_id != trade_id
            ]

    def execute_trade(self, proposal, responding_agent_id, response_commodities):
        if proposal.status == "accepted":
            proposer_vp_ids = self.agent_virtual_players[proposal.proposer_id]
            responder_vp_ids = self.agent_virtual_players[responding_agent_id]

            proposer_trade_details = " + ".join(
                f"{quantity} {commodity}"
                for commodity, quantity in proposal.offered_commodities.items()
            )

            for vp_id in proposer_vp_ids:
                for commodity, quantity in proposal.offered_commodities.items():
                    self.virtual_player_hands[vp_id][commodity] -= quantity

            for vp_id in responder_vp_ids:
                for commodity, quantity in proposal.offered_commodities.items():
                    self.virtual_player_hands[vp_id][commodity] += quantity

            responder_trade_details = " + ".join(
                f"{quantity} {commodity}"
                for commodity, quantity in response_commodities.items()
            )

            for commodity, quantity in response_commodities.items():
                for vp_id in responder_vp_ids:
                    self.virtual_player_hands[vp_id][commodity] -= quantity
                for vp_id in proposer_vp_ids:
                    self.virtual_player_hands[vp_id][commodity] += quantity

            if self.show_state:
                print(
                    f"Trade completed: Agent {proposal.proposer_id} offered {proposer_trade_details} and Agent {responding_agent_id} offered back {responder_trade_details}."
                )

            self.last_trade_outcome = f"Trade completed between Agent {proposal.proposer_id} (offered {proposer_trade_details}) and Agent {responding_agent_id} (offered back {responder_trade_details})."
            self.check_corners_update_score()

    def check_corners_update_score(self):
        for vp_id, hand in self.virtual_player_hands.items():
            bull_card = hand.get("Bull", 0)
            bear_card = hand.get("Bear", 0)
            for commodity, count in hand.items():
                is_corner = count == self.max_possible or (
                    count == self.max_possible - 1 and bull_card
                )
                if is_corner:
                    commodity_obj = next(
                        (c for c in self.commodities if c.name == commodity), None
                    )
                    if commodity_obj:
                        score = commodity_obj.value
                        if bull_card and count == self.max_possible - 1:
                            if self.show_state:
                                print(
                                    f"Virtual Player {vp_id} has a Bull Corner on {commodity}."
                                )
                        if bull_card and count == self.max_possible:
                            score *= 2  # Double Bull Corner
                            if self.show_state:
                                print(
                                    f"Virtual Player {vp_id} has a Double Bull Corner on {commodity}."
                                )
                        if bear_card:
                            score -= 20 * bear_card  # Penalty for holding Bear card

                        self.virtual_player_scores[vp_id] += score
                        if self.show_state:
                            print(
                                f"Virtual Player {vp_id} has cornered the market on {commodity}. Score updated."
                            )

                        for agent_id, vp_ids in self.agent_virtual_players.items():
                            if vp_id in vp_ids:
                                self.scores[
                                    self.agents.index(
                                        next(
                                            agent
                                            for agent in self.agents
                                            if agent.agent_id == agent_id
                                        )
                                    )
                                ] = sum(self.virtual_player_scores[vp] for vp in vp_ids)
                                break
                        self.shuffle_cards()

    def get_observation(self, agent: Agent) -> Tuple[Observation, AvailableActions]:
        agent_hand = self.virtual_player_hands[
            self.agent_virtual_players[agent.agent_id][0]
        ]
        hand_description = ", ".join(
            f"{count} x {commodity}"
            for commodity, count in agent_hand.items()
            if count > 0
        )

        available_actions = AvailableActions(
            instructions="Choose commodities and quantities to trade, respond to pending trades, or indicate which commodity you're willing to trade.",
            predefined={},
            openended={},
        )

        for commodity in self.commodities:
            for quantity in range(1, 5):
                action_id = f"Offer_{commodity.name}_{quantity}"
                action_description = f"Offer {quantity} {commodity.name}"
                available_actions.predefined[action_id] = action_description

        pending_trade_descriptions = []
        for i, proposal in enumerate(self.pending_trades, 1):
            if agent.agent_id != proposal.proposer_id and proposal.status == "pending":
                offered_description = ", ".join(
                    f"{quantity} {commodity}"
                    for commodity, quantity in proposal.offered_commodities.items()
                )
                trade_description = f"Trade {i} offers {offered_description}"
                pending_trade_descriptions.append(trade_description)

                for commodity, quantity in agent_hand.items():
                    if quantity > 0:
                        for offer_quantity in range(1, quantity + 1):
                            accept_action_id = (
                                f"Accept_{i}_{commodity}_{offer_quantity}"
                            )
                            available_actions.predefined[accept_action_id] = (
                                f"Accept trade {i}, offering {offer_quantity} {commodity}"
                            )

        observation_text = f"Agent {agent.agent_id}, it's your turn. Your hand: {hand_description}. {' '.join(pending_trade_descriptions)}"
        return Observation(text=observation_text), available_actions

    def update(self, action: Action, available_actions: AvailableActions, agent: Agent):
        if action.action_id not in available_actions.predefined.keys():
            action_id = random.choice(list(available_actions.predefined.keys()))
            action = Action(action_id)

        action_parts = action.action_id.split("_")
        if "Accept" in action.action_id or "Reject" in action.action_id:
            trade_index = int(action_parts[1]) - 1
            proposal = self.pending_trades[trade_index]

            if "Accept" in action.action_id and agent.agent_id != proposal.proposer_id:
                if len(action_parts) >= 4:
                    responding_commodity = action_parts[2]
                    quantity = int(action_parts[3])
                    response_commodities = {responding_commodity: quantity}
                    self.respond_to_trade(
                        agent.agent_id, proposal.trade_id, True, response_commodities
                    )
                else:
                    if self.show_state:
                        print(
                            f"Action ID {action.action_id} does not contain enough information for trade acceptance."
                        )
            elif "Reject" in action.action_id:
                self.respond_to_trade(agent.agent_id, proposal.trade_id, False)

        elif len(action_parts) == 3 and action_parts[0] == "Offer":
            offered_commodity = action_parts[1]
            quantity = int(action_parts[2])
            self.propose_trade(agent.agent_id, {offered_commodity: quantity})

        else:
            if self.show_state:
                print("Invalid action received.")

    def play(self) -> Tuple[float, float]:
        self.shuffle_cards()

        while not self.game_is_over:
            for current_agent in self.agents:
                self.round_number += 1

                observation, available_actions = self.get_observation(current_agent)
                action = current_agent.take_action(
                    self.rules, observation, available_actions, show_state=True
                )

                self.update(action, available_actions, current_agent)
                self.check_corners_update_score()

                if self.show_state:
                    print(f"End of round {self.round_number}. Scores: {self.scores}")

                if any(score >= self.winning_score for score in self.scores):
                    self.game_is_over = True
                    break

        winning_agent_id = self.agents[self.scores.index(max(self.scores))].agent_id
        print(f"Agent {winning_agent_id} won with a score of {max(self.scores)}.")
        total_score = sum(self.scores)
        normalized_scores = [score / total_score for score in self.scores]
        return tuple(normalized_scores)