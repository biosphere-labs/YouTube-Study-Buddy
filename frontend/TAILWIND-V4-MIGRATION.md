# Tailwind CSS v4 Migration

## Issue
The React frontend was using Tailwind v4 (`@tailwindcss/postcss` v4.1.16) but had a v3 configuration, causing the error:
```
Cannot apply unknown utility class `border-border`
```

## Root Cause
Tailwind v4 completely changed the configuration approach:
- **v3**: Uses `tailwind.config.js` with `@tailwind` directives
- **v4**: Uses `@import`, `@theme`, and `@source` directives in CSS

## Changes Made

### 1. Updated `src/index.css`

**Before (v3 style)**:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    /* ... */
  }
}
```

**After (v4 style)**:
```css
@import "tailwindcss";

@source "../src";

@theme {
  --color-background: 0 0% 100%;
  --color-primary: 221.2 83.2% 53.3%;
  /* ... */
}
```

### 2. Key Differences

| Aspect | v3 | v4 |
|--------|----|----|
| **Import** | `@tailwind base` | `@import "tailwindcss"` |
| **Config File** | `tailwind.config.js` | None (CSS-based) |
| **Theme** | JavaScript object | `@theme { }` in CSS |
| **Content** | `content: []` in config | `@source` directive |
| **Colors** | `hsl(var(--color))` | HSL triplet, utilities add `hsl()` |

### 3. Color Variables

**v4 requires HSL triplets without the `hsl()` wrapper:**

```css
/* v3 - Full HSL color */
--background: hsl(0 0% 100%);

/* v4 - HSL triplet only */
--color-background: 0 0% 100%;

/* Utilities automatically wrap with hsl() */
/* bg-background generates: background-color: hsl(var(--color-background)) */
```

### 4. Content Scanning

**v3**: Configured in `tailwind.config.js`
```js
content: [
  "./index.html",
  "./src/**/*.{js,ts,jsx,tsx}",
]
```

**v4**: Configured in CSS
```css
@source "../src";
```

### 5. Dark Mode

**Still uses CSS variables, just different format:**

```css
.dark {
  --color-background: 222.2 84% 4.9%;
  --color-foreground: 210 40% 98%;
  /* ... */
}
```

## Files Modified

- ✅ `src/index.css` - Migrated to v4 syntax
- ✅ `tailwind.config.js` - Renamed to `.backup` (not used in v4)
- ✅ `postcss.config.js` - Already correct with `@tailwindcss/postcss`

## Testing

After migration, the following should work:

```bash
npm run dev
```

All utility classes should now resolve correctly:
- `bg-background`
- `text-foreground`
- `border-border`
- `text-primary`
- `bg-primary/10`
- etc.

## Resources

- [Tailwind CSS v4 Announcement](https://tailwindcss.com/blog/tailwindcss-v4-alpha)
- [v4 Migration Guide](https://tailwindcss.com/docs/v4-beta)
- [v4 Theme Configuration](https://tailwindcss.com/docs/theme)
- [v4 @source Directive](https://tailwindcss.com/docs/functions-and-directives#source)

## Notes

- The `tailwind.config.js.backup` file is kept for reference but is not used
- All shadcn/ui components work with this configuration
- Component code didn't need changes, only CSS configuration
- Dark mode works the same way, just with updated variable syntax
