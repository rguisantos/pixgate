// Redirect /usr/share/kicad -> $KICAD_REAL_SHARE for extracted KiCad
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <dirent.h>
#include <stdarg.h>
#include <unistd.h>

static const char PREFIX[] = "/usr/share/kicad/";

static const char *redirect(const char *path) {
    static __thread char buf[4096];
    if (!path) return path;
    if (strncmp(path, PREFIX, sizeof(PREFIX) - 1) == 0) {
        const char *base = getenv("KICAD_REAL_SHARE");
        if (base && base[0]) {
            size_t bl = strlen(base);
            // strip trailing slash from base
            while (bl > 1 && base[bl-1] == '/') bl--;
            if (snprintf(buf, sizeof buf, "%.*s/%s", (int)bl, base, path + sizeof(PREFIX) - 1) < (int)sizeof buf)
                return buf;
        }
    }
    return path;
}

int open(const char *path, int flags, ...) {
    static int (*real)(const char *, int, ...);
    if (!real) real = dlsym(RTLD_NEXT, "open");
    mode_t mode = 0;
    va_list ap; va_start(ap, flags);
    mode = (flags & O_CREAT) ? (mode_t)va_arg(ap, int) : 0;
    va_end(ap);
    return real(redirect(path), flags, mode);
}

int open64(const char *path, int flags, ...) {
    static int (*real)(const char *, int, ...);
    if (!real) real = dlsym(RTLD_NEXT, "open64");
    mode_t mode = 0;
    va_list ap; va_start(ap, flags);
    mode = (flags & O_CREAT) ? (mode_t)va_arg(ap, int) : 0;
    va_end(ap);
    return real(redirect(path), flags, mode);
}

FILE *fopen(const char *path, const char *mode) {
    static FILE *(*real)(const char *, const char *);
    if (!real) real = dlsym(RTLD_NEXT, "fopen");
    return real(redirect(path), mode);
}

FILE *fopen64(const char *path, const char *mode) {
    static FILE *(*real)(const char *, const char *);
    if (!real) real = dlsym(RTLD_NEXT, "fopen64");
    return real(redirect(path), mode);
}

int stat(const char *path, struct stat *st) {
    static int (*real)(const char *, struct stat *);
    if (!real) real = dlsym(RTLD_NEXT, "stat");
    return real(redirect(path), st);
}

int stat64(const char *path, struct stat64 *st) {
    static int (*real)(const char *, struct stat64 *);
    if (!real) real = dlsym(RTLD_NEXT, "stat64");
    return real(redirect(path), st);
}

int lstat(const char *path, struct stat *st) {
    static int (*real)(const char *, struct stat *);
    if (!real) real = dlsym(RTLD_NEXT, "lstat");
    return real(redirect(path), st);
}

int access(const char *path, int mode) {
    static int (*real)(const char *, int);
    if (!real) real = dlsym(RTLD_NEXT, "access");
    return real(redirect(path), mode);
}

DIR *opendir(const char *path) {
    static DIR *(*real)(const char *);
    if (!real) real = dlsym(RTLD_NEXT, "opendir");
    return real(redirect(path));
}
