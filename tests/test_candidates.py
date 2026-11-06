import unittest

from pydantic import ValidationError

from candidate import Candidate
from engine.features import extract_features
from sources.seeds import load_seeds
from tags import Category, EffortLevel, PriceTier


class CandidateTests(unittest.TestCase):
    def test_seed_normalization_and_plain_dictionary_output(self):
        for raw in load_seeds():
            with self.subTest(name=raw['name']):
                original = dict(raw)
                result = extract_features(raw)
                self.assertEqual(raw, original)
                self.assertEqual(result['content'], raw['name'])
                self.assertEqual(result['duration_minutes'], 240)
                self.assertEqual(result['indoor_outdoor'], 'indoor')
                self.assertIs(type(result['price_tier']), str)
                self.assertIs(type(result['effort_level']), int)
                self.assertEqual(result['effort_level'], 1)

    def test_explicit_fields_override_legacy_fields(self):
        result = extract_features({
            'content': 'Dinner', 'name': 'Ignored', 'category': 'restaurant',
            'duration_minutes': 90, 'duration_hours': 4,
            'indoor_outdoor': 'outdoor', 'indoor': True,
            'effort_level': 2, 'energy_level': 5,
        })
        self.assertEqual(result['content'], 'Dinner')
        self.assertEqual(result['duration_minutes'], 90)
        self.assertEqual(result['indoor_outdoor'], 'outdoor')
        self.assertEqual(result['effort_level'], 2)
        self.assertEqual(result['category'], 'restaurant')

    def test_model_accepts_enums_and_coerces_numeric_strings(self):
        model = Candidate(content='Dinner', category=Category.RESTAURANT,
                          price_tier=PriceTier.MID, effort_level=EffortLevel.LOW,
                          duration_minutes='90', requires_booking='true')
        self.assertEqual(model.duration_minutes, 90)
        self.assertIs(model.requires_booking, True)
        self.assertEqual(model.model_dump(mode='json')['price_tier'], 'mid')

    def test_tag_normalization_drops_unknown_strings(self):
        with self.assertLogs('candidate', level='WARNING') as captured:
            model = Candidate(content='Dinner', tags=[' JAPANESE ', 'not-a-real-tag'])
        self.assertEqual(model.tags, ['japanese'])
        self.assertIn('not-a-real-tag', captured.output[0])

    def test_misplaced_tags_are_dropped_without_overwriting_fields(self):
        with self.assertLogs('candidate', level='WARNING') as captured:
            model = Candidate(
                content='Dinner', category='restaurant', price_tier='mid',
                neighborhood='plateau', vibe='romantic', indoor_outdoor='indoor',
                tags=[' UPSCALE ', 'mile_end', 'relaxing', 'outdoor',
                      'ddg_search', 'restaurant', 'japanese', 'live_music', 'free'],
            )
        self.assertEqual(model.tags, ['japanese', 'live_music'])
        self.assertEqual(model.price_tier.value, 'mid')
        self.assertEqual(model.neighborhood.value, 'plateau')
        self.assertEqual(model.vibe.value, 'romantic')
        self.assertEqual(model.indoor_outdoor.value, 'indoor')
        for field in ('price_tier', 'neighborhood', 'vibe', 'indoor_outdoor', 'source', 'category'):
            self.assertTrue(any(f'use the {field} field' in line for line in captured.output))

    def test_misplaced_tag_does_not_fill_missing_metadata(self):
        with self.assertLogs('candidate', level='WARNING'):
            model = Candidate(content='Dinner', tags=['mid'])
        self.assertEqual(model.tags, [])
        self.assertIsNone(model.price_tier)

    def test_invalid_metadata_logs_and_defaults(self):
        invalid = {
            'vibe': 'unknown', 'price_tier': 99,
            'neighborhood': 'unknown', 'indoor_outdoor': 'unknown',
            'source': 'unknown', 'duration_minutes': -10,
            'effort_level': 6,
            'requires_booking': 'maybe',
        }
        with self.assertLogs('candidate', level='WARNING'):
            result = extract_features({'content': 'Example', **invalid})
        self.assertEqual(result['category'], 'activity')
        for field in invalid:
            self.assertIsNone(result[field], field)

    def test_missing_category_defaults_to_activity(self):
        self.assertEqual(Candidate(content='Walk').category, Category.ACTIVITY)
        self.assertEqual(extract_features({'content': 'Walk'})['category'], 'activity')

    def test_explicitly_invalid_category_raises(self):
        for category in ('banana', '', None, 42):
            for validate in (Candidate.model_validate, extract_features):
                with self.subTest(category=category, validate=validate):
                    with self.assertRaises(ValidationError) as captured:
                        validate({'content': 'Dinner', 'category': category})
                    self.assertEqual(captured.exception.errors()[0]['loc'], ('category',))

    def test_numeric_boundaries(self):
        for field, value in [('duration_minutes', 0), ('effort_level', 2.5)]:
            with self.subTest(field=field, value=value):
                with self.assertLogs('candidate', level='WARNING'):
                    result = Candidate(content='Example', **{field: value})
                self.assertIsNone(getattr(result, field))

    def test_malformed_identity_and_tag_types_raise(self):
        for raw in ({'content': []}, {'content': 'Example', 'tags': 'cozy'},
                    {'content': 'Example', 'tags': [42]}):
            with self.subTest(raw=raw), self.assertRaises(ValidationError):
                Candidate.model_validate(raw)

    def test_invalid_legacy_duration_is_logged_and_defaulted(self):
        with self.assertLogs('engine.features', level='WARNING'):
            result = extract_features({'name': 'Example', 'duration_hours': 'unknown'})
        self.assertIsNone(result['duration_minutes'])

    def test_defaults_are_independent_and_extra_fields_are_ignored(self):
        first = Candidate(content='First', unused_source_field=True)
        first.tags.append('cozy')
        second = Candidate(content='Second')
        self.assertEqual(second.tags, [])
        self.assertNotIn('unused_source_field', first.model_dump())
        self.assertEqual(extract_features({})['content'], 'unknown')


if __name__ == '__main__':
    unittest.main()
