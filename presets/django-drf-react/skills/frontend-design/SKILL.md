---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use when building web components, pages, or React Native screens. Generates creative, polished code that avoids generic AI aesthetics.
license: Adapted from Strivex — Complete terms in LICENSE.txt
---

# Frontend Design

Build production-grade, visually distinctive interfaces for React (web) and React Native (mobile).

## Design Thinking

Before writing code, understand context and commit to a **bold aesthetic direction**:

- **Purpose**: What problem does this solve? Who uses it?
- **Tone**: Choose an extreme: brutally minimal, maximalist, retro-futuristic, editorial, luxury/refined, art-deco, soft/pastel, brutalist/raw, etc.
- **Constraints**: MUI v5 or shadcn/ui, Framer Motion available, Tailwind (mobile), TypeScript strict
- **Differentiation**: What makes this interface unforgettable?

**CRITICAL**: Choose a clear conceptual direction and execute with precision. Bold maximalism and refined minimalism both work — the key is intentionality.

## Web (React + MUI v5)

### Design Principles

- **Typography**: Use MUI's `sx` prop for custom font-family. Avoid Inter/Roboto for headings — reach for display fonts via Google Fonts.
- **Color**: Use `theme.palette` + custom CSS variables. Dominant accent color with sharp contrast.
- **Motion**: Framer Motion for page transitions and key interactions. `AnimatePresence` for unmounting.
- **Layout**: Break the grid. Asymmetry. Overlap. Negative space OR controlled density.
- **Background**: Gradient meshes, subtle noise texture, layered transparencies.

### Component Structure

```typescript
// src/components/<Module>/<ComponentName>.tsx
import { Box, Typography } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';

interface Props {
  // TypeScript strict — no `any`
}

export function ComponentName({ ...props }: Props) {
  return (
    <Box
      component={motion.div}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
      sx={{
        // MUI sx — use theme tokens, not hardcoded values
        background: theme => `linear-gradient(135deg, ${theme.palette.primary.dark}, ${theme.palette.background.paper})`,
      }}
    >
      {/* content */}
    </Box>
  );
}
```

### TanStack Query Integration

```typescript
// src/hooks/use<Feature>.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../utils/api';

export function use<Feature>() {
  return useQuery({
    queryKey: ['<feature>', /* params */],
    queryFn: () => api.get<FeatureType>('/api/v1/<endpoint>/'),
    staleTime: 5 * 60 * 1000,  // 5 minutes
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
// src/screens/<ScreenName>.tsx
import { SafeAreaView, ScrollView, StyleSheet } from 'react-native';
import Animated, { FadeInDown, useSharedValue } from 'react-native-reanimated';

export function <ScreenName>() {
  return (
    <SafeAreaView style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false}>
        <Animated.View entering={FadeInDown.duration(400).springify()}>
          {/* content */}
        </Animated.View>
      </ScrollView>
    </SafeAreaView>
  );
}
```

## What NEVER to Do

- Generic AI aesthetics: Inter/Roboto/Arial for ALL text, purple gradients on white, cookie-cutter cards
- Hardcoded hex colors (use theme tokens)
- `useState` for server data (use TanStack Query)
- Missing TypeScript types (`any`)
- Non-accessible color contrast (WCAG AA minimum)
- Fixed heights that break on different screen sizes

## Checklist Before Submitting

- [ ] TypeScript compiles: `npx tsc --noEmit`
- [ ] No hardcoded colors — all from theme
- [ ] Responsive: tested at 375px, 768px, 1440px
- [ ] Loading state handled (skeleton or spinner)
- [ ] Error state handled (error boundary or error UI)
- [ ] Empty state handled
- [ ] Framer Motion animations have `reduced-motion` fallback
