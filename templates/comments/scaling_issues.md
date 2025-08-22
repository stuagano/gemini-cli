# 🚀 Killer Demo: Scaling Issue Detection

## 📊 Analysis Summary

**Risk Score:** {{risk_score}}/100  
**Production Ready:** {{production_ready_badge}}  
**Issues Found:** {{total_issues}}  
**Critical Issues:** {{critical_issues}}

{{#if is_high_risk}}
🚨 **HIGH RISK ALERT**: This code has significant scaling issues that could cause production problems.
{{/if}}

{{#if production_ready}}
✅ **Production Ready**: Code meets scaling requirements for production deployment.
{{else}}
❌ **Not Production Ready**: Critical scaling issues must be addressed before deployment.
{{/if}}

---

## 🔍 Detected Issues

{{#if scaling_issues}}
{{#each scaling_issues}}
### {{severity_emoji}} {{type_display}} - {{severity_display}}

**File:** `{{file_path}}:{{line_number}}`  
{{#if function_name}}**Function:** `{{function_name}}`{{/if}}

**Issue:** {{description}}

**Impact at Scale:**
{{#each estimated_impact_at_scale}}
- **{{@key}}**: {{this}}
{{/each}}

**Recommendation:** {{fix_recommendation}}

{{#if code_snippet}}
```{{file_extension}}
{{code_snippet}}
```
{{/if}}

**Confidence:** {{confidence_percentage}}%

---
{{/each}}
{{else}}
✅ **Excellent!** No scaling issues detected in this PR.

Your code appears to be well-optimized for production scaling. Great job following performance best practices!
{{/if}}

## 🎯 Scaling Impact Assessment

{{#each impact_categories}}
### {{icon}} {{category_name}}
{{description}}

{{#if recommendations}}
**Recommendations:**
{{#each recommendations}}
- {{this}}
{{/each}}
{{/if}}
{{/each}}

## 📈 Performance Projections

{{#if performance_profile}}
| Metric | Current | 1K users | 10K users | 100K users |
|--------|---------|----------|-----------|-------------|
| **Response Time** | {{performance_profile.current_time}} | {{performance_profile.projected_1k}} | {{performance_profile.projected_10k}} | {{performance_profile.projected_100k}} |
| **Memory Usage** | {{performance_profile.current_memory}} | {{performance_profile.projected_memory_1k}} | {{performance_profile.projected_memory_10k}} | {{performance_profile.projected_memory_100k}} |
| **Database Queries** | {{performance_profile.db_queries}} | {{performance_profile.projected_queries_1k}} | {{performance_profile.projected_queries_10k}} | {{performance_profile.projected_queries_100k}} |

{{#if performance_profile.bottlenecks}}
**Potential Bottlenecks:**
{{#each performance_profile.bottlenecks}}
- {{this}}
{{/each}}
{{/if}}
{{/if}}

## 🛠️ Quick Fixes

{{#if quick_fixes}}
{{#each quick_fixes}}
### {{priority_icon}} {{title}}
{{description}}

```{{language}}
{{code_example}}
```

**Estimated Impact:** {{impact}}  
**Effort:** {{effort}}
{{/each}}
{{else}}
No immediate quick fixes available. Consider the recommendations above for long-term improvements.
{{/if}}

---

## 📋 Action Items

{{#if critical_issues}}
### 🔴 Critical - Must Fix Before Merge
{{#each critical_actions}}
- [ ] {{this}}
{{/each}}
{{/if}}

{{#if high_priority_issues}}
### 🟡 High Priority - Recommended
{{#each high_priority_actions}}
- [ ] {{this}}
{{/each}}
{{/if}}

{{#if medium_priority_issues}}
### 🟦 Medium Priority - Consider
{{#each medium_priority_actions}}
- [ ] {{this}}
{{/each}}
{{/if}}

---

*🚀 Killer Demo powered by Gemini Enterprise Architect*  
*Preventing production scaling issues before they happen*

{{#if show_footer_links}}
**Learn More:**
- [Scaling Best Practices]({{links.best_practices}})
- [Performance Optimization Guide]({{links.optimization}})
- [Production Readiness Checklist]({{links.checklist}})
{{/if}}