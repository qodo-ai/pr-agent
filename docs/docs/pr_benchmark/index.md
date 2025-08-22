# Qodo Merge Pull Request Benchmark

## Methodology

Qodo Merge PR Benchmark evaluates and compares the performance of Large Language Models (LLMs) in analyzing pull request code and providing meaningful code suggestions.
Our diverse dataset contains 400 pull requests from over 100 repositories, spanning multiple [programming languages](#programming-languages) to reflect real-world scenarios.

- For each pull request, we have pre-generated suggestions from eleven different top-performing models using the Qodo Merge `improve` tool. The prompt for response generation can be found [here](https://github.com/qodo-ai/pr-agent/blob/main/pr_agent/settings/code_suggestions/pr_code_suggestions_prompts_not_decoupled.toml). 

- To benchmark a model, we generate its suggestions for the same pull requests and ask a high-performing judge model to **rank** the new model's output against the pre-generated baseline suggestions. We utilize OpenAI's `o3` model as the judge, though other models have yielded consistent results. The prompt for this ranking judgment is available [here](https://github.com/Codium-ai/pr-agent-settings/tree/main/benchmark).

- We aggregate ranking outcomes across all pull requests, calculating performance metrics for the evaluated model. 

- We also analyze the qualitative feedback from the judge to identify the model's comparative strengths and weaknesses against the established baselines.
This approach provides not just a quantitative score but also a detailed analysis of each model's strengths and weaknesses.

A list of the models used for generating the baseline suggestions, and example results, can be found in the [Appendix](#appendix-example-results).

[//]: # (Note that this benchmark focuses on quality: the ability of an LLM to process complex pull request with multiple files and nuanced task to produce high-quality code suggestions.)

[//]: # (Other factors like speed, cost, and availability, while also relevant for model selection, are outside this benchmark's scope. We do specify the thinking budget used by each model, which can be a factor in the model's performance.)

[//]: # ()

## PR Benchmark Results

<table>
  <thead>
    <tr>
      <th style="text-align:left;">Model Name</th>
      <th style="text-align:left;">Version (Date)</th>
      <th style="text-align:left;">Thinking budget tokens</th>
      <th style="text-align:center;">Score</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="text-align:left;">GPT-5</td>
      <td style="text-align:left;">2025-08-07</td>
      <td style="text-align:left;">medium</td>
      <td style="text-align:center;"><b>72.2</b></td>
    </tr>
    <tr>
      <td style="text-align:left;">GPT-5</td>
      <td style="text-align:left;">2025-08-07</td>
      <td style="text-align:left;">low</td>
      <td style="text-align:center;"><b>67.8</b></td>
    </tr>
    <tr>
      <td style="text-align:left;">GPT-5</td>
      <td style="text-align:left;">2025-08-07</td>
      <td style="text-align:left;">minimal</td>
      <td style="text-align:center;"><b>62.7</b></td>
    </tr>
    <tr>
      <td style="text-align:left;">o3</td>
      <td style="text-align:left;">2025-04-16</td>
      <td style="text-align:left;">'medium' (<a href="https://ai.google.dev/gemini-api/docs/openai">8000</a>)</td>
      <td style="text-align:center;"><b>62.5</b></td>
    </tr>
    <tr>
      <td style="text-align:left;">o4-mini</td>
      <td style="text-align:left;">2025-04-16</td>
      <td style="text-align:left;">'medium' (<a href="https://ai.google.dev/gemini-api/docs/openai">8000</a>)</td>
      <td style="text-align:center;"><b>57.7</b></td>
    </tr>
    <tr>
      <td style="text-align:left;">Gemini-2.5-pro</td>
      <td style="text-align:left;">2025-06-05</td>
      <td style="text-align:left;">4096</td>
      <td style="text-align:center;"><b>56.3</b></td>
    </tr>
    <tr>
      <td style="text-align:left;">Gemini-2.5-pro</td>
      <td style="text-align:left;">2025-06-05</td>
      <td style="text-align:left;">1024</td>
      <td style="text-align:center;"><b>44.3</b></td>
    </tr>
    <tr>
      <td style="text-align:left;">Grok-4</td>
      <td style="text-align:left;">2025-07-09</td>
      <td style="text-align:left;">unknown</td>
      <td style="text-align:center;"><b>41.7</b></td>
    </tr>
    <tr>
      <td style="text-align:left;">Claude-4-sonnet</td>
      <td style="text-align:left;">2025-05-14</td>
      <td style="text-align:left;">4096</td>
      <td style="text-align:center;"><b>39.7</b></td>
    </tr>
    <tr>
      <td style="text-align:left;">Claude-4-sonnet</td>
      <td style="text-align:left;">2025-05-14</td>
      <td style="text-align:left;"></td>
      <td style="text-align:center;"><b>39.0</b></td>
    </tr>
    <tr>
      <td style="text-align:left;">Codex-mini</td>
      <td style="text-align:left;">2025-06-20</td>
      <td style="text-align:left;"><a href="https://platform.openai.com/docs/models/codex-mini-latest">unknown</a></td>
      <td style="text-align:center;"><b>37.2</b></td>
    </tr>
    <tr>
      <td style="text-align:left;">Gemini-2.5-flash</td>
      <td style="text-align:left;">2025-04-17</td>
      <td style="text-align:left;"></td>
      <td style="text-align:center;"><b>33.5</b></td>
    </tr>
    <tr>
      <td style="text-align:left;">Claude-4-opus-20250514</td>
      <td style="text-align:left;">2025-05-14</td>
      <td style="text-align:left;"></td>
      <td style="text-align:center;"><b>32.8</b></td>
    </tr>
    <tr>
      <td style="text-align:left;">Claude-3.7-sonnet</td>
      <td style="text-align:left;">2025-02-19</td>
      <td style="text-align:left;"></td>
      <td style="text-align:center;"><b>32.4</b></td>
    </tr>
    <tr>
      <td style="text-align:left;">GPT-4.1</td>
      <td style="text-align:left;">2025-04-14</td>
      <td style="text-align:left;"></td>
      <td style="text-align:center;"><b>26.5</b></td>
    </tr>
  </tbody>
</table>

## Results Analysis

### O3

Final score: **62.5**

strengths:

- **High precision & compliance:** Generally respects task rules (limits, “added lines” scope, YAML schema) and avoids false-positive advice, often returning an empty list when appropriate.  
- **Clear, actionable output:** Suggestions are concise, well-explained and include correct before/after patches, so reviewers can apply them directly.  
- **Good critical-bug detection rate:** Frequently spots compile-breakers or obvious runtime faults (nil / NPE, overflow, race, wrong selector, etc.), putting it at least on par with many peers.  
- **Consistent formatting:** Produces syntactically valid YAML with correct labels, making automated consumption easy.

weaknesses:

- **Narrow coverage:** Tends to stop after 1-2 issues; regularly misses additional critical defects that better answers catch, so it is seldom the top-ranked review.  
- **Occasional inaccuracies:** A few replies introduce new bugs, give partial/duplicate fixes, or (rarely) violate rules (e.g., import suggestions), hurting trust.  
- **Conservative bias:** Prefers silence over risk; while this keeps precision high, it lowers recall and overall usefulness on larger diffs.  
- **Little added insight:** Rarely offers broader context, optimisations or holistic improvements, causing it to rank only mid-tier in many comparisons.

### O4 Mini ('medium' thinking tokens)

Final score: **57.7**

strengths:

- **Good rule adherence:** Most answers respect the “new-lines only”, 3-suggestion, and YAML-schema limits, and frequently choose the safe empty list when the diff truly adds no critical bug.
- **Clear, minimal patches:** When the model does spot a defect it usually supplies terse, valid before/after snippets and short, targeted explanations, making fixes easy to read and apply.
- **Language & domain breadth:** Demonstrates competence across many ecosystems (C/C++, Java, TS/JS, Go, Rust, Python, Bash, Markdown, YAML, SQL, CSS, translation files, etc.) and can detect both compile-time and runtime mistakes.
- **Often competitive:** In a sizeable minority of cases the model ties for best or near-best answer, occasionally being the only response to catch a subtle crash or build blocker.

weaknesses:

- **High miss rate:** A large share of examples show the model returning an empty list or only minor advice while other reviewers catch clear, high-impact bugs—indicative of weak defect-detection recall.
- **False or harmful fixes:** Several answers introduce new compilation errors, propose out-of-scope changes, or violate explicit rules (e.g., adding imports, version bumps, touching untouched lines), reducing trustworthiness.
- **Shallow coverage:** Even when it identifies one real issue it often stops there, missing additional critical problems found by stronger peers; breadth and depth are inconsistent.

### Gemini-2.5 Pro (4096 thinking tokens)

Final score: **56.3**

strengths:

- **High formatting compliance:** The model almost always produces valid YAML, respects the three-suggestion limit, and supplies clear before/after code snippets and short rationales.
- **Good “first-bug” detection:** It frequently notices the single most obvious regression (crash, compile error, nil/NPE risk, wrong path, etc.) and gives a minimal, correct patch—often judged “on-par” with other solid answers.
- **Clear, concise writing:** Explanations are brief yet understandable for reviewers; fixes are scoped to the changed lines and rarely include extraneous context.
- **Low rate of harmful fixes:** Truly dangerous or build-breaking advice is rare; most mistakes are omissions rather than wrong code.

weaknesses:

- **Limited breadth of review:** The model regularly stops after the first or second issue, missing additional critical problems that stronger answers surface, so it is often out-ranked by more comprehensive peers.
- **Occasional guideline violations:** A noticeable minority of answers touch unchanged lines, exceed the 3-item cap, suggest adding imports, or drop the required YAML wrapper, leading to automatic downgrades.
- **False positives / speculative fixes:** In several cases it flags non-issues (style, performance, redundant code) or supplies debatable “improvements”, lowering precision and sometimes breaching the “critical bugs only” rule.
- **Inconsistent error coverage:** For certain domains (build scripts, schema files, test code) it either returns an empty list when real regressions exist or proposes cosmetic edits, indicating gaps in specialised knowledge.

### Claude-4 Sonnet (4096 thinking tokens)

Final score: **39.7**

strengths:

- **High guideline & format compliance:** Almost always returns valid YAML, keeps ≤ 3 suggestions, avoids forbidden import/boiler-plate changes and provides clear before/after snippets.
- **Good pinpoint accuracy on single issues:** Frequently spots at least one real critical bug and proposes a concise, technically correct fix that compiles/runs.
- **Clarity & brevity of patches:** Explanations are short, actionable, and focused on changed lines, making the advice easy for reviewers to apply.

weaknesses:

- **Low coverage / recall:** Regularly surfaces only one minor issue (or none) while missing other, often more severe, problems caught by peer models.
- **High “empty-list” rate:** In many diffs the model returns no suggestions even when clear critical bugs exist, offering zero reviewer value.
- **Occasional incorrect or harmful fixes:** A non-trivial number of suggestions are speculative, contradict code intent, or would break compilation/runtime; sometimes duplicates or contradicts itself.
- **Inconsistent severity labelling & duplication:** Repeats the same point in multiple slots, marks cosmetic edits as “critical”, or leaves `improved_code` identical to original.


### Claude-4 Sonnet

Final score: **39.0**

strengths:

- **Consistently well-formatted & rule-compliant output:** Almost every answer follows the required YAML schema, keeps within the 3-suggestion limit, and returns an empty list when no issues are found, showing good instruction following.

- **Actionable, code-level patches:** When it does spot a defect the model usually supplies clear, minimal diffs or replacement snippets that compile / run, making the fix easy to apply.

- **Decent hit-rate on “obvious” bugs:** The model reliably catches the most blatant syntax errors, null-checks, enum / cast problems, and other first-order issues, so it often ties or slightly beats weaker baseline replies.

weaknesses:

- **Shallow coverage:** It frequently stops after one easy bug and overlooks additional, equally-critical problems that stronger reviewers find, leaving significant risks unaddressed.

- **False positives & harmful fixes:** In a noticeable minority of cases it misdiagnoses code, suggests changes that break compilation or behaviour, or flags non-issues, sometimes making its output worse than doing nothing.

- **Drifts into non-critical or out-of-scope advice:** The model regularly proposes style tweaks, documentation edits, or changes to unchanged lines, violating the “critical new-code only” requirement.


### Gemini-2.5 Flash

strengths:

- **High precision / low false-positive rate:** The model often stays silent or gives a single, well-justified fix, so when it does speak the suggestion is usually correct and seldom touches unchanged lines, keeping guideline compliance high.  
- **Good guideline awareness:** YAML structure is consistently valid; suggestions rarely exceed the 3-item limit and generally restrict themselves to newly-added lines.  
- **Clear, concise patches:** When a defect is found, the model produces short rationales and tidy “improved_code” blocks that reviewers can apply directly.  
- **Risk-averse behaviour pays off in “no-bug” PRs:** In examples where the diff truly contained no critical issue, the model’s empty output ranked above peers that offered speculative or stylistic advice.

weaknesses:

- **Very low recall / shallow coverage:** In a large majority of cases it gives 0-1 suggestions and misses other evident, critical bugs highlighted by peer models, leading to inferior rankings.  
- **Occasional incorrect or harmful fixes:** A noticeable subset of answers propose changes that break functionality or misunderstand the code (e.g. bad constant, wrong header logic, speculative rollbacks).  
- **Non-actionable placeholders:** Some “improved_code” sections contain comments or “…” rather than real patches, reducing practical value.  

### GPT-4.1

Final score: **26.5**

strengths:

- **Consistent format & guideline obedience:** Output is almost always valid YAML, within the 3-suggestion limit, and rarely touches lines not prefixed with “+”.  
- **Low false-positive rate:** When no real defect exists, the model correctly returns an empty list instead of inventing speculative fixes, avoiding the “noise” many baseline answers add.  
- **Clear, concise patches when it does act:** In the minority of cases where it detects a bug (e.g., ex-13, 46, 212), the fix is usually correct, minimal, and easy to apply.

weaknesses:

- **Very low recall / coverage:** In a large majority of examples it outputs an empty list or only 1 trivial suggestion while obvious critical issues remain unfixed; it systematically misses circular bugs, null-checks, schema errors, etc.  
- **Shallow analysis:** Even when it finds one problem it seldom looks deeper, so more severe or additional bugs in the same diff are left unaddressed.  
- **Occasional technical inaccuracies:** A noticeable subset of suggestions are wrong (mis-ordered assertions, harmful Bash `set` change, false dangling-reference claims) or carry metadata errors (mis-labeling files as “python”).  
- **Repetitive / derivative fixes:** Many outputs duplicate earlier simplistic ideas (e.g., single null-check) without new insight, showing limited reasoning breadth.

### OpenAI codex-mini

final score: **37.2**

strengths:

- **Can spot high-impact defects:** When it “locks on”, codex-mini often identifies the main runtime or security regression (e.g., race-conditions, logic inversions, blocking I/O, resource leaks) and proposes a minimal, direct patch that compiles and respects neighbouring style.
- **Produces concise, scoped fixes:** Valid answers usually stay within the allowed 3-suggestion limit, reference only the added lines, and contain clear before/after snippets that reviewers can apply verbatim.
- **Occasional broad coverage:** In a minority of cases the model catches multiple independent issues (logic + tests + docs) and outperforms every baseline answer, showing good contextual understanding of heterogeneous diffs.

weaknesses:

- **Output instability / format errors:** A very large share of responses are unusable—plain refusals, shell commands, or malformed/empty YAML—indicating brittle adherence to the required schema and tanking overall usefulness.
- **Critical-miss rate:** Even when the format is correct the model frequently overlooks the single most serious bug the diff introduces, instead focusing on stylistic nits or speculative refactors.
- **Introduces new problems:** Several suggestions add unsupported APIs, undeclared variables, wrong types, or break compilation, hurting trust in the recommendations.
- **Rule violations:** It often edits lines outside the diff, exceeds the 3-suggestion cap, or labels cosmetic tweaks as “critical”, showing inconsistent guideline compliance.

### Claude-4 Opus

final score: **32.8**

strengths:

- **Format & rule adherence:** Almost always returns valid YAML, stays within the ≤3-suggestion limit, and usually restricts edits to newly-added lines, so its output is easy to apply automatically.
- **Concise, focused patches:** When it does find a real bug it gives short, well-scoped explanations plus minimal diff snippets, often outperforming verbose baselines in clarity.
- **Able to catch subtle edge-cases:** In several examples it detected overflow, race-condition or enum-mismatch issues that many other models missed, showing solid code‐analysis capability.

weaknesses:

- **Low recall / narrow coverage:** In a large share of the 399 examples the model produced an empty list or only one minor tip while more serious defects were present, causing it to be rated inferior to most baselines.
- **Frequent incorrect or no-op fixes:** It sometimes supplies identical “before/after” code, flags non-issues, or suggests changes that would break compilation or logic, reducing reviewer trust.
- **Shaky guideline consistency:** Although generally compliant, it still occasionally violates rules (touches unchanged lines, offers stylistic advice, adds imports) and duplicates suggestions, indicating unstable internal checks.

### Grok-4

final score: **32.8**

strengths:

- **Focused and concise fixes:** When the model does detect a problem it usually proposes a minimal, well-scoped patch that compiles and directly addresses the defect without unnecessary noise.  
- **Good critical-bug instinct:** It often prioritises show-stoppers (compile failures, crashes, security issues) over cosmetic matters and occasionally spots subtle issues that all other reviewers miss.  
- **Clear explanations & snippets:** Explanations are short, readable and paired with ready-to-paste code, making the advice easy to apply.  

weaknesses:

- **High miss rate:** In a large fraction of examples the model returned an empty list or covered only one minor issue while overlooking more serious newly-introduced bugs.  
- **Inconsistent accuracy:** A noticeable subset of answers contain wrong or even harmful fixes (e.g., removing valid flags, creating compile errors, re-introducing bugs).  
- **Limited breadth:** Even when it finds a real defect it rarely reports additional related problems that peers catch, leading to partial reviews.  
- **Occasional guideline slips:** A few replies modify unchanged lines, suggest new imports, or duplicate suggestions, showing imperfect compliance with instructions.

## Appendix - Example Results

Some examples of benchmarked PRs and their results:

- [Example 1](https://www.qodo.ai/images/qodo_merge_benchmark/example_results1.html)
- [Example 2](https://www.qodo.ai/images/qodo_merge_benchmark/example_results2.html)
- [Example 3](https://www.qodo.ai/images/qodo_merge_benchmark/example_results3.html)
- [Example 4](https://www.qodo.ai/images/qodo_merge_benchmark/example_results4.html)

### Models Used for Benchmarking

The following models were used for generating the benchmark baseline:

```markdown
(1) anthropic_sonnet_3.7_v1:0

(2) claude-4-opus-20250514

(3) claude-4-sonnet-20250514

(4) claude-4-sonnet-20250514_thinking_2048

(5) gemini-2.5-flash-preview-04-17

(6) gemini-2.5-pro-preview-05-06

(7) gemini-2.5-pro-preview-06-05_1024

(8) gemini-2.5-pro-preview-06-05_4096

(9) gpt-4.1

(10) o3

(11) o4-mini_medium
```

### Programming Languages

The PR benchmark dataset includes pull requests containing code in the following programming languages:

```markdown
["Python", "JavaScript", "TypeScript", "Java", "CSharp", "PHP", "C++", "Go", "Rust", "Swift", "Kotlin", "Ruby", "Dart", "Scala"
```

Pull requests may also include non-code files such as `YAML`, `JSON`, `Markdown`, `Dockerfile` ,`Shell`, etc. 
The benchmarked models should also analyze these files, as they commonly appear in real-world pull requests.


