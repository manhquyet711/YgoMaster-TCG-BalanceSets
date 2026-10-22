"""Manual playtest queue and summaries of client-reported human-vs-CPU runs.

This does not launch the game, control its AI or claim headless simulation.
"""
import argparse
import collections
import csv
import json
from pathlib import Path
import content


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def queue(overlay, trials):
    if not 1 <= trials <= 100:
        raise ValueError('Trials per directed matchup must be 1..100')
    rows = []
    for trial in range(1, trials + 1):
        for match in overlay['encounters']:
            rows.append({'queueId': '%s-%s-%02d' % (overlay['contentVersion'], match['chapterId'], trial),
                         'chapterId': match['chapterId'], 'playerCharacter': match['playerCharacterId'],
                         'opponentCharacter': match['opponentCharacterId'], 'trial': trial,
                         'status': 'pending', 'runId': '', 'firstPlayerObserved': '',
                         'result': '', 'aiIssue': '', 'replayPath': '', 'notes': ''})
    return rows


def summarize(records, include_tests=False):
    starts, ends = {}, {}
    duplicates = 0
    for record in records:
        if record.get('schemaVersion') != 1 or not record.get('runId'):
            raise ValueError('Unsupported or missing run identity')
        if record.get('test') and not include_tests:
            continue
        target = starts if record['event'] == 'start' else ends if record['event'] == 'end' else None
        if target is None:
            raise ValueError('Unknown log event')
        if record['runId'] in target:
            duplicates += 1
            if target[record['runId']] != record:
                raise ValueError('Conflicting duplicate event: ' + record['runId'])
        else:
            target[record['runId']] = record
    groups = {}
    for run_id, start in starts.items():
        key = (start['contentVersion'], start['playerCharacter'], start['opponentCharacter'],
               tuple(start['deckFingerprints']), json.dumps(start.get('binaries', {}), sort_keys=True),
               start.get('controlMode'), bool(start.get('test')))
        if key not in groups:
            groups[key] = {'contentVersion': key[0], 'playerCharacter': key[1], 'opponentCharacter': key[2],
                           'playerDeckFingerprint': key[3][0], 'opponentDeckFingerprint': key[3][1],
                           'binaryHashes': key[4], 'controlMode': key[5], 'test': key[6],
                           'started': 0, 'finished': 0, 'incomplete': 0, 'interrupted': 0,
                           'draws': 0, 'excludedFinishes': 0, 'wins': 0, 'losses': 0,
                           'configuredPlayerFirst': 0, 'configuredCpuFirst': 0}
        group = groups[key]
        group['started'] += 1
        if start.get('firstPlayerConfigured') in (0, 1):
            group['configuredPlayerFirst' if start['firstPlayerConfigured'] == 0 else 'configuredCpuFirst'] += 1
        end = ends.get(run_id)
        if end is None:
            group['incomplete'] += 1
            continue
        group['finished'] += 1
        if end['result'] == 'interrupted':
            group['interrupted'] += 1
        elif end['result'] == 'draw':
            group['draws'] += 1
        elif end.get('eligibleForWinRate') is True and end['result'] in ('win', 'loss'):
            group['wins' if end['result'] == 'win' else 'losses'] += 1
        else:
            group['excludedFinishes'] += 1
    rows = []
    for key in sorted(groups):
        row = groups[key]
        eligible = row['wins'] + row['losses']
        row['eligibleGames'] = eligible
        row['winRate'] = round(row['wins'] / eligible, 4) if eligible else ''
        rows.append(row)
    return {'matchups': rows, 'duplicateEventsIgnored': duplicates,
            'orphanEndEvents': len(set(ends) - set(starts)),
            'note': 'Client-reported human-vs-CPU evidence. Configured starter is not observed starter. No automated AI-vs-AI balance claim.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('queue', 'summary'))
    parser.add_argument('--runtime', type=Path, default=content.ROOT / 'YgoMaster')
    parser.add_argument('--output', type=Path, default=content.DOCS / 'Playtest')
    parser.add_argument('--trials', type=int, default=10)
    parser.add_argument('--include-tests', action='store_true')
    args = parser.parse_args()
    root = args.runtime / 'Data/BalancedCharacters'
    if args.command == 'queue':
        rows = queue(content.load_json(root / 'Generated/Overlay.json'), args.trials)
        write_csv(args.output / 'QUEUE.csv', rows, list(rows[0]))
        print('Generated %d pending manual games; no games were played.' % len(rows))
    else:
        log = root / 'Logs/duels.jsonl'
        records = []
        if log.exists():
            for line_number, line in enumerate(log.read_text(encoding='utf-8-sig').splitlines(), 1):
                if line.strip():
                    try:
                        records.append(json.loads(line))
                    except ValueError as error:
                        raise ValueError('Malformed log line %d; original retained: %s' % (line_number, error))
        result = summarize(records, args.include_tests)
        content.write_json(args.output / 'SUMMARY.json', result)
        if result['matchups']:
            write_csv(args.output / 'MATCHUPS.csv', result['matchups'], list(result['matchups'][0]))
        print('Summarized %d matchup groups. %s' % (len(result['matchups']), result['note']))


if __name__ == '__main__':
    main()
