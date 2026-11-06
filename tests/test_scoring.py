import unittest
from datetime import date, datetime

import preferences as prefs
from engine.features import extract_features
from engine.scoring import (
    _feedback_score, _novelty_score, _preference_score, _temporal_score,
    _weather_score, compute_score,
)


class ScoringTests(unittest.TestCase):
    def test_category_alone_supplies_restaurant_timing(self):
        candidate = extract_features({'content': 'Dinner', 'category': 'restaurant'})
        self.assertEqual(_temporal_score(candidate, datetime(2026, 11, 6, 18)), 1.0)

    def test_activity_category_matches_afternoon_window(self):
        candidate = extract_features({'content': 'Walk'})
        self.assertEqual(_temporal_score(candidate, datetime(2026, 11, 6, 14)), 0.75)

    def test_preference_reads_structured_fields_without_tags(self):
        candidate = extract_features({
            'content': 'Dinner', 'vibe': 'romantic', 'price_tier': 'mid',
            'neighborhood': 'plateau', 'indoor_outdoor': 'indoor',
        })
        weights = [prefs.VIBE_WEIGHTS['romantic'], prefs.PRICE_WEIGHTS['mid'],
                   prefs.NEIGHBORHOOD_WEIGHTS['plateau'], prefs.INDOOR_OUTDOOR_PREFERENCE['indoor']]
        self.assertAlmostEqual(_preference_score(candidate), (sum(weights) / len(weights) + 1) / 2)

    def test_novelty_reads_dedicated_fields_without_tags(self):
        for field, value, history_key in (
            ('category', 'restaurant', 'restaurant'), ('vibe', 'romantic', 'vibe_romantic'),
            ('price_tier', 'mid', 'price_mid'), ('neighborhood', 'plateau', 'plateau'),
        ):
            with self.subTest(field=field):
                candidate = extract_features({'content': 'Example', field: value})
                self.assertEqual(_novelty_score(candidate, {}), 1.0)
                self.assertEqual(_novelty_score(candidate, {history_key: {'last_suggested': date.today()}}), 0.0)

    def test_feedback_matches_dedicated_metadata_across_categories(self):
        for field, value in (('vibe', 'romantic'), ('price_tier', 'mid'),
                             ('neighborhood', 'plateau'), ('indoor_outdoor', 'indoor')):
            with self.subTest(field=field):
                candidate = extract_features({'content': 'Dinner', 'category': 'restaurant', field: value})
                row = {'category': 'event', field: value, 'rating': 1, 'created_at': date.today()}
                self.assertEqual(_feedback_score(candidate, [row]), 1.0)

    def test_missing_metadata_does_not_create_feedback_match(self):
        self.assertEqual(_feedback_score(
            {'category': 'restaurant'}, [{'category': 'event', 'rating': 1}]), 0.5)

    def test_weather_reads_indoor_field(self):
        candidate = extract_features({'content': 'Dinner', 'indoor_outdoor': 'indoor'})
        self.assertEqual(_weather_score(candidate, {'temp_c': -20, 'precip_prob': 1}), 0.8)

    def test_full_score_accepts_candidates_without_tags(self):
        candidate = extract_features({'content': 'Dinner', 'category': 'restaurant'})
        scores = compute_score(candidate, now=datetime(2026, 11, 6, 18))
        self.assertGreaterEqual(scores['final'], 0)
        self.assertLessEqual(scores['final'], 1)


if __name__ == '__main__':
    unittest.main()
