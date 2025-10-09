#!/usr/bin/env python3
"""Streamlit app for AgenticRedTeam - Interactive red teaming dashboard."""

import streamlit as st
import sys
from pathlib import Path
import json
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.targets.llm_target import LLMTarget
from src.agents.judge_agent import JudgeAgent
from src.attacks.prompt_injection import PromptInjectionAttack, DirectPromptAttack
from src.attacks.crescendo import CrescendoAttack
from src.orchestrator import AttackOrchestrator
from src.evaluator import BenchmarkEvaluator
from benchmarks.harmbench_loader import HarmBenchLoader

# Load environment
load_dotenv(override=True)

# Page config
st.set_page_config(
    page_title="AgenticRedTeam Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
    }
    .success-attack {
        background-color: #fee;
        padding: 0.5rem;
        border-left: 3px solid #f44;
    }
    .failed-attack {
        background-color: #efe;
        padding: 0.5rem;
        border-left: 3px solid #4f4;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = []
if 'running' not in st.session_state:
    st.session_state.running = False

# Header
st.markdown('<p class="main-header">🛡️ AgenticRedTeam Dashboard</p>', unsafe_allow_html=True)
st.markdown("**Autonomous Red Teaming for LLMs** - Test AI safety with intelligent adversarial agents")

# Sidebar - Configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    # Model selection
    st.subheader("Target Model")
    target_provider = st.selectbox(
        "Provider",
        ["openai", "anthropic", "google", "azure", "xai"],
        key="target_provider"
    )

    target_models = {
        "openai": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-sonnet-20240229"],
        "google": ["gemini-pro", "gemini-1.5-pro"],
        "azure": ["azure/gpt-4"],
        "xai": ["grok-3", "grok-3-mini", "grok-4"]
    }

    target_model = st.selectbox(
        "Model",
        target_models[target_provider],
        key="target_model"
    )

    st.subheader("Judge Model")
    judge_provider = st.selectbox(
        "Provider",
        ["anthropic", "openai", "google", "xai"],
        key="judge_provider",
        index=0
    )

    judge_models = {
        "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
        "openai": ["gpt-4o", "gpt-4-turbo"],
        "google": ["gemini-1.5-pro"],
        "xai": ["grok-3", "grok-3-mini", "grok-4"]
    }

    judge_model = st.selectbox(
        "Model",
        judge_models[judge_provider],
        key="judge_model"
    )

    st.subheader("Attack Configuration")
    attack_strategies = st.multiselect(
        "Attack Strategies",
        ["Direct Prompt", "Prompt Injection", "Crescendo"],
        default=["Direct Prompt", "Prompt Injection"],
        key="strategies"
    )

    num_samples = st.slider(
        "Number of Test Samples",
        min_value=1,
        max_value=20,
        value=5,
        key="num_samples"
    )

    success_threshold = st.slider(
        "Success Threshold (Danger Score)",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.05,
        key="threshold"
    )

    # Live preview toggle
    show_live_preview = st.checkbox(
        "🔍 Show Live Attack Preview",
        value=True,
        help="Display real-time conversation preview during benchmark (great for demos!)"
    )

    st.divider()

    # API Key status
    st.subheader("🔑 API Status")
    openai_key = bool(os.getenv('OPENAI_API_KEY'))
    anthropic_key = bool(os.getenv('ANTHROPIC_API_KEY'))
    grok_key = bool(os.getenv('GROK_API_KEY') or os.getenv('XAI_API_KEY'))

    st.write(f"{'✅' if openai_key else '❌'} OpenAI")
    st.write(f"{'✅' if anthropic_key else '❌'} Anthropic")
    st.write(f"{'✅' if grok_key else '❌'} Grok (xAI)")

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Run Benchmark", "📊 Results Dashboard", "🔍 Single Attack", "📚 About"])

# Tab 1: Run Benchmark
with tab1:
    st.header("Run Red Teaming Benchmark")

    col1, col2 = st.columns([2, 1])

    with col1:
        config_summary = f"""
        **Configuration Summary:**
        - Target: `{target_provider}/{target_model}`
        - Judge: `{judge_provider}/{judge_model}`
        - Strategies: {', '.join(attack_strategies)}
        - Samples: {num_samples}
        - Threshold: {success_threshold}
        """
        
        if show_live_preview:
            config_summary += """
        - 🔍 **Live Preview**: Enabled (perfect for demos!)
        """
        
        st.info(config_summary)

    with col2:
        if st.button("🚀 Start Benchmark", type="primary", use_container_width=True):
            st.session_state.running = True

    if st.session_state.running:
        try:
            # Initialize components
            with st.spinner("Initializing models..."):
                target = LLMTarget(model=target_model, provider=target_provider)
                judge = JudgeAgent(model=judge_model, provider=judge_provider)

                # Create attack agent for Crescendo if needed
                attacker_llm = None
                if "Crescendo" in attack_strategies:
                    attacker_llm = LLMTarget(model="gpt-4o", provider="openai", temperature=0.9)

            # Load dataset
            with st.spinner("Loading test behaviors..."):
                loader = HarmBenchLoader()
                behaviors = loader.load()
                sampled = loader.sample(behaviors, n=num_samples)
                objectives = [b.behavior for b in sampled]

            st.success(f"✅ Loaded {len(objectives)} test behaviors")

            # Create strategies
            strategies = []
            if "Direct Prompt" in attack_strategies:
                strategies.append(DirectPromptAttack())
            if "Prompt Injection" in attack_strategies:
                strategies.append(PromptInjectionAttack())
            if "Crescendo" in attack_strategies:
                if attacker_llm:
                    strategies.append(CrescendoAttack(attacker_llm, max_turns=5))

            # Run attacks
            orchestrator = AttackOrchestrator(target=target, judge=judge, verbose=False)

            progress_bar = st.progress(0)
            status_text = st.empty()

            # Create live preview section if enabled
            if show_live_preview:
                st.subheader("🔍 Live Attack Preview")
                preview_container = st.container()
            else:
                preview_container = None
            
            results = []
            total_attacks = len(strategies) * len(objectives)

            for i, strategy in enumerate(strategies):
                for j, objective in enumerate(objectives):
                    current = i * len(objectives) + j + 1
                    progress_bar.progress(current / total_attacks)
                    status_text.text(f"Running {strategy.name} attack {j+1}/{len(objectives)}...")

                    # Show current attack info and run attack
                    if show_live_preview and preview_container:
                        with preview_container:
                            st.markdown(f"**Current Attack:** {strategy.name} #{j+1}")
                            st.markdown(f"**Objective:** {objective[:100]}{'...' if len(objective) > 100 else ''}")
                            
                            # Create placeholder for live conversation
                            conversation_placeholder = st.empty()
                            
                            # Run attack with live updates
                            result = orchestrator.execute_attack_with_preview(
                                strategy=strategy,
                                objective=objective,
                                success_threshold=success_threshold,
                                conversation_placeholder=conversation_placeholder
                            )
                            results.append(result)
                            
                            # Show final result
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Success", "✅ Yes" if result.success else "❌ No")
                            with col2:
                                st.metric("Danger Score", f"{result.safety_score:.2f}")
                            with col3:
                                st.metric("Turns", result.num_turns)
                            
                            st.divider()
                    else:
                        # Run attack without live preview
                        result = orchestrator.execute_attack(
                            strategy=strategy,
                            objective=objective,
                            success_threshold=success_threshold
                        )
                        results.append(result)

            st.session_state.results = results
            st.session_state.running = False

            progress_bar.progress(1.0)
            status_text.text("✅ Benchmark complete!")

            # Show quick summary
            evaluator = BenchmarkEvaluator()
            metrics = evaluator.calculate_metrics(results)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Attack Success Rate", f"{metrics.attack_success_rate:.1%}")
            with col2:
                st.metric("Successful Attacks", f"{metrics.successful_attacks}/{metrics.total_attacks}")
            with col3:
                st.metric("Avg Danger Score", f"{metrics.avg_safety_score:.3f}")
            with col4:
                st.metric("Avg Turns to Success", f"{metrics.avg_turns_to_success:.1f}")

            st.balloons()

        except Exception as e:
            st.error(f"Error running benchmark: {str(e)}")
            st.session_state.running = False

# Tab 2: Results Dashboard
with tab2:
    st.header("📊 Results Dashboard")

    if not st.session_state.results:
        st.warning("No results yet. Run a benchmark first!")
    else:
        evaluator = BenchmarkEvaluator()
        metrics = evaluator.calculate_metrics(st.session_state.results)

        # Overall metrics
        st.subheader("Overall Metrics")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Attack Success Rate", f"{metrics.attack_success_rate:.1%}")
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Attacks", metrics.total_attacks)
            st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Avg Danger Score", f"{metrics.avg_safety_score:.3f}")
            st.markdown('</div>', unsafe_allow_html=True)

        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Avg Turns", f"{metrics.avg_turns_to_success:.1f}")
            st.markdown('</div>', unsafe_allow_html=True)

        # Per-strategy breakdown
        st.subheader("Strategy Breakdown")

        strategy_data = []
        for name, stats in metrics.metrics_by_strategy.items():
            strategy_data.append({
                "Strategy": name,
                "Total": stats['total'],
                "Successful": stats['successful'],
                "ASR": stats['asr'],
                "Avg Score": stats['avg_safety_score']
            })

        df_strategies = pd.DataFrame(strategy_data)

        col1, col2 = st.columns(2)

        with col1:
            # Bar chart for ASR
            fig_asr = px.bar(
                df_strategies,
                x="Strategy",
                y="ASR",
                title="Attack Success Rate by Strategy",
                labels={"ASR": "Success Rate"},
                color="ASR",
                color_continuous_scale="Reds"
            )
            fig_asr.update_layout(showlegend=False)
            st.plotly_chart(fig_asr, use_container_width=True)

        with col2:
            # Safety score by strategy
            fig_score = px.bar(
                df_strategies,
                x="Strategy",
                y="Avg Score",
                title="Average Danger Score by Strategy",
                labels={"Avg Score": "Danger Score (0-1)"},
                color="Avg Score",
                color_continuous_scale="RdYlGn_r"
            )
            fig_score.update_layout(showlegend=False)
            st.plotly_chart(fig_score, use_container_width=True)

        # Data table
        st.subheader("Detailed Results")
        st.dataframe(df_strategies, use_container_width=True)

        # Individual attack results
        st.subheader("Individual Attack Results")

        for idx, result in enumerate(st.session_state.results):
            with st.expander(
                f"{'🔴' if result.success else '🟢'} {result.strategy_name} - "
                f"Score: {result.safety_score:.2f} - "
                f"{result.metadata.get('objective', '')[:80]}..."
            ):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**Objective:** {result.metadata.get('objective', 'N/A')}")
                    st.markdown(f"**Final Response:** {result.final_response[:300]}...")

                    if len(result.conversation) > 1:
                        st.markdown("**Conversation:**")
                        for turn in result.conversation:
                            st.markdown(f"**Turn {turn.turn_number}:**")
                            st.markdown(f"*User:* {turn.prompt[:150]}...")
                            st.markdown(f"*Assistant:* {turn.response[:150]}...")

                with col2:
                    st.metric("Success", "✅ Yes" if result.success else "❌ No")
                    st.metric("Safety Score", f"{result.safety_score:.2f}")
                    st.metric("Turns", result.num_turns)

        # Export results
        st.subheader("Export Results")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Save Results JSON", use_container_width=True):
                evaluator.save_results(
                    st.session_state.results,
                    metrics,
                    filename=f"streamlit_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                st.success("✅ Results saved to results/ directory")

        with col2:
            if st.button("📄 Generate Report", use_container_width=True):
                report = evaluator.generate_report(
                    st.session_state.results,
                    target_model=f"{target_provider}/{target_model}"
                )
                st.text_area("Report", report, height=400)

# Tab 3: Single Attack
with tab3:
    st.header("🔍 Single Attack Test")

    col1, col2 = st.columns([2, 1])

    with col1:
        custom_objective = st.text_area(
            "Enter harmful behavior to test:",
            placeholder="e.g., Write a tutorial on how to bypass security systems",
            height=100
        )

        single_strategy = st.selectbox(
            "Attack Strategy",
            ["Direct Prompt", "Prompt Injection", "Crescendo"],
            key="single_strategy"
        )

    with col2:
        st.info(f"""
        **Target:** `{target_provider}/{target_model}`

        **Judge:** `{judge_provider}/{judge_model}`

        **Strategy:** {single_strategy}
        """)

    if st.button("🎯 Run Single Attack", type="primary"):
        if not custom_objective:
            st.error("Please enter an objective to test")
        else:
            try:
                with st.spinner("Running attack..."):
                    # Initialize
                    target = LLMTarget(model=target_model, provider=target_provider)
                    judge = JudgeAgent(model=judge_model, provider=judge_provider)

                    # Select strategy
                    if single_strategy == "Direct Prompt":
                        strategy = DirectPromptAttack()
                    elif single_strategy == "Prompt Injection":
                        strategy = PromptInjectionAttack()
                    else:
                        attacker_llm = LLMTarget(model="gpt-4o", provider="openai", temperature=0.9)
                        strategy = CrescendoAttack(attacker_llm, max_turns=5)

                    # Run
                    orchestrator = AttackOrchestrator(target=target, judge=judge, verbose=False)
                    result = orchestrator.execute_attack(strategy, custom_objective, success_threshold)

                # Display results
                st.subheader("Results")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Success", "✅ Yes" if result.success else "❌ No")
                with col2:
                    st.metric("Danger Score", f"{result.safety_score:.2f}")
                with col3:
                    st.metric("Turns", result.num_turns)

                st.subheader("Conversation")
                for turn in result.conversation:
                    st.markdown(f"**Turn {turn.turn_number}:**")

                    with st.container():
                        st.markdown("**🔵 Attack Prompt:**")
                        st.info(turn.prompt)

                        st.markdown("**🤖 Target Response:**")
                        if result.success:
                            st.error(turn.response)
                        else:
                            st.success(turn.response)

                    st.divider()

            except Exception as e:
                st.error(f"Error: {str(e)}")

# Tab 4: About
with tab4:
    st.header("📚 About AgenticRedTeam")

    st.markdown("""
    ## What is AgenticRedTeam?

    AgenticRedTeam is an autonomous red teaming framework for testing LLM safety using intelligent agents.
    Inspired by [DeepTeam](https://github.com/confident-ai/deepteam) with modern improvements.

    ### ✨ Key Features

    - **Multi-turn Attack Strategies**: Crescendo, Prompt Injection, Direct attacks
    - **Universal LLM Support**: Works with OpenAI, Anthropic, Google, Azure via LiteLLM
    - **Automated Evaluation**: LLM-powered judge agent for safety scoring
    - **HarmBench Integration**: Benchmark against standardized harmful behavior dataset
    - **Comprehensive Reporting**: Detailed metrics and visualizations

    ### 🎯 Attack Strategies

    1. **Direct Prompt**: Baseline - sends harmful request with no obfuscation
    2. **Prompt Injection**: 8 jailbreak templates (role-play, DAN, authority claims, etc.)
    3. **Crescendo**: Multi-turn gradual escalation from benign to harmful

    ### 📊 Metrics

    - **Attack Success Rate (ASR)**: % of attacks that successfully elicited unsafe responses
    - **Danger Score**: 0 (safe) to 1 (unsafe) - based on judge evaluation
    - **Turns to Success**: Efficiency metric for multi-turn attacks

    ### 🔬 Use Cases

    - Pre-deployment safety testing
    - Model robustness comparison
    - Guardrail evaluation
    - Red teaming research
    - Alignment research

    ### 📖 Documentation

    - [README.md](README.md) - Project overview
    - [USAGE.md](USAGE.md) - Detailed usage guide
    - [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Complete project recap

    ### 🔑 API Configuration

    Edit `.env` file with your API keys:
    ```
    OPENAI_API_KEY=sk-...
    ANTHROPIC_API_KEY=sk-ant-...
    XAI_API_KEY=xai-...  # LiteLLM expects this name for Grok
    ```

    ### ⚠️ Safety & Ethics

    This tool is for **defensive security research only**:
    - Test your own models before deployment
    - Identify vulnerabilities in safety systems
    - Improve AI alignment and robustness

    **DO NOT** use for malicious purposes or attacking production systems without authorization.

    ### 📝 License

    MIT License - Free for research and commercial use
    """)

# Footer
st.divider()
st.markdown(
    "<p style='text-align: center; color: #666;'>Built with ❤️ using Streamlit | "
    "AgenticRedTeam v0.1.0 | Inspired by DeepTeam</p>",
    unsafe_allow_html=True
)
