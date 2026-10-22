"""Apply the 2026-10-22 visual review of the supplied local deck photographs.

Names/quantities are transcription corrections, not balance substitutions.
Previously published Kaiba/Joey decks are not modified.
"""
import hashlib
from pathlib import Path
import content

PHOTOS = Path(r'G:\Game\Joey\Desk list')
CORRECTIONS = {
    'mako': {'Great Turtle Who Feeds on Flames': 'Giant Turtle Who Feeds on Flames'},
    'bandit_keith': {"Robotic Knight? [CHECK: top-left normal monster is 'Robotic ...' / mechanical car artwork]": 'Bokoichi the Freightening Car'},
    'gravekeepers': {'Oracle of Shai': 'Charm of Shabti'},
    'jaden': {
        'Elemental HERO Thunder Giant [CHECK: bottom-left pair]': 'Elemental HERO Thunder Giant',
        'Unresolved Fusion A [CHECK: bottom row, second pair]': 'Elemental HERO Wildedge',
        'Unresolved Fusion B [CHECK: bottom-right pair]': 'Elemental HERO Rampart Blaster',
    },
}


def main():
    evidence = []
    for cid, _, _, _ in content.ROSTER:
        if cid in ('yugi', 'kaiba', 'joey'):
            continue  # Already reviewed in the preceding milestone.
        path = content.MODE / 'SourceDecks' / (cid + '.json')
        source = content.load_json(path)
        corrections = CORRECTIONS.get(cid, {})
        for zone in ('main', 'extra', 'side'):
            for card in source[zone]:
                old = card['name']
                if old in corrections:
                    card['name'] = corrections[old]
                    note = 'Photo review 2026-10-22: %s -> %s (quantity unchanged).' % (old, card['name'])
                    if note not in source['corrections']:
                        source['corrections'].append(note)
                card['status'] = 'photo-verified'
        source['verificationStatus'] = 'photo-verified'
        source['photoReview'] = {
            'date': '2026-10-22', 'reviewer': 'AI visual inspection',
            'photoSha256': hashlib.sha256((PHOTOS / source['sourcePhoto']).read_bytes()).hexdigest(),
            'note': 'Compared all pictured names and visible copy counts, including Fusion piles; no balance edits.',
        }
        content.write_json(path, source)
        evidence.append({'characterId': cid, 'photo': source['sourcePhoto'], **source['photoReview'],
                         'mainCount': sum(c['quantity'] for c in source['main']),
                         'extraCount': sum(c['quantity'] for c in source['extra']),
                         'corrections': source['corrections']})
    aliases = content.load_json(content.MODE / 'Aliases.json')
    for name, card_id, passcode in [('Slifer the Sky Dragon', 4999, 10000020),
                                    ('The Winged Dragon of Ra', 5000, 10000010),
                                    ('Limiter Removal', 5129, 23171610)]:
        mapping = '%d %d' % (passcode, card_id)
        if mapping not in (content.DATA / 'YdkIds.txt').read_text().splitlines():
            raise ValueError('Expected local passcode mapping missing: ' + mapping)
        aliases[name] = {'canonicalName': name, 'masterDuelId': card_id,
                         'evidence': 'Explicit original-card ID verified in local YdkIds.txt: ' + mapping}
    aliases['Marie the Fallen One'] = {
        'canonicalName': 'Darklord Marie', 'masterDuelId': 5209,
        'evidence': 'Official Konami database identifies renamed original card, cid=5209; local name table matches. https://www.db.yugioh-card.com/yugiohdb/card_search.action?cid=5209&ope=2',
    }
    content.write_json(content.MODE / 'Aliases.json', aliases)
    content.write_json(content.DOCS / 'PHOTO-REVIEW-0.2.2.json', evidence)
    content.resolve()


if __name__ == '__main__':
    main()
