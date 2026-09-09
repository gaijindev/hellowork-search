"""Example: search Hello Work for IT jobs in Tokyo containing a keyword."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import hellowork as hw

s = hw.new_session()
# Tokyo (13), IT occupations (1100 with parent group 11), free word in job description,
# full-width text with full-width-space separators, 0 = OR.
r = hw.search(s, freeword="英語", freeword_mode="0",
              free_targets=("3",), occupations=("1100",), todofuken="13")
print("hits:", hw.page_count(r.text))
for it in hw.collect(s, r, max_pages=2):
    print(it["kjno"], "|", it["title"], "|", it["company"], "|", it["pay"], "|", it["place"])
    print("  ", it["url"])
