# Augment Daily Usage Analytics - SQL Query Guide

This guide provides working SQL examples for analyzing the `augment-daily-usage` dataset in Dremio.

## 📊 Dataset Overview

**Table**: `"@vando.pereira@dremio.com"."augment-daily-usage"`
- **Total Records**: 2,241 usage records
- **Total Users**: 140 unique users
- **Date Range**: May 1, 2025 - June 17, 2025
- **Update Frequency**: Daily usage metrics

## 📋 Schema Structure

| Column | Type | Description |
|--------|------|-------------|
| `"Date"` | Date | Daily usage date (⚠️ **Reserved keyword - must be quoted**) |
| `user_id` | String | User email address |
| `total_active_days` | Integer | Number of active days |
| `has_used_chat` | Boolean | Whether user used chat feature (0/1) |
| `has_used_completions` | Boolean | Whether user used code completions (0/1) |
| `has_used_agent` | Boolean | Whether user used agent feature (0/1) |
| `completions_total` | Integer | Total code completions offered |
| `completions_accepted` | Integer | Number of completions accepted |
| `completions_acceptance_rate_percentage` | Float | Acceptance rate percentage |
| `chat_messages_day` | Integer | Number of chat messages per day |
| `agent_chats_day` | Integer | Number of agent chats per day |

## ✅ Working SQL Queries

### 1. **Basic Data Exploration**

```sql
-- View recent usage data
SELECT * FROM "@vando.pereira@dremio.com"."augment-daily-usage" LIMIT 10

-- Dataset summary statistics
SELECT 
    COUNT(DISTINCT user_id) "total_users",
    COUNT(*) "total_records",
    MAX("Date") "latest_date",
    MIN("Date") "earliest_date"
FROM "@vando.pereira@dremio.com"."augment-daily-usage"
```

### 2. **User Performance Analysis**

```sql
-- Top performers by completion acceptance rate
SELECT 
    user_id, 
    AVG(completions_acceptance_rate_percentage) "avg_acceptance_rate"
FROM "@vando.pereira@dremio.com"."augment-daily-usage" 
WHERE completions_total > 0
GROUP BY user_id 
ORDER BY AVG(completions_acceptance_rate_percentage) DESC 
LIMIT 10

-- Users with highest completion volumes
SELECT 
    user_id,
    SUM(completions_total) "total_completions",
    SUM(completions_accepted) "total_accepted",
    AVG(completions_acceptance_rate_percentage) "avg_acceptance_rate"
FROM "@vando.pereira@dremio.com"."augment-daily-usage"
WHERE completions_total > 0
GROUP BY user_id
ORDER BY SUM(completions_total) DESC
LIMIT 10
```

### 3. **Feature Adoption Analysis**

```sql
-- Feature usage summary
SELECT 
    SUM(has_used_chat) "chat_users",
    SUM(has_used_completions) "completion_users", 
    SUM(has_used_agent) "agent_users",
    COUNT(DISTINCT user_id) "total_users"
FROM "@vando.pereira@dremio.com"."augment-daily-usage"

-- Daily feature usage trends
SELECT 
    "Date",
    COUNT(DISTINCT CASE WHEN has_used_chat = 1 THEN user_id END) "daily_chat_users",
    COUNT(DISTINCT CASE WHEN has_used_completions = 1 THEN user_id END) "daily_completion_users",
    COUNT(DISTINCT CASE WHEN has_used_agent = 1 THEN user_id END) "daily_agent_users"
FROM "@vando.pereira@dremio.com"."augment-daily-usage"
WHERE "Date" >= '2025-06-01'
GROUP BY "Date"
ORDER BY "Date" DESC
LIMIT 10
```

### 4. **Recent Activity Analysis**

```sql
-- Recent user activity (last 2 weeks)
SELECT 
    user_id, 
    "Date", 
    completions_acceptance_rate_percentage,
    completions_total,
    chat_messages_day,
    agent_chats_day
FROM "@vando.pereira@dremio.com"."augment-daily-usage" 
WHERE "Date" >= '2025-06-01' 
ORDER BY "Date" DESC, completions_acceptance_rate_percentage DESC 
LIMIT 20

-- Most active users in recent period
SELECT 
    user_id,
    COUNT(*) "active_days",
    SUM(completions_total) "total_completions",
    SUM(chat_messages_day) "total_chat_messages",
    SUM(agent_chats_day) "total_agent_chats"
FROM "@vando.pereira@dremio.com"."augment-daily-usage"
WHERE "Date" >= '2025-06-01'
GROUP BY user_id
ORDER BY COUNT(*) DESC, SUM(completions_total) DESC
LIMIT 10
```

### 5. **Power User Identification**

```sql
-- Multi-feature power users
SELECT 
    user_id,
    COUNT(*) "active_days",
    AVG(completions_acceptance_rate_percentage) "avg_acceptance_rate",
    SUM(completions_total) "total_completions",
    SUM(chat_messages_day) "total_chat_messages",
    SUM(agent_chats_day) "total_agent_chats"
FROM "@vando.pereira@dremio.com"."augment-daily-usage"
WHERE has_used_chat = 1 AND has_used_completions = 1 AND has_used_agent = 1
GROUP BY user_id
ORDER BY COUNT(*) DESC, SUM(completions_total) DESC
LIMIT 10
```

## ⚠️ Important Dremio SQL Syntax Notes

### **Reserved Keywords**
- **`"Date"`** must be quoted because it's a reserved keyword in Dremio
- **Schema and table names** with special characters must be quoted: `"@vando.pereira@dremio.com"`

### **Correct Syntax Examples**
```sql
-- ✅ Correct
SELECT "Date", user_id FROM "@vando.pereira@dremio.com"."augment-daily-usage"

-- ❌ Wrong
SELECT Date, user_id FROM "@vando.pereira@dremio.com"."augment-daily-usage"
```

### **Column Aliases**
```sql
-- ✅ Correct
SELECT AVG(completions_acceptance_rate_percentage) "avg_rate"

-- ❌ Wrong  
SELECT AVG(completions_acceptance_rate_percentage) as avg_rate
```

### **Multiple Queries**
- **Execute one query at a time** - Dremio doesn't support multiple statements in a single execution
- **Use separate API calls** for different analyses

## 🎯 Key Insights from Sample Data

### **Top Performers** (by acceptance rate):
1. **raghu.gyambavantha@dremio.com**: 45.0% average acceptance rate
2. **alex.dutra@dremio.com**: 43.46% average acceptance rate
3. **soumyaranjan.mishra@dremio.com**: 39.91% average acceptance rate

### **Usage Patterns**:
- **140 unique users** across Dremio organization
- **2,241 daily usage records** spanning 47+ days
- **Mixed feature adoption**: Chat, Completions, and Agent features
- **Varying engagement levels**: From occasional to power users

### **Data Quality**:
- Some records have `NaN` values for acceptance rates (users with no completions)
- Boolean flags (0/1) for feature usage tracking
- Comprehensive daily metrics for all three main features

## 🌐 Using in the Enhanced Dremio Reporting Server

### **Web Interface**: http://localhost:5003/query
- Click on **"Augment Usage Data"** example to load basic query
- Click on **"Recent Usage by User"** for filtered results
- Click on **"Top Performers by Acceptance Rate"** for analytics

### **API Usage**:
```bash
curl -X POST http://localhost:5003/api/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM \"@vando.pereira@dremio.com\".\"augment-daily-usage\" LIMIT 10"}'
```

---

*This dataset provides comprehensive insights into Augment Code usage patterns across the Dremio organization, enabling data-driven decisions for product development and user engagement strategies.*
