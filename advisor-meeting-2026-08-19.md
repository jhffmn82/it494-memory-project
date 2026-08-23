# IT 494 advisor meeting: summary and reading list

**Date:** 2026-08-19

Notes from an exploratory conversation. The goal at this stage is to understand the problem and decide what to investigate. Part 2 is a reading list I have not read yet.

---

## Part 1: What we discussed

### 1. Classification vs relationships

At the GAO the task was making sense of free-text employee survey comments against the EES instrument's nine indexes.

The finding I came away with: **central ideas can be pulled out of human text reliably, even where rigid classification fails.** Topic discovery worked. What did not work was asking one tool to do discovery and classification at once, and expecting every comment to land in exactly one category. The fix was separating the jobs, with BERTopic discovering the naturally occurring narratives and classification running against the instrument's own indexes as fixed anchors.

The specific thing that failed is worth being precise about, because it is narrower than "classification does not work." Deriving a *parent* taxonomy from the embedding geometry collapsed: the dendrogram folded everything into a single parent, because the embeddings were picking up the shared register of federal survey comments rather than their subject matter. The organization had already written the taxonomy I was trying to derive, so the answer was to use it rather than to reconstruct it.

For entities rather than raw text, my working view is that relations are the expensive part to maintain and probably where the value is. Subsumptive classes look derivable from the most specific term, and instance properties are cheap. Untested.

### 2. Persistence in AI

A model is stateless, so anything that appears to remember is machinery built around it. Named in the conversation: vector stores, retrieval-augmented generation, and caching. I know roughly what these do. I do not know how they compare, where each breaks down, or what else exists.

What I want to find out, starting from a problem I have: my own system cannot learn that it gave a wrong answer. It records filing something in the wrong place, but a wrong answer leaves no trace, so there is nothing to measure improvement against. I want to know whether that is solved and I simply have not encountered it.

My own system is described in section 5, which is where it came up in the conversation.

### 3. Use cases

**(a) An AI-assisted chat help desk that learns from conversations over time.** The AWS Summit example was a utility answering billing questions with access to account information. Store the raw conversations, build a map of how conversations progress, track semantics and conclusions, digest them into long-term memory. Many users, one organization.

**What my GAO work says about whether this is feasible.** The part that worked there was discovery. Pulling the central ideas out of free human text is something the tooling did well, and BERTopic found the naturally occurring narratives in the employee comments. What failed was making one tool do discovery and rigid classification at the same time, and expecting every comment to land cleanly in one exclusive category. Once those jobs were separated, with discovery on one side and classification against the instrument's fixed indexes on the other, the pipeline worked.

I expect the same split to apply here. Building an organic flow chart of how conversations actually progress, from raw transcripts, is something I think an AI can handle well, as long as the design accepts up front that a large portion of conversations will be outliers rather than treating that as a defect. Where a fixed taxonomy is also needed, the utility already has one in its dispute codes, the same way the agency already had its survey indexes.

I also came out of that work with a set of methods for judging whether this kind of output is any good: how to compute cluster centroids so the distances mean what you think they mean, which linkage to use when merging, why over-splitting is recoverable and over-merging is not, and how to audit near-misses and check label quality. That is the part I would bring to this, and it is the reason I think the use case is tractable rather than speculative.

**The other reason this one interests me:** a help desk has an outcome signal my own system does not. Ticket closed, reopened, escalated, repeat contact. My system has no way to learn that it gave a wrong answer, and here that signal comes with the job.

**(b) Large projects spanning multiple chats over time, needing more context than one conversation holds.** During annual training I ran separate chats for flight schedule, storyboard, weather update, and situation report against one shared knowledge base. The D&D campaign and the assistant backend are the same shape.

Concurrent sessions cannot share a context window regardless of its size. That is the claim I would check first, because the use case rests on it.

### 4. Knowledge graphs

Interested in learning the domain, with no formal grounding in it or in persistent memory for AI, and unlikely to encounter either in a classroom. Action item: gather resources and start reading.

### 5. What I have built, and what it is doing right now

Raised at the end of the conversation. I want to be straightforward that this was built inartfully. I had no knowledge of this field when I started, so nothing about it follows a known design. It accreted as I hit problems, and it is a pile of scripts and text files rather than a system anyone would draw on a whiteboard. It is also in daily use and doing real work, which is the part worth talking about.

**What it is.** Every conversation I have with an AI is saved as a raw transcript and never edited. At the end of a working session a summary of that session is written and filed into a tree, organized by area of my life and then by topic. Those summaries are rolled up, so a higher level can answer a question without reading everything underneath it. A maintenance pass runs on a schedule to fold in new material and re-check older summaries against their sources. It is wired into the tools I use, so a new chat starts knowing the map exists and can search it and read from it.

**What it is doing now.** It runs continuously and I use it every day. The value shows up on large projects that span many chats over months, where the work needs far more context than any single conversation can hold, and where decisions made weeks ago have to still be available and still be correct.

The clearest example is annual training. I ran separate chats at the same time for the flight schedule, the storyboard, the weather update, and the situation report, all against one shared knowledge base. For the storyboards I pulled images and video out of email, matched them against the mission tracker, AMRS, and the flight schedule using their metadata, and built the storyboards from a cached template. Each of those threads would have exceeded a single conversation on its own, and they had to agree with each other.

The D&D campaign I run and the assistant setup itself are the same shape: long-running, many sessions, and dependent on earlier decisions staying findable.

**How it keeps itself current.** Each maintenance pass audits a rotating subset of summaries against the original transcripts, trying to disprove the dates, numbers, and claims in them, and re-summarizes any whose source has changed since it was written. Growth is handled by folding rather than removal: nothing is deleted, but children fold up into a parent and redundant siblings merge, so what has to be read to answer a question stays bounded while the detail stays recoverable at the leaf. When it does get something wrong, I correct it by hand.

**On validating any of this.** I do not have real metrics. I set up a fixed set of questions with known answers and it does answer them, but that set is imperfect and I would not claim it measures much. So I am not in a position to state this system's limitations with any confidence. Problems get patched as they surface, which is fine for my own use and is not evidence of anything. Working out what should actually be measured is one of the things I want to get out of reading.

If anything, that is where the time should go. Taking this from something that works for me to something validated and tested looks like the useful next step.

I do not currently know how to do that. Working out how this kind of system is measured, and by what, is the thing I need reading for before I can claim anything about it.

### How the discussion went

I kept my own system out of the conversation until the end. What drew the most interest was not the design but that it had been useful, specifically for large multi-chat projects sustained over time.

---

## Part 2: Reading list

Assembled with LLM assistance, as discussed. Citations were checked against source pages, so titles, authors, venues and identifiers should be correct. The one-line notes describe what each item is; they are not my readings, and I have not read any of these yet.

The categories below are how the survey organized the space. They are new to me and are part of what I need to learn.

- **Structured agent memory:** systems treating memory as a managed component rather than a retrieval call.
- **Hierarchical summarization:** summarize, then summarize the summaries, and retrieve at whichever level fits.
- **Consolidation:** moving information out of a session into durable structure.
- **Parametric memory:** changing the weights instead of keeping an external store.
- **Long context and caching:** alternatives to storing anything.

### Start here

1. **Kumaran, Hassabis and McClelland (2016), "What Learning Systems do Intelligent Agents Need? Complementary Learning Systems Theory Updated."** *Trends in Cognitive Sciences* 20(7). DOI:10.1016/j.tics.2016.05.004
   Cognitive-science account of a fast episodic memory feeding a slow structured one, written for an AI audience.

2. **Park et al. (2023), "Generative Agents: Interactive Simulacra of Human Behavior."** UIST 2023. arXiv:2304.03442
   Agents that store observations and periodically synthesize higher-level reflections from them.

3. **Sarthi et al. (2024), "RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval."** ICLR 2024. arXiv:2401.18059
   Builds a tree by recursively clustering and summarizing text, then retrieves at multiple levels.

4. **Rasmussen et al. (2025), "Zep: A Temporal Knowledge Graph Architecture for Agent Memory."** arXiv:2501.13956
   Agent memory as a temporal knowledge graph; contradicted facts are marked invalid by timestamp rather than deleted.

5. **Edge et al. (2024), "From Local to Global: A Graph RAG Approach to Query-Focused Summarization."** Microsoft Research. arXiv:2404.16130
   Builds an entity graph from documents and pre-generates summaries for clusters within it.

### Consolidation

6. **McClelland, McNaughton and O'Reilly (1995).** *Psychological Review* 102(3). DOI:10.1037/0033-295X.102.3.419
   The original complementary-learning-systems argument.

7. **Teyler and Rudy (2007), "The hippocampal indexing theory and episodic memory."** *Hippocampus* 17(12). DOI:10.1002/hipo.20350
   Theory that the hippocampus stores a pointer to a memory rather than the memory itself.

8. **Tononi and Cirelli (2014), "Sleep and the Price of Plasticity."** *Neuron* 81(1). DOI:10.1016/j.neuron.2013.12.025
   Argues sleep performs downscaling, so consolidation involves subtraction.

9. **Zacks et al. (2007), "Event perception: a mind-brain perspective."** *Psychological Bulletin* 133(2). DOI:10.1037/0033-2909.133.2.273
   How continuous experience gets segmented into discrete events, and why those become memory units.

10. **Sumers, Yao, Narasimhan and Griffiths (2024), "Cognitive Architectures for Language Agents."** TMLR. arXiv:2309.02427
    A framework dividing agent memory into working, episodic, semantic and procedural.

11. **Rezazadeh et al. (2025), "MemTree: Dynamic Tree Memory Representation for LLMs."** ICLR 2025. arXiv:2410.14052
    Maintains a summary tree online as new material arrives, rather than building it once.

12. **Talebirad et al. (2026), "Toward a Theory of Hierarchical Memory for Language Agents."** arXiv:2603.21564
    Formal framework for hierarchical memory; describes several existing systems in one vocabulary.

13. **Wu et al. (2021), "Recursively Summarizing Books with Human Feedback."** arXiv:2109.10862
    Summarizes long texts by summarizing sections and then summarizing those summaries.

### Retrieval, vector search, caching

14. **Wang et al. (2024), "Searching for Best Practices in Retrieval-Augmented Generation."** EMNLP 2024. arXiv:2407.01219
    Compares RAG components empirically, including sparse, dense, and hybrid retrieval.

15. **Douze et al. (2024), "The Faiss library."** arXiv:2401.08281
    The vector-search library most systems are built on, and its index selection trade-offs.

16. **Kuffo, Krippner and Boncz (2025), "PDX: A Data Layout for Vector Similarity Search."** SIGMOD 2025. arXiv:2503.04422
    A storage layout for vectors, with measurements of exact versus approximate search.

17. **Malkov and Yashunin, "Hierarchical Navigable Small World graphs."** arXiv:1603.09320
    The approximate nearest-neighbor index used by most vector databases.

18. **Chan et al. (2025), "Don't Do RAG: When Cache-Augmented Generation is All You Need."** WWW 2025. arXiv:2412.15605
    Proposes preloading a corpus into the model's cache instead of retrieving from it.

19. **"NoLiMa: Long-Context Evaluation Beyond Literal Matching."** arXiv:2502.05167
    Tests long-context performance when question and answer share no literal keywords.

20. **Jeong et al. (2024), "Adaptive-RAG."** arXiv:2403.14403
    Decides per query whether retrieval is needed and how much.

### Benchmarks

21. **LoCoMo**, arXiv:2402.17753. Benchmark for very long-term conversational memory.

22. **LongMemEval.** Benchmark covering recall over long chat histories, including knowledge updates and abstention.

23. **MemoryAgentBench**, arXiv:2507.05257. Benchmark delivering information incrementally across turns.

### Summary faithfulness

24. **BooookScore**, ICLR 2024, arXiv:2310.00785. Measures coherence in book-length summarization.

25. **FABLES**, COLM 2024, arXiv:2404.01261. Human evaluation of faithfulness in book-length summaries.

### Knowledge graphs

26. **Chen (1976), "The Entity-Relationship Model: Toward a Unified View of Data."** ACM TODS 1(1).
    The origin of the entity, attribute and relation model.

27. **Angles et al. (2017), "Foundations of Modern Query Languages for Graph Databases."** ACM Computing Surveys 50(5). DOI:10.1145/3104031
    The difference between property graphs and triple stores, and what each query language assumes.

28. **Hogan et al. (2021), "Knowledge Graphs."** ACM Computing Surveys 54(4). arXiv:2003.02320
    The standard survey. Sections 1 to 3 cover identity, context, and construction.

29. **Snodgrass (1999), "Developing Time-Oriented Database Applications in SQL."** Morgan Kaufmann. Free PDF from the author.
    Modeling facts that were true during a period, and the difference between when something was true and when it was recorded.

30. **Weikum, Dong, Razniewski and Suchanek (2021), "Machine Knowledge: Creation and Curation of Comprehensive Knowledge Bases."** arXiv:2009.11564
    How large knowledge bases are actually built and maintained.

31. **Pan et al. (2024), "Unifying Large Language Models and Knowledge Graphs: A Roadmap."** IEEE TKDE. arXiv:2306.08302
    Taxonomy of ways language models and knowledge graphs are combined.

32. **Rossi et al. (2021), "Knowledge Graph Embedding for Link Prediction: A Comparative Analysis."** ACM TKDD. arXiv:2002.00819
    Comparison of link-prediction methods. Included so I know what this subfield is, since searching the term leads here.

### Learning structure from conversations

33. **Kecht, Egger, Kratsch and Roglinger (2021), "Event Log Construction from Customer Service Conversations Using Natural Language Inference."** ICPM 2021. DOI:10.1109/ICPM53251.2021.9576869
    Turns support conversations into event logs so process mining can run on them.

34. **Gung et al. (2023), "Intent Induction from Conversations for Task-Oriented Dialogue Track at DSTC 11."** SIGDIAL 2023. arXiv:2304.12982
    A shared task on discovering intents from customer service conversations without labels, with results across thirty-four teams.

35. **De Raedt, Godin, Demeester and Develder (2023), "IDAS: Intent Discovery with Abstractive Summarization."** ACL 2023 workshop. DOI:10.18653/v1/2023.nlp4convai-1.7
    Summarizes each utterance before clustering rather than clustering the raw text.

36. **Wegmann, Schraagen and Nguyen (2022), "Same Author or Just Same Topic?"** ACL 2022 workshop. arXiv:2204.04907
    Separating writing style from subject matter in text embeddings.

### Learning from outcomes

37. **Brynjolfsson, Li and Raymond (2025), "Generative AI at Work."** Quarterly Journal of Economics 140(2). DOI:10.1093/qje/qjae044
    Field study of AI assistance in a customer support setting, measured on resolution outcomes.

38. **Ouyang et al. (2026), "ReasoningBank: Scaling Agent Self-Evolving with Reasoning Memory."** ICLR 2026. arXiv:2509.25140
    An agent writing memory from its own successful and failed attempts.

39. **Liu, Zhang and Choi (2025), "User Feedback in Human-LLM Dialogues."** EMNLP 2025. arXiv:2507.23158
    Examines how noisy user feedback is when used as a learning signal.

40. **Rezazadeh et al. (2025), "Collaborative Memory: Multi-User Memory Sharing in LLM Agents with Dynamic Access Control."** arXiv:2505.18279
    Shared memory across users where not everyone may see everything.

### Shared state across sessions

41. **Erman, Hayes-Roth, Lesser and Reddy (1980), "The Hearsay-II Speech-Understanding System."** ACM Computing Surveys 12(2). DOI:10.1145/356810.356816
    The original blackboard architecture: independent components coordinating only through shared state.

42. **Hayes-Roth (1985), "A Blackboard Architecture for Control."** Artificial Intelligence 26(3). DOI:10.1016/0004-3702(85)90063-3
    Extends the blackboard idea to deciding which action to take next.

43. **Salemi et al. (2026), "LLM-Based Multi-Agent Blackboard System for Information Discovery in Data Science."** arXiv:2510.01285
    A modern blackboard system for multiple language-model agents.

44. **Pollertlam and Kornsuwannawit (2026), "Beyond the Context Window: A Cost-Performance Analysis of Fact-Based Memory vs. Long-Context LLMs."** arXiv:2603.04814
    Compares external memory against putting everything in the context window.
