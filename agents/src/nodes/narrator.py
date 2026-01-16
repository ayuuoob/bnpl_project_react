"""
Narrator Node - Generates the final structured response.

Transforms raw tool results into the standard output format:
- Answer Summary
- Key Metrics
- Drivers / Why
- Recommended Actions
- Data & Assumptions
"""

from typing import Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ..state import AgentState, ResponseFormat


class NarratorNode:
    """
    Generates a structured, human-readable response.
    
    Takes raw results from tools and creates:
    1. Executive summary
    2. Key metrics with values
    3. Driver analysis
    4. Actionable recommendations
    5. Data source attribution
    """
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        self.llm = llm
        self._narrator_prompt = self._build_narrator_prompt()
    
    def _build_narrator_prompt(self) -> ChatPromptTemplate:
        """Build the narrator prompt for LLM-assisted response generation."""
        return ChatPromptTemplate.from_messages([
            ("system", """You are an analytics narrator for a BNPL business.

Given the raw data results, create a structured executive response.

Format your response EXACTLY as follows:

[Answer Summary]
1-3 lines with the final numbers and conclusion.

[Key Metrics]
- Metric Name: value (time window)
- Include top 3 breakdowns if relevant

[Drivers / Why]
- 2-4 bullet points explaining causation based on data

[Recommended Actions]
For each action include:
- Description
- Impact: High/Medium/Low
- Effort: High/Medium/Low
- Justification grounded in the metrics

[Data & Assumptions]
- Tools used
- Tables queried
- Time range
- Any limitations

Be executive-friendly. Use actual numbers from the data.
Do NOT hallucinate numbers - only use what's in the results."""),
            ("human", """User Question: {question}

Intent: {intent}

Raw Results:
{results}

Generate the structured response:""")
        ])
    
    async def __call__(self, state: AgentState) -> AgentState:
        """Generate the final structured response."""
        state.current_node = "narrator"
        
        # Try LLM-based narration first
        if self.llm:
            response = await self._llm_narrate(state)
        else:
            response = self._template_narrate(state)
        
        state.final_response = response
        return state
    
    async def _llm_narrate(self, state: AgentState) -> str:
        """Use LLM to generate response."""
        try:
            # Format results for LLM
            results_text = self._format_results_for_llm(state)
            
            chain = self._narrator_prompt | self.llm
            response = await chain.ainvoke({
                "question": state.user_query,
                "intent": state.intent,
                "results": results_text,
            })
            
            return response.content
            
        except Exception as e:
            # Fallback to template
            return self._template_narrate(state)
    
    def _format_results_for_llm(self, state: AgentState) -> str:
        """Format raw results for LLM input."""
        lines = []
        
        for i, result in enumerate(state.raw_results, 1):
            result_type = result.get("type", "unknown")
            result_data = result.get("result", "No data")
            
            lines.append(f"--- Result {i} ({result_type}) ---")
            lines.append(str(result_data)[:2000])  # Limit size
            lines.append("")
        
        # Add validation notes
        if state.validation and state.validation.issues:
            lines.append("--- Validation Notes ---")
            for issue in state.validation.issues:
                lines.append(f"- {issue}")
        
        return "\n".join(lines)
    
    def _template_narrate(self, state: AgentState) -> str:
        """Generate response using templates (no LLM)."""
        sections = []
        
        # 1. Answer Summary
        sections.append(self._build_summary(state))
        
        # 2. Key Metrics
        sections.append(self._build_key_metrics(state))
        
        # 3. Drivers / Why
        sections.append(self._build_drivers(state))
        
        # 4. Recommended Actions
        sections.append(self._build_recommendations(state))
        
        # 5. Data & Assumptions
        sections.append(self._build_data_section(state))
        
        return "\n\n".join(sections)
    
    def _build_summary(self, state: AgentState) -> str:
        """Build the answer summary section."""
        lines = ["[Answer Summary]"]
        
        # Extract key info from results
        if state.raw_results:
            primary = state.raw_results[0].get("result", "")
            
            # Try to extract the main metric value
            if "Value:" in str(primary):
                import re
                match = re.search(r'\*\*Value:\s*([^*]+)\*\*', str(primary))
                if match:
                    value = match.group(1).strip()
                    lines.append(f"Based on the analysis, the {state.entities.metrics[0] if state.entities.metrics else 'requested metric'} is **{value}**.")
                else:
                    lines.append("Analysis complete. See key metrics below for details.")
            else:
                lines.append("Analysis complete. See key metrics below for details.")
        else:
            lines.append("Unable to retrieve data for this query.")
        
        # Add time window context
        if state.entities.time_window:
            lines.append(f"_Time period: {state.entities.time_window.start_date} to {state.entities.time_window.end_date}_")
        
        return "\n".join(lines)
    
    def _build_key_metrics(self, state: AgentState) -> str:
        """Build the key metrics section."""
        lines = ["[Key Metrics]"]
        
        if state.raw_results:
            for result in state.raw_results:
                result_data = result.get("result", "")
                result_type = result.get("type", "")
                
                if result_type == "primary":
                    # Extract metrics from the result
                    lines.append(str(result_data)[:500])
                elif "breakdown" in str(result_data).lower():
                    lines.append("\n**Breakdown:**")
                    lines.append(str(result_data)[:300])
        else:
            lines.append("- No metrics available")
        
        return "\n".join(lines)
    
    def _build_drivers(self, state: AgentState) -> str:
        """Build the drivers/why section."""
        lines = ["[Drivers / Why]"]
        
        # Look for breakdown results to identify drivers
        drivers_found = False
        for result in state.raw_results:
            if result.get("type") == "drill_down":
                drivers_found = True
                # Try to extract top contributors
                lines.append(f"- Analysis from drill-down: {result.get('query', 'additional analysis')}")
        
        if not drivers_found:
            # Generate generic drivers based on intent
            if state.intent == "growth_analytics":
                lines.extend([
                    "- Review top-performing segments for growth opportunities",
                    "- Analyze underperforming channels for improvement",
                ])
            elif state.intent == "risk":
                lines.extend([
                    "- Monitor cohorts with elevated late rates",
                    "- Review collection strategy for aging buckets",
                ])
            elif state.intent == "merchant_perf":
                lines.extend([
                    "- Identify high-GMV merchants for partnership expansion",
                    "- Address merchants with elevated dispute rates",
                ])
            else:
                lines.append("- Further breakdown analysis recommended for root cause")
        
        return "\n".join(lines)
    
    def _build_recommendations(self, state: AgentState) -> str:
        """Build the recommendations section."""
        lines = ["[Recommended Actions]"]
        
        recommendations = self._get_recommendations_for_intent(state)
        
        for rec in recommendations:
            lines.append(f"\n**{rec['action']}**")
            lines.append(f"- Impact: {rec['impact']}")
            lines.append(f"- Effort: {rec['effort']}")
            lines.append(f"- Justification: {rec['justification']}")
        
        return "\n".join(lines)
    
    def _get_recommendations_for_intent(self, state: AgentState) -> List[dict]:
        """Get recommendations based on intent."""
        intent_recs = {
            "growth_analytics": [
                {
                    "action": "Focus on high-GMV segments",
                    "impact": "High",
                    "effort": "Medium",
                    "justification": "Top segments drive disproportionate value",
                },
                {
                    "action": "Improve repeat user rate with loyalty program",
                    "impact": "Medium",
                    "effort": "Medium",
                    "justification": "Repeat users have higher LTV",
                },
            ],
            "risk": [
                {
                    "action": "Tighten underwriting for high-risk cohorts",
                    "impact": "High",
                    "effort": "Medium",
                    "justification": "Reduce future late payments",
                },
                {
                    "action": "Implement early intervention for 1-7 day bucket",
                    "impact": "Medium",
                    "effort": "Low",
                    "justification": "Prevent escalation to worse buckets",
                },
            ],
            "merchant_perf": [
                {
                    "action": "Review high-dispute merchants",
                    "impact": "High",
                    "effort": "Low",
                    "justification": "Reduce operational costs and user complaints",
                },
                {
                    "action": "Expand partnerships with top GMV merchants",
                    "impact": "High",
                    "effort": "Medium",
                    "justification": "Concentrate growth with proven partners",
                },
            ],
            "funnel": [
                {
                    "action": "Optimize checkout flow at highest drop-off point",
                    "impact": "High",
                    "effort": "Medium",
                    "justification": "Direct conversion improvement",
                },
                {
                    "action": "A/B test approval messaging",
                    "impact": "Medium",
                    "effort": "Low",
                    "justification": "Improve perceived approval experience",
                },
            ],
        }
        
        return intent_recs.get(state.intent, [
            {
                "action": "Review data for actionable insights",
                "impact": "Medium",
                "effort": "Low",
                "justification": "Custom analysis may reveal opportunities",
            }
        ])
    
    def _build_data_section(self, state: AgentState) -> str:
        """Build the data & assumptions section."""
        lines = ["[Data & Assumptions]"]
        
        # Tools called
        tools_used = set(tc.tool_name for tc in state.tool_calls)
        lines.append(f"- **Tools called**: {', '.join(tools_used) or 'None'}")
        
        # Tables (infer from plan)
        if state.plan:
            lines.append(f"- **Primary tool**: {state.plan.primary_tool}")
        
        # Time range
        if state.entities.time_window:
            lines.append(f"- **Time range**: {state.entities.time_window.start_date} to {state.entities.time_window.end_date}")
        else:
            lines.append("- **Time range**: Last 30 days (default)")
        
        # Filters
        if state.entities.group_by:
            lines.append(f"- **Grouped by**: {', '.join(state.entities.group_by)}")
        
        # Limitations
        if state.validation and state.validation.issues:
            lines.append("- **Limitations**:")
            for issue in state.validation.issues:
                lines.append(f"  - {issue}")
        
        # Latency
        total_latency = sum(tc.latency_ms or 0 for tc in state.tool_calls)
        if total_latency:
            lines.append(f"- **Query latency**: {total_latency:.0f}ms")
        
        return "\n".join(lines)
