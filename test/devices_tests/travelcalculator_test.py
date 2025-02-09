"""Unit test for TravelCalculator objects."""

from unittest.mock import patch

from xknx.devices import TravelCalculator, TravelStatus


class TestTravelCalculator:
    """Test class for TravelCalculator objects."""

    # TravelCalculator(25, 50) means:
    #
    #     2 steps / sec UP
    #     4 steps / sec DOWN
    #
    # INIT
    #
    def test_init(self) -> None:
        """Test initial status."""
        travelcalculator = TravelCalculator(25, 50)
        assert not travelcalculator.is_closed()
        assert not travelcalculator.is_closing()
        assert not travelcalculator.is_opening()
        assert not travelcalculator.is_traveling()
        assert travelcalculator.position_reached()
        assert travelcalculator.current_position() is None

    def test_set_position(self) -> None:
        """Test set position."""
        travelcalculator = TravelCalculator(25, 50)
        travelcalculator.set_position(70)
        assert travelcalculator.position_reached()
        assert travelcalculator.current_position() == 70

    def test_set_position_after_travel(self) -> None:
        """Set explicit position after start_travel should stop traveling."""
        travelcalculator = TravelCalculator(25, 50)
        travelcalculator.start_travel(30)
        travelcalculator.set_position(80)
        assert travelcalculator.position_reached()
        assert travelcalculator.current_position() == 80

    def test_travel_down(self) -> None:
        """Test travel down."""
        travelcalculator = TravelCalculator(25, 50)
        with patch("time.time") as mock_time:
            mock_time.return_value = 1580000000.0
            travelcalculator.set_position(40)
            travelcalculator.start_travel(60)

            # time not changed, still at beginning
            assert travelcalculator.current_position() == 40
            assert not travelcalculator.position_reached()
            assert travelcalculator.travel_direction == TravelStatus.DIRECTION_DOWN

            mock_time.return_value = 1580000001.0
            assert travelcalculator.current_position() == 44
            assert not travelcalculator.position_reached()

            mock_time.return_value = 1580000002.0
            assert travelcalculator.current_position() == 48
            assert not travelcalculator.position_reached()

            mock_time.return_value = 1580000004.0
            assert travelcalculator.current_position() == 56
            assert not travelcalculator.position_reached()

            mock_time.return_value = 1580000005.0
            # position reached
            assert travelcalculator.current_position() == 60
            assert travelcalculator.position_reached()

            mock_time.return_value = 1580000010.0
            assert travelcalculator.current_position() == 60
            assert travelcalculator.position_reached()

    def test_travel_up(self) -> None:
        """Test travel up."""
        travelcalculator = TravelCalculator(25, 50)
        with patch("time.time") as mock_time:
            mock_time.return_value = 1580000000.0
            travelcalculator.set_position(70)
            travelcalculator.start_travel(50)

            # time not changed, still at beginning
            assert travelcalculator.current_position() == 70
            assert not travelcalculator.position_reached()
            assert travelcalculator.travel_direction == TravelStatus.DIRECTION_UP

            mock_time.return_value = 1580000002.0
            assert travelcalculator.current_position() == 66
            assert not travelcalculator.position_reached()

            mock_time.return_value = 1580000004.0
            assert travelcalculator.current_position() == 62
            assert not travelcalculator.position_reached()

            mock_time.return_value = 1580000008.0
            assert travelcalculator.current_position() == 54
            assert not travelcalculator.position_reached()

            mock_time.return_value = 1580000010.0
            # position reached
            assert travelcalculator.current_position() == 50
            assert travelcalculator.position_reached()

            mock_time.return_value = 1580000020.0
            assert travelcalculator.current_position() == 50
            assert travelcalculator.position_reached()

    def test_stop(self) -> None:
        """Test stopping."""
        travelcalculator = TravelCalculator(25, 50)
        with patch("time.time") as mock_time:
            mock_time.return_value = 1580000000.0
            travelcalculator.set_position(80)
            travelcalculator.start_travel(60)
            assert travelcalculator.travel_direction == TravelStatus.DIRECTION_UP

            # stop aftert two seconds
            mock_time.return_value = 1580000002.0
            travelcalculator.stop()

            mock_time.return_value = 1580000004.0
            assert travelcalculator.current_position() == 76
            assert travelcalculator.position_reached()

            # restart after 1 additional second (3 seconds)
            mock_time.return_value = 1580000005.0
            travelcalculator.start_travel(68)

            # running up for 6 seconds
            mock_time.return_value = 1580000006.0
            assert travelcalculator.current_position() == 74
            assert not travelcalculator.position_reached()

            mock_time.return_value = 1580000009.0
            assert travelcalculator.current_position() == 68
            assert travelcalculator.position_reached()

    def test_travel_down_with_updates(self) -> None:
        """Test travel down with position updates from bus."""
        travelcalculator = TravelCalculator(25, 50)
        with patch("time.time") as mock_time:
            mock_time.return_value = 1580000000.0
            travelcalculator.set_position(40)
            travelcalculator.start_travel(100)  # 15 seconds to reach 100

            # time not changed, still at beginning
            assert travelcalculator.current_position() == 40
            assert not travelcalculator.position_reached()
            assert travelcalculator.travel_direction == TravelStatus.DIRECTION_DOWN

            mock_time.return_value = 1580000002.0
            assert travelcalculator.current_position() == 48
            assert not travelcalculator.position_reached()
            # update from bus matching calculation
            travelcalculator.update_position(48)
            assert travelcalculator.current_position() == 48
            assert not travelcalculator.position_reached()

            mock_time.return_value = 1580000010.0
            assert travelcalculator.current_position() == 80
            assert not travelcalculator.position_reached()
            # update from bus not matching calculation takes precedence (1 second slower)
            travelcalculator.update_position(76)
            assert travelcalculator.current_position() == 76
            assert not travelcalculator.position_reached()
            # travel time extended by 1 second due to update from bus
            mock_time.return_value = 1580000015.0
            assert travelcalculator.current_position() == 96
            assert not travelcalculator.position_reached()
            mock_time.return_value = 1580000015.0 + 1
            assert travelcalculator.current_position() == 100
            assert travelcalculator.position_reached()

    def test_travel_up_with_updates(self) -> None:
        """Test travel up with position updates from bus."""
        travelcalculator = TravelCalculator(25, 50)
        with patch("time.time") as mock_time:
            mock_time.return_value = 1580000000.0
            travelcalculator.set_position(70)
            travelcalculator.start_travel(50)  # 10 seconds to reach 50

            mock_time.return_value = 1580000005.0
            assert travelcalculator.current_position() == 60
            assert not travelcalculator.position_reached()
            # update from bus not matching calculation takes precedence (1 second faster)
            travelcalculator.update_position(58)
            assert travelcalculator.current_position() == 58
            assert not travelcalculator.position_reached()
            # position reached 1 second earlier than predicted
            mock_time.return_value = 1580000010.0 - 1
            assert travelcalculator.current_position() == 50
            assert travelcalculator.position_reached()

    def test_change_direction(self) -> None:
        """Test changing direction while travelling."""
        travelcalculator = TravelCalculator(50, 25)
        with patch("time.time") as mock_time:
            mock_time.return_value = 1580000000.0
            travelcalculator.set_position(60)
            travelcalculator.start_travel(80)
            assert travelcalculator.travel_direction == TravelStatus.DIRECTION_DOWN

            # change direction after two seconds
            mock_time.return_value = 1580000002.0
            assert travelcalculator.current_position() == 64
            travelcalculator.start_travel(48)
            assert travelcalculator.travel_direction == TravelStatus.DIRECTION_UP

            assert travelcalculator.current_position() == 64
            assert not travelcalculator.position_reached()

            mock_time.return_value = 1580000004.0
            assert travelcalculator.current_position() == 56
            assert not travelcalculator.position_reached()

            mock_time.return_value = 1580000006.0
            assert travelcalculator.current_position() == 48
            assert travelcalculator.position_reached()

    def test_travel_full_up(self) -> None:
        """Test travelling to the full up position."""
        travelcalculator = TravelCalculator(25, 50)
        with patch("time.time") as mock_time:
            mock_time.return_value = 1580000000.0
            travelcalculator.set_position(30)
            travelcalculator.start_travel_up()

            mock_time.return_value = 1580000014.0
            assert not travelcalculator.position_reached()
            assert not travelcalculator.is_closed()
            assert not travelcalculator.is_open()

            mock_time.return_value = 1580000015.0
            assert travelcalculator.position_reached()
            assert travelcalculator.is_open()
            assert not travelcalculator.is_closed()

    def test_travel_full_down(self) -> None:
        """Test travelling to the full down position."""
        travelcalculator = TravelCalculator(25, 50)
        with patch("time.time") as mock_time:
            mock_time.return_value = 1580000000.0
            travelcalculator.set_position(20)
            travelcalculator.start_travel_down()

            mock_time.return_value = 1580000019.0
            assert not travelcalculator.position_reached()
            assert not travelcalculator.is_closed()
            assert not travelcalculator.is_open()

            mock_time.return_value = 1580000020.0
            assert travelcalculator.position_reached()
            assert travelcalculator.is_closed()
            assert not travelcalculator.is_open()

    def test_is_traveling(self) -> None:
        """Test if cover is traveling and position reached."""
        travelcalculator = TravelCalculator(25, 50)
        with patch("time.time") as mock_time:
            mock_time.return_value = 1580000000.0
            assert not travelcalculator.is_traveling()
            assert travelcalculator.position_reached()

            travelcalculator.set_position(80)
            assert not travelcalculator.is_traveling()
            assert travelcalculator.position_reached()

            mock_time.return_value = 1580000000.0
            travelcalculator.start_travel_down()

            mock_time.return_value = 1580000004.0
            assert travelcalculator.is_traveling()
            assert not travelcalculator.position_reached()

            mock_time.return_value = 1580000005.0
            assert not travelcalculator.is_traveling()
            assert travelcalculator.position_reached()

    def test_is_opening_closing(self) -> None:
        """Test reports is_opening and is_closing."""
        travelcalculator = TravelCalculator(25, 50)
        with patch("time.time") as mock_time:
            mock_time.return_value = 1580000000.0
            assert not travelcalculator.is_opening()
            assert not travelcalculator.is_closing()

            travelcalculator.set_position(80)
            assert not travelcalculator.is_opening()
            assert not travelcalculator.is_closing()

            mock_time.return_value = 1580000000.0
            travelcalculator.start_travel_down()
            assert not travelcalculator.is_opening()
            assert travelcalculator.is_closing()

            mock_time.return_value = 1580000004.0
            assert not travelcalculator.is_opening()
            assert travelcalculator.is_closing()

            mock_time.return_value = 1580000005.0
            assert not travelcalculator.is_opening()
            assert not travelcalculator.is_closing()
            # up direction
            travelcalculator.start_travel(50)
            assert travelcalculator.is_opening()
            assert not travelcalculator.is_closing()

            mock_time.return_value = 1580000030.0
            assert not travelcalculator.is_opening()
            assert not travelcalculator.is_closing()
