/* kv_cocoa.m — the macOS backend.
 *
 * One NSWindow, one layer-backed NSView, and a ring of translated events.
 * Nothing here decides what a frame looks like; it opens a window, says what
 * happened to it, and puts a finished buffer of pixels on the screen.
 */
#include "kv.h"

#import <Cocoa/Cocoa.h>
#import <QuartzCore/QuartzCore.h>

KvEv kv_ev;

#define QN 512
static KvEv     q[QN];
static int      qhead = 0, qtail = 0;
static NSWindow *win = nil;
static NSView   *view = nil;
static int       alive = 0;
static double    scale = 1.0;
static int64_t   pxw = 0, pxh = 0;
static CGColorSpaceRef cspace = NULL;

static void push(KvEv e) {
    int n = (qtail + 1) % QN;
    if (n == qhead) return;          /* a full queue drops, it never blocks */
    q[qtail] = e;
    qtail = n;
}

static KvEv blank(int64_t kind) {
    KvEv e;
    memset(&e, 0, sizeof e);
    e.kind = kind;
    return e;
}

/* ------------------------------------------------------------- delegates */

@interface KvView : NSView
@end
@implementation KvView
- (BOOL)acceptsFirstResponder { return YES; }
- (BOOL)acceptsFirstMouse:(NSEvent *)e { (void)e; return YES; }
- (BOOL)wantsUpdateLayer { return YES; }
@end

@interface KvDelegate : NSObject <NSWindowDelegate>
@end
@implementation KvDelegate
- (BOOL)windowShouldClose:(id)sender { (void)sender; push(blank(KV_EV_CLOSE)); return NO; }
- (void)windowDidResize:(NSNotification *)n { (void)n; push(blank(KV_EV_RESIZE)); }
- (void)windowDidChangeBackingProperties:(NSNotification *)n { (void)n; push(blank(KV_EV_RESIZE)); }
- (void)windowDidBecomeKey:(NSNotification *)n { (void)n; push(blank(KV_EV_FOCUS)); }
- (void)windowDidResignKey:(NSNotification *)n { (void)n; push(blank(KV_EV_BLUR)); }
- (void)windowDidExpose:(NSNotification *)n { (void)n; push(blank(KV_EV_EXPOSE)); }
@end

static KvDelegate *del = nil;

/* ------------------------------------------------------------ geometry */

static void measure(void) {
    NSRect b = [view bounds];
    scale = [win backingScaleFactor];
    if (scale < 1.0) scale = 1.0;
    pxw = (int64_t)(b.size.width * scale + 0.5);
    pxh = (int64_t)(b.size.height * scale + 0.5);
    if (pxw < 1) pxw = 1;
    if (pxh < 1) pxh = 1;
}

/* --------------------------------------------------------- translation */

static int64_t mods_of(NSEvent *e) {
    NSEventModifierFlags f = [e modifierFlags];
    int64_t m = 0;
    if (f & NSEventModifierFlagShift)   m += KV_MOD_SHIFT;
    if (f & NSEventModifierFlagControl) m += KV_MOD_CTRL;
    if (f & NSEventModifierFlagOption)  m += KV_MOD_ALT;
    if (f & NSEventModifierFlagCommand) m += KV_MOD_SUPER;
    return m;
}

/* Window coordinates are bottom-left and in points; everything above this
 * line is top-left and in pixels, because that is what a framebuffer is. */
static void locate(NSEvent *e, KvEv *out) {
    NSPoint p = [view convertPoint:[e locationInWindow] fromView:nil];
    NSRect b = [view bounds];
    out->x = (int64_t)(p.x * scale);
    out->y = (int64_t)((b.size.height - p.y) * scale);
}

static int64_t named_key(unsigned short code) {
    switch (code) {
        case 123: return KV_KEY_LEFT;
        case 124: return KV_KEY_RIGHT;
        case 126: return KV_KEY_UP;
        case 125: return KV_KEY_DOWN;
        case 36:  case 76: return KV_KEY_ENTER;
        case 48:  return KV_KEY_TAB;
        case 51:  return KV_KEY_BACKSPACE;
        case 117: return KV_KEY_DELETE;
        case 53:  return KV_KEY_ESCAPE;
        case 115: return KV_KEY_HOME;
        case 119: return KV_KEY_END;
        case 116: return KV_KEY_PAGEUP;
        case 121: return KV_KEY_PAGEDOWN;
        case 49:  return KV_KEY_SPACE;
        default:  return 0;
    }
}

/* True when the event was consumed here and must not reach NSApp. Key presses
 * without Command are swallowed, because an unhandled one makes the system
 * beep and this window has no menu to hand them to. */
static int translate(NSEvent *e) {
    NSEventType t = [e type];
    KvEv ev;
    switch (t) {
        case NSEventTypeLeftMouseDown:
        case NSEventTypeRightMouseDown:
        case NSEventTypeOtherMouseDown:
            ev = blank(KV_EV_DOWN);
            ev.button = (t == NSEventTypeLeftMouseDown) ? 1 : (t == NSEventTypeRightMouseDown) ? 2 : 3;
            ev.clicks = [e clickCount];
            ev.mods = mods_of(e); locate(e, &ev); push(ev);
            return 0;
        case NSEventTypeLeftMouseUp:
        case NSEventTypeRightMouseUp:
        case NSEventTypeOtherMouseUp:
            ev = blank(KV_EV_UP);
            ev.button = (t == NSEventTypeLeftMouseUp) ? 1 : (t == NSEventTypeRightMouseUp) ? 2 : 3;
            ev.mods = mods_of(e); locate(e, &ev); push(ev);
            return 0;
        case NSEventTypeMouseMoved:
        case NSEventTypeLeftMouseDragged:
        case NSEventTypeRightMouseDragged:
        case NSEventTypeOtherMouseDragged:
            ev = blank(KV_EV_MOVE);
            ev.button = (t == NSEventTypeLeftMouseDragged) ? 1
                      : (t == NSEventTypeRightMouseDragged) ? 2
                      : (t == NSEventTypeOtherMouseDragged) ? 3 : 0;
            ev.mods = mods_of(e); locate(e, &ev); push(ev);
            return 0;
        case NSEventTypeScrollWheel: {
            ev = blank(KV_EV_SCROLL);
            double sx = [e scrollingDeltaX], sy = [e scrollingDeltaY];
            if (![e hasPreciseScrollingDeltas]) { sx *= 12.0; sy *= 12.0; }
            ev.dx = sx * scale; ev.dy = sy * scale;
            ev.mods = mods_of(e); locate(e, &ev); push(ev);
            return 0;
        }
        case NSEventTypeKeyDown: {
            int64_t m = mods_of(e);
            ev = blank(KV_EV_KEYDOWN);
            ev.mods = m;
            ev.key = named_key([e keyCode]);
            /* The letter the key would type with nothing held down, so that a
             * shortcut can be told from another one. A key press carries no
             * text otherwise — the text arrives as its own event, and a
             * shortcut suppresses that. */
            NSString *base = [e charactersIgnoringModifiers];
            if ([base length] > 0) {
                unichar c0 = [base characterAtIndex:0];
                if (c0 >= 'A' && c0 <= 'Z') c0 = (unichar)(c0 + 32);
                if (c0 >= 32 && c0 < 127) { ev.text[0] = (char)c0; ev.text[1] = 0; }
            }
            push(ev);
            if (m & KV_MOD_SUPER) return 0;      /* let the menu have it */
            NSString *s = [e characters];
            if ([s length] > 0) {
                unichar c = [s characterAtIndex:0];
                if (c >= 32 && c != 127) {
                    KvEv te = blank(KV_EV_TEXT);
                    te.mods = m;
                    const char *u = [s UTF8String];
                    if (u) { strncpy(te.text, u, sizeof te.text - 1); push(te); }
                }
            }
            return 1;
        }
        case NSEventTypeKeyUp:
            ev = blank(KV_EV_KEYUP);
            ev.mods = mods_of(e);
            ev.key = named_key([e keyCode]);
            push(ev);
            return 1;
        default:
            return 0;
    }
}

/* -------------------------------------------------------------- the API */

int64_t kvp_open(const char *title, int64_t w, int64_t h) {
    @autoreleasepool {
        [NSApplication sharedApplication];
        [NSApp setActivationPolicy:NSApplicationActivationPolicyRegular];

        NSRect r = NSMakeRect(0, 0, (CGFloat)w, (CGFloat)h);
        NSUInteger style = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable
                         | NSWindowStyleMaskMiniaturizable | NSWindowStyleMaskResizable;
        win = [[NSWindow alloc] initWithContentRect:r styleMask:style
                                            backing:NSBackingStoreBuffered defer:NO];
        [win setTitle:[NSString stringWithUTF8String:title ? title : "keal-view"]];
        [win setMinSize:NSMakeSize(240, 160)];
        [win setAcceptsMouseMovedEvents:YES];
        [win center];

        view = [[KvView alloc] initWithFrame:r];
        [view setWantsLayer:YES];
        [[view layer] setContentsGravity:kCAGravityResize];
        [win setContentView:view];
        [win makeFirstResponder:view];

        del = [[KvDelegate alloc] init];
        [win setDelegate:del];

        /* A minimal menu, so that Command-Q quits the way every other Mac
         * application does. A window with no menu bar is a window a user
         * cannot leave. */
        NSMenu *bar = [[NSMenu alloc] init];
        NSMenuItem *appItem = [[NSMenuItem alloc] init];
        [bar addItem:appItem];
        NSMenu *appMenu = [[NSMenu alloc] init];
        NSString *name = [[NSProcessInfo processInfo] processName];
        [appMenu addItemWithTitle:[@"Quit " stringByAppendingString:name]
                           action:@selector(terminate:) keyEquivalent:@"q"];
        [appItem setSubmenu:appMenu];
        [NSApp setMainMenu:bar];

        cspace = CGColorSpaceCreateDeviceRGB();

        [win makeKeyAndOrderFront:nil];
        [NSApp activateIgnoringOtherApps:YES];
        [NSApp finishLaunching];

        measure();
        alive = 1;
        return 1;
    }
}

void kvp_close(void) {
    @autoreleasepool {
        alive = 0;
        if (win) { [win close]; win = nil; view = nil; }
        if (cspace) { CGColorSpaceRelease(cspace); cspace = NULL; }
    }
}

int64_t kvp_alive(void) { return alive; }

int64_t kvp_poll(void) {
    if (qhead == qtail) {
        @autoreleasepool {
            for (;;) {
                NSEvent *e = [NSApp nextEventMatchingMask:NSEventMaskAny
                                                untilDate:[NSDate distantPast]
                                                   inMode:NSDefaultRunLoopMode
                                                  dequeue:YES];
                if (!e) break;
                if (!translate(e)) [NSApp sendEvent:e];
                if (((qtail + 1) % QN) == qhead) break;
            }
        }
    }
    if (qhead == qtail) { kv_ev.kind = KV_EV_NONE; return KV_EV_NONE; }
    kv_ev = q[qhead];
    qhead = (qhead + 1) % QN;
    if (kv_ev.kind == KV_EV_RESIZE) measure();
    return kv_ev.kind;
}

void kvp_wait(int64_t ms) {
    if (qhead != qtail) return;
    @autoreleasepool {
        NSDate *until = ms < 0 ? [NSDate distantFuture]
                               : [NSDate dateWithTimeIntervalSinceNow:(double)ms / 1000.0];
        NSEvent *e = [NSApp nextEventMatchingMask:NSEventMaskAny untilDate:until
                                           inMode:NSDefaultRunLoopMode dequeue:YES];
        if (e && !translate(e)) [NSApp sendEvent:e];
    }
}

void kvp_wake(void) {
    @autoreleasepool {
        NSEvent *e = [NSEvent otherEventWithType:NSEventTypeApplicationDefined
                                        location:NSMakePoint(0, 0) modifierFlags:0
                                       timestamp:0 windowNumber:0 context:nil
                                         subtype:0 data1:0 data2:0];
        [NSApp postEvent:e atStart:NO];
    }
}

void kvp_present(const uint32_t *fb, int64_t w, int64_t h) {
    if (!view || !fb || w < 1 || h < 1) return;
    @autoreleasepool {
        /* The bytes are copied because CoreAnimation composites on its own
         * schedule and the next frame starts writing this buffer the moment
         * this call returns. A four-megabyte copy is the price of not
         * tearing, and it is a fifth of a millisecond. */
        CFDataRef data = CFDataCreate(NULL, (const UInt8 *)fb, (CFIndex)(w * h * 4));
        if (!data) return;
        CGDataProviderRef prov = CGDataProviderCreateWithCFData(data);
        CGImageRef img = CGImageCreate((size_t)w, (size_t)h, 8, 32, (size_t)(w * 4), cspace,
                                       kCGImageAlphaNoneSkipFirst | kCGBitmapByteOrder32Little,
                                       prov, NULL, false, kCGRenderingIntentDefault);
        [CATransaction begin];
        [CATransaction setDisableActions:YES];
        [[view layer] setContentsScale:scale];
        [[view layer] setContents:(__bridge id)img];
        [CATransaction commit];
        CGImageRelease(img);
        CGDataProviderRelease(prov);
        CFRelease(data);
    }
}

/* The system's own number for this window. `screencapture -l <n>` captures
 * exactly it, which is how the pictures in the README are made and how a
 * window can be looked at from outside the process that owns it. */
/* Cocoa repaints the title bar whenever it is told, so there is nothing to
 * arrange in advance. */
void kvp_prefer_dark(int64_t dark) { (void)dark; }

/* The title bar belongs to the system, not to the framebuffer, so a dark
 * application has to say so or it gets a white strip above a black window. */
void kvp_set_dark(int64_t dark) {
    if (!win) return;
    @autoreleasepool {
        [win setAppearance:[NSAppearance appearanceNamed:
            dark ? NSAppearanceNameDarkAqua : NSAppearanceNameAqua]];
    }
}

int64_t kvp_window_id(void) { return win ? (int64_t)[win windowNumber] : 0; }

int64_t kvp_width(void)  { return pxw; }
int64_t kvp_height(void) { return pxh; }
double  kvp_scale(void)  { return scale; }

void kvp_set_title(const char *t) {
    if (!win || !t) return;
    @autoreleasepool { [win setTitle:[NSString stringWithUTF8String:t]]; }
}

void kvp_set_cursor(int64_t shape) {
    @autoreleasepool {
        NSCursor *c;
        switch (shape) {
            case KV_CURSOR_HAND:     c = [NSCursor pointingHandCursor]; break;
            case KV_CURSOR_TEXT:     c = [NSCursor IBeamCursor]; break;
            case KV_CURSOR_RESIZE_H: c = [NSCursor resizeLeftRightCursor]; break;
            case KV_CURSOR_RESIZE_V: c = [NSCursor resizeUpDownCursor]; break;
            default:                 c = [NSCursor arrowCursor]; break;
        }
        [c set];
    }
}

double kvp_now_ms(void) {
    return (double)clock_gettime_nsec_np(CLOCK_MONOTONIC) / 1.0e6;
}

char *kvp_clipboard_get(void) {
    @autoreleasepool {
        NSString *s = [[NSPasteboard generalPasteboard] stringForType:NSPasteboardTypeString];
        const char *u = s ? [s UTF8String] : "";
        if (!u) u = "";
        char *out = (char *)malloc(strlen(u) + 1);
        if (out) strcpy(out, u);
        return out;
    }
}

void kvp_clipboard_set(const char *s) {
    if (!s) return;
    @autoreleasepool {
        NSPasteboard *pb = [NSPasteboard generalPasteboard];
        [pb clearContents];
        [pb setString:[NSString stringWithUTF8String:s] forType:NSPasteboardTypeString];
    }
}

/* 0 sans, 1 sans bold, 2 monospace. The first path that is actually there
 * wins; a machine that has none of them gets an empty string and the caller
 * says so rather than drawing nothing. */
char *kvp_font_path(int64_t which) {
    static const char *sans[] = {
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Geneva.ttf", NULL };
    static const char *bold[] = {
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Geneva.ttf", NULL };
    static const char *mono[] = {
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Supplemental/Courier New.ttf",
        "/System/Library/Fonts/Courier.ttc", NULL };
    const char **list = which == 1 ? bold : which == 2 ? mono : sans;
    for (int i = 0; list[i]; i++) {
        FILE *f = fopen(list[i], "rb");
        if (f) { fclose(f); char *o = (char *)malloc(strlen(list[i]) + 1); if (o) strcpy(o, list[i]); return o; }
    }
    char *o = (char *)malloc(1); if (o) o[0] = 0; return o;
}
