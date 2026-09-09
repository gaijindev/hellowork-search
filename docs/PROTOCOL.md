# Hello Work (hellowork.mhlw.go.jp) Job Search - Scriptable Protocol

Hello Work's internet job-search site is a server-rendered Java app. The entire search workflow can be driven with plain HTTP (curl or any HTTP client). No JavaScript execution, captcha, login, or geo-restriction is involved for unauthenticated search. All endpoints below live under:

```
BASE = https://www.hellowork.mhlw.go.jp/kensaku/
```

Notes:
- Use a browser-like TLS fingerprint if possible (e.g. curl_cffi with `impersonate="chrome"`); plain curl may also work but impersonation is safer.
- The site is Shift_JIS-era UI but serves UTF-8. Japanese text in requests must be UTF-8 encoded form data.

---

## 1. Session init

```
GET BASE + GECA110010.do?action=initDisp&screenId=GECA110010
```

This sets a `JSESSIONID` cookie. Keep cookies for the whole workflow (search -> pagination -> detail fetches all use the same session).

## 2. Search request

```
POST BASE + GECA110010.do
Content-Type: application/x-www-form-urlencoded
```

The search form is `form_1`. These fields drive the query:

### Core fields (always send)

| Field | Value |
|---|---|
| `screenId` | `GECA110010` |
| `action` | `` (empty) |
| `kjKbnRadioBtn` | `1` (general jobs; 2=new grads, 5=disabled-applicant listings) |
| `searchBtn` | ` 検索する` (note the leading space; presence of this field triggers the search) |
| `kyujinkensu` | `0` |
| `searchClear` | `0` |
| `summaryDisp` | `false` |
| `searchInitDisp` | `0` |
| `preCheckFlg` | `false` |
| `hiddenViewedKyujinList` | `` |
| `CHECKEDKJNOLIST` | `` |
| `iNFTeikyoRiyoDantaiID` | `` |
| `kiboSuruSKSU1Hidden` / `2` / `3` | `` |
| `ensenHidden`, `roudousijyoHidden` | `` |
| `codeAssistType`, `codeAssistKind`, `codeAssistCode`, `codeAssistItemCode`, `codeAssistItemName`, `codeAssistDivide` | `` |
| `maba_vrbs` | Copy the value verbatim from the init page's hidden `maba_vrbs` input (a comma-separated button registry). |

### Query-driving fields

| Field | Meaning |
|---|---|
| `todohukenHidden` | Prefecture code. `13` = Tokyo. (Standard JIS prefecture codes.) |
| `freeWordInput` | Free-word query. **All characters must be full-width** (e.g. `社内ＳＥ`, not `社内SE`; ASCII letters/digits must be converted to their full-width forms). **Multiple words are separated by a full-width space (U+3000)**, e.g. `情シス　ヘルプデスク`. Half-width input is rejected with a generic input error. |
| `freeWordRadioBtn` | Word matching: **`0` = OR** (any word), **`1` = AND** (all words). Counter-intuitive: 0 is OR. |
| `freeCKBox` | Which listing fields the free word searches. Repeatable checkbox: `1`=職種 (job title), `2`=事業所名 (company), `3`=仕事内容 (job description), `4`=最寄り駅, `5`=就業場所 (work location), `6`=事業内容, `7`=必要な免許・資格, `8`=必要な経験, `9`=その他. Send each desired value as its own `freeCKBox` pair. |
| `nOTKNSKFreeWordInput` | NOT word: exclude listings containing this (e.g. `講師` to drop teaching roles). |
| `easyShokusyuBox` | Occupation code (easy-search set). Useful values: `1100` = IT全般 (all IT), `1101` = システムエンジニア, `1102` = PM等, `1103` = ヘルプデスク, `1104` = Webデザイナー. |
| `daiEasyShokusyuBox` | **Required pairing**: the 2-digit parent group of every `easyShokusyuBox` code (`1100` -> `11`). If you send an occupation code without its parent group, the request is rejected. One `daiEasyShokusyuBox` per selected group. |
| `jyoukenBox` | Condition checkboxes (repeatable): `20260101001`=新着(直近3日), `20260101003`=正社員, `20260101004`=正社員以外, `20260101024`=経験不問, `20260101025`=学歴不問, `20260101026`=資格不問, `20260101027`=転勤なし, `20260101031`=駅近(徒歩10分以内). |
| `tokusyuBox` | Special-feature checkboxes (industry-specific sets; mostly not needed for IT search). |

### Encoding pitfall

When a field is repeated (checkboxes), send **repeated key=value pairs** (`freeCKBox=1&freeCKBox=3`). Do NOT rely on HTTP-client "dict with list value" shortcuts - some clients (e.g. curl_cffi) mis-serialize those, and the site then rejects the request.

### Error handling

A rejected request returns HTTP 200 with the search form re-rendered and the text `入力エラーがあります`; offending field containers get the CSS class `input_error`. A successful search returns the results page containing `検索結果`/`<table class="kyujin` rows and a `NNN件` hit count.

## 3. Results page

- Hit count: first `([\d,]+)件` in the page text.
- Each listing is a `<table class="kyujin">` block containing, in labeled form: 受付年月日 (posted date), 紹介期限日 (deadline), 職種 (title), 仕事の内容, 事業所名 (company), 就業場所 (location), 賃金 (`270,333円〜270,333円` monthly range), 求人番号 (`NNNNN-NNNNNNNN` - the stable job ID), tags such as `新着`, `正社員`, `経験不問`, `学歴不問`, `転勤なし`, `オンライン自主応募可` (online self-application available), plus 求人数.
- Detail link per row: `<a href="./GECA110010.do?screenId=GECA110010&action=dispDetailBtn&kJNo=<digits>&kJKbn=1&jGSHNo=<urlencoded-token>&fullPart=1&...">`. Fetch it with a plain GET inside the same session - the `jGSHNo` token is what binds the row, so take the href verbatim from the page.

## 4. Sort, page size, pagination

The results page re-renders the same form with all state echoed into hidden inputs. To manipulate the list, repost the form with every hidden field plus:

| Field | Values |
|---|---|
| `fwListNaviSort` (hidden) | `1`=新着順 (newest first - default), `2`=下限賃金順, `3`=上限賃金順, `5`=紹介期限日順 |
| `fwListNaviDisp` (hidden) | `10`, `30`, or `50` (results per page) |
| `fwListNaviBtnNext` | `次へ＞` - go to next page |
| `fwListNaviBtnPrev` | `＜前へ` - previous page |
| `fwListNaviBtn2`..`5` | jump to numbered page |

Set the hidden `fwListNaviSort`/`fwListNaviDisp` (the visible `<select>`s `fwListNaviSortTop`/`fwListNaviDispTop` are just JS sugar over these). Last page reached when the 次へ button renders `disabled`.

## 5. Example queries (field excerpts)

Tokyo, IT occupations, job-description contains "英語", excluding 講師 (teaching):

```
screenId=GECA110010&action=&kjKbnRadioBtn=1&searchBtn= 検索する
&todohukenHidden=13
&freeWordInput=英語&freeWordRadioBtn=0&freeCKBox=3&nOTKNSKFreeWordInput=講師
&daiEasyShokusyuBox=11&easyShokusyuBox=1100
(plus the core always-send fields from section 2)
```

Tokyo helpdesk listings, bilingual, newest first, 50/page:

```
daiEasyShokusyuBox=11&easyShokusyuBox=1103
&freeWordInput=英語&freeWordRadioBtn=0&freeCKBox=3
then repost results form with fwListNaviSort=1&fwListNaviDisp=50&fwListNaviBtnNext=次へ＞
```

Multi-word OR over title+description ("社内SE" or "情シス" or "ヘルプデスク" or "デスクトップサポート"):

```
freeWordInput=社内ＳＥ　情シス　ヘルプデスク　デスクトップサポート  (full-width, U+3000 separators)
freeWordRadioBtn=0
freeCKBox=1&freeCKBox=3
```

## 6. Application flow caveat

Search and detail reads are fully automatable. Applying is not a plain web form: listings flagged `オンライン自主応募可` support online application but require a 求職者マイページ account login (Hello Work job-seeker registration); other listings are handled via the local 安定所 (Hello Work office) by phone or visit, quoting the 求人番号.
