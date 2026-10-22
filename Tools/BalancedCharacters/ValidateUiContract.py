"""Inspect the installed IL2CPP contract used by the balanced duel-panel hooks.
This does not execute native code or test the game UI.
"""
import pathlib
import struct
import sys

b = (pathlib.Path(sys.argv[1]) / 'masterduel_Data/il2cpp_data/Metadata/global-metadata.dat').read_bytes()
assert struct.unpack_from('<II', b) == (0xFAB11BAF, 31)
h = struct.unpack_from('<62I', b, 8)
def string(index):
    p = h[4] + index
    return b[p:b.index(0, p)].decode('utf-8')
types = [struct.unpack_from('<16I8H2I', b, h[38]+i*88) for i in range(h[39]//88)]
def find_type(name, required_fields):
    matches = []
    for t in types:
        if string(t[0]) != name:
            continue
        fields = {string(struct.unpack_from('<3I', b, h[22]+j*12)[0]): j for j in range(t[8], t[8]+t[18])}
        if set(required_fields).issubset(fields):
            matches.append((t, fields))
    assert len(matches) == 1, 'Ambiguous or missing native class: ' + name
    return matches[0]
for name, fields, method, expected in [
    ('ChapterMap', ('gateID', 'chapterDataDic'), 'OnClickChapter', ['sb', 'data']),
    ('ChapterMap', ('gateID', 'chapterDataDic'), 'InitChapter', ['chapterID', 'chapterData']),
    ('ChapterMap', ('gateID', 'chapterDataDic'), 'Create', []),
    ('DuelDialog', ('rootRentalEom',), 'Open', ['data'])]:
    t, _ = find_type(name, fields)
    methods = [struct.unpack_from('<7I4H', b, h[10]+j*36) for j in range(t[9], t[9]+t[16])]
    methods = [m for m in methods if string(m[0]) == method]
    assert len(methods) == 1
    m = methods[0]
    names = [string(struct.unpack_from('<3I', b, h[20]+j*12)[0]) for j in range(m[4], m[4]+m[10])]
    assert names == expected, (name, method, names)
    print('PASS native signature', name + '.' + method + '(' + ', '.join(names) + ')')
print('NOT TESTED: runtime hook execution, chapter clicks, deck panel and Play button')
