# 📊 PRIORITY INDEX FORMULA

## Current Implementation

### Formula:
```
P_i(t) = A_i(t) × (E_i(t) + λ × D_i(t))
```

### Variables:
- **A_i(t)**: Accessibility
  - `1.0` if room is accessible (path exists)
  - `0.0` if room is blocked/inaccessible
  
- **E_i(t)**: Expected evacuees
  - Number of evacuees remaining in room
  - Example: 2 people = 2.0
  
- **D_i(t)**: Average danger level
  - Range: [0, 1]
  - Average of all cell danger levels (d_c) in the room
  - Example: 0.00 (safe), 0.20 (warm), 0.50 (dangerous), 1.00 (burning)
  
- **λ (lambda)**: Danger weight
  - Value: 50.0
  - Amplifies the effect of danger on priority

### Priority Calculation Examples:

**Safe Room (No Fire):**
- E_i = 2, D_i = 0.00
- P = 1 × (2 + 50×0.00) = **2.00**

**Slightly Warm Room:**
- E_i = 2, D_i = 0.05
- P = 1 × (2 + 50×0.05) = **4.50** ← Shows granularity!

**Room with Some Fire:**
- E_i = 2, D_i = 0.20
- P = 1 × (2 + 50×0.20) = **12.00**

**Dangerous Room:**
- E_i = 2, D_i = 0.50
- P = 1 × (2 + 50×0.50) = **27.00**

**Fully Burning Room:**
- E_i = 2, D_i = 1.00
- P = 1 × (2 + 50×1.00) = **52.00** ← HIGHEST priority!

### Key Behaviors:

1. **Fire rooms get MUCH higher priority**
   - Small increase in D_i (0.00 → 0.20) causes P to jump from 2.00 → 12.00 (6x increase!)
   
2. **Granular values**
   - Priority changes smoothly as danger increases
   - Not rounded to integers
   - Displayed with 2 decimal places: `P = 12.34`

3. **Zero priority conditions**
   - Room is cleared AND no evacuees: P = 0.00
   - Room is inaccessible (A_i = 0): P = 0.00

### Comparison with Other Rooms:

If we have 6 rooms:
```
O1: E=2, D=0.20 → P = 12.00 ← Fire room, HIGHEST!
O2: E=1, D=0.00 → P = 1.00
O3: E=1, D=0.00 → P = 1.00
O4: E=1, D=0.05 → P = 3.50  ← Slightly warmer
O5: E=2, D=0.00 → P = 2.00
O6: E=1, D=0.00 → P = 1.00
```

**Agent will prioritize: O1 (12.00) first!**

### Display:
- Shows on office rooms only
- Format: "P = X.XX"
- Updates every frame as danger changes
- Blue badge with white background

---

## Implementation Location:
- **File**: `sim/policy/decision_engine.py`
- **Function**: `calculate_priority_index(room_id, agent_position)`
- **Line**: ~93

---

## Speed Controls:
- **J**: Decrease speed (1x, 2x, 3x, 4x, 5x)
- **L**: Increase speed
- **Range**: 1x to 5x (integer only)
- **NO FREEZING GUARANTEED!**

