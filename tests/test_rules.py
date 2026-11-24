"""Tests for the fixed scoring rules. Run:  python -m unittest discover tests"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
import green_claims_checker as g  # noqa: E402


def claim(**flags):
    f = {k: False for k in g.FLAGS}
    f.update(flags)
    c = g.Claim(quote="test", page=1, topic="other", rewrite="", flags=f)
    g.assess(c)
    return c


class Verdicts(unittest.TestCase):
    def test_offsets_not_approved(self):
        self.assertEqual(claim(offset_based=True, quantified=True, scope_stated=True, evidence_cited=True).score, 0)

    def test_broad_term_without_evidence_not_approved(self):
        self.assertEqual(claim(generic_term=True).score, 0)

    def test_broad_term_with_evidence_not_red(self):
        self.assertNotEqual(claim(generic_term=True, evidence_cited=True).score, 0)

    def test_absolute_without_evidence_not_approved(self):
        self.assertEqual(claim(absolute_claim=True, quantified=True, scope_stated=True).score, 0)

    def test_target_without_plan_or_evidence_not_approved(self):
        self.assertEqual(claim(future_target=True, quantified=True, scope_stated=True).score, 0)

    def test_fully_supported_is_approved(self):
        c = claim(quantified=True, scope_stated=True, evidence_cited=True, comparative=True, baseline_stated=True)
        self.assertEqual(c.score, 2)
        self.assertEqual(g.LABEL[c.score], "Approved")

    def test_comparison_without_baseline_is_moderate(self):
        self.assertEqual(claim(quantified=True, scope_stated=True, evidence_cited=True, comparative=True).score, 1)

    def test_missing_number_is_moderate(self):
        c = claim(scope_stated=True, evidence_cited=True)
        self.assertEqual(c.score, 1)
        self.assertIn("No number given", [r[0] for r in c.reasons])

    def test_target_with_plan_and_evidence_approved(self):
        self.assertEqual(claim(future_target=True, plan_stated=True, quantified=True, scope_stated=True,
                               evidence_cited=True).score, 2)

    def test_explanations(self):
        self.assertTrue(g.verdict_why(claim(generic_term=True)).startswith("Not approved because"))
        self.assertTrue(g.verdict_why(claim(scope_stated=True)).startswith("Moderately approved"))


class Reading(unittest.TestCase):
    def test_page_markers(self):
        s = g.to_sentences("[p.3] Our emissions fell 20% in 2024. We planted trees.")
        self.assertEqual(s[0].page, 3)

    def test_filter_keeps_green_sentences_in_long_text(self):
        text = ("The board met four times this year to review the accounts. " * 80
                + "Our scope 1 emissions fell 12% compared with 2020.")
        kept = [x.text for x in g.candidates(text)]
        self.assertTrue(any("emissions" in k for k in kept))
        self.assertFalse(any("board met" in k for k in kept))

    def test_parse_json_with_fence(self):
        self.assertEqual(g.parse_json_array('```json\n[{"quote":"x"}]\n```'), [{"quote": "x"}])


class Reports(unittest.TestCase):
    def test_csv_and_html(self):
        c = claim(generic_term=True)
        c.quote = 'Eco-friendly <and> "green"'
        with tempfile.TemporaryDirectory() as d:
            g.write_csv([c], os.path.join(d, "r.csv"))
            g.write_html([c], os.path.join(d, "r.html"), "test.pdf")
            page = open(os.path.join(d, "r.html"), encoding="utf-8").read()
            self.assertIn("&lt;and&gt;", page)
            self.assertIn("Not approved", open(os.path.join(d, "r.csv"), encoding="utf-8-sig").read())


if __name__ == "__main__":
    unittest.main()
