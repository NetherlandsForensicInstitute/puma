import unittest
from unittest.mock import MagicMock, patch

from puma.state_graph.state import SimpleState


class TestSimpleStateValidate(unittest.TestCase):
    def test_validate_succeeds_when_required_xpaths_present_and_invalid_absent(self):
        state = SimpleState(xpaths=["//present"], invalid_xpaths=["//invalid"])
        state.id = "Home"
        driver = MagicMock()
        driver.is_present.side_effect = lambda xpath: xpath == "//present"

        self.assertTrue(state.validate(driver))

    def test_validate_logs_missing_required_xpath(self):
        state = SimpleState(xpaths=["//present", "//missing"])
        state.id = "Home"
        driver = MagicMock()
        driver.is_present.side_effect = lambda xpath: xpath == "//present"

        with patch("puma.state_graph.state.logger") as mock_logger:
            self.assertFalse(state.validate(driver))
            mock_logger.debug.assert_called_once()
            message = mock_logger.debug.call_args[0][0]
            self.assertIn("//missing", message)
            self.assertIn("Home", message)
            self.assertIn("required xpath not found", message)

    def test_validate_logs_present_invalid_xpath(self):
        state = SimpleState(xpaths=["//present"], invalid_xpaths=["//popup"])
        state.id = "Home"
        driver = MagicMock()
        driver.is_present.return_value = True

        with patch("puma.state_graph.state.logger") as mock_logger:
            self.assertFalse(state.validate(driver))
            mock_logger.debug.assert_called_once()
            message = mock_logger.debug.call_args[0][0]
            self.assertIn("//popup", message)
            self.assertIn("invalid xpath is present", message)


if __name__ == "__main__":
    unittest.main()
