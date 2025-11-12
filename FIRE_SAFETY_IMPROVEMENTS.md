# 🔥 Fire Safety Improvements

## Overview
Made fire less aggressive and added self-preservation logic for responders.

---

## 🚒 Agent Self-Preservation

### New Safety Thresholds:
1. **Danger Level 0.70** → **RETREAT**: Abort mission and escape
   - Agent drops any carried evacuee (safety first!)
   - Clears current target
   - Routes to nearest exit via safe path
   
2. **Danger Level 0.95** → **DEATH**: Agent dies
   - OR if agent enters burning cell

### Pathfinding Changes:
- **Default danger threshold:** 0.8 → **0.6** (more cautious)
- **Multi-stage escape routing:**
  - Try safe path (danger < 0.7) first
  - Then moderate danger (< 0.85)
  - Finally accept any path (emergency)

---

## 🔥 Fire Spread Adjustments

### Slower Fire Growth:
```json
"Q_threshold": 50.0 → 75.0 kW     // Higher ignition threshold (harder to spread)
"fire_growth_rate": 0.0469 → 0.0117  // FAST (α_fast) → MEDIUM (α_med)
```

**Impact:**
- Fire takes **~2x longer** to reach ignition threshold
- Spreads **~60% slower** between cells
- More time for agents to complete rescues

### Fire Growth Rates (NIST/SFPE):
- α_slow = 0.00293 kW/s²
- **α_medium = 0.0117 kW/s²** ← NEW DEFAULT
- α_fast = 0.0469 kW/s² ← OLD DEFAULT
- α_ultra = 0.187 kW/s²

---

## 🎮 Dynamic Fire Toggle

### Press 'F' to Toggle:
- **Fire OFF** → **Fire ON**: Spawns fire in origin room (O1)
- **Fire ON** → **Fire OFF**: Extinguishes all fires

### Features:
- Fire spawns dynamically at current simulation time
- Can test pathfinding first, then add fire
- Fire state persists until toggled again
- Visual indicator in status bar

---

## 📊 Expected Improvements

### Before Changes:
- 100% agent mortality
- 58-71% rescue rate
- All agents die regardless of team size

### After Changes (Expected):
- Agents retreat before dying
- Higher rescue rates
- Some agents survive
- More realistic behavior

---

## 🔧 Configuration

All thresholds are configurable in `params.json`:

```json
"hazard": {
  "enabled": false,  // Fire off by default
  "Q_threshold": 75.0,  // Higher = slower spread
  "fire_growth_rate": 0.0117,  // Medium growth
  "danger_escape_threshold": 0.70,  // Retreat at 70% danger
  "danger_death_threshold": 0.95  // Death at 95% danger
}
```

---

## ⚠️ Agent Behavior Logic

```
danger_level:
  0.00 - 0.69: Normal operations
  0.70 - 0.94: RETREAT MODE (abort & escape)
  0.95 - 1.00: LETHAL (instant death)
  
is_burning: INSTANT DEATH (no matter the danger level)
```

Agents now prioritize their own survival while still attempting maximum rescues!

