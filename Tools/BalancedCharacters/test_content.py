import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import content


class ContentTests(unittest.TestCase):
    def setUp(self):
        self.deck = {'schemaVersion': 1, 'characterId': 'test', 'revision': 'source-v1',
                     'expectedMainCount': 40, 'expectedExtraCount': 1,
                     'main': [{'cardId': i, 'quantity': 3} for i in range(1, 14)] + [{'cardId': 14, 'quantity': 1}],
                     'extra': [{'cardId': 15, 'quantity': 1}], 'side': []}
        self.catalog = set(range(1, 20))

    def test_valid_and_wire_counts(self):
        content.validate_deck(self.deck, self.catalog)
        wire = content.wire_deck(self.deck)
        self.assertEqual(40, len(wire['Main']['CardIds']))
        self.assertEqual(40, len(wire['Main']['Rare']))
        self.assertEqual([15], wire['Extra']['CardIds'])

    def test_fingerprint_order_independent(self):
        other = copy.deepcopy(self.deck)
        other['main'].reverse()
        self.assertEqual(content.deck_fingerprint(self.deck), content.deck_fingerprint(other))

    def test_fingerprint_zone_sensitive(self):
        other = copy.deepcopy(self.deck)
        other['main'][-1], other['extra'][0] = other['extra'][0], other['main'][-1]
        self.assertNotEqual(content.deck_fingerprint(self.deck), content.deck_fingerprint(other))

    def test_invalid_ids(self):
        for value in (0, -1, 999, True, '1'):
            with self.subTest(value=value):
                deck = copy.deepcopy(self.deck)
                deck['main'][0]['cardId'] = value
                with self.assertRaises(ValueError):
                    content.validate_deck(deck, self.catalog)

    def test_invalid_quantities(self):
        for value in (0, -1, 4, True, '1'):
            with self.subTest(value=value):
                deck = copy.deepcopy(self.deck)
                deck['main'][0]['quantity'] = value
                with self.assertRaises(ValueError):
                    content.validate_deck(deck, self.catalog)

    def test_duplicate_and_side_cards(self):
        deck = copy.deepcopy(self.deck)
        deck['main'][-1]['cardId'] = 1
        with self.assertRaises(ValueError):
            content.validate_deck(deck, self.catalog)
        deck = copy.deepcopy(self.deck)
        deck['side'] = [{'cardId': 16, 'quantity': 1}]
        with self.assertRaises(ValueError):
            content.validate_deck(deck, self.catalog)

    def test_total_copy_limit_across_zones(self):
        self.deck['extra'] = [{'cardId': 1, 'quantity': 1}]
        with self.assertRaises(ValueError):
            content.validate_deck(self.deck, self.catalog)

    def test_missing_prerequisite_writes_no_payloads(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content.write_json(root / 'data' / 'CardList.json', {'1': 1})
            with patch.object(content, 'ROOT', root), patch.object(content, 'DATA', root / 'data'), patch.object(content, 'MODE', root / 'mode'):
                with self.assertRaises(ValueError):
                    content.compile_prototype()
            self.assertFalse((root / 'Tools').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
