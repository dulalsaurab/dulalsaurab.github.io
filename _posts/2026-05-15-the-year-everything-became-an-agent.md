---
layout: post
title: "The Year Everything Became an Agent"
date: 2026-05-15 07:00:00-0700
description: "On building tools that think, breaking them, and finding what comes after"
tags: AI Agents RAG MCP LLM Workflows
categories: blog
giscus_comments: true
related_posts: true
---

<style>
body { text-align: justify }
</style>

*On building tools that think, breaking them, and finding what comes after*

---

> "We shape our tools, and thereafter our tools shape us."
> — Marshall McLuhan (attributed)

There's a moment in every builder's journey when the thing you're building starts behaving in ways you didn't expect. Not broken — *emergent*. You build a search tool and suddenly it's answering questions you never designed it for. You wire an LLM to a config generator and watch it produce something that *almost* works — close enough to be exciting, far enough to be dangerous.

This is the story of that year. The year we went from "let's see if an LLM can help write configs" to orchestrating entire investigative workflows where machines reason, humans judge, and the boundary between the two keeps shifting.

It's not a technical spec. It's a map of the territory — drawn while walking it.

---

## The First Agent (Early 2025)

It started with a simple frustration.

Our detection platform is how we find bad actors in networks. You write a config that says: "start with these accounts, fan out through these relationships, label anything suspicious." Simple in concept. Brutal in practice.

To write a config, you needed to know the config language, understand dozens of signal types, navigate internal label systems, set up a development environment, run build commands, submit diffs, test against the testing framework. A dozen tools, half-documented, glued together by tribal knowledge passed down through oncall rotations.

We asked: *what if you could just describe what you want to find, and the machine writes the config?*

So we built the Detection Agent. Our first agent. A chatbot sitting inside the platform UI, powered by an LLM, connected to tools.

But here's the thing about agents — they're only as smart as the tools you give them. An LLM without context is a confident fabricator. It'll happily invent signal names that sound plausible but don't exist. It'll generate config syntax that looks right but references phantom entities.

The agent needed eyes. It needed to *see* the real signals.

```
THE AGENT'S REASONING LOOP

User: 'Find signals related to account blocking'
                    ↓
      Reason: What tools do I need?
                    ↓
        Act: Call signal_search
                    ↓
  Observe: Got 5 relevant signals with descriptions
                    ↓
    Reason: Now I can generate the config
                    ↓
  Act: Generate detection config using real signal names
                    ↓
    Observe: Config passes syntax validation
                    ↓
           Response to user
```

### Building the Eyes: Signal Search RAG V1

This is where RAG entered our vocabulary.

> **RAG — In Plain Terms**
>
> **Retrieval-Augmented Generation** is a simple idea with profound consequences: instead of asking an LLM to *remember* everything (it can't), you let it *search* a knowledge base at query time, then generate answers grounded in what it found.
>
> Think of it as giving the LLM a library card instead of asking it to memorize the library.
>
> The pipeline: embed your documents into vectors → store in a vector database → at query time, embed the question → find nearest documents → feed them to the LLM as context → generate grounded answers.

We had ~30,000 behavioral signals. Each with a symbolic name, a description (sometimes cryptic, sometimes missing), source code, and metadata. No LLM on earth has this in its training data. Without RAG, the agent was flying blind.

> **What's a signal?**
>
> A signal is a named, versioned computation over user or account activity that produces a value — things like "number of accounts this user blocked in the last 7 days" or "whether this account was created from a flagged device." They're the atomic units of detection logic: each one measures one specific behavior, and you compose them in configs to express complex patterns. There can be tens of thousands of them in a mature integrity system, each with its own name, semantics, and quirks.

So we built it. Three days of hacking in July 2025:

- Pulled all signals from the internal signal catalog API
- Used `llama3.1-8b-instruct` to generate human-readable descriptions from signal code
- Embedded everything with DragonPlus (768 dimensions) into XDB (our vector storage)
- Wrapped it as a tool: `signal_search`

And just like that, the agent could see. Ask it "find signals related to account blocking" and it returned real signals, with real names, that actually existed in the system.

We built a second tool — `config_search` — same principle, different corpus. Now the agent could find existing configs as reference examples.

> **MCP — The Universal Adapter**
>
> **Model Context Protocol** is how agents talk to tools. Think USB-C for AI — a standard interface so any tool can plug into any agent without custom wiring.
>
> The agent says: *"I need to search for signals related to blocking."*
> MCP translates that into a structured tool call.
> The tool does its thing and returns results.
> The agent incorporates the results and keeps reasoning.
>
> Why this matters: when we improved Signal Search from V1 to V2, the agent got better *automatically*. Zero agent code changes. The protocol decouples the thinker from the tools.

We launched. People used it. The first configs generated by an AI agent went through diff review and landed. It worked.

Sort of.

---

## The Humbling (Mid 2025)

> "The first version of anything is just a list of assumptions waiting to be disproven."

Here's what nobody tells you about building AI agents: the demo is always magical. The tenth real-world use is where it falls apart.

Our agent started hallucinating. Not dramatically — subtly. It would return a signal called `user_block_count` when the real signal was `block_event_received`. Close enough to seem right. Wrong enough to break a config.

Token limits hit like a wall. The models we had (8K–32K context windows) couldn't hold everything simultaneously: the system prompt explaining the platform, the signal search results, the user's conversation history, the config being generated. Something always got pushed out.

We tried prompt engineering. *"Only use signals returned by the search tool. Never invent signal names."* It helped — for a while. But every instruction we added consumed tokens that could have been used for actual reasoning. We were fighting a zero-sum game.

> *The fundamental tension: you want the agent to know more (rich context), do more (many tools), and remember more (long conversations). With limited tokens, you can only pick two. The third degrades.*

The agent deteriorated over long conversations. By turn 8, it had forgotten the instructions from turn 1. Context window pollution — the technical term for "the machine forgot what it was doing because you talked too much."

And then there were the models themselves. Instruction-following was unreliable. You could ask for JSON output and get markdown. Ask for a specific format and get a creative reinterpretation. The model wasn't a reliable executor — it was a probabilistic artist.

```
THE DEGRADATION CYCLE

  More tools      Context grows      Less room       Quality drops
= more context →  = tokens       →   for          →  = add more
    needed          consumed          reasoning        guardrails
        ↑__________________________________________________|
```

We learned something important in this phase: **prompt engineering has diminishing returns**. There's a point where adding more instructions makes things *worse*, not better. You're not teaching the model — you're overwhelming it.

The agent didn't die. It just stopped being trustworthy. And an untrustworthy agent is worse than no agent at all — it gives you confidence without correctness.

We needed a different architecture.

---

## The Modular Turn (Late 2025)

> "The way to build complex systems that work is to build them from simple systems that work."
> — Kevin Kelly

The answer came not from better models (though those helped) but from better *architecture*. Our internal AI platform introduced Skills — and everything changed.

> **Skills — Composable Intelligence**
>
> A **Skill** is a self-contained module that an agent loads on demand. Each skill brings its own tools, its own documentation, and its own domain knowledge.
>
> The key insight: **lazy-loading**. Instead of cramming everything into the system prompt upfront (Agent 1.0), the agent loads only the skills relevant to the current task. Ask about signals? Load the signal search skill. Ask about analytics? Load that instead. Never both at once unless needed.
>
> This solved the token budget problem — not by getting more tokens, but by spending fewer of them on things that don't matter *right now*.

Think of it as the difference between carrying an entire encyclopedia in your backpack versus knowing which library shelf to walk to.

```
THE ARCHITECTURE SHIFT

Agent 1.0 — The Monolith
┌──────────────────────────────────────────────┐
│  Everything loaded upfront:                  │
│  All tools + All instructions + All context  │
│  = Token Explosion                           │
└──────────────────────────────────────────────┘
                      ↓ Evolution ↓

Agent 2.0 — Skills
┌─────────────────────────────────────────────────────────────┐
│               Agent Core (lightweight router)               │
│   ↙ on demand  ↙ on demand   ↙ on demand   ↙ on demand    │
│ [Signal Search] [Analytics] [Config Gen] [Other Skills]     │
└─────────────────────────────────────────────────────────────┘
```

Signal Search became a skill — not hardwired into one agent, but available to *any* agent that needed it. When we shipped Signal Search V2, dozens of agents got better overnight. One improvement, multiplied across an ecosystem.

And V2 was a real improvement. We'd learned from V1's failures:

- **Hybrid retrieval** — 70% vector similarity + 30% keyword matching — because sometimes the user knows the exact signal name, and sometimes they're describing a concept
- **Quality-aware re-ranking** — stop surfacing garbage signals just because they have similar embeddings
- **Jargon expansion** — domain-specific acronyms can mean very specific things in a given field; the system needed to know that
- **Coverage expansion** — coverage went from ~30K to ~51K signals; we'd been missing 16,000 accessor signals entirely

The numbers told the story.

> **Hit@10 — What It Means**
>
> Hit@10 is an information retrieval metric: given a query, did the correct result appear somewhere in the top 10 results? It's the signal search equivalent of "did the investigator find what they were actually looking for without having to scroll forever?" A score of 26% means three out of four searches came up empty. A score of 66% means most searches land.

Hit@10 jumped from 26% to 66%. Users were finding what they needed. Hundreds of weekly active users. Dozens of consumer agents. The skill had become infrastructure.

But even with better skills, better models, better tools — we were still asking one entity (the agent) to hold an entire process in its head. And processes, real investigative processes, have a property that conversations don't:

*They have steps that should never involve judgment, and steps that should always involve judgment.*

An agent doesn't know the difference.

---

## The Workflow Revolution (2026)

> "The future is already here — it's just not evenly distributed."
> — William Gibson

The paradigm shift wasn't about better agents. It was about *not using agents for everything*.

Think about what happens in an investigation. You trigger a case. You pull signals. You analyze patterns. You decide if something is suspicious. You escalate or close. Each of these is a step. But they're fundamentally different *kinds* of steps:

- **"Pull signals for this account"** — deterministic. Same input, same output, every time. No judgment needed.
- **"Is this pattern suspicious?"** — non-deterministic. Requires reasoning, context, maybe creativity.
- **"Should we escalate?"** — human. Some decisions should never be automated.

Asking one LLM agent to handle all three in a single conversation is like asking a philosopher to also be a calculator and a judge. Possible, but fragile.

**Workflows** separated these concerns.

```
THE AGENTIC WORKFLOW — EACH NODE DOES WHAT IT'S BEST AT

[Trigger]  →  [Action: Fetch signals]  →  [Agent: Analyze patterns]
(scheduled/      (deterministic)             (non-deterministic)
  event)                                             ↓
                                          [Confidence check]
                                         ↙              ↘
                                      High            Uncertain
                                       ↓                  ↓
                              [Deterministic:       [Human (HITL):
                              Create task + notify]  Review & decide]
                                                          ↓
                                                   [Log & close]
```

This is the insight that changed everything: **deterministic steps should be deterministic**. Don't ask an LLM to send an email — just send the email. Don't ask an LLM to filter a list by threshold — just filter it. Reserve the LLM for what it's actually good at: reasoning under ambiguity.

> **Workflow Node Types:**
>
> - **Triggers** — cron schedules, events, webhooks (what starts the workflow)
> - **Agent nodes** — LLM reasoning (the "think" steps)
> - **Action nodes** — deterministic execution (the "do" steps)
> - **Conditional nodes** — branching logic (the "decide" steps)
> - **HITL nodes** — human-in-the-loop pauses (the "judge" steps)

For rapid prototyping and external integrations, **n8n** is invaluable — fast to iterate, easy to share patterns, great for proving out a workflow before promoting it. Internally, we had our own equivalent: **AWB (Agentic Workflow Builder)** — same drag-and-drop canvas paradigm as n8n, but built for production use inside the company. You could describe what you wanted in natural language and let the AI generate the initial workflow structure, then refine from there.

> **AWB vs. n8n**
>
> Think of AWB as the internal, enterprise-grade version of n8n. n8n wins on speed and community templates — great for prototyping and external integrations. AWB wins on reliability, internal data access, and compliance — where you actually want to run things in production. We used both: n8n to prove the pattern, AWB to ship it.

**What workflows solved that agents couldn't:**

| Single Agent | Workflow |
|---|---|
| Everything in one context → token explosion | Each node has its own context → focused |
| Forgets early steps → drift | State passed explicitly → no drift |
| Fails silently | Branching + HITL → graceful degradation |
| LLM does things it shouldn't | Deterministic nodes handle deterministic work |

I've been building these patterns — chaining signal discovery (non-deterministic, RAG-powered) with config validation (deterministic, rule-based) and human review (HITL checkpoints) into unified investigative workflows. Prototyping in n8n for speed, migrating to AWB for production reliability.

The narrative shifted. We stopped asking "how do I make the agent smarter?" and started asking "how do I design a system where each part does what it's best at?"

---

## What I've Learned

```
THE PROGRESSION — EACH LAYER ENABLES THE NEXT

[Tools: 'Search']  →  [Agents: 'Reason']  →  [Skills: 'Compose']  →  [Workflows: 'Orchestrate']
```

If I had to distill this year into lessons, they'd be these:

**Start with tools, not agents.** The sexiest part of the stack is the agent — the reasoning loop, the autonomy, the "AI" of it all. But the boring part — the RAG pipeline, the validator, the search index — is where the real value lives. An agent without good tools is just a confident bullshitter.

**The token window is a design constraint, not a bug.** Early on, I treated token limits as something to work around. Now I see them as a forcing function for better architecture. If you can't fit everything in one context, maybe everything shouldn't be in one context. That's not a limitation — it's the architecture telling you to decompose.

**Skills beat prompts.** Writing a 2000-word system prompt is a trap. It feels productive. But a modular skill that loads only when needed and brings exactly the right context — that scales. That composes. That doesn't break when you add something new.

**Deterministic steps should be deterministic.** The most common mistake in agent design: using an LLM for things that have a correct answer. Sending an email, filtering a list, calling an API with known parameters. These aren't reasoning tasks. They're execution tasks. Treat them differently.

**Human-in-the-loop is not a failure of automation.** It's a design pattern. The most sophisticated workflows I've built have explicit human checkpoints — not because the machine *can't* decide, but because some decisions *shouldn't* be delegated. Knowing where to put the pause is as important as knowing where to put the agent.

**The unit of progress isn't the model — it's the system.** Better models help. But the jump from "interesting demo" to "production tool" came from system design: RAG for grounding, MCP for modularity, skills for composability, workflows for orchestration. Each layer enabled the next. None alone was sufficient.

---

```
THE FULL ARC — ONE YEAR

Early 2025           Mid 2025            Late 2025              2026
[First agent]    →  [Hallucinations] →  [Skills           →  [Workflows:
[First RAG tool]    [Token walls]       framework]            det + non-det]
[It works!]         [It breaks...]      [Signal Search V2]    [It orchestrates!]
                                        [It composes!]
```

---

*The year started with a question: can an LLM help write configs?*

*It ends with a different question: what should machines decide, and what should humans decide, and how do we build systems that know the difference?*

*I don't think we've answered it yet. But we're closer than we were twelve months ago.*

*And the tools keep getting better.*
