import React, { useEffect, useMemo, useRef, useState } from 'react';
import { SafeAreaView, View, Text, Pressable, FlatList, Vibration, TextInput, Alert } from 'react-native';
import { NavigationContainer, ParamListBase, useFocusEffect } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

// ---- Minimal design system ----
const Card: React.FC<{children: React.ReactNode, onPress?: ()=>void, style?: any}> = ({children, onPress, style}) => (
  <Pressable onPress={onPress} style={({pressed})=>[{
    backgroundColor:'#0b1020', borderRadius:20, padding:16, marginVertical:8,
    borderWidth:1, borderColor:'#243', shadowColor:'#000', shadowOpacity:0.2, shadowRadius:8,
    transform:[{scale: pressed?0.98:1}],
  }, style]}>
    <Text style={{color:'#dfe8ff', fontSize:16}}>{children}</Text>
  </Pressable>
)

const Button: React.FC<{title:string, onPress:()=>void, variant?:'primary'|'ghost'}> = ({title,onPress,variant='primary'}) => (
  <Pressable onPress={onPress} style={({pressed})=> [{
    backgroundColor: variant==='primary' ? '#5b8cff' : 'transparent',
    borderWidth: variant==='primary'?0:1, borderColor:'#38507a',
    paddingVertical:12, paddingHorizontal:16, borderRadius:14, alignItems:'center', marginVertical:6,
    opacity: pressed?0.85:1
  }]}>
    <Text style={{color: variant==='primary' ? '#071225' : '#dfe8ff', fontWeight:'700'}}>{title}</Text>
  </Pressable>
)

const Screen: React.FC<{title:string, children:React.ReactNode, right?:React.ReactNode}> = ({title, children, right}) => (
  <SafeAreaView style={{flex:1, backgroundColor:'#060a17'}}>
    <View style={{paddingHorizontal:16, paddingTop:4, paddingBottom:6, flexDirection:'row', justifyContent:'space-between', alignItems:'center'}}>
      <Text style={{color:'#dfe8ff', fontSize:22, fontWeight:'800'}}>{title}</Text>
      {right}
    </View>
    <View style={{paddingHorizontal:16, flex:1}}>
      {children}
    </View>
  </SafeAreaView>
)

// ---- Simple store (no external deps) ----
// In-memory store with AsyncStorage shim (optional). You can swap for Zustand easily.
const mem: any = { data: null };
const load = async ()=>{
  try{ const raw = await (global as any).AsyncStorage?.getItem('mindgym_v1'); if(raw) mem.data = JSON.parse(raw);}catch{}
}
const save = async ()=>{
  try{ await (global as any).AsyncStorage?.setItem('mindgym_v1', JSON.stringify(mem.data)); }catch{}
}

export type StatKey = 'stroop'|'nback'|'memory';
export type Stats = {
  streak: number;
  lastPlayedISO: string | null;
  totals: Record<StatKey, { sessions:number; best:number; avg:number }>;
}

const todayKey = ()=> new Date().toDateString();

const initStats = (): Stats => ({
  streak: 0,
  lastPlayedISO: null,
  totals: {
    stroop:{sessions:0,best:0,avg:0},
    nback:{sessions:0,best:0,avg:0},
    memory:{sessions:0,best:0,avg:0},
  }
})

// naive event bus
const listeners: Function[] = [];
const notify = ()=> listeners.forEach(fn=>fn());

const useStats = ()=>{
  const [, force] = useState(0);
  useEffect(()=>{ const l = ()=>force(x=>x+1); listeners.push(l); return ()=>{ const i = listeners.indexOf(l); if(i>=0) listeners.splice(i,1);} },[]);
  if(!mem.data) mem.data = initStats();
  return {
    stats: mem.data as Stats,
    updateGame: async (key:StatKey, score:number)=>{
      const t = mem.data.totals[key];
      t.sessions += 1;
      t.best = Math.max(t.best, score);
      t.avg = Math.round(((t.avg*(t.sessions-1))+score)/t.sessions);
      // streak logic
      const last = mem.data.lastPlayedISO ? new Date(mem.data.lastPlayedISO) : null;
      const d = new Date();
      const lastKey = last?.toDateString();
      const nowKey = d.toDateString();
      if(!last){ mem.data.streak = 1; }
      else if(lastKey===nowKey){ /* same day: do nothing */ }
      else {
        const diff = Math.round((Number(d)-Number(last))/86400000);
        mem.data.streak = diff===1 ? mem.data.streak+1 : 1;
      }
      mem.data.lastPlayedISO = new Date().toISOString();
      notify();
      await save();
    }
  }
}

// ---- Home ----
const HomeScreen = ({navigation}: any)=>{
  const {stats} = useStats();
  return (
    <Screen title="MindGym 🧠">
      <View style={{backgroundColor:'#0b1020', padding:16, borderRadius:20, borderColor:'#243', borderWidth:1, marginBottom:12}}>
        <Text style={{color:'#8fb0ff'}}>Daily streak</Text>
        <Text style={{color:'#dfe8ff', fontSize:36, fontWeight:'900'}}>{stats.streak}🔥</Text>
        <Text style={{color:'#9fb3d9'}}>Keep your streak by completing any game each day.</Text>
      </View>

      <Text style={{color:'#9fb3d9', marginBottom:8}}>Daily Workout</Text>
      <Card onPress={()=>navigation.navigate('Stroop')}>
        🔤 Stroop Focus Test — speed & inhibition
      </Card>
      <Card onPress={()=>navigation.navigate('NBack')}>
        🔁 N‑Back (1‑Back) — working memory
      </Card>
      <Card onPress={()=>navigation.navigate('Stats')}>
        📊 Stats & Progress
      </Card>

      <View style={{marginTop:16}}>
        <Text style={{color:'#9fb3d9'}}>Tips</Text>
        <Text style={{color:'#6e88b7', marginTop:4}}>• Aim for 2–3 short sessions daily.\n• Difficulty adapts as you score higher.\n• Take breaks – quality over grind.</Text>
      </View>
    </Screen>
  )
}

// ---- Stroop Test ----
const COLORS = [
  { name:'RED', hex:'#ff5b5b'},
  { name:'GREEN', hex:'#5bff88'},
  { name:'BLUE', hex:'#5b8cff'},
  { name:'YELLOW', hex:'#ffd95b'},
]

type StroopItem = { word:string; ink:string; isMatch:boolean };

const mkStroop = (difficulty:number): StroopItem=>{
  const w = COLORS[Math.floor(Math.random()*COLORS.length)];
  const c = COLORS[Math.floor(Math.random()*COLORS.length)];
  const forceMatch = Math.random() < Math.min(0.2 + difficulty*0.1, 0.8);
  const ink = forceMatch ? w.hex : c.hex;
  const isMatch = forceMatch ? true : (ink===w.hex);
  return { word: w.name, ink, isMatch };
}

const StroopScreen = ({navigation}: any)=>{
  const {updateGame} = useStats();
  const [difficulty, setDifficulty] = useState(1); // 1..5
  const [round, setRound] = useState(0);
  const [score, setScore] = useState(0);
  const [item, setItem] = useState<StroopItem| null>(null);
  const [timeLeft, setTimeLeft] = useState(45);

  useEffect(()=>{ let t = setInterval(()=> setTimeLeft(x=> x>0? x-1:0), 1000); return ()=>clearInterval(t); },[]);
  useEffect(()=>{ if(timeLeft===0){ onEnd(); } },[timeLeft]);

  const next = ()=>{
    const it = mkStroop(difficulty);
    setItem(it); setRound(r=>r+1);
  }
  useEffect(()=>{ next(); },[]);

  const answer = (isMatch:boolean)=>{
    if(!item) return;
    if(item.isMatch===isMatch){ setScore(s=>s+1); Vibration.vibrate(10);} else { Vibration.vibrate(80); }
    if((round+1)%6===0) setDifficulty(d=> Math.min(5, d+1));
    next();
  }

  const onEnd = async ()=>{
    await updateGame('stroop', score);
    Alert.alert('Session complete', `Score: ${score}`, [{text:'OK', onPress:()=>navigation.replace('Results', {game:'Stroop', score})}]);
  }

  return (
    <Screen title="Stroop Focus">
      <View style={{alignItems:'center', marginVertical:8}}>
        <Text style={{color:'#9fb3d9'}}>Time left</Text>
        <Text style={{color: timeLeft<10? '#ff8f8f': '#dfe8ff', fontSize:32, fontWeight:'900'}}>{timeLeft}s</Text>
      </View>
      <View style={{backgroundColor:'#0b1020', padding:24, borderRadius:20, borderWidth:1, borderColor:'#243', alignItems:'center'}}>
        <Text style={{color:'#6e88b7'}}>Round {round+1}</Text>
        <Text style={{color:item? item.ink : '#dfe8ff', fontSize:48, fontWeight:'900', letterSpacing:1}}>{item?.word ?? ''}</Text>
        <Text style={{color:'#9fb3d9', marginTop:8}}>Does ink color match the word?</Text>
        <View style={{flexDirection:'row', gap:12, marginTop:14}}>
          <Button title="YES" onPress={()=>answer(true)} />
          <Button title="NO" onPress={()=>answer(false)} variant='ghost' />
        </View>
      </View>
      <View style={{alignItems:'center', marginTop:16}}>
        <Text style={{color:'#9fb3d9'}}>Score</Text>
        <Text style={{color:'#dfe8ff', fontSize:28, fontWeight:'800'}}>{score}</Text>
      </View>
      <Button title="End Session" onPress={onEnd} variant='ghost' />
    </Screen>
  )
}

// ---- N‑Back (1‑Back) ----
const letters = 'ABCDEFGH'.split('');

type NBackItem = { char:string };

const NBackScreen = ({navigation}: any)=>{
  const {updateGame} = useStats();
  const [difficulty, setDifficulty] = useState(1); // controls speed
  const [sequence, setSequence] = useState<NBackItem[]>([]);
  const [index, setIndex] = useState(0);
  const [hits, setHits] = useState(0);
  const [miss, setMiss] = useState(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const speedMs = useMemo(()=> Math.max(1400 - difficulty*150, 650), [difficulty]);

  const pushNext = ()=>{
    setSequence(seq=> [...seq, {char: letters[Math.floor(Math.random()*letters.length)]}]);
  }

  useEffect(()=>{ pushNext(); },[]);

  useEffect(()=>{
    timerRef.current && clearInterval(timerRef.current as any);
    timerRef.current = setInterval(()=>{
      setIndex(i=> i+1);
      setSequence(seq=> seq.length<50 ? [...seq, {char: letters[Math.floor(Math.random()*letters.length)]}] : seq);
    }, speedMs);
    return ()=>{ timerRef.current && clearInterval(timerRef.current as any); }
  }, [speedMs]);

  useEffect(()=>{
    if(index>0 && index%10===0) setDifficulty(d=> Math.min(7, d+1));
    if(index>=40){ // end
      const score = Math.max(0, hits*2 - miss);
      updateGame('nback', score).then(()=>{
        Alert.alert('Session complete', `Score: ${score}`, [{text:'OK', onPress:()=>navigation.replace('Results', {game:'N‑Back', score})}]);
      })
    }
  },[index])

  const current = sequence[index]?.char ?? '';
  const prev = sequence[index-1]?.char ?? '';

  const respond = (match:boolean)=>{
    const isMatch = current && prev && current===prev;
    if(match===isMatch){ setHits(h=>h+1); Vibration.vibrate(10);} else { setMiss(m=>m+1); Vibration.vibrate(60);} 
    setIndex(i=>i+1);
    setSequence(seq=> seq.length<50 ? [...seq, {char: letters[Math.floor(Math.random()*letters.length)]}] : seq);
  }

  return (
    <Screen title="1‑Back Memory">
      <View style={{alignItems:'center', marginVertical:12}}>
        <Text style={{color:'#6e88b7'}}>Difficulty</Text>
        <Text style={{color:'#dfe8ff', fontSize:28, fontWeight:'900'}}>{difficulty}</Text>
      </View>
      <View style={{alignItems:'center', justifyContent:'center', backgroundColor:'#0b1020', padding:24, borderRadius:20, borderWidth:1, borderColor:'#243', height:180}}>
        <Text style={{color:'#9fb3d9'}}>Current</Text>
        <Text style={{color:'#dfe8ff', fontSize:64, fontWeight:'900', letterSpacing:2}}>{current}</Text>
      </View>
      <View style={{flexDirection:'row', gap:12, marginTop:16}}>
        <Button title="MATCH" onPress={()=>respond(true)} />
        <Button title="DIFFERENT" onPress={()=>respond(false)} variant='ghost' />
      </View>
      <View style={{flexDirection:'row', justifyContent:'space-between', marginTop:16}}>
        <View>
          <Text style={{color:'#6e88b7'}}>Hits</Text>
          <Text style={{color:'#dfe8ff', fontSize:24, fontWeight:'800'}}>{hits}</Text>
        </View>
        <View>
          <Text style={{color:'#6e88b7'}}>Miss</Text>
          <Text style={{color:'#dfe8ff', fontSize:24, fontWeight:'800'}}>{miss}</Text>
        </View>
      </View>
    </Screen>
  )
}

// ---- Results & Stats ----
const ResultsScreen = ({route, navigation}: any)=>{
  const {game, score} = route.params;
  return (
    <Screen title="Great work!">
      <View style={{backgroundColor:'#0b1020', padding:24, borderRadius:20, borderWidth:1, borderColor:'#243', alignItems:'center'}}>
        <Text style={{color:'#9fb3d9'}}>Completed</Text>
        <Text style={{color:'#dfe8ff', fontSize:28, fontWeight:'900'}}>{game}</Text>
        <Text style={{color:'#6e88b7', marginTop:8}}>Score</Text>
        <Text style={{color:'#dfe8ff', fontSize:36, fontWeight:'900'}}>{score}</Text>
      </View>
      <Button title="Back to Home" onPress={()=>navigation.replace('Home')} />
      <Button title="Play Again" onPress={()=>navigation.goBack()} variant='ghost' />
    </Screen>
  )
}

const StatsScreen = ()=>{
  const {stats} = useStats();
  const items = Object.entries(stats.totals) as [StatKey, {sessions:number;best:number;avg:number}][];
  return (
    <Screen title="Your Stats">
      <View style={{backgroundColor:'#0b1020', padding:16, borderRadius:20, borderWidth:1, borderColor:'#243', marginBottom:12}}>
        <Text style={{color:'#9fb3d9'}}>Streak</Text>
        <Text style={{color:'#dfe8ff', fontSize:32, fontWeight:'900'}}>{stats.streak} days</Text>
        <Text style={{color:'#6e88b7'}}>Last played: {stats.lastPlayedISO ? new Date(stats.lastPlayedISO).toLocaleString() : '—'}</Text>
      </View>
      {items.map(([key, v])=> (
        <View key={key} style={{backgroundColor:'#0b1020', padding:16, borderRadius:18, borderWidth:1, borderColor:'#243', marginBottom:10}}>
          <Text style={{color:'#dfe8ff', fontSize:18, fontWeight:'800'}}>{key.toUpperCase()}</Text>
          <Text style={{color:'#6e88b7'}}>Sessions: {v.sessions}</Text>
          <Text style={{color:'#6e88b7'}}>Best: {v.best}</Text>
          <Text style={{color:'#6e88b7'}}>Average: {v.avg}</Text>
        </View>
      ))}
    </Screen>
  )
}

// ---- Root Nav ----
const Stack = createNativeStackNavigator();

export default function App(){
  useEffect(()=>{ load(); },[]);
  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown:false }}>
        <Stack.Screen name="Home" component={HomeScreen} />
        <Stack.Screen name="Stroop" component={StroopScreen} />
        <Stack.Screen name="NBack" component={NBackScreen} />
        <Stack.Screen name="Results" component={ResultsScreen} />
        <Stack.Screen name="Stats" component={StatsScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  )
}

// ---- Expo compatibility note ----
// This single file prototype avoids third‑party state libs and uses React Navigation only.
// To persist stats between app launches, install AsyncStorage and add this to global:
// import AsyncStorage from '@react-native-async-storage/async-storage';
// (global as any).AsyncStorage = AsyncStorage;
// That’s it. Enjoy!
