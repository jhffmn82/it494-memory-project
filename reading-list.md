# Reading list

The Phase 1 working list, assistant-compiled from its survey with citations verified against source pages, for Justin's review. Each entry except the nine marked *library* names its reference copy in `papers/` and its one-pager in `summaries/one-pagers/` by slug; *library* entries have neither yet (the digest covers them from abstracts) and carry DOIs in `papers/MANIFEST.md` for an ISU library pull.

The advisor-meeting record of 2026-08-19 keeps the original 44 items with fuller annotations; this working index supersedes it and adds the ten knowledge-graph items requested on 2026-08-25.

## Start here

1. Kumaran, Hassabis, McClelland 2016. What Learning Systems do Intelligent Agents Need? Trends in Cognitive Sciences 20(7). *library* · kumaran2016-cls-updated
2. Park et al. 2023. Generative Agents. UIST 2023. arXiv:2304.03442 · park2023-generative-agents
3. Sarthi et al. 2024. RAPTOR. ICLR 2024. arXiv:2401.18059 · sarthi2024-raptor
4. Rasmussen et al. 2025. Zep: A Temporal Knowledge Graph Architecture for Agent Memory. arXiv:2501.13956 · rasmussen2025-zep
5. Edge et al. 2024. From Local to Global: A Graph RAG Approach. arXiv:2404.16130 · edge2024-graphrag

## Consolidation and agent memory

6. McClelland, McNaughton, O'Reilly 1995. Psychological Review 102(3). *library* · mcclelland1995-cls
7. Teyler, Rudy 2007. The hippocampal indexing theory. Hippocampus 17(12). *library* · teyler2007-hippocampal-index
8. Tononi, Cirelli 2014. Sleep and the Price of Plasticity. Neuron 81(1). *library* · tononi2014-shy
9. Zacks et al. 2007. Event perception. Psychological Bulletin 133(2). *library* · zacks2007-event-perception
10. Sumers et al. 2024. Cognitive Architectures for Language Agents. TMLR. arXiv:2309.02427 · sumers2024-coala
11. Rezazadeh et al. 2025. MemTree. ICLR 2025. arXiv:2410.14052 · rezazadeh2025-memtree
12. Talebirad et al. 2026. Toward a Theory of Hierarchical Memory. arXiv:2603.21564 · talebirad2026-hierarchical-theory
13. Wu et al. 2021. Recursively Summarizing Books with Human Feedback. arXiv:2109.10862 · wu2021-recursive-books

## Retrieval, vector search, caching

14. Wang et al. 2024. Searching for Best Practices in RAG. EMNLP 2024. arXiv:2407.01219 · wang2024-rag-best-practices
15. Douze et al. 2024. The Faiss library. arXiv:2401.08281 · douze2024-faiss
16. Kuffo, Krippner, Boncz 2025. PDX. SIGMOD 2025. arXiv:2503.04422 · kuffo2025-pdx
17. Malkov, Yashunin 2016. HNSW graphs. TPAMI. arXiv:1603.09320 · malkov2016-hnsw
18. Chan et al. 2025. Don't Do RAG: Cache-Augmented Generation. WWW 2025. arXiv:2412.15605 · chan2025-cag
19. Modarressi et al. 2025. NoLiMa. ICML 2025. arXiv:2502.05167 · nolima2025-long-context
20. Jeong et al. 2024. Adaptive-RAG. NAACL 2024. arXiv:2403.14403 · jeong2024-adaptive-rag

## Benchmarks and faithfulness

21. Maharana et al. 2024. LoCoMo. ACL 2024. arXiv:2402.17753 · maharana2024-locomo
22. Hu, Wang, McAuley 2025. MemoryAgentBench. arXiv:2507.05257 · wu2025-memoryagentbench
23. Chang et al. 2024. BooookScore. ICLR 2024. arXiv:2310.00785 · chang2024-booookscore
24. Kim et al. 2024. FABLES. COLM 2024. arXiv:2404.01261 · kim2024-fables

## Knowledge graphs: foundations

25. Chen 1976. The Entity-Relationship Model. ACM TODS 1(1). *library* · chen1976-er-model
26. Angles et al. 2017. Foundations of Modern Query Languages for Graph Databases. ACM CSUR 50(5). arXiv:1610.06264 · angles2017-graph-query-foundations
27. Hogan et al. 2021. Knowledge Graphs. ACM CSUR 54(4). arXiv:2003.02320 · hogan2021-knowledge-graphs
28. Snodgrass 1999. Developing Time-Oriented Database Applications in SQL. Morgan Kaufmann, author-released PDF · snodgrass1999-time-oriented-db
29. Weikum et al. 2021. Machine Knowledge. FnT Databases. arXiv:2009.11564 · weikum2021-machine-knowledge
30. Pan et al. 2024. Unifying Large Language Models and Knowledge Graphs. IEEE TKDE. arXiv:2306.08302 · pan2024-unifying-llm-kg
31. Rossi et al. 2021. KG Embedding for Link Prediction. ACM TKDD. arXiv:2002.00819 · rossi2021-kg-embedding

## Knowledge graphs: added 2026-08-25

Curated to ten from a verified 28-item survey, weighted toward representation and current practice; the remainder are listed at the bottom. Knowledge graphs are one candidate representation, not a commitment.

32. Angles 2018. The Property Graph Database Model. AMW 2018, CEUR Vol-2100. What a property graph formally is; the model closest to a tree of pages with typed links · angles2018-property-graph-model
33. Hernandez, Hogan, Krotzsch 2015. Reifying RDF: What Works Well With Wikidata? SSWS at ISWC 2015. The four ways to represent qualified, non-binary facts, compared on real data · hernandez2015-reifying-rdf-wikidata
34. Cai et al. 2024. A Survey on Temporal Knowledge Graph. arXiv:2403.04782. Where facts-valid-for-an-interval lives; representation chapters, not the embedding chapters · cai2024-temporal-kg-survey
35. Rost et al. 2021. Bitemporal Property Graphs to Organize Evolving Systems. arXiv:2111.13499. Valid time and transaction time on every node and edge, so corrections never erase history · rost2021-bitemporal-property-graphs
36. Fowler 2021. Bitemporal History. martinfowler.com. The practitioner bridge to the same idea. HTML · fowler2021-bitemporal-history
37. Vrandecic, Krotzsch 2014. Wikidata. CACM 57(10). The largest deployed store of time-scoped, source-attributed, supersedable facts · vrandecic2014-wikidata
38. Zhong et al. 2024. A Comprehensive Survey on Automatic Knowledge Graph Construction. ACM CSUR 56(4). arXiv:2302.05019. The construction pipeline end to end · zhong2023-kg-construction-survey
39. Noy et al. 2019. Industry-scale Knowledge Graphs: Lessons and Challenges. CACM 62(8). How Google, Microsoft, Facebook, eBay and IBM actually run them. Free HTML at queue.acm.org/detail.cfm?id=3332266 · noy2019-industry-scale-kgs
40. Xu et al. 2024. RAG with Knowledge Graphs for Customer Service Question Answering. SIGIR 2024 industry track. arXiv:2404.17723. LinkedIn's deployed graph, directly on the help-desk use case · xu2024-kg-rag-customer-service
41. Balog, Kenter 2019. Personal Knowledge Graphs: A Research Agenda. ICTIR 2019. The academic niche closest to the existing system · balog2019-personal-kg-agenda

## Conversation mining and outcomes

42. Kecht et al. 2021. Event Log Construction from Customer Service Conversations. ICPM 2021 · kecht2021-event-log-nli
43. Gung et al. 2023. Intent Induction from Conversations, DSTC 11. SIGDIAL 2023. arXiv:2304.12982 · gung2023-dstc11-intent
44. De Raedt et al. 2023. IDAS: Intent Discovery with Abstractive Summarization. NLP4ConvAI at ACL 2023 · deraedt2023-idas
45. Wegmann et al. 2022. Same Author or Just Same Topic? RepL4NLP 2022. arXiv:2204.04907 · wegmann2022-style-content
46. Brynjolfsson, Li, Raymond 2025. Generative AI at Work. QJE 140(2). *library* · brynjolfsson2025-genai-at-work
47. Ouyang et al. 2026. ReasoningBank. ICLR 2026. arXiv:2509.25140 · ouyang2026-reasoningbank
48. Liu, Zhang, Choi 2025. User Feedback in Human-LLM Dialogues. EMNLP 2025. arXiv:2507.23158 · liu2025-user-feedback
49. Rezazadeh et al. 2025. Collaborative Memory. arXiv:2505.18279 · rezazadeh2025-collaborative-memory

## Shared state across sessions

50. Erman, Hayes-Roth, Lesser, Reddy 1980. The Hearsay-II Speech-Understanding System. ACM CSUR 12(2). *library* · erman1980-hearsay-ii
51. Hayes-Roth 1985. A Blackboard Architecture for Control. Artificial Intelligence 26(3). *library* · hayesroth1985-blackboard-control
52. Salemi et al. 2026. LLM-Based Multi-Agent Blackboard System. arXiv:2510.01285 · salemi2026-blackboard-llm
53. Pollertlam, Kornsuwannawit 2026. Beyond the Context Window. arXiv:2603.04814 · pollertlam2026-beyond-context-window

## Build references: added 2026-08-25 for the harness

Twenty-two sources surveyed and verified for the six gaps the harness build opened. These are stage references, consulted when building the stage they govern, not read-through material. Grouping matches the pipeline.

Contracts and cheap models: 54. Willard, Louf 2023. Efficient Guided Generation. arXiv:2307.09702 · willard2023-guided-generation / 55. Geng et al. 2023. Grammar-Constrained Decoding. EMNLP 2023 · geng2023-grammar-constrained / 56. Tam et al. 2024. Let Me Speak Freely? EMNLP 2024 Industry. arXiv:2408.02442 · tam2024-format-restrictions / 57. Chen, Zaharia, Zou 2023. FrugalGPT. arXiv:2305.05176 · chen2023-frugalgpt / 58. Ong et al. 2025. RouteLLM. ICLR 2025. arXiv:2406.18665 · ong2024-routellm / 59. Zhou et al. 2024. UniversalNER. ICLR 2024. arXiv:2308.03279 · zhou2024-universalner

Segmentation and extraction: 60. Hearst 1997. TextTiling. CL 23(1) · hearst1997-texttiling / 61. Koshorek et al. 2018. Text Segmentation as Supervised Learning. NAACL 2018 · koshorek2018-supervised-segmentation / 62. Xing, Carenini 2021. Dialogue Topic Segmentation. SIGDIAL 2021 · xing2021-dialogue-segmentation / 63. Niklaus et al. 2018. OpenIE Survey. COLING 2018 · niklaus2018-openie-survey / 64. Zhang, Soh 2024. Extract, Define, Canonicalize. EMNLP 2024 · zhang2024-edc-kg-construction / 65. Caufield et al. 2024. SPIRES. Bioinformatics 40(3) · caufield2024-spires

Judging and agreement: 66. Zheng et al. 2023. Judging LLM-as-a-Judge. NeurIPS 2023 · zheng2023-llm-as-judge / 67. Wang et al. 2023. LLMs are not Fair Evaluators. ACL 2024. arXiv:2305.17926 · wang2023-not-fair-evaluators / 68. Panickssery, Bowman, Feng 2024. Self-Preference in LLM Evaluators. NeurIPS 2024 · panickssery2024-self-preference / 69. Kamalloo et al. 2023. Evaluating Open-Domain QA. ACL 2023 · kamalloo2023-open-qa-eval / 70. Artstein, Poesio 2008. Inter-Coder Agreement. CL 34(4) · artstein2008-intercoder-agreement

Narrative ground truth and injection: 71. Kocisky et al. 2018. NarrativeQA. TACL · kocisky2017-narrativeqa / 72. Pang et al. 2022. QuALITY. NAACL 2022 · pang2021-quality / 73. Wang et al. 2024. NovelQA. arXiv:2403.12766 · wang2024-novelqa / 74. Liu et al. 2023. Lost in the Middle. TACL 2024. arXiv:2307.03172 · liu2023-lost-in-the-middle / 75. Jiang et al. 2023. LongLLMLingua. ACL 2024. arXiv:2310.06839 · jiang2023-longllmlingua

## Cut from the knowledge-graph survey, available on request

Named Graphs (Carroll et al., WWW 2005); RDF-star foundations (Hartig 2017); OWL 2 Profiles tutorial (Krotzsch 2012); the OneGraph vision paper (Lassila et al. 2023); LLM information-extraction survey; LLM-empowered KG construction survey (Bian 2025); entity-resolution overview (Christophides et al.); Open IE survey; Knowledge Vault (Dong et al. 2014); AutoKnow (Amazon, KDD 2020); GQL and SQL/PGQ pattern matching (SIGMOD 2023); a practitioner piece on why KG projects fail; the PKG ecosystem survey and PKG API tool paper; text-lifelog knowledge-base construction; LifeGraph; PIMO.
