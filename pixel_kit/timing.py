# Time and easing for the timeline.


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def seg(t, a, b):
    """0 before a, 1 after b, linear between."""
    return clamp((t - a) / (b - a))


def ease(x):
    return x * x * (3 - 2 * x)


def lerp(a, b, k):
    return a + (b - a) * k


def path(t, way):
    """way: [(t, x, y), ...]: a piecewise eased path; returns x, y, direction (1/-1)."""
    if t <= way[0][0]:
        return way[0][1], way[0][2], 1
    for (t0, x0, y0), (t1, x1, y1) in zip(way, way[1:]):
        if t0 <= t <= t1:
            k = ease(seg(t, t0, t1))
            return lerp(x0, x1, k), lerp(y0, y1, k), (1 if x1 >= x0 else -1)
    return way[-1][1], way[-1][2], 1
