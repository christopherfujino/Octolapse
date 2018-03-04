import unittest
from tempfile import NamedTemporaryFile

import octoprint_octolapse.trigger as trigger
from octoprint_octolapse.position import Position
from octoprint_octolapse.settings import OctolapseSettings


class Test_Trigger(unittest.TestCase):
    def setUp(self):
        self.Settings = OctolapseSettings(NamedTemporaryFile().name)

    def tearDown(self):
        del self.Settings

    def test_IsInPosition_Rect_Forbidden(self):
        restrictionsDict = [
            {"Shape": "rect", "X": 10.0, "Y": 10.0, "X2": 20.0, "Y2": 20.0, "Type": "forbidden", "R": 1.0}]
        restrictions = self.Settings.CurrentSnapshot().GetTriggerPositionRestrictions(restrictionsDict)
        self.assertTrue(trigger.is_in_position(restrictions, 0, 0))
        self.assertTrue(trigger.is_in_position(restrictions, 100, 0))
        self.assertTrue(trigger.is_in_position(restrictions, 20.1, 20.1))
        self.assertTrue(trigger.is_in_position(restrictions, 15, 25))
        self.assertTrue(trigger.is_in_position(restrictions, 25, 15))

        self.assertFalse(trigger.is_in_position(restrictions, 10, 10))
        self.assertFalse(trigger.is_in_position(restrictions, 15, 15))
        self.assertFalse(trigger.is_in_position(restrictions, 20, 20))

    def test_IsInPosition_Rect_Required(self):
        restrictionsDict = [
            {"Shape": "rect", "X": 10.0, "Y": 10.0, "X2": 20.0, "Y2": 20.0, "Type": "required", "R": 1.0}]
        restrictions = self.Settings.CurrentSnapshot().GetTriggerPositionRestrictions(restrictionsDict)
        self.assertFalse(trigger.is_in_position(restrictions, 0, 0))
        self.assertFalse(trigger.is_in_position(restrictions, 100, 0))
        self.assertFalse(trigger.is_in_position(restrictions, 20.1, 20.1))
        self.assertFalse(trigger.is_in_position(restrictions, 15, 25))
        self.assertFalse(trigger.is_in_position(restrictions, 25, 15))

        self.assertTrue(trigger.is_in_position(restrictions, 10, 10))
        self.assertTrue(trigger.is_in_position(restrictions, 15, 15))
        self.assertTrue(trigger.is_in_position(restrictions, 20, 20))

    def test_IsInPosition_Rect_ForbiddenAndRequired(self):
        # test to restrictions, forbidden and required, have them overlap.
        restrictionsDict = [
            {"Shape": "rect", "X": 10.0, "Y": 10.0, "X2": 20.0, "Y2": 20.0, "Type": "required", "R": 1.0},
            {"Shape": "rect", "X": 15.0, "Y": 15.0, "X2": 25.0, "Y2": 25.0, "Type": "forbidden", "R": 1.0},
        ]
        restrictions = self.Settings.CurrentSnapshot().GetTriggerPositionRestrictions(restrictionsDict)
        # out of all areas, restricted and forbidden
        self.assertFalse(trigger.is_in_position(restrictions, 0, 0))
        self.assertFalse(trigger.is_in_position(restrictions, 100, 0))
        self.assertFalse(trigger.is_in_position(restrictions, 12.5, 25))
        self.assertFalse(trigger.is_in_position(restrictions, 25, 12.5))

        # test only in forbidden area
        self.assertFalse(trigger.is_in_position(restrictions, 20.1, 25))
        self.assertFalse(trigger.is_in_position(restrictions, 20.1, 20.1))
        self.assertFalse(trigger.is_in_position(restrictions, 25, 20.1))

        # test in required area only
        self.assertTrue(trigger.is_in_position(restrictions, 10, 10))
        self.assertTrue(trigger.is_in_position(restrictions, 12.5, 12.5))
        self.assertTrue(trigger.is_in_position(restrictions, 14.99, 14.99))

        # test overlapping area
        self.assertFalse(trigger.is_in_position(restrictions, 15, 15))
        self.assertFalse(trigger.is_in_position(restrictions, 20, 20))
        self.assertFalse(trigger.is_in_position(restrictions, 15, 20))
        self.assertFalse(trigger.is_in_position(restrictions, 20, 15))
        self.assertFalse(trigger.is_in_position(restrictions, 17.5, 17.5))

    def test_IsInPosition_Circle_Forbidden(self):
        restrictionsDict = [{"Shape": "circle", "R": 1.0, "Y": 10.0, "X": 10.0, "Type": "forbidden", "X2": 0, "Y2": 0}]
        restrictions = self.Settings.CurrentSnapshot().GetTriggerPositionRestrictions(restrictionsDict)
        # tests outside forbidden area
        self.assertTrue(trigger.is_in_position(restrictions, 0, 0))
        self.assertTrue(trigger.is_in_position(restrictions, 100, 0))
        self.assertTrue(trigger.is_in_position(restrictions, 9, 9))
        self.assertTrue(trigger.is_in_position(restrictions, 11, 11))
        self.assertTrue(trigger.is_in_position(restrictions, 9, 11))
        self.assertTrue(trigger.is_in_position(restrictions, 11, 9))
        # tests inside forbidden area
        self.assertFalse(trigger.is_in_position(restrictions, 10, 10))
        self.assertFalse(trigger.is_in_position(restrictions, 10, 9))
        self.assertFalse(trigger.is_in_position(restrictions, 9, 10))
        self.assertFalse(trigger.is_in_position(restrictions, 10, 11))
        self.assertFalse(trigger.is_in_position(restrictions, 11, 10))

    def test_IsInPosition_Circle_Required(self):
        restrictionsDict = [
            {"Shape": "circle", "R": 1.0, "Y": 10.0, "X": 10.0, "Type": "required", "X2": 20.0, "Y2": 20.0}]
        restrictions = self.Settings.CurrentSnapshot().GetTriggerPositionRestrictions(restrictionsDict)
        # tests outside area
        self.assertFalse(trigger.is_in_position(restrictions, 0, 0))
        self.assertFalse(trigger.is_in_position(restrictions, 100, 0))
        self.assertFalse(trigger.is_in_position(restrictions, 9, 9))
        self.assertFalse(trigger.is_in_position(restrictions, 11, 11))
        self.assertFalse(trigger.is_in_position(restrictions, 9, 11))
        self.assertFalse(trigger.is_in_position(restrictions, 11, 9))

        # tests inside area
        self.assertTrue(trigger.is_in_position(restrictions, 10, 10))
        self.assertTrue(trigger.is_in_position(restrictions, 10, 9))
        self.assertTrue(trigger.is_in_position(restrictions, 9, 10))
        self.assertTrue(trigger.is_in_position(restrictions, 10, 11))
        self.assertTrue(trigger.is_in_position(restrictions, 11, 10))

    def test_IsInPosition_Circle_ForbiddenAndRequired(self):
        # test to restrictions, forbidden and required, have them overlap.
        restrictionsDict = [
            {"Shape": "circle", "R": 1.0, "Y": 10.0, "X": 10.0, "Type": "required", "X2": 20.0, "Y2": 20.0},
            {"Shape": "circle", "R": 1.0, "Y": 10.0, "X": 11.0, "Type": "forbidden", "X2": 25.0, "Y2": 25.0},
        ]
        restrictions = self.Settings.CurrentSnapshot().GetTriggerPositionRestrictions(restrictionsDict)
        # out of all areas, restricted and forbidden
        self.assertFalse(trigger.is_in_position(restrictions, 0, 0))
        self.assertFalse(trigger.is_in_position(restrictions, 100, 0))

        # test only in forbidden area
        self.assertFalse(trigger.is_in_position(restrictions, 12, 10))
        self.assertFalse(trigger.is_in_position(restrictions, 11, 11))
        self.assertFalse(trigger.is_in_position(restrictions, 11, 9))

        # test in required area only
        self.assertTrue(trigger.is_in_position(restrictions, 10, 11))
        self.assertTrue(trigger.is_in_position(restrictions, 10, 9))
        self.assertTrue(trigger.is_in_position(restrictions, 9, 10))

        # test overlapping area
        self.assertFalse(trigger.is_in_position(restrictions, 10, 10))
        self.assertFalse(trigger.is_in_position(restrictions, 11, 10))
        self.assertFalse(trigger.is_in_position(restrictions, 10.5, 10))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(Test_Trigger)
    unittest.TextTestRunner(verbosity=3).run(suite)
