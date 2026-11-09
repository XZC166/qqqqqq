"""Conservative complete granules from a dated public weekly publication."""
from datetime import datetime, timezone
import json
from hashlib import sha256
import re
from urllib.parse import unquote, urlsplit

from research_crawler.items import SourceEvidence, VerifiedMaterial
from research_crawler.policy import AccessDecision, classify_response


def _flat(text):
    return ' '.join(text.split())


class GovInfoWeeklyCompilationAdapter:
    publisher = 'Office of the Federal Register, National Archives and Records Administration'

    def extract(self, response, candidate, metadata_response):
        now = datetime.now(timezone.utc).isoformat()
        decision = classify_response(response.url, response.status, response.text)
        evidence = SourceEvidence(response.url, now, response.status, sha256(response.body).hexdigest())
        result = dict(decision=decision, evidence=evidence, material=None)
        if metadata_response is None:
            return result
        md = metadata_response
        md_decision = classify_response(md.url, md.status, md.text)
        def values(name):
            return md.css(f'meta[name="{name}"]::attr(content)').getall()
        def one(name):
            v = values(name)
            return v[0].strip() if len(v) == 1 else ''
        match = re.fullmatch(r'/content/pkg/(WCPD-\d{4}-\d{2}-\d{2})/html/(WCPD-[^/]+)\.htm', urlsplit(response.url).path)
        expected = f'https://www.govinfo.gov/app/details/{match[1]}/{match[2]}' if match else ''
        pre = response.css('body > pre')
        text = pre[0].xpath('string(.)').get(default='').strip() if len(pre) == 1 else ''
        lines = text.splitlines()
        header = re.fullmatch(r'\[Weekly Compilation of Presidential Documents Volume (\d+), Number \d+ \([A-Za-z]+, ([A-Za-z]+ \d{1,2}, \d{4})\)\]', lines[0]) if lines else None
        try:
            issue_date = datetime.strptime(header[2], '%B %d, %Y').date().isoformat() if header else ''
        except ValueError:
            issue_date = ''
        pages = re.fullmatch(r'\[Pages? (\d+)(?:-(\d+))?\]', lines[1]) if len(lines) > 1 else None
        page_numbers = [int(n) for n in re.findall(r'^\s*\[\[Page (\d+)\]\]\s*$', text, re.M)]
        page_complete = False
        if pages:
            first, last = int(pages[1]), int(pages[2] or pages[1])
            page_complete = first <= last and page_numbers in (list(range(first+1,last+1)), list(range(first,last+1)))
        online = re.fullmatch(r'\[Online from the Government Publishing Office, www\.gpo\.gov\]', lines[2]) if len(lines) > 2 else None
        # Rxx is the publisher's escaped typesetting control, not source prose.
        content = '\n'.join(lines[3:]) if online else ''
        content = re.sub(r'^\s*<R\d{2}>\s*$', '', content, flags=re.M).strip()
        parts = re.split(r'\n\s*\n', content, maxsplit=1)
        title = _flat(parts[0]) if len(parts) == 2 else ''
        metadata_title = _flat(one('dc.title'))
        citation = f'{header[1]} WCPD {pages[1]} ' if header and pages else ''
        published_title = metadata_title[len(citation):] if citation and metadata_title.startswith(citation) else ''
        metadata_ok = bool(
            decision is AccessDecision.ALLOW and md_decision is AccessDecision.ALLOW
            and response.url == candidate.source_url
            and urlsplit(response.url).hostname == 'www.govinfo.gov'
            and match and match[2].startswith(match[1] + '-Pg')
            and md.url == candidate.metadata_url == expected
            and unquote(one('dc.identifier')) == expected
            and one('dc.publisher') == self.publisher
            and one('dc.date') == issue_date == match[1][5:]
            and issue_date and title == published_title
        )
        complete = bool(metadata_ok and page_complete and online
            and re.search(r'</pre>\s*</body>\s*</html>\s*$', response.text, re.I)
            and not re.search(r'could not be verified|tape was incomplete|(?:complete )?tape was not available', text, re.I)
            and len(parts) == 2 and len(parts[1].strip()) > 80)
        body = re.sub(r'^\s*\[\[Page \d+\]\]\s*$', '', content, flags=re.M).strip()
        result['evidence'] = SourceEvidence(response.url, now, response.status, sha256(response.body).hexdigest(), body_complete=complete)
        result['supporting_evidence'] = [dict(evidence=SourceEvidence(md.url, now, md.status, sha256(md.body).hexdigest(), metadata_verified=metadata_ok), raw_response=md.body, decision=md_decision)]
        if complete:
            result['material'] = VerifiedMaterial(self.publisher, issue_date, '; '.join(v.strip() for v in values('dc.creator') if v.strip()) or '未注明', title, '', '', body, response.url)
            result['field_sources'] = {name: md.url for name in ('source', 'time', 'author', 'title')}
            result.update(abstract_origin='none', keywords_origin='none')
        return result


class GovInfoCongressionalRecordAdapter:
    """Issue text plus an already saved, publisher-authorized API metadata page.

    API search metadata establishes identity only. All exported prose must come
    from the public original granule and its independently checked issue header.
    """

    def extract(self, response, candidate, metadata_response):
        now = datetime.now(timezone.utc).isoformat()
        decision = classify_response(response.url, response.status, response.text)
        evidence = SourceEvidence(response.url, now, response.status, sha256(response.body).hexdigest())
        result = dict(decision=decision, evidence=evidence, material=None)
        md = metadata_response
        if md is None:
            return result
        match = re.fullmatch(r'/content/pkg/(CREC-\d{4}-\d{2}-\d{2})/html/(CREC-[^/]+)\.htm', urlsplit(response.url).path)
        try:
            records = json.loads(md.text)['results']
            selected = [r for r in records if match and r.get('packageId') == match[1] and r.get('granuleId') == match[2]]
        except (ValueError, TypeError, KeyError):
            return result
        if len(selected) != 1:
            return result
        record = selected[0]
        pre = response.css('body > pre')
        text = pre[0].xpath('string(.)').get(default='').strip() if len(pre) == 1 else ''
        lines = text.splitlines()
        header = re.fullmatch(r'\[Congressional Record Volume \d+, Number \d+ \([A-Za-z]+, ([A-Za-z]+ \d{1,2}, \d{4})\)\]', lines[0]) if lines else None
        try:
            issued = datetime.strptime(header[1], '%B %d, %Y').date().isoformat() if header else ''
        except ValueError:
            issued = ''
        marker = next((i for i, line in enumerate(lines) if re.fullmatch(r'From the Congressional Record Online through the Government (?:Publishing|Printing) Office \[www\.gpo\.gov\]', line)), None)
        publisher = 'U.S. Government Publishing Office' if marker is not None and 'Publishing' in lines[marker] else 'U.S. Government Printing Office'
        content = '\n'.join(lines[marker+1:]).strip() if marker is not None else ''
        # Some older granules repeat their issue citation before the heading.
        content = re.sub(r'^\[Congressional Record: [^\n]+\]\s*\nFrom the Congressional Record Online via GPO Access \[wais\.access\.gpo\.gov\]\s*', '', content)
        parts = re.split(r'\n\s*\n', content, maxsplit=1)
        title = _flat(parts[0]) if len(parts) == 2 else ''
        pages = next((re.fullmatch(r'\[Pages? ([SHE])?(\d+)(?:-([SHE])?(\d+))?\]', line) for line in lines[:4] if line.startswith('[Page')), None)
        page_complete = False
        if pages:
            prefix, start, end_prefix, end = pages.groups()
            prefix, start, end = prefix or '', int(start), int(end or start)
            actual = re.findall(r'^\s*\[\[Page ([SHE]?\d+)\]\]\s*$', text, re.M)
            expected = [prefix+str(i) for i in range(start+1,end+1)]
            page_complete = end >= start and (not end_prefix or end_prefix == prefix) and actual in (expected, [prefix+str(start)]+expected)
        else:
            # The publisher's 1994 legacy exports print [Page S/H/E] without
            # numerals. They do not assert a missing page range. A matching
            # indexed granule, full HTTP document and explicit article-ending
            # rule still establish the complete published textual object.
            page_complete = bool(any(re.fullmatch(r'\[Page [SHE]\]', line) for line in lines[:4])
                                 and not re.search(r'\[\[Page ', text))
        metadata_ok = bool(
            decision is AccessDecision.ALLOW and md.status == 200
            and response.url == candidate.source_url and urlsplit(response.url).hostname == 'www.govinfo.gov'
            and md.url == candidate.metadata_url and urlsplit(md.url).hostname == 'api.govinfo.gov'
            and urlsplit(md.url).path == '/search'
            and record.get('collectionCode') == 'CREC' and record.get('governmentAuthor') == ['Congress']
            and issued and issued == record.get('dateIssued') == match[1][5:]
            and title and title == _flat(record.get('title', ''))
        )
        complete = bool(metadata_ok and page_complete and len(parts) == 2 and len(parts[1]) > 80
            and re.search(r'\n\s*_{10,}\s*$', content)
            and re.search(r'</pre>\s*</body>\s*</html>\s*$', response.text, re.I)
            and not re.search(r'could not be verified|tape was incomplete|text (?:is )?(?:missing|omitted)', text, re.I))
        result['completion_checks'] = dict(metadata_issue_title_identity=metadata_ok,
            declared_pages_accounted_for=page_complete,
            publisher_pagination='numbered page range' if pages else 'legacy chamber label without page numerals',
            explicit_granule_end=bool(re.search(r'\n\s*_{10,}\s*$', content)),
            closed_source_document=bool(re.search(r'</pre>\s*</body>\s*</html>\s*$', response.text,re.I)))
        body = re.sub(r'^\s*\[\[Page [SHE]?\d+\]\]\s*$', '', content, flags=re.M)
        body = re.sub(r'\n\s*_{10,}\s*$', '', body).strip()
        result['evidence'] = SourceEvidence(response.url, now, response.status, sha256(response.body).hexdigest(), body_complete=complete)
        result['supporting_evidence'] = [dict(evidence=SourceEvidence(md.url, now, md.status, sha256(md.body).hexdigest(), metadata_verified=metadata_ok),raw_response=md.body,decision=AccessDecision.ALLOW)]
        if complete:
            result['material'] = VerifiedMaterial(publisher, issued, 'Congress', title, '', '', body, response.url)
            result['field_sources'] = dict(source=response.url, time=response.url, author=md.url, title=response.url)
            result.update(abstract_origin='none', keywords_origin='none')
        return result
