# MindGym — Cognitive Training App (Prototype)

**Short:** MindGym is a lightweight, mobile-first cognitive training app with short, adaptive workouts designed to improve attention and working memory. This prototype includes Stroop (focus/inhibition) and 1‑Back (working memory) drills, streak tracking, and basic stats.

## What’s included
- `App.tsx` — single-file Expo React Native prototype
- `package.json` — minimal dependencies
- `README.md` — this file
- `TEAM.md` — team members and roles
- `DEMO_SCRIPT.md` — storyboard and voiceover to create a 2–5 minute demo
- `PRESENTATION.md` — short slide deck in markdown

## How to run (Expo)
1. Install Expo CLI:
   ```
   npm i -g expo
   ```

2. Create project and replace `App.tsx`:
   ```
   expo init mindgym --template blank-typescript
   ```
   Replace the generated `App.tsx` with the `App.tsx` in this repo.

3. Install dependencies:
   ```
   npm install @react-navigation/native @react-navigation/native-stack
   npx expo install react-native-screens react-native-safe-area-context
   ```

4. (Optional — persistence)
   ```
   npm install @react-native-async-storage/async-storage
   ```
   Add at top of `App.tsx`:
   ```ts
   import AsyncStorage from '@react-native-async-storage/async-storage';
   (global as any).AsyncStorage = AsyncStorage;
   ```

5. Run:
   ```
   npx expo start
   ```
   Use Expo Go (iOS/Android) or an emulator to run it.

## Project ideas (next steps)
- Add Dual‑N‑Back, Number Span, Simon Grid
- Supabase backend for profiles & leaderboards
- Charts for progress (weekly/monthly)
- Push reminders & session planner
- Accessibility & color-blind friendly modes

## License
MIT — see LICENSE file.
