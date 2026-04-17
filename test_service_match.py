"""Regression tests for multilingual service matching."""

import unittest

from models.service import Service
from utils.service_match import find_service


class ServiceMatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.services = [
            Service(
                name="Haircut",
                aliases=["बाल कटवाना", "વાળ કાપવા", "baal katna", "baal katvana", "hair cut", "cutting"],
                duration=30,
                price=500,
                category="Hair",
            ),
            Service(
                name="Facial",
                aliases=["फेशियल", "ફેશિયલ", "face treatment", "facial treatment"],
                duration=45,
                price=800,
                category="Facial",
            ),
        ]

    def test_matches_gujarati_script_variant(self) -> None:
        matched = find_service("હેર કટ", self.services)
        self.assertIsNotNone(matched)
        self.assertEqual(matched.name, "Haircut")

    def test_matches_romanized_gujarati_variant(self) -> None:
        matched = find_service("val kapva", self.services)
        self.assertIsNotNone(matched)
        self.assertEqual(matched.name, "Haircut")

    def test_matches_common_misheard_facial_variant(self) -> None:
        matched = find_service("fesial", self.services)
        self.assertIsNotNone(matched)
        self.assertEqual(matched.name, "Facial")


if __name__ == "__main__":
    unittest.main()
