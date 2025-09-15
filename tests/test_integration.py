import unittest
import asyncio
from unittest.mock import patch, MagicMock

from edpmt.transparent import EDPMTransparent
from edpmt.web_ui import start_web_ui

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.config = {'hardware_simulators': True}
        self.edpmt = EDPMTransparent(config=self.config)

    @patch('edpmt.web_ui.aiohttp.web.AppRunner')
    @patch('edpmt.web_ui.aiohttp.web.TCPSite')
    def test_start_web_ui(self, mock_tcpsite, mock_apprunner):
        mock_runner = MagicMock()
        mock_apprunner.return_value = mock_runner
        mock_site = MagicMock()
        mock_tcpsite.return_value = mock_site

        asyncio.run(start_web_ui(self.edpmt, host='localhost', port=8085))

        mock_apprunner.assert_called()
        mock_tcpsite.assert_called()
        mock_runner.setup.assert_called()
        mock_site.start.assert_called()

if __name__ == '__main__':
    unittest.main()
