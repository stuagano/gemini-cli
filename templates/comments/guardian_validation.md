# 🛡️ Guardian: Architecture Validation

## 📊 Validation Summary

**Architecture Score:** {{architecture_score}}/100 {{architecture_badge}}  
**Compliance Status:** {{compliance_status}}  
**Pattern Violations:** {{pattern_violations}}  
**Security Compliance:** {{security_compliance_score}}/100

{{#if passes_validation}}
✅ **Architecture Approved**: Changes align with established patterns and standards.
{{else}}
❌ **Architecture Issues**: Violations detected that require attention.
{{/if}}

---

## 🏗️ Architecture Analysis

### 📐 Design Pattern Compliance

{{#if pattern_analysis}}
{{#each pattern_analysis}}
#### {{status_icon}} {{pattern_name}}

**Status:** {{compliance_status}}  
**Score:** {{score}}/100

{{description}}

{{#if violations}}
**Violations:**
{{#each violations}}
- **{{violation_type}}**: {{description}}
  - *File*: `{{file_path}}:{{line_number}}`
  - *Impact*: {{impact}}
  - *Fix*: {{recommended_fix}}
{{/each}}
{{/if}}

{{#if recommendations}}
**Recommendations:**
{{#each recommendations}}
- {{this}}
{{/each}}
{{/if}}

---
{{/each}}
{{else}}
✅ All architectural patterns are properly implemented.
{{/if}}

### 🏛️ SOLID Principles Assessment

| Principle | Score | Status | Notes |
|-----------|-------|--------|-------|
| **Single Responsibility** | {{solid.srp.score}}/100 | {{solid.srp.status}} | {{solid.srp.notes}} |
| **Open/Closed** | {{solid.ocp.score}}/100 | {{solid.ocp.status}} | {{solid.ocp.notes}} |
| **Liskov Substitution** | {{solid.lsp.score}}/100 | {{solid.lsp.status}} | {{solid.lsp.notes}} |
| **Interface Segregation** | {{solid.isp.score}}/100 | {{solid.isp.status}} | {{solid.isp.notes}} |
| **Dependency Inversion** | {{solid.dip.score}}/100 | {{solid.dip.status}} | {{solid.dip.notes}} |

{{#if solid.violations}}
**SOLID Violations:**
{{#each solid.violations}}
- **{{principle}}**: {{description}}
  - *Location*: `{{file_path}}`
  - *Impact*: {{impact}}
  - *Solution*: {{solution}}
{{/each}}
{{/if}}

### 🧱 Layer Architecture Validation

{{#if layer_architecture}}
**Architecture Type:** {{layer_architecture.type}}  
**Layer Count:** {{layer_architecture.layers}}  
**Separation Score:** {{layer_architecture.separation_score}}/100

{{#if layer_architecture.violations}}
**Layer Violations:**
{{#each layer_architecture.violations}}
- **{{violation_type}}**: {{description}}
  - *From*: {{from_layer}} → *To*: {{to_layer}}
  - *File*: `{{file_path}}`
  - *Why it's wrong*: {{rationale}}
  - *Correct approach*: {{correct_approach}}
{{/each}}
{{/if}}

{{#if layer_architecture.dependency_graph}}
**Dependency Flow:**
```
{{layer_architecture.dependency_graph}}
```
{{/if}}
{{/if}}

## 🔒 Security Architecture

{{#if security_architecture}}
**Security Score:** {{security_architecture.score}}/100  
**Threat Model Compliance:** {{security_architecture.threat_model_score}}/100

{{#if security_architecture.issues}}
### 🚨 Security Architecture Issues
{{#each security_architecture.issues}}
#### {{severity_emoji}} {{title}} - {{severity}}

{{description}}

**Threat Category:** {{threat_category}}  
**Risk Level:** {{risk_level}}  
**Attack Vector:** {{attack_vector}}

**Mitigation Strategy:**
{{mitigation_strategy}}

{{#if secure_pattern}}
**Recommended Pattern:**
```{{language}}
{{secure_pattern}}
```
{{/if}}

---
{{/each}}
{{/if}}

{{#if security_architecture.recommendations}}
### 🔐 Security Recommendations
{{#each security_architecture.recommendations}}
- {{recommendation}}
  - *Priority*: {{priority}}
  - *Implementation*: {{implementation_guide}}
{{/each}}
{{/if}}
{{/if}}

## 📊 Data Architecture

{{#if data_architecture}}
**Data Flow Score:** {{data_architecture.flow_score}}/100  
**Schema Compliance:** {{data_architecture.schema_compliance}}/100

{{#if data_architecture.issues}}
### 🗄️ Data Architecture Issues
{{#each data_architecture.issues}}
- **{{issue_type}}**: {{description}}
  - *Impact*: {{impact}}
  - *Solution*: {{solution}}
  - *Files*: {{affected_files}}
{{/each}}
{{/if}}

{{#if data_architecture.patterns}}
### 📈 Data Patterns Analysis
{{#each data_architecture.patterns}}
- **{{pattern_name}}**: {{usage_description}}
  - *Appropriateness*: {{appropriateness_score}}/100
  - *Suggestion*: {{suggestion}}
{{/each}}
{{/if}}
{{/if}}

## 🌐 API Architecture

{{#if api_architecture}}
**API Design Score:** {{api_architecture.design_score}}/100  
**RESTful Compliance:** {{api_architecture.rest_compliance}}/100

{{#if api_architecture.violations}}
### 🔌 API Design Violations
{{#each api_architecture.violations}}
- **{{violation_type}}**: {{description}}
  - *Endpoint*: `{{endpoint}}`
  - *Issue*: {{issue_description}}
  - *Best Practice*: {{best_practice}}
  - *Example Fix*: {{example_fix}}
{{/each}}
{{/if}}

{{#if api_architecture.consistency_issues}}
### 🔄 API Consistency Issues
{{#each api_architecture.consistency_issues}}
- {{issue}}
  - *Recommendation*: {{recommendation}}
{{/each}}
{{/if}}
{{/if}}

## 🧩 Component Architecture

{{#if component_architecture}}
**Component Cohesion:** {{component_architecture.cohesion_score}}/100  
**Coupling Score:** {{component_architecture.coupling_score}}/100 (lower is better)

{{#if component_architecture.issues}}
### 🔧 Component Issues
{{#each component_architecture.issues}}
#### {{type}} - {{severity}}

{{description}}

**Component:** `{{component_name}}`  
**Issue Type:** {{issue_type}}

{{#if metrics}}
**Metrics:**
- Lines of Code: {{metrics.loc}}
- Cyclomatic Complexity: {{metrics.complexity}}
- Afferent Coupling: {{metrics.ca}}
- Efferent Coupling: {{metrics.ce}}
{{/if}}

**Refactoring Suggestion:**
{{refactoring_suggestion}}

---
{{/each}}
{{/if}}
{{/if}}

## 📝 Compliance Checklist

{{#if compliance_checklist}}
{{#each compliance_checklist}}
### {{framework_name}} Compliance

{{#each requirements}}
- [{{#if compliant}}x{{else}} {{/if}}] {{requirement}}
  {{#unless compliant}}
  - *Issue*: {{issue}}
  - *Fix*: {{fix_guidance}}
  {{/unless}}
{{/each}}

**Overall Compliance:** {{compliance_percentage}}%
{{/each}}
{{/if}}

## 🎯 Architecture Recommendations

{{#if architecture_recommendations}}
{{#each architecture_recommendations}}
### {{priority_icon}} {{title}} - {{priority}} Priority

{{description}}

**Benefits:**
{{#each benefits}}
- {{this}}
{{/each}}

**Implementation Steps:**
{{#each implementation_steps}}
1. {{this}}
{{/each}}

**Effort Estimate:** {{effort_estimate}}  
**Impact:** {{impact_rating}}/5

{{#if example_implementation}}
**Example Implementation:**
```{{language}}
{{example_implementation}}
```
{{/if}}

---
{{/each}}
{{/if}}

## 🔍 Technical Debt Analysis

{{#if technical_debt}}
**Total Technical Debt:** {{technical_debt.total_hours}} hours  
**Debt Ratio:** {{technical_debt.ratio}}%  
**Interest Rate:** {{technical_debt.interest_rate}}/10

{{#if technical_debt.hotspots}}
### 🔥 Technical Debt Hotspots
{{#each technical_debt.hotspots}}
- **{{component_name}}**: {{debt_hours}} hours
  - *Type*: {{debt_type}}
  - *Priority*: {{priority}}
  - *Refactoring Strategy*: {{refactoring_strategy}}
{{/each}}
{{/if}}

{{#if technical_debt.recommendations}}
### 💡 Debt Reduction Strategy
{{#each technical_debt.recommendations}}
- {{strategy}}
  - *Timeline*: {{timeline}}
  - *ROI*: {{roi}}
{{/each}}
{{/if}}
{{/if}}

## 📈 Architecture Evolution

{{#if architecture_evolution}}
**Evolution Score:** {{architecture_evolution.score}}/100  
**Future Readiness:** {{architecture_evolution.future_readiness}}/100

{{#if architecture_evolution.evolution_paths}}
### 🛤️ Recommended Evolution Paths
{{#each architecture_evolution.evolution_paths}}
- **{{path_name}}**: {{description}}
  - *Timeline*: {{timeline}}
  - *Benefits*: {{benefits}}
  - *Challenges*: {{challenges}}
{{/each}}
{{/if}}
{{/if}}

---

## 🚨 Critical Actions Required

{{#if critical_actions}}
{{#each critical_actions}}
### {{urgency_icon}} {{title}}

**Urgency:** {{urgency_level}}  
**Impact:** {{impact_level}}

{{description}}

**Immediate Steps:**
{{#each immediate_steps}}
1. {{this}}
{{/each}}

**Owner:** {{responsible_team}}  
**Deadline:** {{deadline}}

---
{{/each}}
{{else}}
✅ No critical architecture issues requiring immediate attention.
{{/if}}

## 📋 Guardian Validation Report

**Validation Run:** {{validation_timestamp}}  
**Guardian Version:** {{guardian_version}}  
**Rules Applied:** {{rules_count}}  
**Files Analyzed:** {{files_analyzed}}

{{#if validation_summary}}
**Summary:**
- ✅ Passed: {{validation_summary.passed}}
- ⚠️ Warnings: {{validation_summary.warnings}}
- ❌ Failed: {{validation_summary.failed}}
- 🔍 Manual Review: {{validation_summary.manual_review}}
{{/if}}

---

*🛡️ Guardian architecture validation powered by Gemini Enterprise Architect*  
*Ensuring architectural integrity and long-term maintainability*

{{#if show_footer_links}}
**Learn More:**
- [Architecture Guidelines]({{links.architecture}})
- [Design Patterns Catalog]({{links.patterns}})
- [Security Architecture]({{links.security}})
- [Guardian Documentation]({{links.guardian}})
{{/if}}

{{#if approval_required}}
---
**🔒 Approval Required**  
This PR requires architecture team approval due to significant structural changes.  
Please request review from: {{approval_team}}
{{/if}}