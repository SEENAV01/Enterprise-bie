import unittest
from bie.reasoning.calibration_diagnostics import CalibrationSample, calibration_report

class TestCalibrationDiagnostics(unittest.TestCase):
    def test_perfect_predictions_have_zero_brier(self):
        r=calibration_report([CalibrationSample(1,True),CalibrationSample(0,False)],bin_count=2)
        self.assertAlmostEqual(r.brier_score,0.0)
        self.assertEqual(r.sample_count,2)

    def test_overconfidence_produces_gap(self):
        r=calibration_report([CalibrationSample(.9,False),CalibrationSample(.9,True)],bin_count=2)
        self.assertGreater(r.ece,0)

    def test_invalid_sample_rejected(self):
        with self.assertRaises(ValueError):
            calibration_report([CalibrationSample(1.2,True)])

    def test_version_required(self):
        with self.assertRaises(ValueError):
            calibration_report([CalibrationSample(.5,True)],calibration_version="")
