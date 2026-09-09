"""Daily reference snapshot: IT jobs in Tokyo mentioning 英語 (bilingual IT lane)."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import hellowork as hw

def main():
    s = hw.new_session()
    r = hw.search(s, freeword="英語", freeword_mode="0", free_targets=("3",),
                  occupations=("1100",), todofuken="13", notword="講師")
    items = hw.collect(s, r, max_pages=5)
    os.makedirs("data", exist_ok=True)
    with open("data/listings-it-tokyo-english.jsonl", "w") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print(f"{len(items)} listings")

if __name__ == "__main__":
    main()
