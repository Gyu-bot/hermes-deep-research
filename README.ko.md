[English](README.md)

# Hermes Deep Research

검색 한 번으로는 답이 나오지 않는 질문을 위한 Hermes 스킬입니다.

막연한 요청을 조사 가능한 질문으로 좁히고, 정해진 단계로 나눠 조사하고, 검색 결과 요약 대신 원문을 직접 열어 확인하고, 반대되는 근거를 일부러 찾아보고, 진행 상황을 파일에 저장하면서, 별도의 출처 목록이 딸린 상세 Markdown 보고서를 만듭니다.

모든 과정은 Hermes 표준 도구(웹·브라우저, 파일, 터미널, 보조 에이전트)만으로 돌아갑니다. Insane Search는 필요 없고, 상주 프로세스도 외부 서비스도 쓰지 않습니다. 문서나 PDF는 별개의 결과물이며, 명시적으로 요청했을 때만 만듭니다.

| | |
| --- | --- |
| **이럴 때** | 여러 출처를 봐야 할 때, 주장이 엇갈릴 때, 실제 사용 경험·커뮤니티 반응이 필요할 때, 오래 걸리는 무인 조사 |
| **이럴 땐 아님** | 단순 검색, 규제·감사용 증거 자료 |
| **기본 결과물** | 실행 디렉터리 안의 `report.md` + `sources.json` |
| **필요 조건** | 웹·파일·터미널 도구를 쓸 수 있는 Hermes, Python 3.10 이상(표준 라이브러리만) |

## 설치

먼저 내용을 확인한 뒤, 검증된 명령을 그대로 사용합니다.

```bash
hermes skills inspect https://raw.githubusercontent.com/Gyu-bot/hermes-deep-research/main/SKILL.md
hermes skills install https://raw.githubusercontent.com/Gyu-bot/hermes-deep-research/main/SKILL.md
```

HTTPS로 직접 클론하는 방법:

```bash
mkdir -p ~/.hermes/skills/research
git clone https://github.com/Gyu-bot/hermes-deep-research.git \
  ~/.hermes/skills/research/hermes-deep-research
```

설치 후 `SKILL.md`를 읽어 보세요. 실제 조사 실행 파일은 설치된 스킬 디렉터리 밖에 저장합니다. 스킬 패키지와 조사 결과물을 분리하는 것은 의도된 설계입니다.

Hermes cron은 무인 조사를 할 때만 필요합니다. Bookforge와 Humanize Korean은 선택 사항이며 자동으로 설치되지 않습니다.

<details>
<summary>설치 에이전트 체크리스트</summary>

- 설치 전에 `SKILL.md`와 저장소 내용을 확인합니다.
- Hermes Deep Research 기본 스킬만 설치합니다.
- 보조 에이전트, 웹·브라우저, 파일, 터미널에 대한 Hermes 표준 지원을 확인합니다. Hermes cron은 무인 조사를 요청했을 때만 확인합니다.
- Bookforge나 Humanize Korean은 요청한 결과물에 필요할 때만 설치하고, 먼저 해당 프로젝트의 최신 안내와 호환성을 확인합니다.
- 관련 없는 도구를 설치하거나 자격 증명, 공급자, 다른 설정을 바꾸지 않습니다.
- [개발](#개발)의 테스트와 임시 `init` → `validate` → `status` 점검을 실행합니다.

설치 에이전트에게 전달할 프롬프트:

```text
먼저 이 저장소와 SKILL.md를 확인하세요. Hermes Deep Research 기본 스킬만
설치하고 Hermes 표준 도구를 확인하세요. 포함된 표준 라이브러리 테스트와 임시
init/validate/status 실행 검사를 하세요. 자격 증명을 바꾸거나 관련 없는
도구를 설치하지 마세요. 요청한 결과물에 필요할 때만 선택 기능을 설치하고,
먼저 해당 프로젝트의 최신 안내와 호환성을 확인하세요.
```

</details>

## 사용법

조건이 이미 담긴 요청은 곧바로 조사를 시작합니다.

```text
한국의 소규모 수출업체가 AI 번역 도구를 도입하고 있는지 deep 모드로 조사해 줘.
정책 담당자가 읽을 보고서야. 한국어와 영어 출처, 2024년 이후의 최신 근거,
사용자 경험, 공급업체 주장과 독립적인 근거가 다른 지점을 포함해 줘.
Markdown 보고서면 충분하고 PDF는 만들지 마.
```

주제만 던지면 짧은 확인 질문이 먼저 옵니다.

```text
혼잡통행료를 조사해 줘.
```

어느 도시와 시기를 다룰지, 결과를 어디에 쓸지, 무엇을 꼭 담아야 하는지 물을 수 있습니다. 질문은 최대 세 개이고, 답에 따라 조사 방향이 실제로 달라질 때만 묻습니다.

다른 형태의 요청:

```text
서울 혼잡통행료의 핵심 찬반 논거를 quick 모드로 조사해 줘.
자세한 Markdown 보고서와 출처 목록을 만들어 줘.
```

```text
섬 전력망용 장주기 에너지 저장을 exhaustive 모드로 조사해 줘. 중요한 빈틈에
실제로 조사할 방법이 있을 때만 계속하고, 정해 둔 한도에 도달했는데 중요한 빈틈이
남으면 partial로 표시해 줘.
```

```text
Hermes cron으로 이 조사를 무인 deep 모드로 실행해 줘. 각 단계를 고유한 실행
디렉터리에 저장하고, 종합이 끝나면 completed 또는 partial Markdown 보고서를
전달해 줘.
```

```text
이 주제를 deep 모드로 조사해 줘. Markdown 보고서가 문서로 낼 준비가 됐는지 확인하고,
파일이 바뀌지 않았는지 SHA-256으로 검사한 뒤 최종 PDF도 만들어 줘. Markdown 보고서와
출처 파일도 함께 보존해 줘.
```

## 결과물

실행마다 고유한 디렉터리를 하나씩 쓰며, 보통 `~/.hermes/research/hermes-deep-research/` 아래에 만듭니다. 다른 실행의 디렉터리를 재사용하지 않습니다.

```text
<run-dir>/
├── state.json     # 질문, 모드, 조사 축, 웨이브 이력, 한계, 다음 할 일
├── sources.json   # 출처 목록: 주제, 메모, 사용 방식, 한계
├── notes/         # 완료된 보조 에이전트 조사 노트
└── report.md      # 최종 Markdown 보고서
```

`report.md`가 핵심 결과물입니다. 앞부분 요약, 조사 범위와 방법, 주제별 본문, 일치하는 내용과 충돌하는 내용 및 그 이유, 사례와 맥락, 근거가 탄탄한 부분과 제한적인 부분, 불확실성과 한계, 결론, 그리고 선별한 주요 출처 목록으로 구성됩니다. 앞부분 요약은 본문을 요약할 뿐 본문을 대신하지 않습니다.

`sources.json`은 출처와 보고서를 잇는 지도입니다. 쓸 만한 출처마다 무엇을 다루는지, 어떻게 썼는지, 어디부터는 신뢰하기 어려운지를 기록합니다. 그래서 본문에 문장 단위 각주를 반드시 달 필요가 없습니다.

조사가 충분히 수렴하면 `completed`, 한도에 도달했는데 중요한 빈틈이 남아 있으면 `partial`로 끝납니다. 쓸모 있는 미완성 결과는 `failed`가 아니라 `partial`이며, 남은 빈틈을 보고서에 반드시 밝혀야 합니다.

## 조사 진행 방식

1. **질문의 범위를 정합니다.** 조사 목적과 활용처, 범위와 제외 대상, 최신성 요구, 반드시 다룰 주제, 좋은 결과의 기준을 정리합니다. 독자가 읽을 보고서인지 다른 작업에 넣을 내부 메모인지도 이때 정하고, 문서나 PDF를 명시적으로 요청했는지는 따로 기록합니다. 딥 리서치를 요청한 것이 PDF를 요청한 것은 아닙니다.
2. **조사 축으로 나눕니다.** 합쳤을 때 목적을 모두 덮는 몇 개의 축을 정하고, 축마다 답해야 할 질문, 쓸 만한 검색어 갈래와 언어, 최신성 요구, 어디까지 다뤄야 충분한지, 어떤 반대 주장을 찾아볼지를 적어 둡니다. 반대 근거를 찾는 일은 별도 담당이 아니라 각 축 안에 포함됩니다.
3. **웨이브 단위로 조사합니다.** 웨이브는 검색 한 번이나 도구 호출 한 번이 아니라 조사 단계 하나입니다. 1단계는 여러 언어와 출처 유형에 걸쳐 넓게 훑습니다. 2단계는 원문, 출처 간 독립성, 최신성, 반대 근거를 확인합니다. 3단계는 충돌하는 주장과 그 조건, 실제 경험, 예외 사례를 파고듭니다. 4단계는 남은 빈틈을 좁혀서 메웁니다. `quick`은 이 기능들을 한 웨이브에 압축하고, `exhaustive`는 중요한 빈틈이 남았을 때만 최대 8단계까지 늘립니다.
4. **단계마다 저장합니다.** 노트, 출처, 진행 수치, 엇갈리는 주장, 새로 생긴 단서, 한계, 그리고 구체적인 다음 할 일을 다음 작업을 시작하기 전에 파일로 남깁니다. 대화 기록이 없는 새 세션이 이어받아도 계속할 수 있게 하기 위해서입니다.
5. **멈출 시점을 판단합니다.** 중요한 빈틈에 실제로 조사할 방법이 있고 예산이 남아 있는 동안에는 계속합니다. 새 검색이 이미 아는 내용만 반복하기 시작하면 멈춥니다. 최대 웨이브에서 수렴해도 완료로 봅니다.
6. **보고서를 씁니다.** 결과 종합, 출처 정리, 충돌 검토, 확신 수준 표현, `completed`/`partial` 판단이 모두 끝난 뒤에야 문장 다듬기를 하고, 문서 제작은 그보다도 훨씬 뒤입니다.

검색 횟수와 출처 개수는 진행 상황을 보는 참고 수치일 뿐 완료 조건이 아닙니다. 질문에 제대로 답했는지, 엇갈리는 주장을 설명했는지, 아직 불확실한 부분을 솔직히 밝혔는지가 기준입니다.

## 조사 모드

- **`quick`** — 단순 검색보다는 깊어야 하지만 한 단계로 끝낼 수 있는 질문.
- **`deep`** — 여러 단계가 필요한 일반적인 선택.
- **`exhaustive`** — 중요한 빈틈이 남아 있고 추가 조사가 실제로 도움이 될 때 단계를 더 허용.

아래 수치는 넘지 않도록 정한 상한이며, 채워야 할 목표도 품질의 증거도 아닙니다. 충분히 조사했다면 훨씬 일찍 끝낼 수 있습니다.

| 모드 | 전체 예산 | 최대 웨이브 | 축당 검색 | 축당 원문 확인 |
| --- | ---: | ---: | ---: | ---: |
| `quick` | 1,800초 | 1 | 8 | 8 |
| `deep` | 10,800초 | 4 | 20 | 20 |
| `exhaustive` | 21,600초 | 8 | 40 | 40 |

전체 예산의 최소 20%는 결과를 합치고, 출처를 다시 확인하고, 충돌을 검토하고, 보고서를 쓰는 데 남겨 둡니다. 중요한 빈틈을 메우기 위해 전체 예산 안에서 배분을 조정할 수는 있지만, 무엇을 왜 바꿨는지 `planning.budget_reallocations`에 기록해야 합니다.

## 역할 분담

**메인 에이전트**가 실행 전체를 책임집니다. 축과 웨이브를 계획하고, 실행 파일을 관리하고, 중요하거나 논쟁적인 원문은 직접 열어 확인하고, 같은 자료를 옮긴 출처들을 하나로 묶고, 충돌을 정리하고, `completed`/`partial`을 판단하고, 보고서를 씁니다.

**보조 에이전트**는 범위가 분명한 조사 갈래를 하나씩 맡아 [조사 노트 템플릿](templates/research-note.md) 형식의 Markdown 노트를 돌려줍니다. 병렬로 실행되지만, 공유 실행 디렉터리에 직접 쓰지 않고, 조사 완료 여부를 판단하지 않으며, 메인 에이전트의 원문 확인을 대신하지도 않습니다. 보조 에이전트의 요약은 그 자체로 근거가 되지 않습니다.

조사 갈래는 중첩되지 않고 평평하게 나눕니다. 하나의 축을 언어, 출처 유형, 반대 관점으로 나눌 수는 있지만, 나눈다고 해서 그 축의 상한이 늘어나지는 않습니다. 각 갈래의 검색과 원문 확인 횟수는 같은 축 수치로 합산됩니다.

## 저장과 재시작

실행 디렉터리 자체가 저장 장치입니다. Hermes Gateway가 멈춰도 파일은 남지만, 실행 중이던 보조 에이전트와 모델 호출은 남지 않습니다. 재시작 후에는 노트가 저장되지 않은 갈래를 미완료로 보고 다시 실행하며, 중단된 호출이 이어졌다고 말하지 않습니다. 노트는 저장됐는데 상태 반영이 중단됐다면 다시 조사하지 않고 그 노트를 반영합니다.

Gateway가 내려가 있는 동안에는 아무 일도 진행되지 않습니다. 저장된 cron 일정은 Gateway가 돌아온 뒤 다시 실행되며, 파일을 읽고 그 지점부터 이어 갑니다.

무인 조사에는 Hermes cron을 그대로 씁니다. 감시 프로세스, 데몬, 워커 러너, 자체 스케줄러를 만들지 않고, 범위가 정해진 자체 완결형 반복 작업 하나만 등록합니다. 각 실행(tick)은 정해진 작업 하나를 하고, 결과물을 쓰고, 상태를 저장한 뒤 `[SILENT]`를 반환합니다. 보고서를 최종 상태로 만든 첫 실행만 결과를 원래 대화로 전달합니다. tick이 자기 cron 작업을 수정하는 일은 없습니다. 자세한 방식은 [references/unattended-research.md](references/unattended-research.md)에 있습니다.

## 선택 기능

둘 다 선택 사항이고 자동으로 설치되지 않으며, 쓰기 전에 해당 프로젝트의 최신 안내를 확인해야 합니다.

### Bookforge — 문서나 PDF를 요청했을 때

[Bookforge](https://github.com/gongnyang/bookforge)는 최종 PDF를 만들며, 두 단계의 관문을 통과한 뒤에만 실행합니다. 먼저 문서화 준비 관문입니다. 승인된 보고서를 `report.pre-document.md`로 보존하고, 내용을 더하지 않는 편집만으로 `report.document-candidate.md`를 만든 뒤, 메인 에이전트가 `report.document-readiness-gate.md`에 `PASS`/`FAIL` 판단을 직접 기록합니다. 읽기 좋은지는 자동화가 판단하지 않습니다. 그다음 `scripts/document_gate.py pass`가 승인된 파일을 `report.document-ready.md`로 복사하고 SHA-256으로 묶습니다. Bookforge에 넘기기 직전에 `document_gate.py verify`가 성공해야 하며, 실패하면 렌더링을 진행하지 않습니다.

렌더링을 별도 프로젝트로 분리해 두면 조사와 편집·조판이 섞이지 않고, 이 스킬이 다른 저장소에 의존하지 않아도 됩니다. Bookforge를 쓸 수 없다면 검증된 Markdown 결과물을 전달하고, PDF를 만들었다고 말하지 않습니다. 자세한 내용은 [references/report-documentation.md](references/report-documentation.md)에 있습니다.

### Humanize Korean — 한국어 문장 다듬기

[Humanize Korean](https://github.com/epoko77-ai/im-not-ai)은 한국어 독자용 보고서에서 AI 티가 나는 문장, 번역투, 기계적인 리듬을 걷어냅니다. 원본이 아니라 복사본에서 실행하며, 조사 상태가 이미 확정된 뒤에만 씁니다. 문장을 다듬는 일이 근거를 만들거나 조사 상태를 바꿔서는 안 되기 때문입니다.

편집 결과는 검증되지 않은 후보로 취급합니다. `report.pre-polish.md`와 비교해 사실, 의미, 확신 수준, 범위, 조건, 충돌하는 내용, 한계, 숫자, 날짜, 이름, 인용, 링크, 구조가 바뀌었다면 되돌리거나 수정합니다. 검증할 수 없으면 편집 전 보고서를 그대로 전달합니다.

## 저장소 구조

```text
hermes-deep-research/
├── SKILL.md                            # Hermes가 따르는 동작 규칙
├── references/
│   ├── source-review.md                # 목적에 맞는 출처 평가 기준
│   ├── unattended-research.md          # Hermes cron 사용 방식
│   ├── report-documentation.md         # 2단계 문서화 절차
│   └── LICENSE.md
├── scripts/
│   ├── research_state.py               # 실행 생성 / 조회 / 검증
│   └── document_gate.py                # 문서화 관문 기록 / 검증
├── templates/
│   ├── research-note.md                # 보조 에이전트 노트 형식
│   └── report.md                       # 최종 보고서 구조
└── tests/
```

동작 규칙의 기준은 [SKILL.md](SKILL.md)이고, 이 README는 그 안내서입니다.

## 개발

스크립트와 테스트는 Python 3.10 이상과 표준 라이브러리만 사용합니다. 설치할 의존성이 없습니다.

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/*.py tests/*.py

smoke_root="$(mktemp -d)"
trap 'rm -rf "$smoke_root"' EXIT
python3 scripts/research_state.py init "$smoke_root/run" \
  --query "Smoke-test question" --mode quick --axis "Evidence"
python3 scripts/research_state.py validate "$smoke_root/run"
python3 scripts/research_state.py status "$smoke_root/run"
```

`research_state.py`는 실행을 만들고 형식을 검사합니다. 상태와 모드가 정해진 값인지, 계획 상한이 양수인지, 현재 웨이브가 최대치를 넘지 않는지, 종합용 예산이 20% 이상인지, 예산 조정에 이유가 붙어 있는지, 축의 노트 경로가 실행 디렉터리를 벗어나지 않는지, `completed`/`partial` 실행의 보고서가 비어 있지 않은지를 확인합니다. `document_gate.py`는 승인된 문서 후보의 SHA-256 결속을 기록하고 검증합니다. 두 스크립트 모두 조사 품질을 판단하지 않으며, 원자적으로 파일을 써서 중간에 끊겨도 어중간한 상태가 남지 않습니다.

## 한계와 안전 수칙

- 출처가 많다고 주장이 증명되지는 않습니다. 독립성, 관련성, 조사 방법, 맥락, 반대 근거가 기준입니다. [references/source-review.md](references/source-review.md)를 참고하세요.
- 웹 콘텐츠는 지시가 아니라 신뢰할 수 없는 데이터로 다룹니다. 중요하거나 논쟁적인 주장과 직접 인용은 접근할 수 있는 한 원문에서 확인합니다.
- 독립적으로 보이는 출처가 사실은 하나의 근거 묶음일 때가 많습니다. 전재 기사, 같은 보도자료를 옮긴 글, 같은 주체가 만든 여러 페이지는 개수로 세지 않고 하나로 묶습니다.
- 엇갈리는 주장을 평균 내지 않습니다. 대상 집단, 정의, 시기, 이해관계, 방법이 달라서 생긴 차이라면 그렇게 밝히고, 끝내 풀리지 않은 충돌은 보고서에 그대로 남깁니다.
- 페이지는 바뀌거나, 차단되거나, 유료화되거나, 사라질 수 있습니다. 그로 인한 한계는 감추지 않고 기록합니다.
- 실행이 `partial`로 끝나는 것은 정상적인 결과입니다. 대신 어떤 빈틈이 남았는지 보고서에 밝혀야 합니다.
- 이 스킬은 개인 조사를 돕습니다. 규제나 감사를 위한 증거 시스템이 아니며, 의료·법률·금융·안전 관련 결론에는 최신 권위 자료와 해당 분야 전문가의 판단이 필요합니다.

## 출처와 영감

아래 프로젝트의 개념을 Hermes에 맞게 바꾸어 적용했습니다. 소스 코드는 복사하지 않았고, 링크가 제휴나 보증을 뜻하지도 않습니다.

- [LazyCodex](https://github.com/code-yeongyu/lazycodex), [Oh My OpenAgent (OmO)](https://github.com/code-yeongyu/oh-my-openagent) — 질문을 조사 축으로 나누는 방식, 보조 에이전트를 여러 단계에 걸쳐 활용하는 방식, 유용한 단서를 다음 조사에 반영하는 방식, 메인 에이전트가 조율을 맡는 원칙
- [Serkaion Deep Research](https://clawhub.ai/api/v1/skills/serkaion-deep-research) — 독립적인 출처 교차 확인, 주장에 반대되는 근거를 적극적으로 찾는 검증, 주장별 불확실성 표시
- [Autosolutions Deep Research](https://clawhub.ai/api/v1/skills/autosolutions-deep-research) — 여러 차례에 걸친 조사, 원문 우선, 모순 확인, 구조화된 보조 노트 분리. 다수의 보조 에이전트를 고정 배치하고 출처 수를 목표로 삼는 방식은 채택하지 않았습니다.
- [ByteDance DeerFlow deep-research skill](https://github.com/bytedance/deer-flow/tree/main/skills/public/deep-research) — 넓게 찾은 뒤 깊게 확인하는 방식, 참고 자료를 따라가는 방식, 빈틈으로 되돌아가는 방식, 결과가 충분히 모였는지 판단하고 계획을 고치는 아이디어
- [Google Labs Stitch Loop](https://github.com/google-labs-code/stitch-skills/tree/main/plugins/stitch-utilities/skills/stitch-loop) — 체크포인트와 저장된 다음 작업으로 일을 이어 가는 개념. 끝없이 페이지를 만드는 반복 구조는 가져오지 않았습니다.

## 라이선스

[MIT](LICENSE).
