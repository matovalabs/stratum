// STRATUM for Windows: Go live (live_win.cpp).
#pragma once
#define NOMINMAX
#include <windows.h>
#include <string>
#include "json.h"

namespace live {
// Where the window and the camera go: rectangles [x, y, w, h] as fractions of the frame, from the top left, as the page's
// camera layout picker sends them. camTop: the camera is drawn over the window.
struct Layout { double main[4] = {0, 0, 1, 1}, cam[4] = {0, 0, 0, 0}; bool hasCam = false, camTop = true; };
// The layout in a liveStart / liveLayout request, or the original one (the camera beside the window) when there is none.
Layout layoutFrom(const Json &body);
// Connects and starts streaming `window`; returns an error message, or "" once live. Blocks while connecting.
std::string start(HWND window, const std::string &url, const std::string &key, bool camera, bool mic, const Layout &layout);
// Moves the camera and window while live.
void setLayout(const Layout &layout);
void stop();
Json status();
// Stream keys the producer asked STRATUM to remember, kept in Windows Credential Manager.
void saveKey(const std::string &platform, const std::string &url, const std::string &key);
Json loadKey(const std::string &platform);
}
