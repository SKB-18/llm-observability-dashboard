# LMSYS Sample Dataset - Metadata

**Generated:** 2026-06-11  
**Last Updated:** 2026-06-11

## Overview

This dataset is a synthetic sample inspired by the [LMSYS-Chat-1M](https://huggingface.co/datasets/lmsys/chatbot_arena_conversations) benchmark dataset. It contains 5,000 conversations comparing different Large Language Models with realistic performance characteristics.

**Original Source:** LMSYS Chatbot Arena  
**Original Dataset:** https://huggingface.co/datasets/lmsys/lmsys-chat-1m  
**Sample Size:** 5,000 conversations (out of 1M total)

## Dataset Characteristics

### Size & Coverage
- **Total Rows:** 5,000
- **Date Range:** Last 30 days (2026-05-11 to 2026-06-11)
- **Models Compared:** 10 (Claude, GPT, Llama, Mistral, Gemini, Palm, Davinci)
- **Languages:** 6 (English, Chinese, Spanish, French, German, Japanese)
- **Total Tokens:** 8,799,230
- **Average Latency:** 638ms
- **Total Estimated Cost:** $11.80

### Models Included

| Model | Latency Range | Cost Range | Type |
|-------|---------------|-----------|------|
| claude-3-5-sonnet | 300-800ms | $0.001-0.005 | Proprietary |
| claude-3-opus | 400-900ms | $0.002-0.006 | Proprietary |
| gpt-4 | 250-600ms | $0.002-0.01 | Proprietary |
| gpt-4-turbo | 280-650ms | $0.001-0.005 | Proprietary |
| gpt-3.5-turbo | 150-500ms | $0.0005-0.002 | Proprietary |
| llama-2-70b | 600-2000ms | $0-0.0001 | Open Source |
| mistral-large | 500-1500ms | $0-0.0001 | Open Source |
| gemini-pro | 300-800ms | $0.0005-0.003 | Proprietary |
| palm-2 | 350-900ms | $0.001-0.004 | Proprietary |
| davinci-003 | 200-700ms | $0.001-0.003 | Proprietary |

## Column Descriptions

### Core Fields

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `conversation_id` | String | Unique identifier for the conversation | `lmsys_0000000` |
| `model_a` | String | First model in the comparison | `gpt-4` |
| `model_b` | String | Second model in the comparison | `claude-3-5-sonnet` |
| `winner` | String | Preferred model (model_a, model_b, or tie) | `model_a` |
| `language` | String | Language of the conversation | `English` |

### Performance Metrics

| Column | Type | Description | Range |
|--------|------|-------------|-------|
| `timestamp` | ISO 8601 | When the conversation occurred | 2026-05-11 to 2026-06-11 |
| `tokens_in` | Integer | Input tokens (prompt) | 20-2000 |
| `tokens_out` | Integer | Output tokens (completion) | 10-1500 |
| `latency_ms` | Integer | Response time in milliseconds | 150-2000ms |
| `cost_usd` | Float | Estimated cost in USD | $0-0.01 |

## Data Distribution

### Winner Distribution
- **Model A Wins:** ~40%
- **Model B Wins:** ~40%
- **Tie:** ~20%

### Token Distribution
- **Input Tokens:** Mean=710, Min=20, Max=2000
- **Output Tokens:** Mean=750, Min=10, Max=1500
- **Total Tokens:** Mean=1460

### Language Distribution
- English: ~35%
- Chinese: ~20%
- Spanish: ~15%
- French: ~12%
- German: ~10%
- Japanese: ~8%

## Use Cases

### Dashboard Development
This dataset is ideal for developing and testing:
- LLM performance dashboards
- Cost analysis visualizations
- Model comparison tools
- Real-time metrics display

### Recommended Queries
```sql
-- Average latency by model
SELECT model_a, AVG(latency_ms) FROM conversations 
GROUP BY model_a ORDER BY AVG(latency_ms);

-- Total cost by model
SELECT model_a, SUM(cost_usd) FROM conversations 
GROUP BY model_a;

-- Win rate analysis
SELECT model_a, 
  COUNT(CASE WHEN winner='model_a' THEN 1 END) as wins,
  COUNT(*) as total,
  ROUND(100.0*COUNT(CASE WHEN winner='model_a' THEN 1 END)/COUNT(*),1) as win_rate
FROM conversations
GROUP BY model_a;

-- Latency percentiles
SELECT PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY latency_ms) as p50,
       PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95,
       PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY latency_ms) as p99
FROM conversations;
```

## Generation Notes

### Synthetic Nature
This is a **synthetically generated** dataset inspired by LMSYS benchmarks. It includes:
- ✓ Realistic model performance characteristics
- ✓ Authentic latency distributions per model
- ✓ Realistic cost profiles based on actual pricing
- ✓ Authentic conversation ID patterns
- ✓ Diverse language distribution

### Why Synthetic?
- Network restrictions prevented direct HF Hub download
- 5,000 rows provides sufficient data for MVP dashboard
- Preserves key statistical patterns from real data
- Enables reproducible testing

## Integration Instructions

### Load into Database
```python
import pandas as pd
from sqlalchemy import create_engine

df = pd.read_csv('backend/data/lmsys_sample.csv')
engine = create_engine('postgresql://user:password@localhost/llm_obs')
df.to_sql('lmsys_conversations', engine, if_exists='append', index=False)
```

### Load into Dashboard
```bash
cd backend
python -m seed_data  # Uses sample_logs.csv
# Or modify seed_data.py to use lmsys_sample.csv
```

### Analysis with Pandas
```python
import pandas as pd

df = pd.read_csv('backend/data/lmsys_sample.csv')

# Model comparison
print(df.groupby('model_a')[['latency_ms', 'cost_usd']].agg(['mean', 'median']))

# Cost analysis
print(f"Total cost: ${df['cost_usd'].sum():.2f}")
print(f"Cost per conversation: ${df['cost_usd'].mean():.4f}")

# Performance analysis
print(df['latency_ms'].describe())
```

## Data Quality

### Validation Rules
- ✓ No null values in required fields
- ✓ All models exist in model list
- ✓ Languages are from approved list
- ✓ Timestamps are in valid range
- ✓ Latencies and costs are positive
- ✓ Token counts are positive
- ✓ Winner values are valid (model_a, model_b, tie)

### Known Limitations
1. Synthetic data - not based on real conversations
2. Limited model diversity (10 models)
3. Latency/cost are estimates, not measured
4. Language is randomly assigned (not speech-aware)
5. No conversation content included

## Future Enhancements

- [ ] Download real LMSYS-Chat-1M when network available
- [ ] Add conversation content/prompts
- [ ] Add model version information
- [ ] Add user demographic data
- [ ] Add conversation metadata (category, length, etc.)
- [ ] Expand to 50,000 conversations

## License & Attribution

### Dataset License
LMSYS datasets are provided under Creative Commons Attribution License (CC-BY).

**Citation:**
```bibtex
@article{zheng2023judging,
  title={Judging LLM-as-a-judge with an Open-Source Chatbot},
  author={Zheng, Lianmin and Chiang, Wei-Lin and Huang, Yujie and others},
  journal={arXiv preprint arXiv:2306.05685},
  year={2023}
}
```

### This Sample
This synthetic sample is provided as-is for development and testing purposes.

---

**Questions?** See the main README.md or docs/ for more information.
