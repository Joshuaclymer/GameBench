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
    offered_commodity: str
    quantity: int
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
        self.max_possible = 9  # actual value: 9
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

    def propose_trade(self, proposer_id, offered_commodity, quantity):
        proposer_hand = self.virtual_player_hands[
            self.agent_virtual_players[proposer_id][0]
        ]

        if proposer_hand[offered_commodity] >= quantity:
            if self.show_state:
                print(
                    f"Proposer (Agent {proposer_id}) Hand before trade:",
                    proposer_hand,
                )
            self.pending_trades = [
                proposal
                for proposal in self.pending_trades
                if proposal.proposer_id != proposer_id
            ]
            proposal = TradeProposal(proposer_id, offered_commodity, quantity)
            self.pending_trades.append(proposal)
            if self.show_state:
                print(
                    f"Agent {proposer_id} proposed a trade offering {quantity} {offered_commodity}."
                )
        else:
            if self.show_state:
                print(
                    f"Agent {proposer_id} does not have enough {offered_commodity} to trade."
                )

    def respond_to_trade(self, responder_id, trade_id, accept, offered_commodity=None):
        proposal = next(
            (p for p in self.pending_trades if p.trade_id == trade_id), None
        )

        if proposal and accept and offered_commodity:
            if self.show_state:
                print(f"Agent {responder_id} accepts trade proposal {trade_id}.")
            proposal.status = "accepted"
            self.execute_trade(proposal, responder_id, offered_commodity)
            self.pending_trades = [
                p for p in self.pending_trades if p.trade_id != trade_id
            ]
        elif proposal:
            if self.show_state:
                print(f"Agent {responder_id} rejects trade proposal {trade_id}.")
            self.pending_trades = [
                p for p in self.pending_trades if p.trade_id != trade_id
            ]

    def execute_trade(self, proposal, responding_agent_id, responding_agent_commodity):
        if proposal.status == "accepted":
            proposer_vp_ids = self.agent_virtual_players[proposal.proposer_id]
            responder_vp_ids = self.agent_virtual_players[responding_agent_id]

            for proposer_vp_id in proposer_vp_ids:
                self.virtual_player_hands[proposer_vp_id][
                    proposal.offered_commodity
                ] -= proposal.quantity
                self.virtual_player_hands[proposer_vp_id][
                    responding_agent_commodity
                ] += proposal.quantity

            for responder_vp_id in responder_vp_ids:
                self.virtual_player_hands[responder_vp_id][
                    responding_agent_commodity
                ] -= proposal.quantity
                self.virtual_player_hands[responder_vp_id][
                    proposal.offered_commodity
                ] += proposal.quantity

            if self.show_state:
                print(
                    f"Trade completed: Agent {proposal.proposer_id} offered {proposal.quantity} {proposal.offered_commodity} and Agent {responding_agent_id} offered back {proposal.quantity} {responding_agent_commodity}."
                )

            self.last_trade_outcome = f"Trade completed between Agent {proposal.proposer_id} and Agent {responding_agent_id}."
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
                for commodity, count in agent_hand.items():
                    if (
                        count >= proposal.quantity
                        and commodity != proposal.offered_commodity
                    ):  # Checking if agent has enough to trade
                        trade_description = f"{i}: Offer {proposal.quantity} {proposal.offered_commodity} for {count} {commodity}"
                        pending_trade_descriptions.append(trade_description)
                        accept_action_id = f"Accept_{i}_{commodity}_{proposal.quantity}"
                        available_actions.predefined[accept_action_id] = (
                            f"Accept trade {i}: Offer your {count} {commodity} for {proposal.quantity} {proposal.offered_commodity}"
                        )
                        reject_action_id = f"Reject_{i}"
                        available_actions.predefined[reject_action_id] = (
                            f"Reject trade {i}"
                        )

        observation_text = f"Agent {agent.agent_id}, it's your turn. Your hand: {hand_description}. {' '.join(pending_trade_descriptions)}"
        return Observation(text=observation_text), available_actions

    def update(self, action: Action, available_actions: AvailableActions, agent: Agent):
        action_parts = action.action_id.split("_")

        if "Accept" in action.action_id or "Reject" in action.action_id:
            trade_index = int(action_parts[1]) - 1
            proposal = self.pending_trades[trade_index]

            if "Accept" in action.action_id and agent.agent_id != proposal.proposer_id:
                responding_commodity = action_parts[2]
                quantity = int(action_parts[3])

                proposal.status = "accepted"

                self.respond_to_trade(
                    agent.agent_id, proposal.trade_id, True, responding_commodity
                )
            elif "Reject" in action.action_id:
                self.respond_to_trade(agent.agent_id, proposal.proposer_id, False)

        elif len(action_parts) == 3 and action_parts[0] == "Offer":
            offered_commodity = action_parts[1]
            quantity = int(action_parts[2])
            self.propose_trade(agent.agent_id, offered_commodity, quantity)

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
