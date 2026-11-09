"""Conservative automated topic decisions with verbatim, located body evidence.

These are machine checks, never claims of a human reading every document.
Source authenticity/completeness remains the independent quality_audit gate.
"""
import hashlib
import re
from urllib.parse import urlsplit

CHINA = re.compile(r'\b(?:China|Chinese|Peking|Beijing|Taiwan|Formosa|PRC|Sino-American|Sino-U\.S\.|Tiananmen|Xinjiang|Hong Kong)\b', re.I)
US = re.compile(r'\b(?:United States|(?-i:U\.?S\.?)|American|Washington|White House|Trump|Biden|Reagan|Carter|Nixon|Clinton|Kissinger|Eisenhower|Truman|Kennedy|Pentagon|Congress|Rubio|Blinken)\b', re.I)
POLICY = re.compile(r'\b(?:relations?|diploma\w*|normaliz\w*|normalis\w*|recognition|trade|tariffs?|sanctions?|export controls?|containment|communis\w*|propaganda|disinformation|information warfare|political warfare|psychological warfare|public diplomacy|broadcast\w*|Voice of America|human rights|democra\w*|strategic competition|technology competition|security|aggression|invasion|cease-fire|negotiat\w*|peace|arms|alliance|Taiwan Relations Act|military aid|nuclear|semiconductors?|chip restrictions|artificial intelligence)\b', re.I)
RELATION = re.compile(r'\b(?:relations?|diploma\w*|normaliz\w*|normalis\w*|recognition|trade|tariffs?|sanctions?|export controls?|containment|propaganda|disinformation|information warfare|political warfare|psychological warfare|public diplomacy|Voice of America|human rights|strategic competition|technology competition|negotiat\w*|military aid|Taiwan Relations Act|chip restrictions)\b', re.I)
COMMUNICATION = re.compile(r'\b(?:news|media|journalis\w*|discourse|framing|rhetoric|propaganda|disinformation|perception\w*|public opinion|public diplomacy|communication|political|diplomacy|foreign policy|international relations|great power|Sino-American|U\.?S\.?[-–— ]China)\b', re.I)
PROMO = re.compile(r'\b(?:podcast|episode|watch (?:the|our|this)|watch:|video|livestream|live stream|tune in|join us|register (?:now|here|for)|trailer)\b', re.I)
BAD_BODY = re.compile(r'(?:^|\n)\s*(?:Advertisement|Read [Mm]ore:|Related (?:Stories|Articles)|Recommended for you|Subscribe to our newsletter|WATCH:)\b|\ufffd', re.M)
UNRESOLVED = re.compile(r'date (?:conflict|pending)|publication date|migration.date|attribution conflict|collection.*author|author.*(?:conflict|mismatch|pending|verify)|byline|truncat|incomplete|fragment|omitt|ownership.*(?:lack|unverif)|page numbers|replacement character|advertisement|recommendation blocks|title.*mismatch|作者.*冲突|署名.*不明|日期.*冲突|迁移日期|正文.*不完整|模板|推荐阅读', re.I)
TERMS = ('United States','China','Chinese','Taiwan','Formosa','Beijing','Peking','Hong Kong','Xinjiang','Tiananmen','relations','trade','tariffs','sanctions','export controls','propaganda','disinformation','public diplomacy','human rights','Voice of America','normalization','diplomacy','communism','security','nuclear','semiconductors','artificial intelligence','news','media','framing','public opinion')


def assess_topic(row, previous_reason=''):
    body = row['body']
    result = {'approved': False, 'method': 'automated-paragraph-policy-link-v1',
              'body_sha256': hashlib.sha256(body.encode()).hexdigest(),
              'supporting_passages': [], 'reason': ''}
    def hold(reason):
        result['reason'] = reason
        return result
    if UNRESOLVED.search(previous_reason):
        return hold('Unresolved prior field/completeness concern preserved: ' + previous_reason)
    if BAD_BODY.search(body):
        return hold('Body contains a template/recommendation/encoding marker; targeted source cleanup pending.')
    if re.search(r'\b(?:partial transcript|excerpts? (?:from|of)|selected excerpts?)\b', row['title'], re.I) or re.search(r'•\s*EDITORIAL\s*$', body):
        return hold('Source explicitly identifies partial/editorially omitted text; completeness unresolved.')
    if row['source'] == 'The American Presidency Project' and re.search(r'^Digest of|^Statement by (?:the )?(?:Assistant|Deputy|Press|Secretary|Acting|White House)|^United States.*Agreement$', row['title'], re.I):
        return hold('Collection attribution may differ from document author; explicit document-level authorship review pending.')
    category = row['source_category']
    if category == 'new_media':
        if PROMO.search(body):
            return hold('Audiovisual/event promotion is not a full transcript; retain separately.')
        match = re.search(r'/profile/([^/]+)/post/', row['source_url'])
        if not match or match.group(1).endswith('.bsky.social'):
            return hold('Independent institutional ownership proof needed for platform handle.')
        if not row.get('platform_id'):
            return hold('Platform unique ID missing.')
        if re.search(r'\b(?:crashed|crash|shipwreck|typhoon)\b', body, re.I) and not RELATION.search(body):
            return hold('China reference is geographic rather than a substantive policy/discourse relationship.')
    if category == 'research_literature':
        title = row['title']
        bilateral_title = bool(CHINA.search(title) and (US.search(title) or re.search(r'New York Times|Sino-American', title, re.I)))
        international_title = bool(CHINA.search(title) and re.search(r'diploma\w*|foreign policy|international|propaganda|disinformation', title, re.I))
        if not COMMUNICATION.search(title) or not (bilateral_title or international_title):
            return hold('Research title does not establish a bilateral or international political/communication focus; broader context review pending.')
    # Never use bibliographic references or article-end cited titles as evidence.
    stop = re.search(r'(?:^|\n)\s*(?:References|Bibliography|REFERENCES|参考文献)\s*(?:\n|$)', body)
    substantive = body[:stop.start()] if stop else body
    institutional_us = row['source'] in {
        'The American Presidency Project', 'Harry S. Truman Library & Museum',
        'U.S. Department of State', 'The White House', 'U.S. Department of Defense'}
    for m in re.finditer(r'[^\n]+(?:\n(?!\n)[^\n]+)*', substantive):
        text = m.group()
        if len(text) < 80 or not CHINA.search(text) or not POLICY.search(text):
            continue
        if not (US.search(text) or institutional_us):
            continue
        if category == 'new_media' and not RELATION.search(text):
            continue
        if category == 'research_literature' and not RELATION.search(text):
            continue
        result['supporting_passages'].append({'start': m.start(), 'end': m.end(), 'text': text,
            'china_cue': CHINA.search(text).group(), 'policy_cue': POLICY.search(text).group(),
            'us_context': US.search(text).group() if US.search(text) else row['source']})
        if len(result['supporting_passages']) == 3:
            break
    if not result['supporting_passages']:
        return hold('No substantive same-paragraph China/US-policy or communication link established; not approved on a country keyword alone.')
    result.update(approved=True, reason='Automated batch review: verbatim body passage establishes a China/US policy or communication relationship; independent same-document source/field/completeness gate required.',
                  document_scope='complete original platform post, not linked article' if category == 'new_media' else 'same published textual document')
    return result


def derived_fields(row, assessment):
    """Extractive synopsis and literal body-supported terms, with explicit origin."""
    passages = assessment['supporting_passages']
    if not assessment['approved'] or not passages:
        raise ValueError('A positive, body-supported topic decision is required')
    text = passages[0]['text']
    # Retain complete sentences; never silently trim a sentence into a new claim.
    sentences = re.split(r'(?<=[.!?。！？])\s+(?=[A-Z“"\u4e00-\u9fff])', text)
    chosen = []
    for sentence in sentences:
        if CHINA.search(sentence) and POLICY.search(sentence):
            chosen.append(sentence)
        if chosen and sum(map(len, chosen)) >= 240:
            break
    synopsis = ' '.join(chosen) if chosen else text
    keywords = []
    for term in TERMS:
        match = re.search(r'(?<!\w)' + re.escape(term) + r'(?!\w)', row['body'], re.I)
        if match:
            keywords.append(match.group())
        if len(keywords) == 12:
            break
    return '据正文整理：' + synopsis, '; '.join(keywords)
