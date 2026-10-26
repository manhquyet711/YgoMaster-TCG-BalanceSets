"""Offline character-deck importer/compiler. Python 3.9+, standard library only.

Reads Master Duel card tables using the layout in YdkHelper.LoadCardDataFromGame.
No web API, invented card IDs, or automatic fuzzy name substitutions.
"""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'YgoMaster' / 'Data'
MODE = DATA / 'BalancedCharacters'
DOCS = ROOT / 'Docs' / 'BalancedCharacters'
ROSTER = [
    ('yugi', 'Yugi', 40, 0), ('yugi_battle_city', 'Yugi (Battle City)', 40, 4),
    ('kaiba', 'Kaiba', 40, 3), ('joey', 'Joey', 40, 3), ('weevil', 'Weevil', 40, 0),
    ('rex', 'Rex', 40, 0), ('mako', 'Mako Tsunami', 40, 0),
    ('mai', 'Mai Valentine', 40, 0), ('bandit_keith', 'Bandit Keith', 40, 0),
    ('bonz', 'Bonz', 40, 0), ('pegasus', 'Pegasus', 40, 2),
    ('marik_bakura', 'Marik Ishtar (Marik/Bakura mix)', 40, 0),
    ('gravekeepers', 'Ishtar (Gravekeepers)', 40, 0),
    ('grandpa', 'Grandpa (Exodia)', 41, 0), ('jaden', 'Jaden Yuki', 40, 15)]
# v2: "Three years ago I posted a set of balanced old-school decks" photo set.
# New characters get new IDs; v1 decks stay immutable under Decks/source-v1.
ROSTER_V2 = [
    ('yugi', 'Yugi (Season 1)', 40, 0), ('yugi_season2', 'Yugi (Season 2)', 40, 4),
    ('kaiba', 'Kaiba', 40, 3), ('joey', 'Joey', 40, 3), ('weevil', 'Weevil', 40, 0),
    ('rex', 'Rex', 40, 0), ('mako', 'Mako Tsunami', 40, 0),
    ('mai', 'Mai Valentine', 40, 0), ('bandit_keith', 'Bandit Keith', 40, 0),
    ('bonz', 'Bonz', 40, 0), ('pegasus', 'Pegasus', 40, 2),
    ('yami_bakura', 'Yami Bakura', 40, 0),
    ('gravekeepers', 'Ishtar (Gravekeepers)', 40, 0),
    ('grandpa', 'Grandpa (Exodia)', 40, 0), ('jaden', 'Jaden Yuki', 40, 15)]
# v3: Goat Era Duelists, AI-designed and Goat-legal (decks in goat_set.py).
sys.path.insert(0, str(Path(__file__).resolve().parent))
import goat_set  # noqa: E402
ROSTER_V3 = [(cid, name, sum(main.values()), sum(extra.values())) for cid, name, main, extra in goat_set.DECKS]
# v4: Duel Royale, Konami's official pre-built decks as printed (lists in Royale/decklists.json).
import royale_set  # noqa: E402
ROSTER_V4 = royale_set.roster()
# v5 / v6: Goat and Edison Format Strategies, real tournament decks tuned for CPU balance (strategy_set.py).
import strategy_set  # noqa: E402
ROSTER_V5 = strategy_set.roster('goat')
ROSTER_V6 = strategy_set.roster('edison')
ROSTERS = {'source-v1': ROSTER, 'source-v2': ROSTER_V2, 'source-v3': ROSTER_V3, 'source-v4': ROSTER_V4,
           'source-v5': ROSTER_V5, 'source-v6': ROSTER_V6}
# Deck sources that count as reviewed: photographed lists, designed sets checked by their own tool,
# or official printed decks.
VERIFIED = ('photo-verified', 'designed', 'official')
# Gate name prefix per set; each set has its own Solo folder.
GATE_TITLE = {'source-v3': 'Goat Era - ', 'source-v4': 'Duel Royale - ',
              'source-v5': 'Goat Format - ', 'source-v6': 'Edison Format - '}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def load_game_config(path):
    text = path.read_text(encoding='utf-8-sig')
    text = re.sub(r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/',
                  lambda m: m[0] if m[0].startswith('"') else '', text)
    text = re.sub(r'"(?:\\.|[^"\\])*"|,\s*(?=[}\]])',
                  lambda m: m[0] if m[0].startswith('"') else '', text)
    return json.loads(text)


def normalize(name):
    return name.replace('\u2019', "'").replace('\u2018', "'").casefold().strip()


def active_revision():
    path = MODE / 'Mode.json'
    revision = load_json(path).get('activeDeckRevision', 'source-v1') if path.exists() else 'source-v1'
    if revision not in ROSTERS:
        raise ValueError('Unknown deck revision: ' + str(revision))
    return revision


def source_dir(revision):
    # v1 sources predate revisions and stay at the folder root.
    return MODE / 'SourceDecks' if revision == 'source-v1' else MODE / 'SourceDecks' / revision


def card_table():
    folder = DATA / 'CardData'
    names = (folder / 'en-US' / 'CARD_Name.bytes').read_bytes()
    indexes = (folder / 'en-US' / 'CARD_Indx.bytes').read_bytes()
    props = (folder / '#' / 'CARD_Prop.bytes').read_bytes()
    if len(indexes) % 8 or len(props) != len(indexes) - 8:
        raise ValueError('Unexpected card-table lengths; do not infer IDs')
    cards = {}
    for i in range(len(props) // 8):
        name_offset, _ = struct.unpack_from('<II', indexes, i * 8)
        prop_a, _ = struct.unpack_from('<II', props, i * 8)
        card_id = prop_a & 0xffff
        end = names.find(b'\0', name_offset)
        if name_offset >= len(names) or end < 0:
            raise ValueError('Invalid name offset at index %d' % i)
        name = names[name_offset:end].decode('utf-8')
        if card_id:
            if card_id in cards and cards[card_id] != name:
                raise ValueError('Conflicting card ID %d' % card_id)
            cards[card_id] = name
    return cards


def import_sources():
    """Preserve saved transcription and explicitly flag all unverified photo data."""
    text = (DOCS / 'Character_Deck_Lists.md').read_text(encoding='utf-8')
    sources = {}
    for character_id, title, main_count, extra_count in ROSTER:
        marker = '## ' + title + '\n'
        if marker not in text:
            raise ValueError('Missing heading ' + title)
        section = text.split(marker, 1)[1].split('\n## ', 1)[0]
        source = {'schemaVersion': 1, 'characterId': character_id,
                  'sourcePhoto': re.search(r'^Photo: (.+)$', section, re.M).group(1),
                  'verificationStatus': 'transcribed-needs-photo-review',
                  'expectedMainCount': main_count, 'expectedExtraCount': extra_count,
                  'main': [], 'extra': [], 'side': [], 'corrections': []}
        zone = 'main'
        for line in section.splitlines():
            if line == '### Fusion Deck':
                zone = 'extra'
            match = re.match(r'^- (\d+) x (.+)$', line)
            if match:
                quantity, name = int(match[1]), match[2]
                source[zone].append({'name': name, 'quantity': quantity,
                                     'status': 'unresolved' if '[CHECK' in name else 'transcribed'})
        if character_id == 'kaiba':
            # Directly inspected photo: two Blizzard Dragons. The old markdown
            # accidentally split a single uncertain entry into two bullet lines.
            source['main'] = [entry for entry in source['main']
                              if not ('Unresolved normal Dragon' in entry['name']
                                      or "title appears to end" in entry['name'])]
            source['main'].append({'name': 'Blizzard Dragon', 'quantity': 2,
                                   'status': 'photo-verified'})
            source['corrections'].append('Two Blizzard Dragons identified from source photo; removed malformed split entry.')
        source_path = MODE / 'SourceDecks' / (character_id + '.json')
        if source_path.exists():
            raise ValueError('Source already exists; import never overwrites reviewed data: ' + str(source_path))
        sources[source_path] = source
    # Validate all imports before writing any source file.
    for path, source in sources.items():
        write_json(path, source)
    write_json(MODE / 'Roster.json', [{'id': cid, 'displayName': name, 'deckRevision': 'source-v1',
                'deckFile': 'Decks/source-v1/' + cid + '.json', 'presentationId': cid}
                for cid, name, _, _ in ROSTER])


def resolve():
    revision = active_revision()
    roster = ROSTERS[revision]
    cards = card_table()
    known = load_json(DATA / 'CardList.json')
    by_name = collections.defaultdict(list)
    for cid, name in cards.items():
        by_name[normalize(name)].append(cid)
    aliases_path = MODE / 'Aliases.json'
    aliases = load_json(aliases_path) if aliases_path.exists() else {}
    rows, deck_reports = [], []
    staged = {}
    for cid, title, _, _ in roster:
        source = load_json(source_dir(revision) / (cid + '.json'))
        output = {key: source[key] for key in ('schemaVersion', 'characterId', 'expectedMainCount', 'expectedExtraCount')}
        output.update(revision=revision, main=[], extra=[], side=[])
        errors = []
        for zone in ('main', 'extra', 'side'):
            seen = set()
            for entry in source[zone]:
                source_name = entry['name']
                alias = aliases.get(source_name)
                lookup_name = alias['canonicalName'] if alias else source_name
                ids = by_name.get(normalize(lookup_name), [])
                if alias and 'masterDuelId' in alias:
                    chosen = alias['masterDuelId']
                    if chosen not in ids:
                        raise ValueError('Explicit ID does not match local canonical name: ' + source_name)
                    ids = [chosen]
                status = 'resolved' if len(ids) == 1 and entry['status'] != 'unresolved' else 'unresolved'
                card_id = ids[0] if status == 'resolved' else None
                if card_id is not None and str(card_id) not in known:
                    status = 'not-in-installed-catalog'
                rows.append({'characterId': cid, 'zone': zone, 'sourceName': source_name,
                             'quantity': entry['quantity'], 'canonicalName': cards.get(card_id, ''),
                             'masterDuelId': card_id or '', 'resolutionStatus': status,
                             'evidence': alias['evidence'] if alias else 'local CARD_Name/CARD_Indx/CARD_Prop tables',
                             'photoStatus': entry['status'], 'effectNote': 'not playtested; modern engine effects'})
                if status != 'resolved':
                    errors.append('Unresolved card: ' + source_name)
                    continue
                if card_id in seen:
                    errors.append('Duplicate source entry: ' + source_name)
                seen.add(card_id)
                output[zone].append({'cardId': card_id, 'quantity': entry['quantity']})
            actual = sum(x['quantity'] for x in source[zone])
            expected = source['expectedMainCount'] if zone == 'main' else source['expectedExtraCount'] if zone == 'extra' else 0
            if actual != expected:
                errors.append('%s source count %d != expected %d' % (zone, actual, expected))
        verified = source['verificationStatus'] in VERIFIED
        if not verified:
            errors.append('Full source photo review pending')
        deck_reports.append({'characterId': cid, 'ready': not errors, 'errors': errors,
                             'mainCount': sum(x['quantity'] for x in source['main']),
                             'extraCount': sum(x['quantity'] for x in source['extra'])})
        if not errors:
            validate_deck(output, set(map(int, known)), revision)
            staged[cid] = output
    # Only validated, fully reviewed decks are published. Stale outputs fail closed.
    for cid, _, _, _ in roster:
        path = MODE / 'Decks' / revision / (cid + '.json')
        if cid in staged:
            if path.exists() and load_json(path) != staged[cid]:
                raise ValueError('Immutable ' + revision + ' changed; create a new revision: ' + cid)
            write_json(path, staged[cid])
        elif path.exists():
            raise ValueError('Previously published deck is now invalid: ' + cid)
    MODE.mkdir(parents=True, exist_ok=True)
    with (MODE / 'CardMap.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    write_json(DOCS / 'CARD-AUDIT.json', {'cardTableCount': len(cards), 'revision': revision, 'decks': deck_reports})
    print(json.dumps({'revision': revision, 'cardTableCount': len(cards), 'readyDecks': list(staged),
                      'blockedDecks': [x['characterId'] for x in deck_reports if not x['ready']]}, indent=2))


def validate_deck(deck, catalog, revision='source-v1'):
    if deck['schemaVersion'] != 1 or deck['revision'] != revision or revision not in ROSTERS:
        raise ValueError('Unsupported deck schema/revision')
    for zone in ('main', 'extra', 'side'):
        seen = set()
        for card in deck[zone]:
            card_id, quantity = card['cardId'], card['quantity']
            if type(card_id) is not int or card_id <= 0 or card_id not in catalog:
                raise ValueError('Invalid card ID')
            if type(quantity) is not int or not 1 <= quantity <= 3:
                raise ValueError('Invalid quantity')
            if card_id in seen:
                raise ValueError('Duplicate card entry')
            seen.add(card_id)
        expected = deck['expectedMainCount'] if zone == 'main' else deck['expectedExtraCount'] if zone == 'extra' else 0
        if sum(c['quantity'] for c in deck[zone]) != expected:
            raise ValueError('Incorrect ' + zone + ' count')
    if not 40 <= deck['expectedMainCount'] <= 60 or not 0 <= deck['expectedExtraCount'] <= 15:
        raise ValueError('Deck size outside engine limits')
    total = collections.Counter()
    for zone in ('main', 'extra', 'side'):
        total.update({x['cardId']: x['quantity'] for x in deck[zone]})
    if any(q > 3 for q in total.values()):
        raise ValueError('More than three copies across zones')


def deck_fingerprint(deck):
    zones = {zone: sorted((card['cardId'], card['quantity']) for card in deck[zone])
             for zone in ('main', 'extra', 'side')}
    return hashlib.sha256(json.dumps(zones, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def wire_deck(deck):
    result = {}
    for zone, key in (('main', 'Main'), ('extra', 'Extra'), ('side', 'Side')):
        ids = [x['cardId'] for x in deck[zone] for _ in range(x['quantity'])]
        result[key] = {'CardIds': ids, 'Rare': [1] * len(ids)}
    return result


def compile_prototype():
    """Compile explicitly selected verified characters into an additive Solo overlay."""
    catalog = set(map(int, load_json(DATA / 'CardList.json')))
    mode_path = MODE / 'Mode.json'
    mode = load_json(mode_path) if mode_path.exists() else {}
    characters = mode.get('activeCharacterIds', ['yugi', 'kaiba', 'joey'])
    revision = mode.get('activeDeckRevision', 'source-v1')
    if revision not in ROSTERS:
        raise ValueError('Unknown deck revision: ' + str(revision))
    roster = ROSTERS[revision]
    roster_ids = [row[0] for row in roster]
    if not 2 <= len(characters) <= len(roster_ids) or len(set(characters)) != len(characters) or any(c not in roster_ids for c in characters):
        raise ValueError('Select two to fifteen distinct reviewed characters')
    decks = {}
    for cid in characters:
        path = MODE / 'Decks' / revision / (cid + '.json')
        if not path.exists():
            raise ValueError('Prototype blocked: reviewed/resolved deck missing: ' + cid)
        decks[cid] = load_json(path)
        validate_deck(decks[cid], catalog, revision)
        source = load_json(source_dir(revision) / (cid + '.json'))
        if source['verificationStatus'] not in VERIFIED:
            raise ValueError('Source photo is not verified: ' + cid)
    solo = load_game_config(DATA / 'Solo.json')['Master']['Solo']
    existing_gates = set(map(int, solo['gate']))
    existing_chapters = {int(ch) for chapters in solo['chapter'].values() for ch in chapters}
    npc_ids = {int(ch.get('npc_id', 0)) for chapters in solo['chapter'].values() for ch in chapters.values()}
    ids_path = MODE / 'Ids.json'
    if ids_path.exists():
        allocations = load_json(ids_path)
    else:
        allocations = {'schemaVersion': 1, 'characters': {}}
    allocated = allocations['characters']
    # Chapter IDs use a per-character opponent slot. v1 slots are the original
    # roster positions, so existing battle IDs never move when the roster changes.
    v1_ids = [row[0] for row in ROSTER]
    for cid, value in allocated.items():
        if 'slot' not in value:
            if cid not in v1_ids:
                raise ValueError('Allocated character without a slot: ' + cid)
            value['slot'] = v1_ids.index(cid) + 1
    for cid in roster_ids:
        if cid not in allocated:
            used_gates = existing_gates | {v['gateId'] for v in allocated.values()}
            used_npcs = npc_ids | {v['npcId'] for v in allocated.values()}
            allocated[cid] = {'gateId': max(used_gates) + 1, 'npcId': max(used_npcs) + 1,
                              'slot': max([v['slot'] for v in allocated.values()] + [0]) + 1}
    allocated_gates = [v['gateId'] for v in allocated.values()]
    allocated_npcs = [v['npcId'] for v in allocated.values()]
    allocated_slots = [v['slot'] for v in allocated.values()]
    if len(set(allocated_gates)) != len(allocated) or len(set(allocated_npcs)) != len(allocated) or \
            len(set(allocated_slots)) != len(allocated) or any(not 1 <= x <= 8999 for x in allocated_slots):
        raise ValueError('Duplicate allocated IDs')
    if any(x in existing_gates for x in allocated_gates) or any(x in npc_ids for x in allocated_npcs):
        raise ValueError('Balanced IDs collide with existing campaign')
    if any(x <= 0 or x * 10000 + 9000 > 2147483647 for x in allocated_gates):
        raise ValueError('Allocated gate IDs overflow chapter IDs')
    names = {cid: name for cid, name, _, _ in roster}
    gates, chapters, encounters, texts, thumbs = {}, {}, [], [], []
    original_thumbs = (DATA / 'ClientData/SoloGateCards.txt').read_text(encoding='utf-8-sig')
    used_thumb_gates = {int(line.split(',')[0]) for line in original_thumbs.splitlines()
                       if line.strip() and not line.lstrip().startswith('//')}
    # Verified original signature monsters selected from each actual deck.
    preferred_names = {'yugi': 'Dark Magician', 'yugi_battle_city': 'Slifer the Sky Dragon',
        'yugi_season2': 'Slifer the Sky Dragon', 'yami_bakura': 'Dark Necrofear',
        'kaiba': 'Blue-Eyes White Dragon', 'joey': 'Red-Eyes Black Dragon',
        'weevil': 'Insect Queen', 'rex': 'Black Tyranno', 'mako': 'The Legendary Fisherman',
        'mai': 'Harpie Lady Sisters', 'bandit_keith': 'Barrel Dragon', 'bonz': 'Pumpking the King of Ghosts',
        'pegasus': 'Relinquished', 'marik_bakura': 'Dark Necrofear',
        'gravekeepers': "Gravekeeper's Chief", 'grandpa': 'Exodia the Forbidden One',
        'jaden': 'Elemental HERO Bladedge',
        'goat_yugi': 'Dark Magician', 'goat_kaiba': 'Blue-Eyes White Dragon', 'goat_joey': 'Red-Eyes Black Dragon',
        'goat_mai': 'Harpie Lady Sisters', 'goat_pegasus': 'Relinquished', 'goat_bakura': 'Dark Necrofear',
        'goat_marik': 'Lava Golem', 'goat_ishizu': 'Mudora',
        'royale_dark_magician': 'Dark Magician', 'royale_blue_eyes': 'Blue-Eyes White Dragon',
        'royale_gearfried': 'Gearfried the Swordmaster', 'royale_lava_golem': 'Lava Golem',
        'royale_legendary_ocean': 'Levia-Dragon - Daedalus', 'royale_relinquished': 'Relinquished',
        'royale_des_gardius': 'Masked Beast Des Gardius'}
    showcase = strategy_set.showcase()
    preferred_names.update({cid: card for cid, (card, label) in showcase.items()})
    names_by_id = card_table()
    signatures = {}
    for cid in characters:
        signature_ids = [c['cardId'] for c in decks[cid]['main']
                         if names_by_id[c['cardId']] == preferred_names.get(cid)]
        signatures[cid] = signature_ids[0] if len(signature_ids) == 1 else decks[cid]['main'][0]['cardId']

    # Short opponent names for the small header on each map card (read by the client patch).
    map_labels = {'yugi': 'Yugi S1', 'yugi_season2': 'Yugi S2', 'yugi_battle_city': 'Yugi BC',
        'kaiba': 'Kaiba', 'joey': 'Joey', 'weevil': 'Weevil', 'rex': 'Rex', 'mako': 'Mako',
        'mai': 'Mai', 'bandit_keith': 'Keith', 'bonz': 'Bonz', 'pegasus': 'Pegasus',
        'yami_bakura': 'Bakura', 'marik_bakura': 'Marik', 'gravekeepers': 'Gravekeeper',
        'grandpa': 'Grandpa', 'jaden': 'Jaden',
        'goat_yugi': 'Yugi', 'goat_kaiba': 'Kaiba', 'goat_joey': 'Joey', 'goat_mai': 'Mai', 'goat_pegasus': 'Pegasus',
        'goat_bakura': 'Bakura', 'goat_marik': 'Marik', 'goat_ishizu': 'Ishizu',
        'royale_dark_magician': 'Dark Magician', 'royale_blue_eyes': 'Blue-Eyes', 'royale_gearfried': 'Gearfried',
        'royale_lava_golem': 'Lava Golem', 'royale_legendary_ocean': 'Ocean', 'royale_relinquished': 'Relinquished',
        'royale_des_gardius': 'Des Gardius'}
    map_labels.update({cid: label for cid, (card, label) in showcase.items()})

    def deck_size(cid):
        main = sum(c['quantity'] for c in decks[cid]['main'])
        extra = sum(c['quantity'] for c in decks[cid].get('extra', []))
        return '%d cards' % main + (' + %d Extra' % extra if extra else '')

    for player in characters:
        gate = allocations['characters'][player]['gateId']
        if gate in used_thumb_gates:
            raise ValueError('Allocated gate collides with existing thumbnail')
        chapter_rows = {}
        previous_chapter = 0
        for opponent in characters:
            if player == opponent:
                continue
            chapter_id = gate * 10000 + allocated[opponent]['slot']
            if chapter_id in existing_chapters:
                raise ValueError('Allocated chapter collides with existing campaign')
            chapter_rows[str(chapter_id)] = {'parent_chapter': previous_chapter, 'difficulty': 1,
                'mydeck_set_id': 0, 'set_id': 1, 'unlock_id': 0, 'begin_sn': '',
                'npc_id': allocations['characters'][opponent]['npcId'], 'anime': 0}
            encounters.append({'chapterId': chapter_id, 'gateId': gate,
                               'playerCharacterId': player, 'opponentCharacterId': opponent})
            previous_chapter = chapter_id
            texts.extend(['[IDS_SOLO.CHAPTER%d]' % chapter_id, names[player] + ' vs ' + names[opponent],
                          '[IDS_SOLO.CHAPTER%d_EXPLANATION]' % chapter_id,
                          'Opponent: %s, %s deck, %s. You play %s, %s. Fixed decks, 8000 LP each.'
                          % (names[opponent], names_by_id[signatures[opponent]], deck_size(opponent),
                             names[player], deck_size(player)),
                          '[IDS_SOLO.CHAPTER%d_MAPLABEL]' % chapter_id,
                          'vs ' + map_labels.get(opponent, names[opponent])])
        goal_id = gate * 10000 + 9000
        if goal_id in existing_chapters or str(goal_id) in chapter_rows:
            raise ValueError('Allocated goal chapter collides with existing content')
        chapter_rows[str(goal_id)] = {'parent_chapter': previous_chapter, 'difficulty': 0,
            'mydeck_set_id': 0, 'set_id': 0, 'unlock_id': 0, 'begin_sn': '', 'npc_id': 0, 'anime': 0}
        gates[str(gate)] = {'priority': 100 + roster_ids.index(player), 'parent_gate': 0,
            'view_gate': 0, 'unlock_id': 0, 'clear_chapter': goal_id, 'category': 1}
        chapters[str(gate)] = chapter_rows
        texts.extend(['[IDS_SOLO.GATE%d]' % gate, GATE_TITLE.get(revision, 'Balanced Characters - ') + names[player],
                      '[IDS_SOLO.GATE%d_EXPLANATION]' % gate, 'Choose an opponent. You play ' + names[player] + "'s fixed deck."])
        thumbs.append('%d,%d,0,0.2' % (gate, signatures[player]))
    output = ROOT / 'Tools' / 'BalancedCharacters' / 'Generated'
    for player in characters:
        for opponent in characters:
            if player == opponent:
                continue
            duel = {'life': [8000, 8000], 'hnum': [5, 5], 'noshuffle': False,
                    'Type': 0, 'MyType': 0, 'FirstPlayer': -1, 'cpu': 100, 'cpuflag': None,
                    'name': [player, opponent], 'Deck': [wire_deck(decks[player]), wire_deck(decks[opponent])]}
            write_json(output / (player + '__' + opponent + '.json'),
                       {'schemaVersion': 1, 'runtimeIntegrated': True, 'Duel': duel,
                        'deckFingerprints': [deck_fingerprint(decks[player]), deck_fingerprint(decks[opponent])]})
    overlay = {'schemaVersion': 1, 'contentVersion': mode.get('contentVersion', '0.2.0'), 'deckRevision': revision,
               'gate': gates, 'chapter': chapters, 'encounters': encounters,
               'deckFingerprints': {c: deck_fingerprint(decks[c]) for c in characters}}
    write_json(ids_path, allocations)
    # Server display names come from Roster.json; retired characters stay listed.
    roster_path = MODE / 'Roster.json'
    roster_rows = load_json(roster_path) if roster_path.exists() else []
    order = [row['id'] for row in roster_rows]
    by_id = {row['id']: row for row in roster_rows}
    for cid, name, _, _ in roster:
        if cid not in by_id:
            by_id[cid] = {'id': cid, 'presentationId': cid}
            order.append(cid)
        by_id[cid].update(displayName=name, deckRevision=revision,
                          deckFile='Decks/' + revision + '/' + cid + '.json')
    write_json(roster_path, [by_id[cid] for cid in order])
    write_json(MODE / 'Generated/Overlay.json', overlay)
    write_json(output / 'Overlay.json', overlay)
    ids_text = DATA / 'ClientData/IDS/IDS_BALANCED_CHARACTERS.txt'
    ids_text.write_text('\n'.join(texts) + '\n', encoding='utf-8')
    (MODE / 'Generated/SoloGateCards.txt').write_text('\n'.join(thumbs) + '\n', encoding='utf-8')
    print('Generated %d gates / %d directed encounters for %s' % (len(gates), len(encounters), ', '.join(characters)))


# Shown in the Balanced Settings Editor's "Deck set" list.
REVISION_INFO = {
    'source-v1': 'Original 2021 lists by u/Rosehn (14 characters, incl. Yugi Battle City and Marik/Bakura)',
    'source-v2': 'Updated and finalized 2024 lists by u/Rosehn (15 characters)',
    'source-v3': 'Goat Era Duelists: AI-built balanced set, Goat-legal (8 characters)',
    'source-v4': "Duel Royale: Konami's 7 official pre-built decks, as printed",
    'source-v5': 'Goat Format Strategies: 8 tournament decks (2005 Goat list), tuned for balance',
    'source-v6': 'Edison Format Strategies: 8 tournament decks (2010 Edison list), tuned for balance',
}
# Sets built into packs (Revisions/<revision>). The game loads every set listed in Mode.json "sets",
# each into its own Solo folder: v2 Balanced Characters, v3 Goat Era Duelists, v4 Duel Royale,
# v5 Goat Format Strategies, v6 Edison Format Strategies.
PACKED_REVISIONS = ['source-v2', 'source-v3', 'source-v4', 'source-v5', 'source-v6']
SET_FOLDERS = [('source-v2', 2102, 'Balanced - '), ('source-v3', 2104, 'Goat Era - '), ('source-v4', 2103, 'Royale - '),
               ('source-v5', 2105, 'Goat Format - '), ('source-v6', 2106, 'Edison Format - ')]


def build_packs():
    """Compile every deck revision into Revisions/<revision>/ so the Settings Editor can switch
    sets by copying files. Working files (active overlay, texts, roster, generated pairs) are
    restored afterwards, so the active revision and the repository stay unchanged."""
    import shutil
    import tempfile
    ids_text = DATA / 'ClientData/IDS/IDS_BALANCED_CHARACTERS.txt'
    # Roster.json and Ids.json are not restored: they only gain entries (names and gate/chapter IDs
    # of every packed set), and the server needs those entries to load any of the packs.
    keep = [MODE / 'Mode.json', ids_text,
            MODE / 'Generated', ROOT / 'Tools' / 'BalancedCharacters' / 'Generated']
    original_mode = load_json(MODE / 'Mode.json')
    with tempfile.TemporaryDirectory() as tmp:
        saved = []
        for i, path in enumerate(keep):
            target = Path(tmp) / str(i)
            if path.is_dir():
                shutil.copytree(path, target)
            elif path.exists():
                shutil.copy2(path, target)
            else:
                target = None  # did not exist (e.g. the single-set IDS file after `sets`): remove afterwards
            saved.append((path, target))
        try:
            for revision in PACKED_REVISIONS:
                all_rows = ROSTERS[revision]
                # only characters with a compiled deck (v1 Yugi was never playable: Spellbinding Circle)
                roster = [r for r in all_rows if (MODE / 'Decks' / revision / (r[0] + '.json')).exists()]
                mode = dict(original_mode, activeDeckRevision=revision, activeCharacterIds=[r[0] for r in roster])
                write_json(MODE / 'Mode.json', mode)
                compile_prototype()
                pack = MODE / 'Revisions' / revision
                pack.mkdir(parents=True, exist_ok=True)
                shutil.copy2(MODE / 'Generated/Overlay.json', pack / 'Overlay.json')
                shutil.copy2(MODE / 'Generated/SoloGateCards.txt', pack / 'SoloGateCards.txt')
                shutil.copy2(ids_text, pack / 'IDS_BALANCED_CHARACTERS.txt')
                write_json(pack / 'Pack.json', {
                    'schemaVersion': 1, 'revision': revision, 'contentVersion': mode['contentVersion'],
                    'description': REVISION_INFO.get(revision, revision),
                    'activeCharacterIds': mode['activeCharacterIds'],
                    'characters': [r[1] for r in roster]})
                print('Pack %s: %d characters' % (revision, len(roster)))
        finally:
            for path, target in saved:
                if target is None:
                    if path.exists():
                        path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
                    shutil.copytree(target, path)
                else:
                    shutil.copy2(target, path)
    print('Restored the active revision %s' % original_mode.get('activeDeckRevision'))


def install_sets(data=None):
    """Configure a Data folder to load every packed set at once, each in its own Solo folder:
    Mode.json "sets", one IDS text file per set (the client loads every file in ClientData/IDS),
    and one merged gate thumbnail list. Start Game.exe refreshes the text and thumbnails too."""
    data = Path(data) if data else DATA
    mode_dir = data / 'BalancedCharacters'
    mode_path = mode_dir / 'Mode.json'
    mode = load_json(mode_path)
    sets = []
    thumbs = []
    ids_dir = data / 'ClientData' / 'IDS'
    for revision, folder_gate, prefix in SET_FOLDERS:
        pack = mode_dir / 'Revisions' / revision
        if not (pack / 'Pack.json').exists():
            raise ValueError('Pack missing: ' + str(pack))
        sets.append({'revision': revision, 'folderGate': folder_gate, 'deckPrefix': prefix})
        text = (pack / 'IDS_BALANCED_CHARACTERS.txt').read_text(encoding='utf-8-sig')
        (ids_dir / ('IDS_BALANCED_%s.txt' % revision.upper().replace('-', '_'))).write_text(text, encoding='utf-8')
        thumbs.extend(l for l in (pack / 'SoloGateCards.txt').read_text(encoding='utf-8-sig').splitlines() if l.strip())
    single = ids_dir / 'IDS_BALANCED_CHARACTERS.txt'
    if single.exists():
        single.unlink()  # same texts as the v2 set file; one copy only
    (mode_dir / 'Generated').mkdir(exist_ok=True)
    (mode_dir / 'Generated' / 'SoloGateCards.txt').write_text('\n'.join(thumbs) + '\n', encoding='utf-8')
    mode['sets'] = sets
    write_json(mode_path, mode)
    print('Configured %d deck sets in %s: %s' % (len(sets), data, ', '.join(s['revision'] for s in sets)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['import', 'resolve', 'compile', 'packs', 'sets'])
    parser.add_argument('data', nargs='?', help='sets: the Data folder to configure (default: repository Data)')
    args = parser.parse_args()
    try:
        {'import': import_sources, 'resolve': resolve, 'compile': compile_prototype,
         'packs': build_packs, 'sets': lambda: install_sets(args.data)}[args.command]()
    except (ValueError, KeyError, OSError) as error:
        print('BLOCKED: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
