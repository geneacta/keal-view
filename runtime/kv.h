/* kv.h — the C face of keal-view.
 *
 * Everything in this file that is `static inline` is compiled *into the Keal
 * translation unit*, because `native """..."""` pastes its text there and the
 * whole program is one C file. That is the fact the whole design rests on: a
 * call from Keal to one of these is not a call, it is the instruction it
 * contains. The rasteriser, the font engine and the compositor are therefore
 * written in Keal without paying anything for it.
 *
 * What is *not* inline lives in one of the platform files (kv_cocoa.m,
 * kv_win32.c, kv_x11.c) and is cold by construction: opening a window,
 * pumping the event queue, handing a finished frame to the screen.
 *
 * The pixel format is the same on all three platforms and is not negotiable:
 * a uint32_t holding 0xAARRGGBB, which is what CoreGraphics reads as
 * kCGImageAlphaPremultipliedFirst|kCGBitmapByteOrder32Little, what a Win32
 * BI_RGB DIB reads, and what an X11 32-bit TrueColor visual reads, on every
 * little-endian machine any of the three runs on.
 */
#ifndef KEAL_VIEW_KV_H
#define KEAL_VIEW_KV_H

#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

/* ---------------------------------------------------------------- events */

/* One event, filled by the platform layer and read field by field from Keal.
 * A struct rather than a return value because the text of a key press has to
 * come across as its own `own String`, and a record cannot carry one. */
typedef struct {
    int64_t kind;     /* KV_EV_* below; 0 when the queue is empty        */
    int64_t x, y;     /* pointer position, in pixels, top-left origin    */
    int64_t button;   /* 1 left, 2 right, 3 middle                       */
    int64_t key;      /* KV_KEY_* for the named keys, else 0             */
    int64_t mods;     /* sum of KV_MOD_*                                 */
    int64_t clicks;   /* 1 single, 2 double, 3 triple                    */
    double  dx, dy;   /* scroll delta, in pixels                         */
    char    text[16]; /* UTF-8 of a text-input event, NUL-terminated     */
} KvEv;

#define KV_EV_NONE     0
#define KV_EV_CLOSE    1
#define KV_EV_RESIZE   2
#define KV_EV_MOVE     3
#define KV_EV_DOWN     4
#define KV_EV_UP       5
#define KV_EV_SCROLL   6
#define KV_EV_KEYDOWN  7
#define KV_EV_KEYUP    8
#define KV_EV_TEXT     9
#define KV_EV_FOCUS   10
#define KV_EV_BLUR    11
#define KV_EV_EXPOSE  12

#define KV_MOD_SHIFT   1
#define KV_MOD_CTRL    2
#define KV_MOD_ALT     4
#define KV_MOD_SUPER   8

/* Named keys. Printable characters arrive as KV_EV_TEXT instead, so this list
 * only has to cover what a text field and a menu need. */
#define KV_KEY_LEFT      1
#define KV_KEY_RIGHT     2
#define KV_KEY_UP        3
#define KV_KEY_DOWN      4
#define KV_KEY_ENTER     5
#define KV_KEY_TAB       6
#define KV_KEY_BACKSPACE 7
#define KV_KEY_DELETE    8
#define KV_KEY_ESCAPE    9
#define KV_KEY_HOME     10
#define KV_KEY_END      11
#define KV_KEY_PAGEUP   12
#define KV_KEY_PAGEDOWN 13
#define KV_KEY_SPACE    14

/* Cursor shapes a window may ask for. */
#define KV_CURSOR_ARROW   0
#define KV_CURSOR_HAND    1
#define KV_CURSOR_TEXT    2
#define KV_CURSOR_RESIZE_H 3
#define KV_CURSOR_RESIZE_V 4

/* ------------------------------------------------- the platform boundary */

#ifdef __cplusplus
extern "C" {
#endif

extern KvEv kv_ev;

int64_t kvp_open(const char *title, int64_t w, int64_t h);
void    kvp_close(void);
int64_t kvp_alive(void);
int64_t kvp_poll(void);
void    kvp_wait(int64_t ms);
void    kvp_wake(void);
void    kvp_present(const uint32_t *fb, int64_t w, int64_t h);
int64_t kvp_width(void);
int64_t kvp_height(void);
double  kvp_scale(void);
void    kvp_set_title(const char *t);
void    kvp_set_cursor(int64_t shape);
double  kvp_now_ms(void);
char   *kvp_clipboard_get(void);
void    kvp_clipboard_set(const char *s);
char   *kvp_font_path(int64_t which);
int64_t kvp_window_id(void);
void    kvp_set_dark(int64_t dark);

#ifdef __cplusplus
}
#endif

/* ----------------------------------------------------------- the surface */

/* The framebuffer belongs to this translation unit — the one Keal compiles
 * into — so that every write to it is a plain store the C compiler can see
 * through, and the platform layer only ever reads it once a frame. */
static uint32_t *kv_fb = NULL;
static int64_t   kv_fb_w = 0, kv_fb_h = 0;

static inline int64_t kv_surface(int64_t w, int64_t h) {
    if (w < 1) w = 1;
    if (h < 1) h = 1;
    if (w == kv_fb_w && h == kv_fb_h) return 1;
    uint32_t *n = (uint32_t *)realloc(kv_fb, (size_t)w * (size_t)h * 4);
    if (!n) return 0;
    kv_fb = n; kv_fb_w = w; kv_fb_h = h;
    return 1;
}

static inline int64_t kv_surface_w(void) { return kv_fb_w; }
static inline int64_t kv_surface_h(void) { return kv_fb_h; }

/* A store, bounds-checked. The check costs a predictable branch and buys the
 * property that no Keal program can scribble outside the window — which is
 * the whole reason the rasteriser is allowed to live in Keal at all. */
static inline void kv_set(int64_t x, int64_t y, int64_t argb) {
    if ((uint64_t)x < (uint64_t)kv_fb_w && (uint64_t)y < (uint64_t)kv_fb_h)
        kv_fb[y * kv_fb_w + x] = (uint32_t)argb;
}

static inline int64_t kv_get(int64_t x, int64_t y) {
    if ((uint64_t)x < (uint64_t)kv_fb_w && (uint64_t)y < (uint64_t)kv_fb_h)
        return (int64_t)kv_fb[y * kv_fb_w + x];
    return 0;
}

/* An opaque horizontal run of one colour. Keal calls this once per span
 * rather than once per pixel where the span is already known to be solid and
 * clipped — the one place a memory-filling loop beats an inlined store, and
 * the only drawing primitive that is not Keal's own. */
static inline void kv_span(int64_t x, int64_t y, int64_t n, int64_t argb) {
    if ((uint64_t)y >= (uint64_t)kv_fb_h) return;
    if (x < 0) { n += x; x = 0; }
    if (x + n > kv_fb_w) n = kv_fb_w - x;
    if (n <= 0) return;
    uint32_t *p = kv_fb + y * kv_fb_w + x, c = (uint32_t)argb;
    for (int64_t i = 0; i < n; i++) p[i] = c;
}

static inline void kv_flush(void) {
    kvp_present(kv_fb, kv_fb_w, kv_fb_h);
}

/* -------------------------------------------------------------- the blob */

/* A byte array Keal can read. Keal has no binary file reading and no byte
 * type, so a font file arrives as a pointer and is read a byte at a time —
 * which, inlined, is one load. The size sits in the eight bytes before the
 * data so that a read can be bounds-checked without a second call. */
static inline int64_t kv_blob_new(int64_t size) {
    if (size < 0) return 0;
    unsigned char *m = (unsigned char *)malloc((size_t)size + 8);
    if (!m) return 0;
    memcpy(m, &size, 8);
    return (int64_t)(m + 8);
}

static inline int64_t kv_blob_size(int64_t h) {
    if (!h) return 0;
    int64_t n; memcpy(&n, (unsigned char *)h - 8, 8); return n;
}

static inline int64_t kv_blob_get(int64_t h, int64_t i) {
    if (!h) return -1;
    if ((uint64_t)i >= (uint64_t)kv_blob_size(h)) return -1;
    return (int64_t)((unsigned char *)h)[i];
}

static inline void kv_blob_set(int64_t h, int64_t i, int64_t v) {
    if (h && (uint64_t)i < (uint64_t)kv_blob_size(h))
        ((unsigned char *)h)[i] = (unsigned char)v;
}

static inline void kv_blob_free(int64_t h) {
    if (h) free((unsigned char *)h - 8);
}

/* Reading a file into a blob is the only file access keal-view adds, and it
 * exists because `readFile` answers a String and a font is not text. */
static inline int64_t kv_blob_read(const char *path) {
    FILE *f = fopen(path, "rb");
    if (!f) return 0;
    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return 0; }
    long n = ftell(f);
    if (n < 0) { fclose(f); return 0; }
    rewind(f);
    int64_t h = kv_blob_new((int64_t)n);
    if (!h) { fclose(f); return 0; }
    size_t got = fread((void *)h, 1, (size_t)n, f);
    fclose(f);
    if (got != (size_t)n) { kv_blob_free(h); return 0; }
    return h;
}

/* ------------------------------------------------------- off the screen */

/* Write the surface out as a BMP. This is here for two reasons and neither
 * is convenience: a continuous-integration machine has no display, and a
 * rasteriser is only trustworthy if the frames it produces can be compared
 * against ones checked in. BMP because the format is a header and the rows,
 * bottom up — nothing to compress, nothing to get wrong, and every viewer
 * reads it. */
static inline int64_t kv_save_bmp(const char *path) {
    if (!kv_fb || kv_fb_w < 1 || kv_fb_h < 1) return 0;
    FILE *f = fopen(path, "wb");
    if (!f) return 0;
    int64_t w = kv_fb_w, h = kv_fb_h;
    uint32_t pixels = (uint32_t)(w * h * 4), total = 14 + 108 + pixels;
    unsigned char hdr[14 + 108];
    memset(hdr, 0, sizeof hdr);
    hdr[0] = 'B'; hdr[1] = 'M';
    memcpy(hdr + 2, &total, 4);
    uint32_t off = 14 + 108; memcpy(hdr + 10, &off, 4);
    uint32_t dib = 108; memcpy(hdr + 14, &dib, 4);
    int32_t iw = (int32_t)w, ih = (int32_t)h;
    memcpy(hdr + 18, &iw, 4);
    memcpy(hdr + 22, &ih, 4);            /* positive: rows run bottom-up */
    uint16_t planes = 1, bpp = 32;
    memcpy(hdr + 26, &planes, 2); memcpy(hdr + 28, &bpp, 2);
    uint32_t comp = 3; memcpy(hdr + 30, &comp, 4);   /* BI_BITFIELDS */
    memcpy(hdr + 34, &pixels, 4);
    uint32_t mr = 0x00FF0000u, mg = 0x0000FF00u, mb = 0x000000FFu, ma = 0xFF000000u;
    memcpy(hdr + 54, &mr, 4); memcpy(hdr + 58, &mg, 4);
    memcpy(hdr + 62, &mb, 4); memcpy(hdr + 66, &ma, 4);
    uint32_t sRGB = 0x73524742u; memcpy(hdr + 70, &sRGB, 4);
    fwrite(hdr, 1, sizeof hdr, f);
    for (int64_t y = h - 1; y >= 0; y--) fwrite(kv_fb + y * w, 4, (size_t)w, f);
    fclose(f);
    return 1;
}

/* ------------------------------------------------------- event accessors */

static inline int64_t kv_ev_kind(void)   { return kv_ev.kind; }
static inline int64_t kv_ev_x(void)      { return kv_ev.x; }
static inline int64_t kv_ev_y(void)      { return kv_ev.y; }
static inline int64_t kv_ev_button(void) { return kv_ev.button; }
static inline int64_t kv_ev_key(void)    { return kv_ev.key; }
static inline int64_t kv_ev_mods(void)   { return kv_ev.mods; }
static inline int64_t kv_ev_clicks(void) { return kv_ev.clicks; }
static inline double  kv_ev_dx(void)     { return kv_ev.dx; }
static inline double  kv_ev_dy(void)     { return kv_ev.dy; }
static inline char   *kv_ev_text(void) {
    size_t n = strlen(kv_ev.text) + 1;
    char *s = (char *)malloc(n);
    if (s) memcpy(s, kv_ev.text, n);
    return s;
}

#endif /* KEAL_VIEW_KV_H */
