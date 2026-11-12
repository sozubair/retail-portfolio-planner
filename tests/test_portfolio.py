import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for sub in ("", "01_investment_prioritiser", "02_store_economics", "03_review_pack"):
    sys.path.insert(0, str(ROOT / sub))

import economics as E  # noqa: E402
import prioritiser as P  # noqa: E402
import generate_data  # noqa: E402
import review_pack as RP  # noqa: E402


class Economics(unittest.TestCase):
    def test_npv_matches_hand_calc(self):
        # -100 now, +60 at years 1 and 2, at 10%: -100 + 60/1.1 + 60/1.21 = 4.13
        self.assertAlmostEqual(E.npv(0.10, [-100, 60, 60]), 4.132, places=2)

    def test_irr_of_known_series(self):
        # -100, 0, 121 -> IRR 10% exactly
        self.assertAlmostEqual(E.irr([-100, 0, 121]), 0.10, places=3)

    def test_payback_interpolates(self):
        # -100, 40, 40, 40 -> cumulative crosses zero midway through year 3 -> 2.5
        self.assertAlmostEqual(E.payback_years([-100, 40, 40, 40]), 2.5, places=2)

    def test_positive_npv_project_is_invest_or_review(self):
        data = E.load_formats()
        flagship = next(f for f in data["formats"] if f["format"] == "flagship")
        r = E.evaluate(flagship, data["params"])
        self.assertGreater(r["npv"], 0)
        self.assertIn(r["verdict"][0], ("invest", "review"))

    def test_popup_is_rejected_on_base_case(self):
        data = E.load_formats()
        popup = next(f for f in data["formats"] if f["format"] == "popup_seasonal")
        self.assertEqual(E.evaluate(popup, data["params"])["verdict"][0], "reject")

    def test_slower_ramp_lowers_npv(self):
        data = E.load_formats()
        mall = next(f for f in data["formats"] if f["format"] == "mall_standard")
        base = E.evaluate(mall, {**data["params"], "sales_ramp_mult": 1.0})["npv"]
        slow = E.evaluate(mall, {**data["params"], "sales_ramp_mult": 0.8})["npv"]
        self.assertLess(slow, base)


class Prioritiser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = ROOT / "01_investment_prioritiser" / "portfolios" / "fy27.json"

    def test_respects_budget(self):
        r = P.build(self.port)
        self.assertLessEqual(r["spend"], r["budget"])

    def test_respects_delivery_slots(self):
        r = P.build(self.port)
        self.assertLessEqual(r["slots_used"], r["max_slots"])

    def test_must_do_always_funded(self):
        r = P.build(self.port)
        funded_ids = {s["id"] for s in r["chosen"]}
        self.assertIn("LDN-LEASE", funded_ids)  # the committed refit

    def test_negative_npv_never_funded(self):
        r = P.build(self.port)
        for s in r["chosen"]:
            self.assertGreater(s["npv"], 0)

    def test_tighter_budget_funds_fewer(self):
        wide = P.build(self.port, budget=9000000)
        tight = P.build(self.port, budget=4000000)
        self.assertLessEqual(len(tight["chosen"]), len(wide["chosen"]))

    def test_value_uses_economics_npv(self):
        # a candidate's NPV should equal the economics model NPV for its format (no override)
        r = P.build(self.port)
        data = E.load_formats()
        fmt = {f["format"]: f for f in data["formats"]}
        paris = next(s for s in r["scored"] if s["id"] == "PAR-MALL")
        econ = E.evaluate(fmt["mall_standard"], data["params"])
        self.assertAlmostEqual(paris["npv"], econ["npv"], places=2)


class ReviewPack(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        generate_data.main()
        RP.APPROVALS.write_text("{}")  # start unapproved

    def test_capex_bridge_ties_to_total(self):
        df = RP.load()
        b = RP.capex_bridge(df)
        for _, r in b.iterrows():
            self.assertAlmostEqual(r.volume_effect + r.rate_effect, r.total_var, places=2)

    def test_biggest_drag_is_western_europe(self):
        df = RP.load()
        s = RP.summarise(df)
        self.assertEqual(s.open_var.idxmin(), "Western Europe")

    def test_cost_watch_is_north_america(self):
        df = RP.load()
        b = RP.capex_bridge(df)
        self.assertEqual(b.rate_effect.idxmax(), "North America")

    def test_pack_is_draft_until_approved(self):
        RP.APPROVALS.write_text("{}")
        _, md, status = RP.build()
        self.assertTrue(status.startswith("DRAFT"))
        self.assertIn("DRAFT", md)

    def test_approval_flips_status_and_is_content_bound(self):
        RP.APPROVALS.write_text("{}")
        RP.approve("Test Reviewer")
        _, md, status = RP.build()
        self.assertTrue(status.startswith("APPROVED"))
        # tampering with the data changes the hash, so the old approval no longer applies
        df = RP.load()
        s = RP.summarise(df)
        s.loc["UK & Ireland", "actual_openings"] = 99
        b = RP.capex_bridge(df)
        self.assertNotIn(RP.content_hash(s, b), RP.approvals())
        RP.APPROVALS.write_text("{}")  # clean up


if __name__ == "__main__":
    unittest.main()
