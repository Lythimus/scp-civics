"""Offline tests for communities.py: python3 -m unittest discover -s skills/scp-communities/tests

Every polygon, block and census row here is made up. No resident's address belongs here.
"""
import io
import sys
import tempfile
import unittest
import urllib.parse
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import communities as cm  # noqa: E402

SQUARE = [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]
DONUT = [[[0, 0], [0, 4], [4, 4], [4, 0], [0, 0]], [[1, 1], [3, 1], [3, 3], [1, 3], [1, 1]]]


def feature(name, rings, key="name"):
    return {"a": {key: name}, "rings": rings}


class Geometry(unittest.TestCase):
    def test_contains_and_holes(self):
        self.assertTrue(cm.contains(SQUARE, 0.5, 0.5))
        self.assertFalse(cm.contains(SQUARE, 1.5, 0.5))
        self.assertTrue(cm.contains(DONUT, 0.5, 2))
        self.assertFalse(cm.contains(DONUT, 2, 2), "a point in the hole is outside")

    def test_bbox_short_circuit(self):
        self.assertFalse(cm.contains(SQUARE, 5, 5, cm.bbox(SQUARE)))

    def test_km_to_polygon(self):
        self.assertEqual(cm.km_to_polygon(SQUARE, 0.5, 0.5), 0.0)
        # 0.01 degree east of the edge at the equator is about 1.11 km
        self.assertAlmostEqual(cm.km_to_polygon(SQUARE, 1.01, 0.5), 1.113, places=2)

    def test_centroid(self):
        x, y = cm.centroid([[[0, 0], [0, 2], [2, 2], [2, 0], [0, 0]]])
        self.assertAlmostEqual(x, 1)
        self.assertAlmostEqual(y, 1)

    def test_touches(self):
        far = [[[5, 5], [5, 6], [6, 6], [6, 5], [5, 5]]]
        overlap = [[[0.5, 0.5], [0.5, 2], [2, 2], [2, 0.5], [0.5, 0.5]]]
        self.assertFalse(cm.touches(SQUARE, far))
        self.assertTrue(cm.touches(SQUARE, overlap, step=1))

    def test_areas(self):
        areas = cm.Areas([feature("A", SQUARE), feature("B", [[[1, 0], [1, 1], [2, 1], [2, 0], [1, 0]]])], "name")
        self.assertEqual(areas.at(0.5, 0.5), ["A"])
        self.assertEqual(areas.at(1.5, 0.5), ["B"])
        self.assertEqual(areas.names(), ["A", "B"])


class Census(unittest.TestCase):
    def test_num_sentinels(self):
        self.assertIsNone(cm.num("-666666666"))
        self.assertIsNone(cm.num(None))
        self.assertEqual(cm.num("250,000+"), 250000)
        self.assertEqual(cm.num("12"), 12)

    def test_acs_sum_root_sum_of_squares(self):
        row = {"T_001E": "10", "T_001M": "3", "T_002E": "20", "T_002M": "4"}
        est, moe = cm.acs_sum(row, "T", ["001", "002"])
        self.assertEqual(est, 30)
        self.assertAlmostEqual(moe, 5)

    def test_acs_share_formula(self):
        row = {"T_001E": "1000", "T_001M": "100", "T_002E": "200", "T_002M": "50"}
        p, moe, reliable = cm.acs_share(row, "T", ["002"], ["001"])
        self.assertAlmostEqual(p, 20)
        # sqrt(50^2 - 0.2^2 * 100^2) / 1000 = sqrt(2100) / 1000
        self.assertAlmostEqual(moe, 100 * (2100 ** 0.5) / 1000)
        self.assertTrue(reliable)

    def test_acs_share_ratio_fallback_and_unreliable(self):
        row = {"T_001E": "100", "T_001M": "90", "T_002E": "90", "T_002M": "10"}
        p, moe, reliable = cm.acs_share(row, "T", ["002"], ["001"])
        self.assertAlmostEqual(moe, 100 * ((10 ** 2 + 0.9 ** 2 * 90 ** 2) ** 0.5) / 100)
        self.assertFalse(reliable)
        self.assertEqual(cm.acs_share({}, "T", ["002"], ["001"]), (None, None, False))

    def test_fmt_share(self):
        self.assertEqual(cm.fmt_share((20.0, 4.6, True)), "20% ±5")
        self.assertIn("unreliable", cm.fmt_share((3.0, 4.0, False)))
        self.assertEqual(cm.fmt_share((None, None, False)), "n/a")


def block(pop, lat, lon, **kw):
    b = {"pop": pop, "lat": lat, "lon": lon, "hisp": 0, "white": 0, "black": 0, "asian": 0, "p2_total": pop}
    b.update(kw)
    return b


class Blocks(unittest.TestCase):
    def setUp(self):
        self.communities = cm.Areas([feature("NORTH", SQUARE)], "name")
        self.council = cm.Areas([feature("1", SQUARE, "district")], "district")
        self.flum = cm.Areas([feature("Heavy Industrial", [[[0, 0], [0, 0.5], [1, 0.5], [1, 0], [0, 0]]], "dev_type")],
                             "dev_type")
        self.blocks = {"a": block(10, 0.25, 0.5, black=6), "b": block(30, 0.75, 0.5), "c": block(5, 3, 3)}
        cm.assign_blocks(self.blocks, self.communities, self.council, self.flum)

    def test_assignment(self):
        self.assertEqual(self.blocks["a"]["community"], "NORTH")
        self.assertEqual(self.blocks["a"]["flum"], "Heavy Industrial")
        self.assertEqual(self.blocks["b"]["flum"], "")
        self.assertEqual(self.blocks["c"]["community"], "")

    def test_tiling_reports_loose_population(self):
        lines = cm.tiling(self.blocks, self.communities)
        self.assertIn("40 of 45 people", lines[0])
        self.assertIn("5 are not", lines[0])
        self.assertTrue(any("5 people are in blocks outside every council district" in l for l in lines))

    def test_near_population(self):
        site = [{"lat": 0.25, "lon": 0.5}]
        inside = [b for b in self.blocks.values() if b["community"] == "NORTH"]
        self.assertEqual(cm.near_population(inside, site, 1), 10)  # b is ~55 km away at these made-up coordinates
        self.assertEqual(cm.near_population(inside, site, 100), 40)

    def test_totals(self):
        t = cm.block_totals(self.blocks.values())
        self.assertEqual((t["pop"], t["black"]), (45, 6))


class Rezonings(unittest.TestCase):
    def test_split_ordinances(self):
        self.assertEqual(cm.split_ordinances("26-9-1; 82-1-7"), ["26-9-1", "82-1-7"])
        self.assertEqual(cm.split_ordinances("* and others"), [])
        self.assertEqual(cm.split_ordinances("26-9-2 "), ["26-9-2"])

    def test_families(self):
        self.assertTrue(cm.is_industrial("M-2"))
        self.assertFalse(cm.is_industrial("MS"))
        self.assertEqual(cm.zone_family(["C-3"], ["M-1"]), "newly industrial (M)")
        self.assertEqual(cm.zone_family(["M-2"], ["M-1"]), "within industrial (M to M)")
        self.assertEqual(cm.zone_family(["O-L"], ["M-1", "R-1M"]), "newly industrial (M)")
        self.assertEqual(cm.zone_family(["R-1A"], ["C-2"]), "commercial")
        self.assertEqual(cm.zone_family(["C-2"], ["R-1A(M)"]), "residential")
        self.assertEqual(cm.zone_family(["C-2"], ["O-L"]), "other")

    def test_place_ordinances(self):
        communities = cm.Areas([feature("NORTH", SQUARE)], "name")
        council = cm.Areas([feature("5", SQUARE, "district")], "district")
        zoning = [{"a": {"zoning": "M1 ", "oridnance": "19-1-1; 05-4-12"}, "rings": SQUARE},
                  {"a": {"zoning": "R-1AM", "oridnance": " "}, "rings": SQUARE}]
        placed = cm.place_ordinances(zoning, communities, council)
        self.assertEqual(placed["19-1-1"], [("NORTH", "5", "M1")])
        self.assertIn("05-4-12", placed)
        self.assertEqual(len(placed), 2)
        self.assertEqual(cm.norm_zone("R-1AM"), "R1AM")


class Privacy(unittest.TestCase):
    def test_layer_queries_never_ask_for_links_or_logins(self):
        captured = {}

        def fake(layer, fields, *a, **k):
            captured[layer] = fields
            return []
        stub = mock.Mock(rezoning_matters=lambda: [], load_all=lambda m, c: ([], []), summarize=lambda r: r)
        with mock.patch.object(cm, "arcgis", fake), mock.patch.object(cm, "load_decisions", return_value=stub), \
                redirect_stdout(io.StringIO()):
            cm.main(["--cache", tempfile.mkdtemp(), "distribution", "--decisions-cache", tempfile.mkdtemp()])
        self.assertIn(cm.ZONING_LAYER, captured)
        for fields in captured.values():
            for bad in ("hyperlink", "created_user", "last_edited_user", "owner"):
                self.assertNotIn(bad, fields)

    def test_cache_refuses_plugin_folder(self):
        with self.assertRaises(SystemExit):
            cm.Cache(Path(cm.__file__).resolve().parent / "cache")

    def test_point_output_has_no_block_figures(self):
        with mock.patch.object(cm, "geocode", return_value=[{"score": 100, "address": "X", "location": {"x": 0.5, "y": 0.5}}]), \
                mock.patch.object(cm, "load_geo", return_value=(cm.Areas([feature("NORTH", SQUARE)], "name"),
                                                                cm.Areas([feature("1", SQUARE, "district")], "district"),
                                                                cm.Areas([], "dev_type"))), \
                mock.patch.object(cm, "fetch_json", return_value={"features": [{"attributes": {"GEOID": "220890627003"}}]}), \
                mock.patch.object(cm, "acs_small_areas", return_value={}):
            out = io.StringIO()
            with redirect_stdout(out):
                code = cm.main(["--cache", tempfile.mkdtemp(), "point", "1 Test St"])
        self.assertEqual(code, 0)
        text = out.getvalue()
        self.assertIn("block group 3", text)
        self.assertNotIn("Block 1", text)
        self.assertIn("left out on purpose", text)


class Income(unittest.TestCase):
    def test_top_coded_median(self):
        self.assertEqual(cm.fmt_income({"B19013_001E": "250,000+", "B19013_001M": "***"}), "$250,000+")
        self.assertEqual(cm.fmt_income({"B19013_001E": "71220", "B19013_001M": "12724"}), "$71,220 ±12,724")
        self.assertEqual(cm.fmt_income({}), "n/a")


class Sites(unittest.TestCase):
    def test_default_is_roster(self):
        sites = [{"roster": True, "id": "1"}, {"roster": False, "id": "2"}]
        self.assertEqual([f["id"] for f in cm.select_sites(sites, False)], ["1"])
        self.assertEqual(len(cm.select_sites(sites, True)), 2)


class CensusKey(unittest.TestCase):
    def test_env_then_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
            fh.write("## Census\n\nCENSUS_API_KEY: abcdef0123456789abcdef01\n")
        with mock.patch.dict(cm.os.environ, {"CENSUS_API_KEY": ""}):
            self.assertEqual(cm.census_key(fh.name), "abcdef0123456789abcdef01")
            self.assertIsNone(cm.census_key(fh.name + ".missing"))
        with mock.patch.dict(cm.os.environ, {"CENSUS_API_KEY": "fromenv0123456789abcdef"}):
            self.assertEqual(cm.census_key(fh.name), "fromenv0123456789abcdef")

    def test_placeholder_is_not_a_key(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
            fh.write("CENSUS_API_KEY: <key>\n")
        with mock.patch.dict(cm.os.environ, {"CENSUS_API_KEY": ""}):
            self.assertIsNone(cm.census_key(fh.name))

    def test_keyed_request_uses_for_in(self):
        seen = []

        def fake(url, *a, **k):
            seen.append(url)
            return [["NAME", "GEO_ID", "T_001E"], ["X", "1500000US220890601001", "5"]]
        with mock.patch.object(cm, "census_key", return_value="k" * 24), mock.patch.object(cm, "fetch_json", fake):
            rows = cm.census_table("acs", "T", "block group")
        self.assertEqual(rows[0]["GEO_ID"], "1500000US220890601001")
        self.assertIn("api.census.gov", seen[0])
        self.assertIn("for=block+group", seen[0])
        self.assertNotIn("%24", seen[0])

    def test_failed_key_falls_back_to_keyless(self):
        def fake(url, *a, **k):
            if "api.census.gov" in url:
                raise cm.SourceError("https://api.census.gov/data/2024/acs/acs5: not JSON")
            return {"response": {"data": [["GEO_ID", "T_001E"], ["1600000US2239720", "7"]]}}
        with mock.patch.object(cm, "census_key", return_value="k" * 24), mock.patch.object(cm, "fetch_json", fake), \
                mock.patch.dict(cm._census, {"warned": False}), mock.patch("sys.stderr", io.StringIO()) as err:
            rows = cm.census_table("acs", "T", "place")
        self.assertEqual(rows, [{"GEO_ID": "1600000US2239720", "T_001E": "7"}])
        self.assertIn("using data.census.gov", err.getvalue())
        self.assertNotIn("k" * 24, err.getvalue(), "the key must never be printed")

    def test_no_key_goes_straight_to_keyless(self):
        seen = []

        def fake(url, *a, **k):
            seen.append(url)
            return {"response": {"data": [["GEO_ID"], ["1000000US220890601001000"]]}}
        with mock.patch.object(cm, "census_key", return_value=None), mock.patch.object(cm, "fetch_json", fake):
            cm.census_table("pl", "P2", "block")
        self.assertEqual(len(seen), 1)
        self.assertIn("DECENNIALPL2020.P2", urllib.parse.unquote_plus(seen[0]))


class Constants(unittest.TestCase):
    def test_every_community_has_a_cdp_and_a_bank(self):
        self.assertEqual(len(cm.CDP), 14)
        self.assertTrue(cm.EAST_BANK <= set(cm.CDP))
        self.assertTrue(all(len(g) == 7 and g.startswith("22") for g in cm.CDP.values()))


if __name__ == "__main__":
    unittest.main()
