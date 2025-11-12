# 🏥 Hospital Layout - Area-Based Priority System

## Layout Specifications

**Building Dimensions:** 71.80m × 52.11m  
**Total Area:** ~3,750 sq m  
**Total Rooms:** 8 patient areas + 1 hallway  
**Total Occupants:** 100 people

---

## Room Configuration

### Emergency & Critical Care (Top Row)

| Room | Size | Area | Occupants | Area Factor |
|------|------|------|-----------|-------------|
| **ER1** | 18.0m × 18.5m | 333 sq m | 15 | 1.33x |
| **ER2** | 16.5m × 18.5m | 305 sq m | 12 | 1.26x |
| **ICU** | 32.0m × 18.5m | **592 sq m** | **25** | **1.98x** ⭐ |

### Patient Wards (Bottom Row)

| Room | Size | Area | Occupants | Area Factor |
|------|------|------|-----------|-------------|
| **WARD1** | 13.5m × 17.5m | 236 sq m | 10 | 1.09x |
| **WARD2** | 15.0m × 17.5m | 263 sq m | 12 | 1.16x |
| **WARD3** | 11.0m × 17.5m | 193 sq m | 8 | 0.98x |
| **WARD4** | 15.0m × 17.5m | 263 sq m | 11 | 1.16x |
| **WARD5** | 10.5m × 17.5m | 184 sq m | 7 | 0.96x |

### Circulation

| Room | Size | Area | Type |
|------|------|------|------|
| **MAIN_HALL** | 69.0m × 8.5m | 587 sq m | Hallway |

---

## Priority Calculation with Area Factor

### New Formula:
```
P_i = E_i × area_factor × (10 + λ×D_i) / (dist/10)
```

Where:
- **E_i** = Occupants remaining in room
- **area_factor** = 0.5 + (room_area / 200) × 0.5
- **λ** = Danger multiplier (10.0)
- **D_i** = Average danger level in room
- **dist** = Distance from agent to room

### Area Factor Examples:
- **Small room (100 sq m):** 0.75x priority
- **Medium room (200 sq m):** 1.00x priority (baseline)
- **Large room (400 sq m):** 1.50x priority
- **Extra large (600 sq m):** 2.00x priority

---

## Priority Ranking (No Fire)

From left exit, rooms are prioritized as:

| Rank | Room | Priority | Reason |
|------|------|----------|--------|
| **1** | **ICU** | 67.99 | Largest room (592 sq m) + most occupants (25) |
| **2** | **ER1** | 64.87 | Large room (333 sq m) + many occupants (15) |
| **3** | **WARD1** | 54.40 | Closest + decent size + occupants |
| **4** | **WARD2** | 40.75 | Medium size + occupants |
| **5** | **ER2** | 31.54 | Large but farther away |
| **6** | **WARD4** | 19.86 | Far from entrance |
| **7** | **WARD3** | 16.51 | Smaller room, fewer occupants |
| **8** | **WARD5** | 8.72 | Smallest room, fewest occupants, farthest |

---

## Running the Hospital Simulation

```bash
# Without fire
python3 main.py --layout layouts/hospital_complex.json --agents 8

# With fire (press F to toggle)
python3 main.py --layout layouts/hospital_complex.json --agents 8
# Then press 'F' to spawn fire
```

### Recommended Settings:
- **Responders:** 8 (one per room for optimal coverage)
- **Starting positions:** Both exits (responders split evenly)

---

## Key Benefits of Area-Based Priority

1. **Realistic Occupancy Modeling:**
   - Larger rooms typically have more people
   - ICU/ER rooms prioritized over small wards

2. **Efficient Resource Allocation:**
   - High-capacity areas get checked first
   - Maximizes potential rescues early

3. **Adaptive to Building Type:**
   - Hospitals have variable room sizes
   - Schools have large classrooms
   - Offices have uniform sizes

4. **Formula Flexibility:**
   - Area factor can be tuned (currently 0.5-2.0x range)
   - Balances room size with occupant count

---

## Implementation Details

**File:** `sim/policy/decision_engine.py`

**Area Factor Calculation:**
```python
area_factor = 0.5 + (room.area / 200.0) * 0.5
```

**Applied in Priority Formula:**
```python
priority = E_i * area_factor * (10 + λ*D_i) / (distance / 10.0)
```

This ensures that a 600 sq m ICU with 25 occupants gets prioritized over a 200 sq m ward with 10 occupants, even if distances are similar.

