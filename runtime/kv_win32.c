/* kv_win32.c — the Windows backend.
 *
 * One window, one device-independent bitmap, and a ring of translated events.
 * The pixel format needs no conversion: a 32-bit BI_RGB DIB is 0x00RRGGBB in
 * a little-endian word, which is what the rasteriser already writes.
 *
 * Built with MinGW-w64 or clang targeting mingw32 — the same requirement
 * `keal build` itself has, because the generated C uses GCC's overflow
 * builtins and MSVC has none.
 */
#include "kv.h"

/* UNICODE before windows.h, so that `MAKEINTRESOURCE` — and with it
 * `IDC_ARROW` and its siblings — expands to the wide form the `…W` entry
 * points take. Without it MinGW hands `LoadCursorW` an `LPSTR` and the
 * compiler is right to refuse. Everything here calls the W functions by name
 * already; this only makes the macros agree. */
#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <windowsx.h>

KvEv kv_ev;

#define QN 512
static KvEv   q[QN];
static int    qhead = 0, qtail = 0;
static HWND   win = NULL;
static int    alive = 0;
static double scale = 1.0;
static int64_t pxw = 0, pxh = 0;
static LARGE_INTEGER freq, start;
static int      want_dark = 0;
static HCURSOR cursors[5];
static int     cursor_now = 0;

static void push(KvEv e) {
    int n = (qtail + 1) % QN;
    if (n == qhead) return;
    q[qtail] = e;
    qtail = n;
}

static KvEv blank(int64_t kind) {
    KvEv e;
    memset(&e, 0, sizeof e);
    e.kind = kind;
    return e;
}

static int64_t mods_now(void) {
    int64_t m = 0;
    if (GetKeyState(VK_SHIFT) < 0)   m += KV_MOD_SHIFT;
    if (GetKeyState(VK_CONTROL) < 0) m += KV_MOD_CTRL;
    if (GetKeyState(VK_MENU) < 0)    m += KV_MOD_ALT;
    if ((GetKeyState(VK_LWIN) < 0) || (GetKeyState(VK_RWIN) < 0)) m += KV_MOD_SUPER;
    return m;
}

static int64_t named_key(WPARAM vk) {
    switch (vk) {
        case VK_LEFT:   return KV_KEY_LEFT;
        case VK_RIGHT:  return KV_KEY_RIGHT;
        case VK_UP:     return KV_KEY_UP;
        case VK_DOWN:   return KV_KEY_DOWN;
        case VK_RETURN: return KV_KEY_ENTER;
        case VK_TAB:    return KV_KEY_TAB;
        case VK_BACK:   return KV_KEY_BACKSPACE;
        case VK_DELETE: return KV_KEY_DELETE;
        case VK_ESCAPE: return KV_KEY_ESCAPE;
        case VK_HOME:   return KV_KEY_HOME;
        case VK_END:    return KV_KEY_END;
        case VK_PRIOR:  return KV_KEY_PAGEUP;
        case VK_NEXT:   return KV_KEY_PAGEDOWN;
        case VK_SPACE:  return KV_KEY_SPACE;
        default:        return 0;
    }
}

static void measure(void) {
    RECT r;
    if (!win || !GetClientRect(win, &r)) return;
    pxw = r.right - r.left;
    pxh = r.bottom - r.top;
    if (pxw < 1) pxw = 1;
    if (pxh < 1) pxh = 1;
    /* GetDpiForWindow is Windows 10 1607 and later; a MinGW header old enough
     * not to declare it is old enough that the fallback is the right answer. */
    typedef UINT (WINAPI *GetDpiForWindow_t)(HWND);
    static GetDpiForWindow_t fn = NULL;
    static int looked = 0;
    if (!looked) {
        looked = 1;
        HMODULE u = GetModuleHandleW(L"user32.dll");
        if (u) fn = (GetDpiForWindow_t)(void *)GetProcAddress(u, "GetDpiForWindow");
    }
    UINT dpi = fn ? fn(win) : 96;
    if (dpi < 48) dpi = 96;
    scale = (double)dpi / 96.0;
}

/* One UTF-16 unit, or a surrogate pair, as UTF-8 in the event's own buffer. */
static void put_text(KvEv *e, unsigned int cp) {
    char *o = e->text;
    if (cp < 0x80) { o[0] = (char)cp; o[1] = 0; return; }
    if (cp < 0x800) {
        o[0] = (char)(0xC0 | (cp >> 6));
        o[1] = (char)(0x80 | (cp & 0x3F));
        o[2] = 0;
        return;
    }
    if (cp < 0x10000) {
        o[0] = (char)(0xE0 | (cp >> 12));
        o[1] = (char)(0x80 | ((cp >> 6) & 0x3F));
        o[2] = (char)(0x80 | (cp & 0x3F));
        o[3] = 0;
        return;
    }
    o[0] = (char)(0xF0 | (cp >> 18));
    o[1] = (char)(0x80 | ((cp >> 12) & 0x3F));
    o[2] = (char)(0x80 | ((cp >> 6) & 0x3F));
    o[3] = (char)(0x80 | (cp & 0x3F));
    o[4] = 0;
}

static LRESULT CALLBACK proc(HWND h, UINT msg, WPARAM wp, LPARAM lp) {
    KvEv e;
    static unsigned int pending_high = 0;
    switch (msg) {
        case WM_CLOSE:   push(blank(KV_EV_CLOSE)); return 0;
        case WM_SIZE:    measure(); push(blank(KV_EV_RESIZE)); return 0;
        case WM_DPICHANGED: measure(); push(blank(KV_EV_RESIZE)); return 0;
        case WM_PAINT: {
            PAINTSTRUCT ps;
            BeginPaint(h, &ps);
            EndPaint(h, &ps);
            push(blank(KV_EV_EXPOSE));
            return 0;
        }
        case WM_SETFOCUS:  push(blank(KV_EV_FOCUS)); return 0;
        case WM_KILLFOCUS: push(blank(KV_EV_BLUR));  return 0;
        case WM_SETCURSOR:
            if (LOWORD(lp) == HTCLIENT) { SetCursor(cursors[cursor_now]); return TRUE; }
            break;
        case WM_MOUSEMOVE:
            e = blank(KV_EV_MOVE);
            e.x = GET_X_LPARAM(lp); e.y = GET_Y_LPARAM(lp);
            e.mods = mods_now();
            if (wp & MK_LBUTTON) e.button = 1;
            else if (wp & MK_RBUTTON) e.button = 2;
            else if (wp & MK_MBUTTON) e.button = 3;
            push(e);
            return 0;
        case WM_LBUTTONDOWN: case WM_RBUTTONDOWN: case WM_MBUTTONDOWN:
        case WM_LBUTTONDBLCLK: case WM_RBUTTONDBLCLK:
            SetCapture(h);
            e = blank(KV_EV_DOWN);
            e.button = (msg == WM_LBUTTONDOWN || msg == WM_LBUTTONDBLCLK) ? 1
                     : (msg == WM_RBUTTONDOWN || msg == WM_RBUTTONDBLCLK) ? 2 : 3;
            e.clicks = (msg == WM_LBUTTONDBLCLK || msg == WM_RBUTTONDBLCLK) ? 2 : 1;
            e.x = GET_X_LPARAM(lp); e.y = GET_Y_LPARAM(lp);
            e.mods = mods_now();
            push(e);
            return 0;
        case WM_LBUTTONUP: case WM_RBUTTONUP: case WM_MBUTTONUP:
            ReleaseCapture();
            e = blank(KV_EV_UP);
            e.button = msg == WM_LBUTTONUP ? 1 : msg == WM_RBUTTONUP ? 2 : 3;
            e.x = GET_X_LPARAM(lp); e.y = GET_Y_LPARAM(lp);
            e.mods = mods_now();
            push(e);
            return 0;
        case WM_MOUSEWHEEL: case WM_MOUSEHWHEEL: {
            POINT p = { GET_X_LPARAM(lp), GET_Y_LPARAM(lp) };
            ScreenToClient(h, &p);
            e = blank(KV_EV_SCROLL);
            e.x = p.x; e.y = p.y;
            double d = (double)GET_WHEEL_DELTA_WPARAM(wp) / (double)WHEEL_DELTA * 40.0;
            if (msg == WM_MOUSEWHEEL) e.dy = d; else e.dx = -d;
            e.mods = mods_now();
            push(e);
            return 0;
        }
        case WM_KEYDOWN: case WM_SYSKEYDOWN: {
            e = blank(KV_EV_KEYDOWN);
            e.key = named_key(wp);
            e.mods = mods_now();
            /* The letter the key would type with nothing held down, so that a
             * shortcut can be told from another one. Ctrl+C sends WM_CHAR 0x03,
             * which is dropped as a control character and rightly so, and the
             * key press would otherwise carry nothing at all. */
            UINT ch = MapVirtualKeyW((UINT)wp, 2 /* MAPVK_VK_TO_CHAR */) & 0x7FFF;
            if (ch >= 'A' && ch <= 'Z') ch += 32;
            if (ch >= 32 && ch < 127) { e.text[0] = (char)ch; e.text[1] = 0; }
            push(e);
            return 0;
        }
        case WM_KEYUP: case WM_SYSKEYUP:
            e = blank(KV_EV_KEYUP);
            e.key = named_key(wp);
            e.mods = mods_now();
            push(e);
            return 0;
        case WM_CHAR: {
            unsigned int c = (unsigned int)wp;
            if (c >= 0xD800 && c <= 0xDBFF) { pending_high = c; return 0; }
            if (c >= 0xDC00 && c <= 0xDFFF) {
                if (!pending_high) return 0;
                c = 0x10000 + ((pending_high - 0xD800) << 10) + (c - 0xDC00);
                pending_high = 0;
            }
            if (c < 32 || c == 127) return 0;
            e = blank(KV_EV_TEXT);
            e.mods = mods_now();
            put_text(&e, c);
            push(e);
            return 0;
        }
        default: break;
    }
    return DefWindowProcW(h, msg, wp, lp);
}

int64_t kvp_open(const char *title, int64_t w, int64_t h) {
    /* Per-monitor DPI awareness, where the system has it; otherwise the
     * window is scaled by the compositor and still looks right, just softer. */
    typedef BOOL (WINAPI *SetCtx_t)(void *);
    HMODULE u = GetModuleHandleW(L"user32.dll");
    if (u) {
        SetCtx_t f = (SetCtx_t)(void *)GetProcAddress(u, "SetProcessDpiAwarenessContext");
        if (f) f((void *)-4); /* PER_MONITOR_AWARE_V2 */
        else {
            typedef BOOL (WINAPI *SetDpi_t)(void);
            SetDpi_t g = (SetDpi_t)(void *)GetProcAddress(u, "SetProcessDPIAware");
            if (g) g();
        }
    }

    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&start);

    cursors[KV_CURSOR_ARROW]    = LoadCursorW(NULL, IDC_ARROW);
    cursors[KV_CURSOR_HAND]     = LoadCursorW(NULL, IDC_HAND);
    cursors[KV_CURSOR_TEXT]     = LoadCursorW(NULL, IDC_IBEAM);
    cursors[KV_CURSOR_RESIZE_H] = LoadCursorW(NULL, IDC_SIZEWE);
    cursors[KV_CURSOR_RESIZE_V] = LoadCursorW(NULL, IDC_SIZENS);

    WNDCLASSEXW wc;
    memset(&wc, 0, sizeof wc);
    wc.cbSize = sizeof wc;
    wc.style = CS_HREDRAW | CS_VREDRAW | CS_DBLCLKS | CS_OWNDC;
    wc.lpfnWndProc = proc;
    wc.hInstance = GetModuleHandleW(NULL);
    wc.hCursor = NULL;                 /* WM_SETCURSOR answers instead */
    wc.hbrBackground = NULL;
    wc.lpszClassName = L"KealViewWindow";
    if (!RegisterClassExW(&wc)) {
        if (GetLastError() != ERROR_CLASS_ALREADY_EXISTS) return 0;
    }

    WCHAR wtitle[512];
    int n = MultiByteToWideChar(CP_UTF8, 0, title ? title : "keal-view", -1,
                                wtitle, 511);
    if (n <= 0) wcscpy(wtitle, L"keal-view");

    /* The requested size is in logical points, so it has to be scaled before
     * the window is created — `GetDpiForWindow` cannot be asked about a window
     * that does not exist yet, and creating it at pixel size opens it at half
     * the size on a 150 % display. `GetDpiForSystem` is Windows 10 1607 and
     * up; older systems are at 96 anyway. Found on X11, where the same mistake
     * was in the same place. */
    UINT sysdpi = 96;
    {
        HMODULE u3 = GetModuleHandleW(L"user32.dll");
        if (u3) {
            typedef UINT (WINAPI * GetDpiForSystem_t)(void);
            GetDpiForSystem_t g = (GetDpiForSystem_t)(void *)
                GetProcAddress(u3, "GetDpiForSystem");
            if (g) sysdpi = g();
        }
    }
    if (sysdpi < 48) sysdpi = 96;
    double open_scale = (double)sysdpi / 96.0;
    RECT want = { 0, 0, (LONG)((double)w * open_scale + 0.5),
                        (LONG)((double)h * open_scale + 0.5) };
    AdjustWindowRectEx(&want, WS_OVERLAPPEDWINDOW, FALSE, 0);
    win = CreateWindowExW(0, L"KealViewWindow", wtitle, WS_OVERLAPPEDWINDOW,
                          CW_USEDEFAULT, CW_USEDEFAULT,
                          want.right - want.left, want.bottom - want.top,
                          NULL, NULL, wc.hInstance, NULL);
    if (!win) return 0;
    /* Before the window is shown: Windows 10 does not repaint a caption that
     * is already on screen, so this is the only moment a dark one takes hold
     * without a resize to shake it loose. */
    kvp_set_dark(want_dark);
    ShowWindow(win, SW_SHOW);
    UpdateWindow(win);
    SetForegroundWindow(win);
    measure();
    alive = 1;
    return 1;
}

void kvp_close(void) {
    alive = 0;
    if (win) { DestroyWindow(win); win = NULL; }
}

int64_t kvp_alive(void) { return alive; }

static void pump(void) {
    MSG m;
    while (PeekMessageW(&m, NULL, 0, 0, PM_REMOVE)) {
        TranslateMessage(&m);
        DispatchMessageW(&m);
        if (((qtail + 1) % QN) == qhead) break;
    }
}

int64_t kvp_poll(void) {
    if (qhead == qtail) pump();
    if (qhead == qtail) { kv_ev.kind = KV_EV_NONE; return KV_EV_NONE; }
    kv_ev = q[qhead];
    qhead = (qhead + 1) % QN;
    return kv_ev.kind;
}

/* Wait for the system to have something to say.
 *
 * This used to pass `MWMO_INPUTAVAILABLE`, and that flag is the whole story of
 * why an idle window burned a core. It tells the wait to return for input that
 * is *already available* — including input a previous `PeekMessage` has
 * already looked at. `QS_ALLINPUT` includes `QS_MOUSEMOVE`, and Windows holds
 * that bit while the cursor sits over a window of this thread. A stationary
 * cursor generates no `WM_MOUSEMOVE`, so `pump` removes nothing and clears
 * nothing, and the wait returns instantly, for ever. Measured at 96–100 % of a
 * core with the pointer resting anywhere over the window — the title bar
 * included, which is not even ours to draw — and 0.00 % the moment it moved
 * off, or the window was minimised, or another window covered it.
 *
 * The flag was there to close a race: a message arriving between the last
 * `PeekMessage` and the wait would otherwise be slept through, and this loop
 * waits for ever when nothing is animating, so a lost wake-up is a frozen
 * window rather than a late frame. So the race is closed the other way, which
 * is the ordinary pattern: ask whether anything is queued, and if something is,
 * do not wait at all. A message arriving after that question sets the wake bit
 * and the wait returns on it. */
void kvp_wait(int64_t ms) {
    if (qhead != qtail) return;
    MSG peek;
    if (!PeekMessageW(&peek, NULL, 0, 0, PM_NOREMOVE)) {
        DWORD t = ms < 0 ? INFINITE : (DWORD)ms;
        MsgWaitForMultipleObjectsEx(0, NULL, t, QS_ALLINPUT, 0);
    }
    pump();
}

void kvp_wake(void) {
    if (win) PostMessageW(win, WM_NULL, 0, 0);
}

void kvp_present(const uint32_t *fb, int64_t w, int64_t h) {
    if (!win || !fb || w < 1 || h < 1) return;
    HDC dc = GetDC(win);
    if (!dc) return;
    BITMAPINFO bi;
    memset(&bi, 0, sizeof bi);
    bi.bmiHeader.biSize = sizeof bi.bmiHeader;
    bi.bmiHeader.biWidth = (LONG)w;
    bi.bmiHeader.biHeight = -(LONG)h;      /* negative: rows run top-down */
    bi.bmiHeader.biPlanes = 1;
    bi.bmiHeader.biBitCount = 32;
    bi.bmiHeader.biCompression = BI_RGB;
    StretchDIBits(dc, 0, 0, (int)w, (int)h, 0, 0, (int)w, (int)h,
                  fb, &bi, DIB_RGB_COLORS, SRCCOPY);
    ReleaseDC(win, dc);
}

int64_t kvp_width(void)  { return pxw; }
int64_t kvp_height(void) { return pxh; }
double  kvp_scale(void)  { return scale; }

void kvp_set_title(const char *t) {
    if (!win || !t) return;
    WCHAR w[512];
    if (MultiByteToWideChar(CP_UTF8, 0, t, -1, w, 511) > 0) SetWindowTextW(win, w);
}

/* Only when it changes.
 *
 * The run loop asks for a cursor shape every frame, which is the right thing
 * for it to do — it does not know what the last frame asked for. Calling
 * `SetCursor` every frame is not: Windows re-sends `WM_SETCURSOR` to the
 * window under the pointer when the shape is re-established, so the frame
 * woke the wait that drew the frame. It only happened while the pointer was
 * over the window, which is the only time `WM_SETCURSOR` is sent at all, and
 * it did not care about focus or about which part of the window — the title
 * bar is non-client and gets one too. */
void kvp_set_cursor(int64_t shape) {
    if (shape < 0 || shape > 4) shape = 0;
    if ((int)shape == cursor_now) return;
    cursor_now = (int)shape;
    SetCursor(cursors[cursor_now]);
}

/* Remember what the application wants before there is a window to want it of.
 * `kvp_open` applies this between creating the window and showing it. */
void kvp_prefer_dark(int64_t dark) { want_dark = dark ? 1 : 0; }

/* The real build number. `GetVersionEx` lies to a process with no manifest —
 * it answers 6.2 for everything since Windows 8 — and `RtlGetVersion` does
 * not. Windows 11 is build 22000 and up, whatever the registry's `ProductName`
 * says about itself. */
static int windows_build(void) {
    static int cached = -1;
    if (cached >= 0) return cached;
    cached = 0;
    HMODULE nt = GetModuleHandleW(L"ntdll.dll");
    if (nt) {
        typedef LONG (WINAPI * RtlGetVersion_t)(void *);
        RtlGetVersion_t f = (RtlGetVersion_t)(void *)GetProcAddress(nt, "RtlGetVersion");
        if (f) {
            struct {
                ULONG size, major, minor, build, platform;
                WCHAR csd[128];
            } v;
            memset(&v, 0, sizeof v);
            v.size = sizeof v;
            if (f(&v) == 0) cached = (int)v.build;
        }
    }
    return cached;
}

/* Windows has no system-wide dark title bar before build 17763, and telling
 * it about one after that is a documented-but-undocumented attribute. Both
 * cases are handled by asking and ignoring a refusal.
 *
 * On **Windows 10** the attribute takes effect immediately on a window that
 * has not been shown, and not at all on one that has: `RedrawWindow(RDW_FRAME)`
 * and `SetWindowPos(SWP_FRAMECHANGED)` both leave the old caption in place,
 * and only a real change of size makes the desktop manager rebuild it. So a
 * window already on screen is nudged one pixel and back — a hack, and here
 * because the alternative is a light caption over a dark application every
 * time the theme is switched.
 *
 * On **Windows 11** the desktop manager repaints the caption by itself, both
 * ways, with no resize at all — measured on 22621 by setting the attribute
 * from outside the process and watching the title bar change. So the nudge is
 * skipped there: it took two `SetWindowPos` calls and about two milliseconds
 * during which `SWP_NOCOPYBITS` invalidates the client area, for no effect
 * anyone can name. Build 22000 is the line. */
void kvp_set_dark(int64_t dark) {
    if (!win) return;
    want_dark = dark ? 1 : 0;
    HMODULE dwm = LoadLibraryW(L"dwmapi.dll");
    if (!dwm) return;
    typedef HRESULT (WINAPI *SetAttr_t)(HWND, DWORD, LPCVOID, DWORD);
    SetAttr_t f = (SetAttr_t)(void *)GetProcAddress(dwm, "DwmSetWindowAttribute");
    int applied = 0;
    if (f) {
        BOOL v = dark ? TRUE : FALSE;
        if (f(win, 20, &v, sizeof v) == S_OK) applied = 1;
        else if (f(win, 19, &v, sizeof v) == S_OK) applied = 1;
    }
    FreeLibrary(dwm);
    if (applied && IsWindowVisible(win) && windows_build() < 22000) {
        RECT r;
        if (GetWindowRect(win, &r)) {
            int w = r.right - r.left, h = r.bottom - r.top;
            UINT flags = SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_NOCOPYBITS;
            SetWindowPos(win, NULL, 0, 0, w, h + 1, flags);
            SetWindowPos(win, NULL, 0, 0, w, h, flags);
        }
    }
}

int64_t kvp_window_id(void) { return (int64_t)(intptr_t)win; }

double kvp_now_ms(void) {
    LARGE_INTEGER n;
    QueryPerformanceCounter(&n);
    if (freq.QuadPart == 0) return 0.0;
    return (double)(n.QuadPart - start.QuadPart) * 1000.0 / (double)freq.QuadPart;
}

/* `OpenClipboard` is a lock, and on a machine with clipboard history switched
 * on — which is the default — the system's own service holds it for a moment
 * after every change. So writing and immediately reading back, which is what a
 * quick Ctrl+C then Ctrl+V does, loses the race often enough to matter: about
 * 6 % of reads straight after a write, measured over three hundred, all of
 * them `ERROR_ACCESS_DENIED` from `OpenClipboard` and never a failure further
 * in. Two attempts were always enough in that measurement; eight is the
 * margin, and the cost is paid only when contended.
 *
 * Failing here is worse than it looks, because a caller cannot tell an empty
 * clipboard from a busy one. */
static int open_clipboard(void) {
    for (int i = 0; i < 8; i++) {
        if (OpenClipboard(win)) return 1;
        Sleep(1);
    }
    return 0;
}

char *kvp_clipboard_get(void) {
    char *out = NULL;
    if (open_clipboard()) {
        HANDLE h = GetClipboardData(CF_UNICODETEXT);
        if (h) {
            WCHAR *w = (WCHAR *)GlobalLock(h);
            if (w) {
                int n = WideCharToMultiByte(CP_UTF8, 0, w, -1, NULL, 0, NULL, NULL);
                if (n > 0) {
                    out = (char *)malloc((size_t)n);
                    if (out) WideCharToMultiByte(CP_UTF8, 0, w, -1, out, n, NULL, NULL);
                }
                GlobalUnlock(h);
            }
        }
        CloseClipboard();
    }
    if (!out) { out = (char *)malloc(1); if (out) out[0] = 0; }
    return out;
}

void kvp_clipboard_set(const char *s) {
    if (!s) return;
    if (!open_clipboard()) return;
    EmptyClipboard();
    int n = MultiByteToWideChar(CP_UTF8, 0, s, -1, NULL, 0);
    if (n > 0) {
        HGLOBAL g = GlobalAlloc(GMEM_MOVEABLE, (size_t)n * sizeof(WCHAR));
        if (g) {
            WCHAR *w = (WCHAR *)GlobalLock(g);
            if (w) {
                MultiByteToWideChar(CP_UTF8, 0, s, -1, w, n);
                GlobalUnlock(g);
                SetClipboardData(CF_UNICODETEXT, g);
            }
        }
    }
    CloseClipboard();
}

char *kvp_font_path(int64_t which) {
    static const char *sans[] = { "C:\\Windows\\Fonts\\segoeui.ttf",
                                  "C:\\Windows\\Fonts\\tahoma.ttf",
                                  "C:\\Windows\\Fonts\\arial.ttf", NULL };
    static const char *bold[] = { "C:\\Windows\\Fonts\\segoeuib.ttf",
                                  "C:\\Windows\\Fonts\\arialbd.ttf",
                                  "C:\\Windows\\Fonts\\tahomabd.ttf", NULL };
    static const char *mono[] = { "C:\\Windows\\Fonts\\consola.ttf",
                                  "C:\\Windows\\Fonts\\cour.ttf", NULL };
    const char **list = which == 1 ? bold : which == 2 ? mono : sans;
    for (int i = 0; list[i]; i++) {
        FILE *f = fopen(list[i], "rb");
        if (f) {
            fclose(f);
            char *o = (char *)malloc(strlen(list[i]) + 1);
            if (o) strcpy(o, list[i]);
            return o;
        }
    }
    char *o = (char *)malloc(1);
    if (o) o[0] = 0;
    return o;
}
