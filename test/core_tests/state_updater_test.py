"""Unit test for StateUpdater."""
import asyncio
import unittest
from unittest.mock import Mock, patch

from xknx import XKNX
from xknx.core.state_updater import StateTrackerType, _StateTracker
from xknx.exceptions import ConversionError
from xknx.remote_value import RemoteValue
from xknx.telegram import GroupAddress


class TestStateUpdater(unittest.TestCase):
    """Test class for state updater."""
    # pylint: disable=protected-access

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_register_unregister(self):
        """Test register and unregister."""
        xknx = XKNX(loop=self.loop)
        self.assertEqual(len(xknx.state_updater._workers), 0)
        # register when state address and sync_state is set
        remote_value_1 = RemoteValue(xknx,
                                     sync_state=True,
                                     group_address_state=GroupAddress('1/1/1'))
        self.assertEqual(len(xknx.state_updater._workers), 1)
        # don't register when sync_state is False
        remote_value_2 = RemoteValue(xknx,
                                     sync_state=False,
                                     group_address_state=GroupAddress('1/1/1'))
        self.assertEqual(len(xknx.state_updater._workers), 1)
        # manual registration
        xknx.state_updater.register_remote_value(remote_value_2)
        self.assertEqual(len(xknx.state_updater._workers), 2)
        # manual unregister
        xknx.state_updater.unregister_remote_value(remote_value_1)
        # only remote_value_2 remaining
        self.assertEqual(len(xknx.state_updater._workers), 1)
        self.assertEqual(list(xknx.state_updater._workers.keys())[0], id(remote_value_2))
        # unregister on RemoteValue.__del__()
        remote_value_2.__del__()
        self.assertEqual(len(xknx.state_updater._workers), 0)

    def test_tracker_parser(self):
        """Test parsing tracker options."""
        xknx = XKNX(loop=self.loop)

        def _get_only_tracker() -> _StateTracker:
            # _workers is unordered so it just works with 1 item
            self.assertEqual(len(xknx.state_updater._workers), 1)
            _tracker = next(iter(xknx.state_updater._workers.values()))
            return _tracker
        # INIT
        remote_value_init = RemoteValue(xknx,
                                        sync_state="init",
                                        group_address_state=GroupAddress('1/1/1'))
        self.assertEqual(_get_only_tracker().tracker_type,
                         StateTrackerType.INIT)
        remote_value_init.__del__()
        # EXPIRE with default time
        remote_value_expire = RemoteValue(xknx,
                                          sync_state="expire",
                                          group_address_state=GroupAddress('1/1/1'))
        self.assertEqual(_get_only_tracker().tracker_type,
                         StateTrackerType.EXPIRE)
        self.assertEqual(_get_only_tracker().update_interval,
                         60 * 60)
        remote_value_expire.__del__()
        # EXPIRE with 30 minutes
        remote_value_expire = RemoteValue(xknx,
                                          sync_state="expire 30",
                                          group_address_state=GroupAddress('1/1/1'))
        self.assertEqual(_get_only_tracker().tracker_type,
                         StateTrackerType.EXPIRE)
        self.assertEqual(_get_only_tracker().update_interval,
                         30 * 60)
        remote_value_expire.__del__()
        # PERIODICALLY with default time
        remote_value_every = RemoteValue(xknx,
                                         sync_state="every",
                                         group_address_state=GroupAddress('1/1/1'))
        self.assertEqual(_get_only_tracker().tracker_type,
                         StateTrackerType.PERIODICALLY)
        self.assertEqual(_get_only_tracker().update_interval,
                         60 * 60)
        remote_value_every.__del__()
        # PERIODICALLY 10 * 60 seconds
        remote_value_every = RemoteValue(xknx,
                                         sync_state="every 10",
                                         group_address_state=GroupAddress('1/1/1'))
        self.assertEqual(_get_only_tracker().tracker_type,
                         StateTrackerType.PERIODICALLY)
        self.assertEqual(_get_only_tracker().update_interval,
                         10 * 60)
        remote_value_every.__del__()

    @patch('logging.Logger.warning')
    def test_tracker_parser_invalid_options(self, logging_warning_mock):
        """Test parsing invalid tracker options."""
        xknx = XKNX(loop=self.loop)

        def _get_only_tracker() -> _StateTracker:
            # _workers is unordered so it just works with 1 item
            self.assertEqual(len(xknx.state_updater._workers), 1)
            _tracker = next(iter(xknx.state_updater._workers.values()))
            return _tracker
        # INVALID string
        remote_value_invalid = RemoteValue(xknx,
                                           sync_state="invalid",
                                           group_address_state=GroupAddress('1/1/1'))
        logging_warning_mock.assert_called_once_with(
            'Can not parse StateUpdater tracker_options "invalid" for %s. '
            'Using default StateTrackerType.EXPIRE 60 minutes.' %
            remote_value_invalid)
        self.assertEqual(_get_only_tracker().tracker_type,
                         StateTrackerType.EXPIRE)
        self.assertEqual(_get_only_tracker().update_interval,
                         60 * 60)
        remote_value_invalid.__del__()
        logging_warning_mock.reset_mock()
        # INVALID type
        remote_value_float = RemoteValue(xknx,
                                         sync_state=5.6,
                                         group_address_state=GroupAddress('1/1/1'))
        logging_warning_mock.assert_called_once_with(
            'Can not parse StateUpdater tracker_options type <class \'float\'> "5.6" for %s. '
            'Using default StateTrackerType.EXPIRE 60 minutes.' %
            remote_value_float)
        self.assertEqual(_get_only_tracker().tracker_type,
                         StateTrackerType.EXPIRE)
        self.assertEqual(_get_only_tracker().update_interval,
                         60 * 60)
        remote_value_float.__del__()
        # intervall too long
        with(self.assertRaises(ConversionError)):
            remote_value_long = RemoteValue(xknx,
                                            sync_state=1441,
                                            group_address_state=GroupAddress('1/1/1'))

            remote_value_long.__del__()

    def test_state_updater_start_update_stop(self):
        """Test start, update_received and stop of StateUpdater."""
        xknx = XKNX(loop=self.loop)
        remote_value_1 = RemoteValue(xknx,
                                     sync_state=True,
                                     group_address_state=GroupAddress('1/1/1'))
        remote_value_2 = RemoteValue(xknx,
                                     sync_state=True,
                                     group_address_state=GroupAddress('1/1/2'))
        xknx.state_updater._workers[id(remote_value_1)] = Mock()
        xknx.state_updater._workers[id(remote_value_2)] = Mock()

        self.assertFalse(xknx.state_updater.started)
        xknx.state_updater.start()
        self.assertTrue(xknx.state_updater.started)
        # start
        xknx.state_updater._workers[id(remote_value_1)].start.assert_called_once()
        xknx.state_updater._workers[id(remote_value_2)].start.assert_called_once()
        # update
        xknx.state_updater.update_received(remote_value_2)
        xknx.state_updater._workers[id(remote_value_1)].update_received.assert_not_called()
        xknx.state_updater._workers[id(remote_value_2)].update_received.assert_called_once()
        # stop
        xknx.state_updater.stop()
        self.assertFalse(xknx.state_updater.started)
        xknx.state_updater._workers[id(remote_value_1)].stop.assert_called_once()
        xknx.state_updater._workers[id(remote_value_2)].stop.assert_called_once()
        # don't update when not started
        xknx.state_updater.update_received(remote_value_1)
        xknx.state_updater._workers[id(remote_value_1)].update_received.assert_not_called()
