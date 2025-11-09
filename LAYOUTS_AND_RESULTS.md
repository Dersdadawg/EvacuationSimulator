# 🗺️ AVAILABLE LAYOUTS & RESULTS GUIDE

## 📁 LAYOUT LOCATIONS

### MAIN LAYOUTS (layouts/):
1. **`office_correct_dimensions.json`** ← CURRENT WORKING ONE
   - 6 offices + 2 exits + hallway
   - 17 total occupants (5,3,2,4,1,2)
   - Fire starts in O1 (top-left)

2. **`hospital_complex.json`** ← NEW! COMPLEX!
   - 8 rooms (ER, ICU, Wards) + 1 exit
   - 61 total occupants
   - Large 70m × 50m building

3. **`school_building.json`** ← NEW!
   - 6 classrooms + cafeteria + 2 exits
   - 140 total students!
   - 60m × 40m school

4. **`corporate_tower.json`** ← NEW!
   - 5 offices + 3 conference rooms + 2 stairs
   - 78 total workers
   - 50m × 45m floor

5. **`shopping_mall.json`** ← NEW!
   - 6 stores + food court + 2 exits
   - 70 total shoppers
   - 55m × 35m mall wing

6. **`apartment_complex.json`** ← NEW!
   - 6 apartments + 1 stair exit
   - 15 residents
   - 45m × 30m floor

### BACKUP LAYOUTS (layouts/backup/):
- All original layouts backed up here
- `office_1f.json`, `office_3f.json`, `office_basic.json`

## 🎮 HOW TO RUN DIFFERENT LAYOUTS

```bash
# Office (working, 17 occupants)
python3 main.py --layout layouts/office_correct_dimensions.json --agents 3

# Hospital (61 occupants, COMPLEX!)
python3 main.py --layout layouts/hospital_complex.json --agents 5

# School (140 students!)
python3 main.py --layout layouts/school_building.json --agents 8

# Corporate Tower (78 workers)
python3 main.py --layout layouts/corporate_tower.json --agents 6

# Shopping Mall (70 shoppers)
python3 main.py --layout layouts/shopping_mall.json --agents 4

# Apartments (15 residents)
python3 main.py --layout layouts/apartment_complex.json --agents 2
```

## 📊 WHERE TO FIND RESULTS

### Terminal Output:
- Shows immediately after simulation ends
- Includes SUCCESS RATE with formula
- Per-agent statistics

### Saved Files:
```
outputs/run_YYYYMMDD_HHMMSS/
├── results.csv          ← All metrics (time, rescued, success rate)
├── timeline.csv         ← Every event with timestamps
├── agent_stats.csv      ← Per-agent travel, rescues
├── summary.png          ← Charts and graphs
└── hazard_final.png     ← Final fire spread visualization
```

**Latest run:** Look in `outputs/` folder, most recent timestamp

## 🎨 ROOM COLORS

- 🟢 **PASTEL GREEN** (#A5D6A7): Room fully evacuated (priority=0, evacuees=0)
- 🔵 **LIGHT BLUE** (#90CAF9): Room blocked by fire (priority=0, evacuees>0)  
- ⬜ **TRANSPARENT**: Active room (still has occupants, rescuable)

## ⚙️ CHANGE RESPONDER COUNT

**File:** `params.json` line 12
```json
"agents": {
  "count": 3,  ← Change this number
}
```

**Or command line:**
```bash
--agents 5
```

## 🎮 CONTROLS DURING SIMULATION

- **SPACE**: Pause/Resume (toggle end menu when complete)
- **J**: Slow down (1x-10x)
- **L**: Speed up (1x-10x)
- **ESC**: Quit

## 🔥 FIRE ORIGIN

Automatically selects first office room if "O1" doesn't exist.
Shows in terminal: `[FIRE] Selected ER1 as fire origin`

