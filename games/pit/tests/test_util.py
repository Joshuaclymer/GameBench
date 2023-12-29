"""Unit tests for the util module"""
import mock
import unittest

from pit import config, util


class SwapTest(unittest.TestCase):
    """Tests of the swap_cards method
    """
    def setUp(self):
        """Sets up cards for swapping"""
        self.cards1 = ['a', 'a', 'b', 'b', 'b']
        self.cards2 = ['a', 'a', 'c', 'd', 'd']

    def test_swap_single(self):
        """Can swap a single card"""
        util.swap_cards(self.cards1, ['a'], self.cards2, ['d'])
        self.assertEqual(sorted(self.cards1), ['a', 'b', 'b', 'b', 'd'])
        self.assertEqual(sorted(self.cards2), ['a', 'a', 'a', 'c', 'd'])

    def test_swap_pair(self):
        """Can swap a pair of cards"""
        util.swap_cards(self.cards1, ['a', 'a'], self.cards2, ['d', 'd'])
        self.assertEqual(sorted(self.cards1), ['b','b','b', 'd', 'd'])
        self.assertEqual(sorted(self.cards2), ['a', 'a', 'a', 'a', 'c'])

    def test_swap_trio(self):
        """Can swap three cards"""
        util.swap_cards(self.cards1, ['a', 'a', 'b'], self.cards2, ['d', 'd', 'c'])
        self.assertEqual(sorted(self.cards1), ['b','b','c', 'd', 'd'])
        self.assertEqual(sorted(self.cards2), ['a', 'a', 'a', 'a', 'b'])

    def test_swap_four(self):
        """Tests swapping foursome of cards"""
        util.swap_cards(self.cards1, ['a', 'b', 'b', 'b'], self.cards2, ['a', 'a', 'd', 'd'])
        self.assertEqual(sorted(self.cards1), ['a','a','a', 'd', 'd'])
        self.assertEqual(sorted(self.cards2), ['a', 'b', 'b', 'b', 'c'])


class HasCardsTest(unittest.TestCase):
    """Tests for the has_cards method"""
    def setUp(self):
        """Sets up starting cards for testing"""
        self.cards = ['a', 'a', 'a', 'b', 'b', 'c', 'c', 'd']
        self.locked_groups = [
            mock.Mock(cards=['b', 'b']),
            mock.Mock(cards=['d']),
        ]

    def test_cards_available(self):
        """has_cards returns True when cards are available
        """
        self.assertTrue(util.has_cards(['c', 'c'], self.cards, self.locked_groups))

    def test_cards_available_none_locked(self):
        """has_cards returns True when cards are available with no locked groups
        """
        self.assertTrue(util.has_cards(['c', 'c'], self.cards, []))

    def test_cards_locked(self):
        """has_cards returns False when cards are locked
        """
        self.assertFalse(util.has_cards(['b', 'b'], self.cards, self.locked_groups))

    def test_cards_not_found(self):
        """has_cards returns False when cards are not in cards at all
        """
        self.assertFalse(util.has_cards(['e', 'e', 'e'], self.cards, self.locked_groups))


class HandTest(unittest.TestCase):
    """Tests for scoring and determining winning hands"""
    def test_simple_winning_hand(self):
        """A hand of all one commodity is a winning hand"""
        cards = ['a'] * config.COMMODITIES_PER_HAND
        self.assertTrue(util.is_winning_hand(cards))

    def test_mixed_hand(self):
        """A hand of mixed commodities is not a winning hand"""
        cards = ['a'] * (config.COMMODITIES_PER_HAND - 3)
        cards.extend(['b', 'b', 'c'])
        self.assertFalse(util.is_winning_hand(cards))

    def test_extra_card_ok(self):
        """A winning hand with one extra card is still a winning hand"""
        cards = ['a'] * config.COMMODITIES_PER_HAND
        cards.append('b')
        self.assertTrue(util.is_winning_hand(cards))

    def test_extra_bear_not_ok(self):
        """Winning hand with one extra card not winning if card is the bear"""
        cards = ['a'] * config.COMMODITIES_PER_HAND
        cards.append(config.BEAR)
        self.assertFalse(util.is_winning_hand(cards))

    def test_extra_bull_wild(self):
        """The bull can act as a wild card"""
        cards = ['a'] * (config.COMMODITIES_PER_HAND - 1)
        cards.append(config.BULL)
        self.assertTrue(util.is_winning_hand(cards))

    def test_extra_bull_wild_extra(self):
        """The bull can act as a wild card in an extra-card hand"""
        cards = ['a'] * (config.COMMODITIES_PER_HAND - 1)
        cards.extend([config.BULL, 'b'])
        self.assertTrue(util.is_winning_hand(cards))

    def test_extra_bull_wild_extra_bear(self):
        """The bear again blocks this from being a winning hand"""
        cards = ['a'] * (config.COMMODITIES_PER_HAND - 1)
        cards.extend([config.BULL, config.BEAR])
        self.assertFalse(util.is_winning_hand(cards))

    def test_score_regular_winning_hand(self):
        """Score for a regular winning hand is correct"""
        commodity = 'wheat'
        cards = [commodity] * config.COMMODITIES_PER_HAND
        score = util.score_hand(cards)
        self.assertEqual(score, config.COMMODITY_VALUES[commodity])

    def test_score_bull_winning_hand(self):
        """Score using BULL as a wildcard is correct"""
        commodity = 'oats'
        cards = [commodity] * (config.COMMODITIES_PER_HAND - 1)
        cards.append(config.BULL)
        score = util.score_hand(cards)
        self.assertEqual(score, config.COMMODITY_VALUES[commodity])

    def test_score_bonus_winning_hand(self):
        """Score with a double bonus for BULL is correct"""
        commodity = 'coffee'
        cards = [commodity] * config.COMMODITIES_PER_HAND
        cards.append(config.BULL)
        score = util.score_hand(cards)
        self.assertEqual(score, config.COMMODITY_VALUES[commodity] * 2)

    def test_score_neutral_hand(self):
        """A neutral hand has a score of 0"""
        cards = ['barley'] * 4 + ['oranges'] * 3 + ['soybeans', 'oats']
        score = util.score_hand(cards)
        self.assertEqual(score, 0)

    def test_score_bull_penalty(self):
        """A non-winning hand with a bull has a negative score"""
        cards = ['barley'] * 4 + ['oranges'] * 3 + ['soybeans', config.BULL]
        score = util.score_hand(cards)
        self.assertEqual(score, -config.BULL_PENALTY)

    def test_score_bear_penalty(self):
        """A non-winning hand with a bear has a negative score"""
        cards = ['barley'] * 4 + ['oranges'] * 3 + ['soybeans', config.BEAR]
        score = util.score_hand(cards)
        self.assertEqual(score, -config.BEAR_PENALTY)

    def test_score_dual_penalty(self):
        """A non-winning hand with both bull and bear is super penalized"""
        cards = ['barley'] * 4 + ['oranges'] * 3 + [config.BULL, config.BEAR]
        score = util.score_hand(cards)
        self.assertEqual(score, -(config.BEAR_PENALTY+config.BULL_PENALTY))


class AvailableCardGroupsTest(unittest.TestCase):
    """Tests for available_card_groups"""
    def setUp(self):
        """Creates some starting cards"""
        self.cards = ['a', 'a', 'a', 'b', 'b', 'c', 'd', 'e', 'e']
        self.locked_cards = ['b', 'b', 'd']
        self.expected = {'a': 3, 'c': 1, 'e': 2}

    def test_available(self):
        """Available cards are found & counted correctly
        """
        available = util.available_card_groups(self.cards, self.locked_cards)
        self.assertEqual(available, self.expected)

    def test_empty_locked(self):
        """Available cards found when no cards locked
        """
        self.locked_cards = []
        self.expected.update({'b': 2, 'd': 1})
        available = util.available_card_groups(self.cards, self.locked_cards)
        self.assertEqual(available, self.expected)

    def test_mixed_locked(self):
        """Available cards found when not locked in complete sets"""
        self.locked_cards.append('a')
        self.expected.update({'a': 2})
        available = util.available_card_groups(self.cards, self.locked_cards)
        self.assertEqual(available, self.expected)


class MatchingTest(unittest.TestCase):
    """Tests for matching cards methods"""
    def setUp(self):
        """Creates starting test data"""
        self.card_groups = {
            'a': 1,
            'b': 2,
            'c': 1,
            'd': 3,
            'e': 2,
            'f': 2,
            'bear': 1,
        }

    def test_match_found(self):
        """Matching groups are found"""
        matches = util.matching_groups(self.card_groups, 2)
        self.assertEqual(matches, [['b', 'b'], ['e', 'e'], ['f', 'f']])

    def test_no_match_found(self):
        """Matching groups are not found"""
        matches = util.matching_groups(self.card_groups, 4)
        self.assertEqual(matches, [])

    def test_match_with_bear(self):
        """Match found with bear included"""
        matches = util.matching_groups_with(['bear'], self.card_groups, 2)
        self.assertEqual(matches, [['a', 'bear'], ['c', 'bear']])

    def test_match_with_bull_and_bear(self):
        """Match found with bull and bear included"""
        self.card_groups['bull'] = 1
        matches = util.matching_groups_with(['bull', 'bear'], self.card_groups, 3)
        self.assertEqual(matches, [['a', 'bull', 'bear'], ['c', 'bull', 'bear']])

    def test_match_only_bull_and_bear(self):
        """Match found with only bull and bear included"""
        self.card_groups['bull'] = 1
        matches = util.matching_groups_with(['bull', 'bear'], self.card_groups, 2)
        self.assertEqual(matches, [['bull', 'bear']])

    def test_match_too_many_cards(self):
        """Match found when more cards requested than quantity"""
        self.card_groups['bull'] = 1
        matches = util.matching_groups_with(['bull', 'bear'], self.card_groups, 1)
        self.assertEqual(matches, [['bull']])

    def test_match_with_nothing(self):
        """Match found with nothing included"""
        matches = util.matching_groups_with([], self.card_groups, 3)
        self.assertEqual(matches, [['d', 'd', 'd']])


class DealTest(unittest.TestCase):
    """Tests for dealing cards"""
    def _flatten(self, hands):
        """Helper flattens 2D cards to a 1D list"""
        return [card for hand in hands for card in hand]

    def test_num_dealt(self):
        """Right number of cards dealt and BULL & BEAR present"""
        cards = self._flatten(util.deal_cards(7, 0))
        self.assertEqual(len(cards), 7*config.COMMODITIES_PER_HAND+2)
        self.assertTrue(config.BULL in cards)
        self.assertTrue(config.BEAR in cards)

    def test_player_hand_lengths(self):
        """Right number of cards dealt to each player position"""
        hands = util.deal_cards(5, 2)
        self.assertEqual(len(hands[0]), config.COMMODITIES_PER_HAND)
        self.assertEqual(len(hands[1]), config.COMMODITIES_PER_HAND)
        self.assertEqual(len(hands[2]), config.COMMODITIES_PER_HAND)
        self.assertEqual(len(hands[3]), config.COMMODITIES_PER_HAND + 1)
        self.assertEqual(len(hands[4]), config.COMMODITIES_PER_HAND + 1)

    def test_all_cards_used(self):
        """Exactly all of the cards are used in the deal"""
        cards = self._flatten(util.deal_cards(3, 1))
        expected = [config.COMMODITIES[0]] * config.COMMODITIES_PER_HAND + \
                   [config.COMMODITIES[1]] * config.COMMODITIES_PER_HAND + \
                   [config.COMMODITIES[2]] * config.COMMODITIES_PER_HAND + \
                   [config.BULL, config.BEAR]
        self.assertEqual(sorted(cards), sorted(expected))

