#pragma once

#include <stddef.h>
#include <stdint.h>

struct ZoneColor
{
    uint8_t r, g, b;
};

inline int hexDigit(uint8_t c)
{
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

// parse #rrggbb colors separated by commas without relying on a null terminator
inline size_t parseZoneColors(const uint8_t *payload, size_t length, ZoneColor *colors, size_t capacity)
{
    if (length == 0 || (length + 1) % 8 != 0) return 0;
    const size_t count = (length + 1) / 8;
    if (count > capacity) return 0;
    for (size_t i = 0; i < count; ++i)
    {
        const size_t start = i * 8;
        if (payload[start] != '#' || (i && payload[start - 1] != ',')) return 0;
        uint8_t channels[3];
        for (size_t channel = 0; channel < 3; ++channel)
        {
            int high = hexDigit(payload[start + 1 + channel * 2]);
            int low = hexDigit(payload[start + 2 + channel * 2]);
            if (high < 0 || low < 0) return 0;
            channels[channel] = static_cast<uint8_t>(high * 16 + low);
        }
        colors[i] = {channels[0], channels[1], channels[2]};
    }
    return count;
}

// place targets at zone centers and interpolate between neighboring targets
inline ZoneColor colorAtLed(const ZoneColor *colors, size_t count, size_t index, size_t ledCount)
{
    const int32_t position = static_cast<int32_t>((2 * index + 1) * count) - static_cast<int32_t>(ledCount);
    const int32_t step = static_cast<int32_t>(2 * ledCount);
    if (count == 1 || position <= 0) return colors[0];
    if (position >= static_cast<int32_t>((count - 1) * step)) return colors[count - 1];
    const size_t left = position / step;
    const int32_t fraction = position % step;
    const ZoneColor a = colors[left], b = colors[left + 1];
    return {
        static_cast<uint8_t>((a.r * (step - fraction) + b.r * fraction + step / 2) / step),
        static_cast<uint8_t>((a.g * (step - fraction) + b.g * fraction + step / 2) / step),
        static_cast<uint8_t>((a.b * (step - fraction) + b.b * fraction + step / 2) / step)
    };
}
