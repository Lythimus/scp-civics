"""Offline tests for facilities.py: python3 skills/scp-facilities/tests/test_facilities.py"""
import importlib.util
import pathlib
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "facilities.py"
spec = importlib.util.spec_from_file_location("fac", SCRIPT)
fac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fac)


def ai(id, name, addr, type="Chemicals And Allied Products", alt=()):
    return {"id": id, "name": name, "physicalAddress": addr, "typeName": type, "alternateIds": list(alt)}
def row(reg, name, street="1 X ST", tri=None):
    return {"RegistryID": reg, "FacName": name, "FacStreet": street, "TRIIDs": tri}

class Key(unittest.TestCase):
    def test_spellings(self):
        for a, b in [("355 Highway 3142", "355 Hwy 3142"), ("355 Louisiana Hwy 3142 • Bldg 732", "355 Hwy 3142"),
                     ("La. Highways 18 and 3142 • 355 Hwy 3142", "355 HWY 3142"), ("261 LA-3142", "261 Hwy 3142"),
                     ("12501B River Road", "12501 River Rd"), ("12501R S River Rd\n(a portion of)", "12501 River Rd"),
                     ("15849-A Old Spanish Trail", "15849 Old Spanish Trail"), ("14891 Airline Drive", "14891 E Airline Hwy"),
                     ("11842 River Rd, Lot 2", "11842 River Rd")]:
            self.assertEqual(fac.join_key(a), fac.join_key(b), a); self.assertTrue(fac.join_key(a))
    def test_distinct_and_empty(self):
        self.assertNotEqual(fac.join_key("471 Hwy 3142"), fac.join_key("473 Hwy 3142"))
        self.assertEqual(fac.join_key("201James Dr E"), "201 JAMES")
        for x in ["29.9298 - 90.3359", "In", "", None, "Hwys 18 & 3142", "Mississippi RM 131"]:
            self.assertEqual(fac.join_key(x), "", x)
    def test_id_forms(self):
        self.assertIn("2208900027", fac.id_forms("LA0000002208900027"))

class Status(unittest.TestCase):
    def entry(self, name, *echo):
        return {"ai": ai("1", name, "1 X St"), "echo": [{"row": row("9", n), "how": h, "shared": s} for n, h, s in echo]}
    def test_tenant_on_neighbors_record(self):
        self.assertEqual(fac.status_cell(self.entry("Vopak Terminal LLC", ("UNION CARBIDE CORP", "ID", True))),
                         "On a shared EPA record, not in this company's name")
    def test_own_name_on_shared_record(self):
        self.assertEqual(fac.status_cell(self.entry("Union Carbide Corp - St Charles", ("UNION CARBIDE CORP", "ID", True))), "EPA active")
    def test_sole_record_in_old_name(self):
        self.assertEqual(fac.status_cell(self.entry("Linde Inc", ("PRAXAIR INC", "ID", False))), "EPA active")
    def test_st_charles_is_not_a_company_match(self):
        self.assertFalse(fac.own_record("St Charles Clean Fuels LLC", "UNION CARBIDE CORP - ST CHARLES PLANT"))
    def test_address_only(self):
        self.assertEqual(fac.status_cell(self.entry("Acme", ("ACME", "address", False))), "EPA active (joined by address)")
    def test_none(self):
        self.assertEqual(fac.status_cell(self.entry("Acme")), "LDEQ AI only")

class Cell(unittest.TestCase):
    def test_shared_marker(self):
        e = {"echo": [{"row": row("9", "COMPLEX "), "how": "ID", "shared": True}, {"row": row("1", "OWN"), "how": "ID", "shared": False}]}
        self.assertEqual(fac.echo_cell(e), "1 OWN; 9 COMPLEX (shared)")

class Join(unittest.TestCase):
    def test_id_beats_address_and_multi(self):
        ais = [ai("1", "A", "5 River Rd", alt=["2208900027"]), ai("2", "B", "5 River Rd"), ai("3", "C", "7 Oak St")]
        out = fac.join(ais, [row("r1", "A", "5 RIVER RD"), row("r2", "?", "5 RIVER RD"), row("r3", "C", "7 OAK ST"), row("r4", "Z", "9 NONE")],
                       {"r1": {"LA0000002208900027"}, "r2": set(), "r3": set(), "r4": set()})
        self.assertEqual(out["r1"], ({"1"}, "ID"))
        self.assertEqual(out["r2"], ({"1", "2"}, "address"))
        self.assertEqual(out["r3"], ({"3"}, "address"))
        self.assertEqual(out["r4"], (set(), ""))

class Render(unittest.TestCase):
    def test_rmp_not_assigned_to_rows(self):
        a, b = ai("1", "Air Co", "12501 River Rd"), ai("2", "Other Co", "12501 River Road")
        groups = {fac.site_key(a): [{"ai": a, "echo": []}, {"ai": b, "echo": []}]}
        rmp = [{"EPAFacilityID": "100", "name": "Air Co H2", "address": "12501B River Road", "sub_last": {"date_val": "2025-01-01"}},
               {"EPAFacilityID": "200", "name": "Elsewhere", "address": "Prospect Ave • Post 2", "sub_last": {"date_val": "2020-01-01", "date_dereg": "2021-01-01"}}]
        md = fac.markdown(groups, [], [], rmp, 2, 0, "2026-11-03")
        self.assertIn("RMP filings at this address: 100 Air Co H2 (validated 2025-01-01).", md)
        self.assertEqual(md.count("100 Air Co H2"), 1)
        self.assertIn("deregistered 2021-01-01", md)
        self.assertIn("no roster address", md)
    def test_selection_ignores_deregistered(self):
        self.assertFalse(fac.echo_selected({"FacStreet": "11842 RIVER RD", "FacSICCodes": None}, {"1 X"}))
        self.assertTrue(fac.echo_selected({"FacStreet": "207 HWY 3142", "FacSICCodes": None}, {fac.join_key("207 Hwy 3142")}))
        self.assertTrue(fac.echo_selected({"FacStreet": "", "FacSICCodes": "2911"}, set()))
    def test_company_filter(self):
        self.assertFalse(fac.looks_like_company(ai("1", "Incident T123456", "")))
        self.assertFalse(fac.looks_like_company(ai("1", "T123456 - dump", "")))
if __name__ == "__main__":
    unittest.main()
