import unittest
import playtest


class PlaytestTests(unittest.TestCase):
    def start(self, run, test=False):
        return {'schemaVersion': 1, 'event': 'start', 'runId': run, 'test': test,
                'contentVersion': 'v1', 'playerCharacter': 'kaiba', 'opponentCharacter': 'joey',
                'deckFingerprints': ['a', 'b'], 'firstPlayerConfigured': 0, 'controlMode': 'human-vs-cpu'}

    def end(self, run, result, eligible, test=False):
        return {'schemaVersion': 1, 'event': 'end', 'runId': run, 'test': test,
                'result': result, 'eligibleForWinRate': eligible}

    def test_incomplete_disconnect_draw_and_test_are_not_losses(self):
        records = [self.start('a'), self.end('a', 'win', True), self.start('b'),
                   self.start('c'), self.end('c', 'interrupted', False),
                   self.start('d'), self.end('d', 'draw', False),
                   self.start('e', True), self.end('e', 'loss', True, True)]
        report = playtest.summarize(records)['matchups'][0]
        self.assertEqual((4, 1, 1, 1, 1, 0, 1.0), tuple(report[k] for k in
                         ('started', 'incomplete', 'interrupted', 'draws', 'wins', 'losses', 'winRate')))

    def test_duplicate_results_do_not_count_twice_and_conflicts_fail(self):
        end = self.end('a', 'win', True)
        result = playtest.summarize([self.start('a'), end, end])
        self.assertEqual(1, result['duplicateEventsIgnored'])
        self.assertEqual(1, result['matchups'][0]['eligibleGames'])
        with self.assertRaises(ValueError):
            playtest.summarize([self.start('a'), end, self.end('a', 'loss', True)])

    def test_revisions_and_binaries_do_not_pool(self):
        starts = [self.start(str(i)) for i in range(3)]
        starts[1]['deckFingerprints'] = ['different', 'b']
        starts[2]['binaries'] = {'serverSha256': 'new'}
        self.assertEqual(3, len(playtest.summarize(starts)['matchups']))

    def test_queue_is_pending_and_directed(self):
        overlay = {'contentVersion': 'v1', 'encounters': [
            {'chapterId': 1, 'playerCharacterId': 'a', 'opponentCharacterId': 'b'},
            {'chapterId': 2, 'playerCharacterId': 'b', 'opponentCharacterId': 'a'}]}
        rows = playtest.queue(overlay, 10)
        self.assertEqual(20, len(rows))
        self.assertEqual(20, len({r['queueId'] for r in rows}))
        self.assertTrue(all(r['status'] == 'pending' and r['runId'] == '' for r in rows))


if __name__ == '__main__':
    unittest.main()
