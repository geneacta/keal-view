/* kv_x11.c — the X11 backend.
 *
 * One window, one XImage over the framebuffer, and a ring of translated
 * events. Xlib only: no toolkit, no compositor protocol, nothing to install
 * beyond libX11 itself, which every X session already has.
 *
 * The pixel format needs no conversion on the usual TrueColor visual — red
 * 0xFF0000, green 0xFF00, blue 0xFF — which is what the rasteriser writes.
 * The image is declared LSBFirst and Xlib converts for a big-endian server.
 */
#include "kv.h"

#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/Xatom.h>
#include <X11/keysym.h>
#include <X11/cursorfont.h>
#include <X11/Xresource.h>
#include <sys/select.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>

KvEv kv_ev;

#define QN 512
static KvEv    q[QN];
static int     qhead = 0, qtail = 0;
static Display *dpy = NULL;
static Window   win = 0;
static GC       gc = 0;
static Visual  *vis = NULL;
static int      depth = 24;
static int      alive = 0;
static double   scale = 1.0;
static int64_t  pxw = 0, pxh = 0;
static Atom     wm_delete, wm_protocols, a_clipboard, a_utf8, a_targets, a_kvsel, a_wake;
static Cursor   cursors[5];
static char    *clipboard_own = NULL;   /* what we last put on the clipboard */
static struct timespec t0;

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

static int64_t mods_of(unsigned int st) {
    int64_t m = 0;
    if (st & ShiftMask)   m += KV_MOD_SHIFT;
    if (st & ControlMask) m += KV_MOD_CTRL;
    if (st & Mod1Mask)    m += KV_MOD_ALT;
    if (st & Mod4Mask)    m += KV_MOD_SUPER;
    return m;
}

static int64_t named_key(KeySym k) {
    switch (k) {
        case XK_Left:      return KV_KEY_LEFT;
        case XK_Right:     return KV_KEY_RIGHT;
        case XK_Up:        return KV_KEY_UP;
        case XK_Down:      return KV_KEY_DOWN;
        case XK_Return:    case XK_KP_Enter: return KV_KEY_ENTER;
        case XK_Tab:       case XK_ISO_Left_Tab: return KV_KEY_TAB;
        case XK_BackSpace: return KV_KEY_BACKSPACE;
        case XK_Delete:    return KV_KEY_DELETE;
        case XK_Escape:    return KV_KEY_ESCAPE;
        case XK_Home:      return KV_KEY_HOME;
        case XK_End:       return KV_KEY_END;
        case XK_Prior:     return KV_KEY_PAGEUP;
        case XK_Next:      return KV_KEY_PAGEDOWN;
        case XK_space:     return KV_KEY_SPACE;
        default:           return 0;
    }
}

/* The scale comes from Xft.dpi in the resource database, which is what every
 * desktop environment sets and what every toolkit reads. No answer means 96,
 * which means 1.0, which is right on the displays that do not say. */
static void read_scale(void) {
    scale = 1.0;
    char *rms = XResourceManagerString(dpy);
    if (!rms) return;
    XrmDatabase db = XrmGetStringDatabase(rms);
    if (!db) return;
    char *type = NULL;
    XrmValue v;
    if (XrmGetResource(db, "Xft.dpi", "Xft.Dpi", &type, &v) && v.addr) {
        double dpi = atof(v.addr);
        if (dpi >= 48.0) scale = dpi / 96.0;
    }
    XrmDestroyDatabase(db);
}

static void answer_selection(XSelectionRequestEvent *req) {
    XSelectionEvent out;
    memset(&out, 0, sizeof out);
    out.type = SelectionNotify;
    out.display = req->display;
    out.requestor = req->requestor;
    out.selection = req->selection;
    out.target = req->target;
    out.time = req->time;
    out.property = None;
    if (clipboard_own) {
        if (req->target == a_targets) {
            Atom offer[2] = { a_targets, a_utf8 };
            XChangeProperty(dpy, req->requestor, req->property, XA_ATOM, 32,
                            PropModeReplace, (unsigned char *)offer, 2);
            out.property = req->property;
        } else if (req->target == a_utf8 || req->target == XA_STRING) {
            XChangeProperty(dpy, req->requestor, req->property, req->target, 8,
                            PropModeReplace, (unsigned char *)clipboard_own,
                            (int)strlen(clipboard_own));
            out.property = req->property;
        }
    }
    XSendEvent(dpy, req->requestor, False, 0, (XEvent *)&out);
}

static void translate(XEvent *ev) {
    KvEv e;
    switch (ev->type) {
        case ClientMessage:
            if (ev->xclient.message_type == wm_protocols
                && (Atom)ev->xclient.data.l[0] == wm_delete) {
                push(blank(KV_EV_CLOSE));
            }
            return;
        case ConfigureNotify:
            if (ev->xconfigure.width != pxw || ev->xconfigure.height != pxh) {
                pxw = ev->xconfigure.width;
                pxh = ev->xconfigure.height;
                if (pxw < 1) pxw = 1;
                if (pxh < 1) pxh = 1;
                push(blank(KV_EV_RESIZE));
            }
            return;
        case Expose:
            if (ev->xexpose.count == 0) push(blank(KV_EV_EXPOSE));
            return;
        case FocusIn:  push(blank(KV_EV_FOCUS)); return;
        case FocusOut: push(blank(KV_EV_BLUR));  return;
        case MotionNotify:
            e = blank(KV_EV_MOVE);
            e.x = ev->xmotion.x;
            e.y = ev->xmotion.y;
            e.mods = mods_of(ev->xmotion.state);
            if (ev->xmotion.state & Button1Mask) e.button = 1;
            else if (ev->xmotion.state & Button3Mask) e.button = 2;
            else if (ev->xmotion.state & Button2Mask) e.button = 3;
            push(e);
            return;
        case ButtonPress:
            /* X11 sends the wheel as buttons 4 to 7. */
            if (ev->xbutton.button >= 4 && ev->xbutton.button <= 7) {
                e = blank(KV_EV_SCROLL);
                e.x = ev->xbutton.x;
                e.y = ev->xbutton.y;
                if (ev->xbutton.button == 4) e.dy = 40.0;
                if (ev->xbutton.button == 5) e.dy = -40.0;
                if (ev->xbutton.button == 6) e.dx = 40.0;
                if (ev->xbutton.button == 7) e.dx = -40.0;
                e.mods = mods_of(ev->xbutton.state);
                push(e);
                return;
            }
            e = blank(KV_EV_DOWN);
            e.button = ev->xbutton.button == 1 ? 1 : ev->xbutton.button == 3 ? 2 : 3;
            e.clicks = 1;
            e.x = ev->xbutton.x;
            e.y = ev->xbutton.y;
            e.mods = mods_of(ev->xbutton.state);
            push(e);
            return;
        case ButtonRelease:
            if (ev->xbutton.button >= 4 && ev->xbutton.button <= 7) return;
            e = blank(KV_EV_UP);
            e.button = ev->xbutton.button == 1 ? 1 : ev->xbutton.button == 3 ? 2 : 3;
            e.x = ev->xbutton.x;
            e.y = ev->xbutton.y;
            e.mods = mods_of(ev->xbutton.state);
            push(e);
            return;
        case KeyPress: {
            char buf[32];
            KeySym ks = 0;
            int n = XLookupString(&ev->xkey, buf, sizeof buf - 1, &ks, NULL);
            e = blank(KV_EV_KEYDOWN);
            e.key = named_key(ks);
            e.mods = mods_of(ev->xkey.state);
            push(e);
            if (n > 0 && (unsigned char)buf[0] >= 32 && (unsigned char)buf[0] != 127) {
                KvEv te = blank(KV_EV_TEXT);
                te.mods = e.mods;
                if (n > (int)sizeof te.text - 1) n = (int)sizeof te.text - 1;
                memcpy(te.text, buf, (size_t)n);
                te.text[n] = 0;
                push(te);
            }
            return;
        }
        case KeyRelease: {
            KeySym ks = XLookupKeysym(&ev->xkey, 0);
            e = blank(KV_EV_KEYUP);
            e.key = named_key(ks);
            e.mods = mods_of(ev->xkey.state);
            push(e);
            return;
        }
        case SelectionRequest:
            answer_selection(&ev->xselectionrequest);
            return;
        case SelectionClear:
            free(clipboard_own);
            clipboard_own = NULL;
            return;
        default:
            return;
    }
}

int64_t kvp_open(const char *title, int64_t w, int64_t h) {
    XInitThreads();
    dpy = XOpenDisplay(NULL);
    if (!dpy) return 0;
    int screen = DefaultScreen(dpy);
    vis = DefaultVisual(dpy, screen);
    depth = DefaultDepth(dpy, screen);
    if (depth < 24) { XCloseDisplay(dpy); dpy = NULL; return 0; }

    XSetWindowAttributes at;
    memset(&at, 0, sizeof at);
    at.background_pixel = BlackPixel(dpy, screen);
    at.event_mask = ExposureMask | KeyPressMask | KeyReleaseMask
                  | ButtonPressMask | ButtonReleaseMask | PointerMotionMask
                  | StructureNotifyMask | FocusChangeMask;
    win = XCreateWindow(dpy, RootWindow(dpy, screen), 0, 0,
                        (unsigned)w, (unsigned)h, 0, depth, InputOutput, vis,
                        CWBackPixel | CWEventMask, &at);
    if (!win) { XCloseDisplay(dpy); dpy = NULL; return 0; }

    wm_protocols = XInternAtom(dpy, "WM_PROTOCOLS", False);
    wm_delete    = XInternAtom(dpy, "WM_DELETE_WINDOW", False);
    a_clipboard  = XInternAtom(dpy, "CLIPBOARD", False);
    a_utf8       = XInternAtom(dpy, "UTF8_STRING", False);
    a_targets    = XInternAtom(dpy, "TARGETS", False);
    a_kvsel      = XInternAtom(dpy, "KEAL_VIEW_SELECTION", False);
    a_wake       = XInternAtom(dpy, "KEAL_VIEW_WAKE", False);
    XSetWMProtocols(dpy, win, &wm_delete, 1);

    kvp_set_title(title);
    /* A hint the common window managers read; the ones that do not simply
     * keep their own title bar, which is theirs to draw. */
    XSizeHints hints;
    memset(&hints, 0, sizeof hints);
    hints.flags = PMinSize;
    hints.min_width = 240;
    hints.min_height = 160;
    XSetWMNormalHints(dpy, win, &hints);

    cursors[KV_CURSOR_ARROW]    = XCreateFontCursor(dpy, XC_left_ptr);
    cursors[KV_CURSOR_HAND]     = XCreateFontCursor(dpy, XC_hand2);
    cursors[KV_CURSOR_TEXT]     = XCreateFontCursor(dpy, XC_xterm);
    cursors[KV_CURSOR_RESIZE_H] = XCreateFontCursor(dpy, XC_sb_h_double_arrow);
    cursors[KV_CURSOR_RESIZE_V] = XCreateFontCursor(dpy, XC_sb_v_double_arrow);

    gc = XCreateGC(dpy, win, 0, NULL);
    XMapRaised(dpy, win);
    XFlush(dpy);

    read_scale();
    pxw = w;
    pxh = h;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    alive = 1;
    return 1;
}

void kvp_close(void) {
    alive = 0;
    if (!dpy) return;
    if (gc) { XFreeGC(dpy, gc); gc = 0; }
    if (win) { XDestroyWindow(dpy, win); win = 0; }
    XCloseDisplay(dpy);
    dpy = NULL;
    free(clipboard_own);
    clipboard_own = NULL;
}

int64_t kvp_alive(void) { return alive; }

static void pump(void) {
    XEvent ev;
    while (dpy && XPending(dpy)) {
        XNextEvent(dpy, &ev);
        translate(&ev);
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

void kvp_wait(int64_t ms) {
    if (qhead != qtail || !dpy) return;
    XFlush(dpy);
    if (XPending(dpy)) { pump(); return; }
    int fd = ConnectionNumber(dpy);
    fd_set r;
    FD_ZERO(&r);
    FD_SET(fd, &r);
    struct timeval tv;
    struct timeval *pt = NULL;
    if (ms >= 0) {
        tv.tv_sec = ms / 1000;
        tv.tv_usec = (ms % 1000) * 1000;
        pt = &tv;
    }
    select(fd + 1, &r, NULL, NULL, pt);
    pump();
}

void kvp_wake(void) {
    if (!dpy) return;
    XClientMessageEvent e;
    memset(&e, 0, sizeof e);
    e.type = ClientMessage;
    e.window = win;
    e.message_type = a_wake;
    e.format = 32;
    XSendEvent(dpy, win, False, 0, (XEvent *)&e);
    XFlush(dpy);
}

void kvp_present(const uint32_t *fb, int64_t w, int64_t h) {
    if (!dpy || !win || !fb || w < 1 || h < 1) return;
    XImage *img = XCreateImage(dpy, vis, (unsigned)depth, ZPixmap, 0,
                               (char *)(void *)fb, (unsigned)w, (unsigned)h,
                               32, (int)(w * 4));
    if (!img) return;
    img->byte_order = LSBFirst;      /* Xlib converts for a big-endian server */
    XPutImage(dpy, win, gc, img, 0, 0, 0, 0, (unsigned)w, (unsigned)h);
    /* The buffer belongs to the caller: hand the image an empty one before
     * destroying it, or XDestroyImage would free the framebuffer. */
    img->data = NULL;
    XDestroyImage(img);
    XFlush(dpy);
}

int64_t kvp_width(void)  { return pxw; }
int64_t kvp_height(void) { return pxh; }
double  kvp_scale(void)  { return scale; }

void kvp_set_title(const char *t) {
    if (!dpy || !win) return;
    const char *s = t ? t : "keal-view";
    XStoreName(dpy, win, s);
    Atom net_name = XInternAtom(dpy, "_NET_WM_NAME", False);
    XChangeProperty(dpy, win, net_name, a_utf8, 8, PropModeReplace,
                    (const unsigned char *)s, (int)strlen(s));
}

void kvp_set_cursor(int64_t shape) {
    if (!dpy || !win) return;
    if (shape < 0 || shape > 4) shape = 0;
    XDefineCursor(dpy, win, cursors[shape]);
}

/* X11 has no title bar of its own — the window manager draws it. This sets
 * the hint GTK-based managers read, and does nothing anywhere else, which is
 * the honest amount of control an X11 client has over its own decorations. */
void kvp_set_dark(int64_t dark) {
    if (!dpy || !win) return;
    Atom v = XInternAtom(dpy, "_GTK_THEME_VARIANT", False);
    const char *s = dark ? "dark" : "light";
    XChangeProperty(dpy, win, v, a_utf8, 8, PropModeReplace,
                    (const unsigned char *)s, (int)strlen(s));
}

int64_t kvp_window_id(void) { return (int64_t)win; }

double kvp_now_ms(void) {
    struct timespec n;
    clock_gettime(CLOCK_MONOTONIC, &n);
    return (double)(n.tv_sec - t0.tv_sec) * 1000.0
         + (double)(n.tv_nsec - t0.tv_nsec) / 1.0e6;
}

char *kvp_clipboard_get(void) {
    char *out = NULL;
    if (clipboard_own) {
        out = (char *)malloc(strlen(clipboard_own) + 1);
        if (out) strcpy(out, clipboard_own);
        return out;
    }
    if (dpy && win) {
        XConvertSelection(dpy, a_clipboard, a_utf8, a_kvsel, win, CurrentTime);
        XFlush(dpy);
        /* Wait for the answer, but not for ever: an owner that never replies
         * must not take the interface with it. */
        for (int tries = 0; tries < 200 && !out; tries++) {
            XEvent ev;
            while (XPending(dpy)) {
                XNextEvent(dpy, &ev);
                if (ev.type == SelectionNotify && ev.xselection.property != None) {
                    Atom actual;
                    int fmt;
                    unsigned long n, rest;
                    unsigned char *data = NULL;
                    if (XGetWindowProperty(dpy, win, a_kvsel, 0, 65536, True,
                                           AnyPropertyType, &actual, &fmt, &n,
                                           &rest, &data) == Success && data) {
                        out = (char *)malloc(n + 1);
                        if (out) { memcpy(out, data, n); out[n] = 0; }
                        XFree(data);
                    }
                    break;
                }
                translate(&ev);
            }
            if (!out) usleep(1000);
        }
    }
    if (!out) { out = (char *)malloc(1); if (out) out[0] = 0; }
    return out;
}

void kvp_clipboard_set(const char *s) {
    if (!dpy || !win || !s) return;
    free(clipboard_own);
    clipboard_own = (char *)malloc(strlen(s) + 1);
    if (clipboard_own) strcpy(clipboard_own, s);
    XSetSelectionOwner(dpy, a_clipboard, win, CurrentTime);
    XFlush(dpy);
}

char *kvp_font_path(int64_t which) {
    static const char *sans[] = {
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/noto/NotoSans-Regular.ttf", NULL };
    static const char *bold[] = {
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", NULL };
    static const char *mono[] = {
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
        "/usr/share/fonts/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMono.ttf", NULL };
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
