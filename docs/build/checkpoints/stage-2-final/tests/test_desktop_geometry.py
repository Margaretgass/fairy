from fairy.desktop.geometry import Point, Rect, clamp_position, snap_to_nearest_side

WINDOW = Rect(0, 0, 72, 72)
SCREEN = Rect(0, 0, 1440, 900)


def test_clamp_keeps_visible_position_unchanged():
    assert clamp_position(Point(100, 200), WINDOW, SCREEN) == Point(100, 200)


def test_clamp_moves_position_inside_right_and_bottom_edges():
    assert clamp_position(Point(2000, 1000), WINDOW, SCREEN) == Point(1368, 828)


def test_clamp_moves_negative_position_inside_top_left():
    assert clamp_position(Point(-20, -50), WINDOW, SCREEN) == Point(0, 0)


def test_clamp_handles_window_larger_than_available_area():
    window = Rect(0, 0, 500, 500)
    available = Rect(100, 200, 300, 250)
    assert clamp_position(Point(900, 900), window, available) == Point(100, 200)


def test_snap_chooses_left_edge_when_left_is_nearer():
    assert snap_to_nearest_side(Point(200, 300), WINDOW, SCREEN) == Point(0, 300)


def test_snap_chooses_right_edge_when_right_is_nearer():
    assert snap_to_nearest_side(Point(1200, 300), WINDOW, SCREEN) == Point(1368, 300)


def test_snap_tie_is_stable_on_left_edge():
    midpoint = (SCREEN.width - WINDOW.width) // 2
    assert snap_to_nearest_side(Point(midpoint, 300), WINDOW, SCREEN) == Point(0, 300)
