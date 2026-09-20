// libs/stb/vendor/stb_impl.c
// Implementation compilation unit for stb_truetype with C ABI export wrappers
#define STB_TRUETYPE_IMPLEMENTATION
#include "stb_truetype.h"

#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>

// ============================================================================
// C ABI Wrappers for Kale FFI
// ============================================================================

typedef struct {
    stbtt_fontinfo info;
    unsigned char* data;
} KaleFont;

KaleFont* kale_font_init_from_memory(unsigned char* data, int64_t data_len) {
    if (!data) return NULL;
    KaleFont* font = (KaleFont*)malloc(sizeof(KaleFont));
    if (!font) return NULL;
    font->data = data;
    if (!stbtt_InitFont(&font->info, data, 0)) {
        free(font);
        return NULL;
    }
    return font;
}

KaleFont* kale_font_init_from_file(const char* filepath) {
    FILE* f = fopen(filepath, "rb");
    if (!f) return NULL;
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);

    unsigned char* buffer = (unsigned char*)malloc(size);
    if (!buffer) {
        fclose(f);
        return NULL;
    }
    fread(buffer, 1, size, f);
    fclose(f);

    KaleFont* font = kale_font_init_from_memory(buffer, (int64_t)size);
    if (!font) {
        free(buffer);
        return NULL;
    }
    return font;
}

void kale_font_free(KaleFont* font) {
    if (font) {
        if (font->data) free(font->data);
        free(font);
    }
}

float kale_font_scale_for_pixel_height(KaleFont* font, float pixels) {
    if (!font) return 0.0f;
    return stbtt_ScaleForPixelHeight(&font->info, pixels);
}

void kale_font_get_vmetrics(KaleFont* font, int64_t* ascent, int64_t* descent, int64_t* line_gap) {
    if (!font) return;
    int a = 0, d = 0, g = 0;
    stbtt_GetFontVMetrics(&font->info, &a, &d, &g);
    if (ascent) *ascent = (int64_t)a;
    if (descent) *descent = (int64_t)d;
    if (line_gap) *line_gap = (int64_t)g;
}

int64_t kale_font_find_glyph_index(KaleFont* font, int64_t unicode_codepoint) {
    if (!font) return 0;
    return (int64_t)stbtt_FindGlyphIndex(&font->info, (int)unicode_codepoint);
}

void kale_font_get_hmetrics(KaleFont* font, int64_t glyph_index, int64_t* advance_width, int64_t* left_side_bearing) {
    if (!font) return;
    int adv = 0, lsb = 0;
    stbtt_GetGlyphHMetrics(&font->info, (int)glyph_index, &adv, &lsb);
    if (advance_width) *advance_width = (int64_t)adv;
    if (left_side_bearing) *left_side_bearing = (int64_t)lsb;
}

int64_t kale_font_get_kern_advance(KaleFont* font, int64_t glyph1, int64_t glyph2) {
    if (!font) return 0;
    return (int64_t)stbtt_GetGlyphKernAdvance(&font->info, (int)glyph1, (int)glyph2);
}

unsigned char* kale_font_render_glyph_bitmap(KaleFont* font, int64_t glyph_index, float scale, int64_t* width, int64_t* height, int64_t* xoff, int64_t* yoff) {
    if (!font) return NULL;
    int w = 0, h = 0, xo = 0, yo = 0;
    unsigned char* bmp = stbtt_GetGlyphBitmap(&font->info, scale, scale, (int)glyph_index, &w, &h, &xo, &yo);
    if (width) *width = (int64_t)w;
    if (height) *height = (int64_t)h;
    if (xoff) *xoff = (int64_t)xo;
    if (yoff) *yoff = (int64_t)yo;
    return bmp;
}

void kale_font_free_bitmap(unsigned char* bitmap) {
    if (bitmap) {
        stbtt_FreeBitmap(bitmap, NULL);
    }
}
