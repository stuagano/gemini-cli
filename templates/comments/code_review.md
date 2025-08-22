# 🤖 Gemini Enterprise Architect - AI Code Review

## 📊 Review Summary

**Overall Score:** {{overall_score}}/100 {{score_badge}}  
**Issues Found:** {{total_issues}}  
**Critical Issues:** {{critical_issues}}  
**Security Concerns:** {{security_issues}}  
**Suggestions:** {{total_suggestions}}

{{#if is_production_ready}}
✅ **Production Ready**: Code meets quality standards for deployment.
{{else}}
❌ **Not Production Ready**: Issues must be addressed before merging.
{{/if}}

---

## 🔍 Multi-Agent Analysis

{{#each agent_analyses}}
### {{agent_icon}} {{agent_name}} Agent Review

{{#if issues}}
**Issues Found:** {{issues.length}}
{{#each issues}}
#### {{severity_emoji}} {{title}} - {{severity_display}}

{{#if file_location}}
**Location:** `{{file_location.file}}:{{file_location.line}}`
{{/if}}

{{description}}

{{#if code_snippet}}
```{{language}}
{{code_snippet}}
```
{{/if}}

{{#if recommendation}}
**💡 Recommendation:** {{recommendation}}
{{/if}}

{{#if impact}}
**📈 Impact:** {{impact}}
{{/if}}

---
{{/each}}
{{/if}}

{{#if suggestions}}
**Suggestions:** {{suggestions.length}}
{{#each suggestions}}
- {{description}}
  {{#if benefit}}*Benefit: {{benefit}}*{{/if}}
{{/each}}
{{/if}}

{{#if insights}}
**Key Insights:**
{{#each insights}}
- {{this}}
{{/each}}
{{/if}}

---
{{/each}}

## 🎯 Critical Issues Requiring Attention

{{#if critical_issues_list}}
{{#each critical_issues_list}}
### 🚨 {{title}}

**Agent:** {{agent}}  
**Severity:** {{severity}}  
{{#if file_location}}**File:** `{{file_location.file}}:{{file_location.line}}`{{/if}}

{{description}}

**Why This Is Critical:**
{{rationale}}

**How to Fix:**
{{fix_steps}}

{{#if example_fix}}
**Example Solution:**
```{{language}}
{{example_fix}}
```
{{/if}}

**Impact if Not Fixed:**
{{impact_if_ignored}}

---
{{/each}}
{{else}}
✅ **Excellent!** No critical issues found in this code review.
{{/if}}

## 🔒 Security Analysis

{{#if security_analysis}}
**Security Score:** {{security_analysis.score}}/100  
**Vulnerabilities:** {{security_analysis.vulnerabilities}}  
**Security Practices:** {{security_analysis.practices_score}}/100

{{#if security_analysis.issues}}
### 🛡️ Security Issues
{{#each security_analysis.issues}}
#### {{severity_emoji}} {{type}} - {{severity}}

{{description}}

{{#if cwe_reference}}
**CWE Reference:** [{{cwe_reference.id}}]({{cwe_reference.url}}) - {{cwe_reference.name}}
{{/if}}

**Risk Level:** {{risk_level}}  
**Exploitability:** {{exploitability}}

**Mitigation:**
{{mitigation_steps}}

{{#if secure_example}}
**Secure Implementation:**
```{{language}}
{{secure_example}}
```
{{/if}}

---
{{/each}}
{{else}}
✅ No security vulnerabilities detected.
{{/if}}

{{#if security_recommendations}}
### 🔐 Security Recommendations
{{#each security_recommendations}}
- {{this}}
{{/each}}
{{/if}}
{{/if}}

## 📈 Code Quality Metrics

| Metric | Score | Target | Status |
|--------|-------|--------|--------|
| **Maintainability** | {{metrics.maintainability}}/100 | >80 | {{metrics.maintainability_status}} |
| **Complexity** | {{metrics.complexity}} | <10 | {{metrics.complexity_status}} |
| **Test Coverage** | {{metrics.test_coverage}}% | >80% | {{metrics.coverage_status}} |
| **Documentation** | {{metrics.documentation}}/100 | >70 | {{metrics.documentation_status}} |
| **Performance** | {{metrics.performance}}/100 | >80 | {{metrics.performance_status}} |

{{#if metrics.trends}}
**Quality Trends:**
{{#each metrics.trends}}
- {{metric}}: {{change}} {{trend_direction}} ({{period}})
{{/each}}
{{/if}}

## 🧠 Architecture & Design Patterns

{{#if architecture_analysis}}
**Pattern Compliance:** {{architecture_analysis.pattern_score}}/100  
**SOLID Principles:** {{architecture_analysis.solid_score}}/100

{{#if architecture_analysis.patterns_detected}}
### ✅ Good Patterns Detected
{{#each architecture_analysis.patterns_detected}}
- **{{pattern_name}}**: {{description}}
  - *Why it's good*: {{benefits}}
{{/each}}
{{/if}}

{{#if architecture_analysis.anti_patterns}}
### ⚠️ Anti-Patterns to Address
{{#each architecture_analysis.anti_patterns}}
- **{{pattern_name}}**: {{description}}
  - *Why it's problematic*: {{issues}}
  - *How to fix*: {{solution}}
{{/each}}
{{/if}}

{{#if architecture_analysis.design_suggestions}}
### 💡 Design Improvements
{{#each architecture_analysis.design_suggestions}}
- {{suggestion}}
  - *Benefit*: {{benefit}}
  - *Effort*: {{effort}}
{{/each}}
{{/if}}
{{/if}}

## 🧪 Testing Assessment

{{#if testing_analysis}}
**Test Quality Score:** {{testing_analysis.quality_score}}/100  
**Coverage:** {{testing_analysis.coverage}}%  
**Test Types:** {{testing_analysis.test_types}}

{{#if testing_analysis.missing_tests}}
### 🔍 Missing Test Coverage
{{#each testing_analysis.missing_tests}}
- **{{area}}**: {{description}}
  - *Risk*: {{risk}}
  - *Suggested tests*: {{suggested_tests}}
{{/each}}
{{/if}}

{{#if testing_analysis.test_improvements}}
### 🎯 Test Improvements
{{#each testing_analysis.test_improvements}}
- {{improvement}}
  - *Impact*: {{impact}}
{{/each}}
{{/if}}
{{/if}}

## 💡 Intelligent Suggestions

{{#if intelligent_suggestions}}
{{#each intelligent_suggestions}}
### {{category_icon}} {{category}}

{{#each suggestions}}
#### {{title}}
{{description}}

{{#if before_after}}
**Before:**
```{{language}}
{{before_after.before}}
```

**After:**
```{{language}}
{{before_after.after}}
```
{{/if}}

**Benefits:**
{{#each benefits}}
- {{this}}
{{/each}}

**Effort:** {{effort}}  
**Impact:** {{impact}}

---
{{/each}}
{{/each}}
{{/if}}

## 🎯 Prioritized Action Plan

{{#if action_plan}}
### 🔴 Must Fix (Critical)
{{#each action_plan.critical}}
- [ ] {{task}}
  - *Timeline*: {{timeline}}
  - *Owner*: {{owner}}
{{/each}}

### 🟡 Should Fix (High Priority)
{{#each action_plan.high}}
- [ ] {{task}}
  - *Timeline*: {{timeline}}
  - *Impact*: {{impact}}
{{/each}}

### 🟦 Could Fix (Medium Priority)
{{#each action_plan.medium}}
- [ ] {{task}}
  - *Benefit*: {{benefit}}
{{/each}}

### 💡 Nice to Have (Low Priority)
{{#each action_plan.low}}
- [ ] {{task}}
{{/each}}
{{/if}}

## 📚 Learning Opportunities

{{#if learning_opportunities}}
**Knowledge Gaps Identified:**
{{#each learning_opportunities}}
- **{{topic}}**: {{description}}
  - *Resources*: {{resources}}
  - *Application*: {{application}}
{{/each}}
{{/if}}

## 🔄 Continuous Improvement

{{#if improvement_suggestions}}
**Team Process Improvements:**
{{#each improvement_suggestions}}
- {{suggestion}}
  - *Benefit*: {{benefit}}
  - *Implementation*: {{implementation}}
{{/each}}
{{/if}}

---

## 📋 Review Checklist

{{#if review_checklist}}
{{#each review_checklist}}
### {{category}}
{{#each items}}
- [{{#if checked}}x{{else}} {{/if}}] {{item}}
{{/each}}
{{/each}}
{{/if}}

## 🎉 Positive Highlights

{{#if positive_highlights}}
**Great Work On:**
{{#each positive_highlights}}
- {{highlight}}
  - *Why it's good*: {{reason}}
{{/each}}
{{/if}}

---

*🤖 Multi-agent review by Gemini Enterprise Architect*  
*QA • Architect • Developer • Security agents working together*

{{#if show_footer_links}}
**Resources:**
- [Code Review Guidelines]({{links.guidelines}})
- [Security Best Practices]({{links.security}})
- [Architecture Patterns]({{links.architecture}})
- [Testing Strategies]({{links.testing}})
{{/if}}

{{#if feedback_form}}
**Feedback:** [Rate this review]({{feedback_form.url}}) to help improve our AI analysis
{{/if}}