---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use when building web components, pages, or React Native screens. Generates creative, polished code that avoids generic AI aesthetics.
license: Apache-2.0 — adapted and modified from anthropics/skills (frontend-design); complete terms in LICENSE.txt
---

# Frontend Design

Build distinctive, production-grade interfaces for React (web) and React Native (mobile).

## Design Thinking

Before writing code, understand context and commit to a **bold aesthetic direction**:

- **Purpose**: What problem does this solve? Who uses it?
- **Tone**: Choose an extreme: brutally minimal, maximalist, retro-futuristic, editorial, luxury/refined, art-deco, soft/pastel, brutalist/raw, etc.
- **Constraints**: MUI v5 or shadcn/ui, Framer Motion available, Tailwind (mobile), TypeScript strict
- **Differentiation**: What makes this interface unforgettable?

**CRITICAL**: Choose a clear direction and execute it with precision. Bold maximalism and refined minimalism both work; intentionality is the key.

## Direction record

Before generating any component file, write the direction in at most 6 lines: style, typography, palette, and the reason for each. Start from the existing theme tokens and say where it diverges. If the request already carries a direction (brand or approved prototype), use it and record only the mapping to tokens. With no theme tokens, propose the minimal tokens (colors and fonts).

## Verify in a browser

Open the rendered screen and capture success, empty, error and loading states, each checked against the direction record. A state that cannot be forced is not verified (give the reason); one absent by design is not applicable (give the reason). If the dev server fails, report its error output; the screen counts as not verified. With no browser, say the screen was not seen, list what stayed unverified, and do not declare the screen done. Use only test or local data; captures are never committed. Never install packages on your own.

## Web (React + MUI v5)

### Design Principles

- **Typography**: Use MUI's `sx` prop for custom font-family. Avoid Inter/Roboto for headings — reach for display fonts via Google Fonts.
- **Color**: Use `theme.palette` + custom CSS variables. Dominant accent color with sharp contrast.
- **Motion**: Framer Motion for page transitions and key interactions. `AnimatePresence` for unmounting.
- **Layout**: Break the grid. Asymmetry. Overlap. Negative space OR controlled density.
- **Background**: Gradient meshes, subtle noise texture, layered transparencies.

### Component Structure

```typescript
import { Box, Typography } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';

interface Props {
}

export function ComponentName({ ...props }: Props) {
  return (
    <Box
      component={motion.div}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
      sx={{
        background: theme => `linear-gradient(135deg, ${theme.palette.primary.dark}, ${theme.palette.background.paper})`,
      }}
    >
      {/* … */}
    </Box>
  );
}
```

### TanStack Query Integration

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../utils/api';

export function use<Feature>() {
  return useQuery({
    queryKey: ['<feature>', /* params */],
    queryFn: () => api.get<FeatureType>('/api/v1/<endpoint>/'),
    staleTime: 5 * 60 * 1000,
  });
}

export function useUpdate<Feature>() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: UpdateInput) => api.patch('/api/v1/<endpoint>/', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['<feature>'] }),
  });
}
```

## Mobile (React Native + Expo)

### Design Principles

- Use NativeWind/Tailwind classes for styling
- Prefer `Animated` API or Reanimated 2 for performance
- 44pt minimum tap targets
- Safe area insets on all screens
- Dark/light mode via `useColorScheme`

### Screen Structure

```typescript
import { SafeAreaView, ScrollView, StyleSheet } from 'react-native';
import Animated, { FadeInDown, useSharedValue } from 'react-native-reanimated';

export function <ScreenName>() {
  return (
    <SafeAreaView style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false}>
        <Animated.View entering={FadeInDown.duration(400).springify()}>
          {/* … */}
        </Animated.View>
      </ScrollView>
    </SafeAreaView>
  );
}
```

## Audit before delivering

Score the rendered screen on these 8 signals of generic output. Mark each present or absent, citing the snippet or capture that supports it:

1. Type with one size and weight everywhere, so nothing leads the eye.
2. A single-hue gradient or default accent used as the whole palette.
3. A grid of identical cards with no emphasis or variation.
4. Text or controls under WCAG AA contrast.
5. Interactive elements with no visible focus style.
6. Motion that decorates without explaining a change.
7. Spacing from stock defaults, with no rhythm between related and unrelated groups.
8. Placeholder-quality copy (lorem, "Title", "Click here").

Fix each present signal, then re-check each fixed signal before delivering. When the request requires a present signal, keep it and record the reason.

## What NEVER to Do

- Hardcoded hex colors (use theme tokens)
- `useState` for server data (use TanStack Query)
- Missing TypeScript types (`any`)
- Fixed heights that break on different screen sizes

## Checklist Before Submitting

- [ ] TypeScript compiles: `npx tsc --noEmit`
- [ ] No hardcoded colors — all from theme
- [ ] Responsive: tested at 375px, 768px, 1440px
- [ ] Capture of each state: loading (skeleton or spinner), error (error UI), empty
- [ ] Framer Motion animations have `reduced-motion` fallback
