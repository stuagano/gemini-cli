# 🔍 Scout: Duplicate Code Detection

## 📊 Detection Summary

**Duplication Health Score:** {{health_score}}/100 {{health_badge}}  
**Duplicates in PR:** {{pr_duplicates}}  
**High Similarity (>90%):** {{high_similarity_count}}  
**Total Project Duplicates:** {{total_duplicates}}

{{#if new_duplicates_introduced}}
🚨 **DUPLICATE ALERT**: This PR introduces new code duplication that should be addressed.
{{else if existing_duplicates_in_pr}}
ℹ️ **Info**: Existing duplicates detected in modified areas.
{{else}}
✅ **Great!** No duplicate code detected in this PR.
{{/if}}

---

## 🎯 Analysis Results

{{#if duplicates_found}}
### 📋 Detected Duplicates

{{#each duplicates}}
#### {{similarity_badge}} {{function_name}} ({{similarity_percentage}}% similar)

**Original:** `{{original_file}}:{{original_line_start}}-{{original_line_end}}`  
**Duplicate:** `{{duplicate_file}}:{{duplicate_line_start}}-{{duplicate_line_end}}`

{{#if in_pr_changes}}
🔄 **In PR Changes** - This duplication is part of the current changes
{{else}}
📍 **Existing** - This duplication already exists in the codebase
{{/if}}

{{#if code_preview}}
**Code Preview:**
```{{language}}
{{code_preview}}
```
{{/if}}

**Refactoring Suggestion:**
{{refactoring_suggestion}}

---
{{/each}}

### 📈 Duplication Patterns

{{#if common_patterns}}
**Most Common Duplicate Patterns:**
{{#each common_patterns}}
- **{{pattern_name}}**: {{count}} instances
  - {{description}}
  - *Refactoring opportunity: {{refactoring_hint}}*
{{/each}}
{{/if}}

{{#if problematic_files}}
**Files with Most Duplicates:**
{{#each problematic_files}}
- `{{file_path}}`: {{duplicate_count}} duplicates
{{/each}}
{{/if}}

{{else}}
### ✅ No Duplicates in Changes

{{#if total_duplicates}}
While no duplicates were found in your changes, the project has {{total_duplicates}} existing duplicates that could benefit from refactoring.
{{else}}
Excellent! Your codebase maintains good DRY (Don't Repeat Yourself) principles.
{{/if}}
{{/if}}

## 🛠️ Refactoring Suggestions

{{#if refactoring_opportunities}}
{{#each refactoring_opportunities}}
### {{priority_icon}} {{title}}

**Impact:** {{impact}}  
**Effort:** {{effort}}  
**Files Affected:** {{file_count}}

{{description}}

**Example Implementation:**
```{{language}}
{{example_code}}
```

**Benefits:**
{{#each benefits}}
- {{this}}
{{/each}}

---
{{/each}}
{{else}}
No specific refactoring opportunities identified at this time.
{{/if}}

## 📊 Project Health Metrics

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| **Duplication Ratio** | {{duplication_ratio}}% | <5% | {{duplication_status}} |
| **Largest Duplicate** | {{largest_duplicate_lines}} lines | <20 lines | {{largest_duplicate_status}} |
| **Duplicate Clusters** | {{duplicate_clusters}} | <3 | {{clusters_status}} |
| **Code Reuse Score** | {{reuse_score}}/100 | >80 | {{reuse_status}} |

{{#if health_trends}}
**Trend Analysis:**
{{#each health_trends}}
- {{period}}: {{change}} {{trend_icon}}
{{/each}}
{{/if}}

## 🎯 Recommendations

{{#if new_duplicates_introduced}}
### 🔴 Immediate Actions Required
- **Extract Common Functionality**: Move duplicate code to shared utilities or base classes
- **Review PR Changes**: Consider whether the duplication is necessary
- **Update Tests**: Ensure shared code is properly tested

### 💡 Refactoring Strategies
1. **Create Utility Functions**: Extract common logic into helper functions
2. **Use Inheritance**: Create base classes for shared behavior
3. **Implement Mixins**: Use composition for cross-cutting concerns
4. **Configuration-Driven**: Replace similar code with configuration parameters

{{else if existing_duplicates_in_pr}}
### 🟡 Optional Improvements
- Consider refactoring existing duplicates while working in this area
- Look for opportunities to consolidate similar patterns
- Update related code to use any new shared utilities

{{else}}
### ✅ Keep Up the Good Work!
- Continue following DRY principles
- Watch for duplication in future changes
- Consider regular duplicate detection scans
{{/if}}

## 🔧 Scout Features in Action

{{#if scout_insights}}
**Scout Analysis Insights:**
{{#each scout_insights}}
- **{{feature}}**: {{description}}
  - *Result*: {{result}}
{{/each}}
{{/if}}

**Scout Capabilities:**
- 🔍 **Real-time Detection**: Identifies duplicates as you code
- 📊 **Similarity Analysis**: Advanced algorithms detect even partial duplicates
- 🛠️ **Refactoring Guidance**: Provides specific suggestions for improvement
- 📈 **Trend Tracking**: Monitors duplication health over time
- ⚡ **Performance Impact**: Prevents code bloat and maintenance overhead

{{#if scout_config}}
**Current Scout Configuration:**
- Similarity Threshold: {{scout_config.similarity_threshold}}
- Minimum Lines: {{scout_config.min_lines}}
- Excluded Patterns: {{scout_config.excluded_patterns}}
{{/if}}

---

## 📝 Action Items

{{#if action_items}}
{{#each action_items}}
### {{priority_icon}} {{priority}} Priority
{{#each items}}
- [ ] {{this}}
{{/each}}
{{/each}}
{{else}}
- [x] Duplicate detection completed
- [x] No action items required
{{/if}}

---

*🔍 Scout duplicate prevention powered by Gemini Enterprise Architect*  
*Keeping your codebase DRY and maintainable*

{{#if show_footer_links}}
**Learn More:**
- [DRY Principles Guide]({{links.dry_principles}})
- [Refactoring Patterns]({{links.refactoring}})
- [Code Quality Metrics]({{links.metrics}})
- [Scout Documentation]({{links.scout_docs}})
{{/if}}