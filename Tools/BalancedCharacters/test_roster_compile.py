import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import content


class RosterCompilerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / 'YgoMaster/Data'
        self.mode = self.data / 'BalancedCharacters'
        shutil.copytree(content.MODE, self.mode, ignore=shutil.ignore_patterns('Logs'))
        for name in ('CardList.json', 'Solo.json', 'ClientData/SoloGateCards.txt'):
            target = self.data / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(content.DATA / name, target)
        (self.data / 'ClientData/IDS').mkdir()
        self.names = content.card_table()

    def compile(self, selected):
        mode = content.load_json(self.mode / 'Mode.json')
        mode['activeCharacterIds'] = selected
        content.write_json(self.mode / 'Mode.json', mode)
        with patch.object(content, 'ROOT', self.root), patch.object(content, 'DATA', self.data), patch.object(content, 'MODE', self.mode), patch.object(content, 'card_table', return_value=self.names), contextlib.redirect_stdout(io.StringIO()):
            content.compile_prototype()
        return content.load_json(self.mode / 'Generated/Overlay.json')

    def test_two_three_and_fourteen_character_graphs(self):
        ready = [x[0] for x in content.ROSTER if x[0] != 'yugi']
        for selected in (['kaiba', 'joey'], ['kaiba', 'joey', 'weevil'], ready):
            with self.subTest(count=len(selected)):
                result = self.compile(selected)
                self.assertEqual(len(selected) * (len(selected) - 1), len(result['encounters']))
                for gate, chapters in result['chapter'].items():
                    clear = result['gate'][gate]['clear_chapter']
                    seen = set()
                    current = clear
                    while current:
                        self.assertNotIn(current, seen)
                        seen.add(current)
                        current = chapters[str(current)]['parent_chapter']
                    self.assertEqual(len(selected), len(seen))
                    self.assertEqual(set(map(int, chapters)), seen)

    def test_existing_battle_ids_and_fingerprints_survive_expansion(self):
        old = self.compile(['kaiba', 'joey'])
        expanded = self.compile([x[0] for x in content.ROSTER if x[0] != 'yugi'])
        for encounter in old['encounters']:
            self.assertIn(encounter, expanded['encounters'])
        for cid in ('kaiba', 'joey'):
            self.assertEqual(old['deckFingerprints'][cid], expanded['deckFingerprints'][cid])

    def test_unavailable_original_yugi_is_blocked(self):
        with self.assertRaisesRegex(ValueError, 'missing: yugi'):
            self.compile(['yugi', 'kaiba'])
        self.assertFalse((self.root / 'Tools').exists())

    def test_duplicate_character_is_rejected(self):
        with self.assertRaises(ValueError):
            self.compile(['kaiba', 'kaiba'])


if __name__ == '__main__':
    unittest.main()
