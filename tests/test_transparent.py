import unittest
import asyncio
from unittest.mock import patch, MagicMock

from edpmt.transparent import EDPMTransparent

class TestEDPMTransparent(unittest.TestCase):
    def setUp(self):
        self.config = {'hardware_simulators': True}
        self.edpmt = EDPMTransparent(config=self.config)

    @patch('edpmt.transparent.asyncio.create_task')
    def test_start_server(self, mock_create_task):
        mock_task = MagicMock()
        mock_create_task.return_value = mock_task

        asyncio.run(self.edpmt.start_server())

        mock_create_task.assert_called()
        self.assertTrue(self.edpmt._server_running)

    def test_stop_server(self):
        self.edpmt._server_running = True
        asyncio.run(self.edpmt.stop_server())
        self.assertFalse(self.edpmt._server_running)

    @patch('edpmt.transparent.get_system_info')
    def test_get_system_info(self, mock_get_system_info):
        mock_get_system_info.return_value = {'platform': 'test_platform'}
        result = asyncio.run(self.edpmt.get_system_info())
        self.assertEqual(result, {'platform': 'test_platform'})
        mock_get_system_info.assert_called_once()

    def test_execute_invalid_action(self):
        with self.assertRaises(ValueError):
            asyncio.run(self.edpmt.execute('invalid_action', {}))

if __name__ == '__main__':
    unittest.main()
