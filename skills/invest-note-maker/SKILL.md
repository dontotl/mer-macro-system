---
name: invest-note-maker
description: Turn investment source material into searchable markdown research notes and 1-page trading memos. Use when the user provides a PDF, Telegram post, article link, screenshot text, broker report, company update, or thematic research and wants it converted into stock-analysis style notes, industry-report style notes, watchlist cards, or reusable markdown saved under invest/. Especially use for Korean stock research, sector notes, earnings/industry summaries, and repeatable note formatting.
---

# Invest Note Maker

## Overview

Convert raw investment material into two reusable outputs:
1. a **detailed searchable note** under `invest/`
2. a **1-page compressed memo** for quick trading or watchlist review

Prefer practical output over literary summary. Extract the investment thesis, identify what is factual vs. assumed, separate strong evidence from promotional language, and leave the user with something reusable later.

## Default output set

Unless the user asks otherwise, produce both:

1. **Detailed note**
   - Path pattern: `invest/YYYY-MM-DD-<slug>-note.md`
   - Purpose: long-form searchable archive

2. **1-page memo**
   - Path pattern: `invest/YYYY-MM-DD-<slug>-note-1page.md`
   - Purpose: fast review, trading lens, scenario framing

If the material is clearly sector-wide rather than company-specific, use an industry-oriented slug and title.

## Workflow

### 1. Ingest the source

Handle the source in the most reliable way available.

- **PDF**: extract text with a local tool first if direct read is unreadable
- **Telegram/public post URL**: fetch the page if accessible; if not accessible, ask for forwarded text or screenshot OCR input
- **Web article/report URL**: fetch readable text
- **Image/screenshot**: read visible text if available; otherwise ask for a cleaner image or pasted text
- **Forwarded chat text**: clean lightly, preserve key numbers and claims

Do not stop at “I can’t read this” if a better extraction route exists.

### 2. Classify the material

Decide what kind of note it is:

- **Stock analysis**: single company, ticker, target price, catalyst, earnings, valuation
- **Industry report**: supply/demand, policy, cycle, competitors, value chain
- **Mixed thesis**: company thesis built on industry backdrop
- **News/event note**: one-off catalyst, regulatory event, M&A, product launch, earnings preview/review

Use that classification to shape emphasis.

### 3. Pull out the real thesis

Extract these first:

- core thesis in one sentence
- 2-4 main drivers
- what must go right
- what could break the thesis
- whether the thesis is near-term, medium-term, or long-duration

Then capture supporting numbers.

### 4. Separate facts from assumptions

Mark the difference between:

- reported facts
- management/author claims
- estimates/projections
- policy-dependent or macro-dependent assumptions

If the source is enthusiastic or promotional, keep the note grounded.

### 5. Write the detailed note

Use this structure unless a different structure is clearly better:

```md
# <title>

- 작성일:
- 출처:
- 성격:
- 종목/산업:
- 태그:

## 한줄 요약

## 투자포인트 요약

## 산업 리포트형 정리

## 기업 분석 핵심

## 숫자로 보는 보고서 핵심

## 해석: 이 자료를 어떻게 읽을까

## 체크리스트

## 검색용 키워드

## 원문 성격 메모
```

Guidelines:
- Use Korean by default unless the user asked otherwise
- Preserve company names, tickers, important units, dates, and percentages
- Keep sections scannable with bullets
- Add your own judgment where useful, but do not blur it with the source author’s opinion

### 6. Write the 1-page memo

Use this structure by default:

```md
# <title> - 1페이지 투자 메모

- 작성일:
- 성격:
- 원문 참고:
- 태그:

## 투자 아이디어 한줄

## 지금 이 종목/산업을 보는 이유

## 핵심 숫자

## 이 자료의 본질

## Bull / Base / Bear 시나리오

## 매매 관점 체크포인트

## 한줄 판단
```

The 1-page memo should answer: “Why should I care, what matters most, and what must I monitor?”

### 7. Save where it will be searchable later

Default location: `invest/`

Use consistent filenames:
- `YYYY-MM-DD-company-or-theme-note.md`
- `YYYY-MM-DD-company-or-theme-note-1page.md`

Slug rules:
- lowercase English slug where possible
- keep it short and searchable
- prefer company English name or sector theme

Examples:
- `2026-04-01-posco-international-yig-note.md`
- `2026-04-01-korean-lng-industry-note.md`
- `2026-04-01-semiconductor-capex-cycle-note.md`

## Quality bar

A good note should make these clear:

1. **What is the thesis?**
2. **Why now?**
3. **What evidence supports it?**
4. **Which claims are still speculative?**
5. **What would you watch next?**

If those five are not clear, the note is not done.

## Tone and judgment

Prefer useful, buy-side-style interpretation over passive summary.

Good:
- “LNG is the most credible profit engine here.”
- “희토류는 실적보다 옵션 가치에 가깝다.”
- “이 숫자는 확인 필요하다.”

Avoid:
- repeating every paragraph of the source
- pretending uncertain projections are facts
- stuffing the note with decorative prose

## When the source is weak or inaccessible

If extraction fails or the source is incomplete:

- say exactly what was accessible
- preserve any metadata you do have
- ask for the smallest missing thing needed (pasted text, clearer image, forwarded message)
- if partially readable, still produce a partial note with a clear limitation section

## Reference files

Read these only when needed:
- `references/note-templates.md` for concrete output skeletons
- `references/evaluation-rubric.md` for how to separate thesis, evidence, and risk
