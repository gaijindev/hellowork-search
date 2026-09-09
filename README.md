# hellowork-search

Unofficial Python client + protocol documentation for searching job listings on
[Hello Work Internet Service](https://www.hellowork.mhlw.go.jp/) (ハローワークインターネットサービス),
Japan's public employment security office job board.

Hello Work has no official public search API. This project documents the site's
form-POST search workflow and provides a small library that drives it:
session handling, query parameters, pagination, result parsing, and detail links.

## Features

- Keyword search with AND/OR/NOT semantics across selectable listing fields
- Occupation codes (e.g. all-IT `1100`, helpdesk `1103`), prefecture filters
- Sort order (newest, salary, deadline), page size, full pagination
- Parsed listing rows: job number (求人番号), title, company, location, salary range, tags
- Direct detail-page URLs per listing

No login is required for search and detail reads.

## Install

```bash
pip install curl_cffi
```

## Quickstart

```python
import hellowork as hw

s = hw.new_session()
r = hw.search(s, freeword="英語", freeword_mode="0",
              free_targets=("3",), occupations=("1100",), todofuken="13")
print(hw.page_count(r.text), "hits")
for item in hw.collect(s, r, max_pages=2):
    print(item["kjno"], item["title"], item["pay"], item["url"])
```

See `examples/search_it_tokyo.py` for a runnable version.

## The four quirks that break naive scrapers

1. **Full-width keywords only.** `freeWordInput` must be full-width text
   (`社内ＳＥ`, not `社内SE`), and multi-word queries separate with a
   full-width space (U+3000). Half-width input is rejected with a generic
   input error.
2. **Inverted AND/OR radio.** `freeWordRadioBtn=0` is OR, `1` is AND.
3. **Occupation codes need their parent group.** Sending
   `easyShokusyuBox=1100` without `daiEasyShokusyuBox=11` is rejected.
4. **Repeated checkboxes must be repeated POST pairs.** Serialize
   `freeCKBox=1&freeCKBox=3` as repeated key=value pairs; some HTTP clients
   mis-encode dict-of-lists and the site rejects the request.

The full field map, pagination protocol, and worked examples are in
[docs/PROTOCOL.md](docs/PROTOCOL.md).

## Caveats

- Applying to jobs is out of scope: listings marked オンライン自主応募可 require a
  求職者マイページ account; others route through a Hello Work office.
- This is an unofficial client. Respect the site's terms and keep request rates low.
- No affiliation with the Ministry of Health, Labour and Welfare.

## License

MIT
