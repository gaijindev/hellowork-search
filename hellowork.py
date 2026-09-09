"""Hello Work (hellowork.mhlw.go.jp) job search - scriptable workflow."""
import re, time, sys
from urllib.parse import urljoin
import curl_cffi.requests as cr

BASE = "https://www.hellowork.mhlw.go.jp/kensaku/"
MABA = "infTkRiyoDantaiBtn,searchShosaiBtn,searchBtn,searchNoBtn,searchClearBtn,searchNoClearBtn,searchNoClearBtn_mobile,dispDetailBtn,kyujinhyoBtn,checkedKyujinViewBtn,checkedKyujinhyoIppanBtn,checkedKyujinhyoDsBtn,changeSearchCond"

def new_session():
    s = cr.Session(impersonate="chrome")
    s.get(BASE + "GECA110010.do?action=initDisp&screenId=GECA110010", timeout=30)
    return s

def search(s, freeword=None, freeword_mode="0", free_targets=("3",), occupations=(),
           todofuken="13", notword=None, kjkbn="1", jyouken=(), tokusyu=()):
    data = {
     "screenId":"GECA110010","action":"","kjKbnRadioBtn":kjkbn,
     "todohukenHidden":todofuken,
     "freeWordInput":freeword or "","freeWordRadioBtn":freeword_mode,
     "nOTKNSKFreeWordInput":notword or "",
     "kyujinkensu":"0","iNFTeikyoRiyoDantaiID":"","searchClear":"0",
     "kiboSuruSKSU1Hidden":"","kiboSuruSKSU2Hidden":"","kiboSuruSKSU3Hidden":"",
     "summaryDisp":"false","searchInitDisp":"0","hiddenViewedKyujinList":"","CHECKEDKJNOLIST":"",
     "codeAssistType":"","codeAssistKind":"","codeAssistCode":"","codeAssistItemCode":"",
     "codeAssistItemName":"","codeAssistDivide":"",
     "maba_vrbs":MABA,"preCheckFlg":"false","searchBtn":" 検索する",
    }
    if freeword: data["freeCKBox"] = list(free_targets)
    for occ in occupations:
        data.setdefault("daiEasyShokusyuBox", []).append(occ[:2])
        data.setdefault("easyShokusyuBox", []).append(occ)
    if jyouken: data["jyoukenBox"] = list(jyouken)
    if tokusyu: data["tokusyuBox"] = list(tokusyu)
    pairs = []
    for k, v in data.items():
        if isinstance(v, list): pairs.extend((k, x) for x in v)
        else: pairs.append((k, v))
    r = s.post(BASE + "GECA110010.do", data=pairs, timeout=30)
    if "入力エラー" in r.text:
        raise RuntimeError("search rejected (input error)")
    return r

def hidden_fields(html):
    fields = {}
    for tag in re.findall(r'<input[^>]*>', html):
        nm = re.search(r'name="([^"]+)"', tag)
        ty = re.search(r'type="([^"]+)"', tag)
        if not nm: continue
        if ty and ty.group(1) in ("submit","button","checkbox","radio","image","file"): continue
        val = re.search(r'value="([^"]*)"', tag)
        fields[nm.group(1)] = (val.group(1) if val else "")
    return fields

def page_count(html):
    m = re.search(r'([\d,]+)\s*件', re.sub(r'<[^>]+>',' ',html))
    return int(m.group(1).replace(",","")) if m else 0

def parse_items(html):
    items = []
    for blk in re.split(r'<table class="kyujin ', html)[1:]:
        it = {}
        m = re.search(r'href="(\./GECA110010\.do\?screenId=GECA110010&amp;action=dispDetailBtn[^"]*)"', blk)
        it["url"] = urljoin(BASE+"GECA110010.do", m.group(1).replace('&amp;','&')) if m else None
        t = re.sub(r'<script.*?</script>','',blk,flags=re.S)
        t = re.sub(r'<[^>]+>','|',t); t = re.sub(r'\|+','|',t)
        def grab(label):
            m = re.search(re.escape(label) + r'(?:\s*[|：])+\s*([^|]*)', t)
            return m.group(1).strip() if m else ""
        it["received"] = grab("受付年月日"); it["deadline"] = grab("紹介期限日")
        it["title"] = grab("職種"); it["company"] = grab("事業所名")
        it["place"] = grab("就業場所")
        m2 = re.search(r'([0-9,]+)円.{0,3}?([0-9,]+)円', t)
        it["pay"] = (m2.group(1)+"~"+m2.group(2)+"円") if m2 else grab("賃金")
        it["kjno"] = grab("求人番号")
        it["tags"] = [x for x in ["新着","経験不問","学歴不問","転勤なし","書類選考なし","オンライン自主応募可","正社員","フル","パート"] if x in t]
        items.append(it)
    return items

def next_page(s, html, disp="50", sort="1"):
    f = hidden_fields(html)
    f["fwListNaviDisp"] = disp; f["fwListNaviSort"] = sort
    f["fwListNaviBtnNext"] = "次へ＞"
    return s.post(BASE + "GECA110010.do", data=f, timeout=30)

def collect(s, first_resp, max_pages=10, disp="50", delay=1.0):
    all_items, html = [], first_resp
    for p in range(max_pages):
        all_items.extend(parse_items(html.text if hasattr(html,"text") else html))
        txt = html.text if hasattr(html,"text") else html
        if 'value="次へ＞" disabled' in txt: break
        time.sleep(delay)
        html = next_page(s, txt, disp=disp)
    return all_items
