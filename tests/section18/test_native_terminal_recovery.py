"""Real TCP/browser recovery after a real canonical worker process crash."""
import unittest
import test_native_ui as native

class NativeTerminalRecovery(unittest.TestCase):
    def test_desktop_actual_partial_terminal_reconciliation(self):
        native.NativeUi.journey(self,'desktop',terminal_recovery=True)
    def test_phone_review_state_and_actual_recovery_controls(self):
        native.NativeUi.journey(self,'phone',terminal_recovery=True)

if __name__=='__main__':unittest.main(verbosity=2)
