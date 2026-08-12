# LLM Integration Plan for Travel Planner Agent

## Context

The current agent is entirely rule-based (regex parsing, greedy selection, hard constraints). The user wants to:
1. Allow free-text preference input (richer than structured fields)
2. Use LLM at each node to make intelligent decisions

## Current State

| Node | Current Approach |
|------|------------------|
| `extract_prefs` | Regex parsing for destination, days, budget |
| `retrieve_places` | Hybrid search (BM25 + vector + RRF) |
| `plan_day` | Greedy selection (fit in 9h, max 5 places) |
| `critic` | Hard constraint validation only |
| `should_continue_loop` | Simple day counter |

## Target Architecture

### Node-by-Node LLM Integration

#### 1. `extract_prefs` (User Preferences from Free Text)
**Current:** `_parse_preferences()` uses regex to extract destination, days, people, budget, style.

**LLM Enhancement:**
- Accept any natural language description of travel preferences
- Extract structured preferences AND understand implicit preferences
- Example: "I want to explore Tokyo for 5 days with my wife. We love good food, hate crowds, prefer quiet temples over tourist traps."

**Prompt Strategy:**
```
Extract user preferences from the input. Return structured data plus "implicit_preferences" 
which captures nuance the user didn't explicitly state as categories.
```

**Output:** `UserPreferences` (structured) + `implicit_preferences` (free text for context)

---

#### 2. `retrieve_places` (Unchanged)
This node already uses hybrid search effectively. The query building can be improved to include implicit preferences.

**Minor Change:** `_build_search_query()` should incorporate implicit_preferences as additional context.

---

#### 3. `plan_day` (LLM-Driven Day Planning)
**Current:** `_select_places_for_day()` is greedy — takes places that fit in 9h, max 5.

**LLM Enhancement:**
- Use LLM to select and sequence places for the day
- Consider: geographic clustering, opening hours, theme/coherence
- Create narrative flow (e.g., "Morning: temples, Afternoon: shopping")
- Incorporate user's implicit preferences

**Prompt Strategy:**
```
Given {day_number} of {total_days} and the user's preferences:
{preferences_summary}

Available places for today:
{places_list}

Select and sequence 3-6 places that:
1. Fit within the daily budget ({budget_per_day} yen)
2. Respect opening hours (all places are assumed open 9am-10pm)
3. Are geographically logical (minimize backtracking)
4. Create a coherent theme or narrative for the day

Return the selected places in optimal visiting order with start times.
```

---

#### 4. `critic` (Enhanced Validation)
**Current:** Only validates hard constraints (cost, time, travel).

**LLM Enhancement:**
- Keep hard constraint validation
- Add LLM judgment on quality, variety, pacing
- Check if plan matches user's implicit preferences

**Prompt Strategy:**
```
Review the day's itinerary for a {travel_style} traveler:
{day_plan_details}

Check:
1. Hard constraints: daily_cost <= {budget}, total_hours <= 10
2. Variety: not too many similar places
3. Pace: reasonable number of activities
4. User preferences match: {implicit_preferences}

Return any concerns or suggestions for improvement.
```

---

#### 5. `should_continue_loop` (Continue or Finalize)
**Current:** Simple `current_day < preferences.days`.

**LLM Enhancement:**
- Judge if the overall itinerary is satisfying
- Check thematic balance across days
- Detect if user would want more/less detail

---

## Implementation Files

### New/Modified Files

| File | Change | Description |
|------|--------|-------------|
| `app/agent/nodes.py` | Modify | Replace rule-based nodes with LLM calls |
| `app/agent/llm.py` | **New** | LLM client wrapper with prompt templates |
| `app/models/preferences.py` | Extend | Add `implicit_preferences` field |
| `app/config.py` | Extend | Add LLM config (model, temperature, etc.) |

### Files to Keep As-Is

- `app/retrieval/hybrid.py` — already working
- `app/retrieval/reranker.py` — already working
- `app/constraints/validator.py` — hard constraints still valid

---

## Verification Plan

1. **Unit tests** for new LLM prompts (mock LLM responses)
2. **Manual testing** with varied inputs:
   - Simple: "Tokyo 3 days"
   - Rich: "5 days in Kyoto with my parents, they like gardens and temples, we enjoy good food but hate crowded places"
3. **Constraint validation** still enforced — LLM suggestions must pass hard constraints
4. **API test** via `POST /api/v1/itinerary/generate` with rich preference text

---

## Rollout Order

1. Add LLM client wrapper with prompt templates (`llm.py`)
2. Extend `UserPreferences` model
3. Rewrite `extract_prefs` with LLM
4. Rewrite `plan_day` with LLM
5. Enhance `critic` with LLM judgment
6. Add tests and verify end-to-end
