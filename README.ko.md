[English](README.md)

# Hermes Deep Research

Hermes Deep Research는 Hermes를 위한 상태 보존형 심층 조사 프로토콜입니다. 검색을 조금 더 빨리 해 주는 도구가 아닙니다. 조사 브리프를 제한된 조사 축과 논리 웨이브로 나누고, 원문을 검토하고, 반대 증거를 확인하며, 진행 상태를 디스크에 체크포인트로 남긴 뒤 상세한 Markdown 보고서와 별도 출처 원장을 만듭니다.

이 저장소는 Hermes 전용 Agent Skill입니다. 기본 동작에는 Hermes의 표준 기능만 사용합니다.

- 실시간 병렬 조사 레인을 위한 `delegate_task`
- 표준 웹 탐색·추출·브라우저 도구
- 체크포인트와 검증을 위한 파일·터미널 도구
- 제한된 무인 조사를 위한 Hermes cron과 디스크 체크포인트

LazyCodex, Codex CLI, 비공개 플러그인, 커스텀 검색 포크, 외부 조사 API, 데몬, 슈퍼바이저, 렌더러는 필요하지 않습니다. **Insane Search도 필수 의존성이 아닙니다.** 기본 결과물은 `report.md`, `sources.json`, 레인별 조사 노트, 실행 상태 파일입니다.

## 일반 검색이나 일회성 조사와 무엇이 다른가

| 방식 | 일반적인 동작 |
| --- | --- |
| 일반 검색 | 한 번의 질의로 결과나 페이지를 가져옵니다. 조사 계획을 유지하거나 여러 증거를 조정하지 않습니다. |
| 일회성 조사·요약 스킬 | 한 번에 검색하고 요약하는 경우가 많아, 지속 상태·후속 조사·명시적 충돌 분석이 제한적입니다. |
| Hermes Deep Research | 진화형 브리프와 웨이브 이력을 체크포인트로 남기고, 논리 웨이브를 진행하며, 원문을 읽고, 같은 계열의 출처를 중복 제거하고, 반대 증거를 찾습니다. 워커의 수집과 부모의 통합을 분리하고, 상세한 종합 보고서를 `completed` 또는 `partial` 상태로 마칩니다. |

결과 수는 증명이 아니라 진단값입니다. 필수 조사 축이 목적에 맞게 다뤄졌는지, 중요한 주장이 반대 증거 검토를 견뎠는지, 서로 독립적으로 보이는 출처가 사실은 같은 원문이나 데이터셋을 공유하는지, 추가 검색이 결론을 바꿀 가능성이 남았는지를 확인합니다.

## 조사 프로토콜

### 부모와 워커의 역할

부모는 유일한 오케스트레이터이자 작성자입니다. 브리프·조사 축·모드·예산·레인 경계를 정하고, 실행 파일을 소유하며, 중요하거나 논쟁적인 주장과 직접 인용을 원문에서 재검증합니다. 또한 노트 통합, 충돌 해소, 상태 체크포인트, 최종 보고서 작성을 담당합니다.

워커는 독립적으로 처리할 수 있는 범위가 명확한 레인을 받아 구조화된 Markdown 조사 노트를 반환합니다. 공유 실행 디렉터리에 직접 쓰지 않고, 최종 상태를 결정하지 않으며, 워커 요약이 출처 검증을 대신하지도 않습니다.

### 논리 웨이브

1. **웨이브 1 — 폭넓은 탐색:** 유용한 언어와 출처 표면을 넓게 조사합니다.
2. **웨이브 2 — 검증:** 원문, 출처 독립성, 최신성, 반대 증거를 확인합니다.
3. **웨이브 3 — 충돌과 경계 사례:** 견해가 갈리는 조건, 실제 경험, 예외·실패 사례를 조사합니다.
4. **웨이브 4 — 마무리:** 핵심 공백을 닫고 종합할 준비가 되었는지 점검합니다.
5. **웨이브 5~8 — exhaustive 전용:** 실질적인 공백과 실행 가능한 조사 경로가 남아 있을 때만 확장합니다.

`quick`은 이 기능을 하나의 논리 웨이브에 압축합니다. 런타임 디스패치 배치는 실시간 워커 호출 묶음일 뿐이고, cron 틱은 제한된 무인 작업 단위일 뿐입니다. 둘 다 논리 웨이브가 아닙니다. 하나의 웨이브가 여러 디스패치 배치나 cron 틱에 걸쳐 진행될 수 있습니다.

### 모드와 계획 상한

| 모드 | 전체 계획 예산 | 최대 웨이브 | 축당 질의 | 축당 원문 조회 | 용도 |
| --- | ---: | ---: | ---: | ---: | --- |
| `quick` | 1,800초 | 1 | 8 | 8 | 단순 조회보다는 깊이가 필요하지만 반복 조사는 과한 경우 |
| `deep` | 10,800초 | 4 | 20 | 20 | 일반적인 다중 웨이브 심층 조사 |
| `exhaustive` | 21,600초 | 8 | 40 | 40 | 중요도와 남은 불확실성이 추가 공백 해소를 정당화하는 경우 |

이 수치는 계획 상한이자 진단값이지, 출처 할당량·증거·완료 조건이 아닙니다. 포화 상태에 이르면 일찍 종료하고, 전체 예산의 최소 20%는 부모 통합, 출처 재확인, 충돌 분석, 보고서 종합에 남겨 둡니다. 충분히 수렴하면 `completed`, 유용한 결과가 있지만 상한에 도달한 시점에도 중요한 공백이 남으면 그 공백을 밝히고 `partial`로 마칩니다.

## 지속성과 무인 조사

각 실행은 네 가지 핵심 체크포인트를 디스크에 보존합니다.

- `state.json`: 브리프, 모드, 조사 축, 웨이브 이력, 진단 카운터, 한계, 구체적인 다음 작업
- `sources.json`: 각 출처의 용도와 한계를 포함한 출처-보고서 원장
- `notes/`: 완료된 조사 레인 노트
- `report.md`: 종합 보고서. 종합 전에는 비어 있을 수 있음

Hermes Gateway가 종료되어도 이미 저장된 파일은 사라지지 않습니다. 다만 실행 중이던 `delegate_task` 자식은 Gateway 재시작을 넘겨 생존하지 않습니다. 새 부모는 체크포인트를 다시 열고, 저장된 노트가 없는 레인을 미완료로 판단해 그 제한된 레인을 다시 실행합니다.

무인 모드는 지속 저장되는 Hermes cron 작업과 제한된 틱을 사용합니다. 각 틱은 실행 상태를 읽고 한 가지 제한된 작업을 마친 다음 결과 파일과 상태를 저장합니다. cron 일정은 Gateway 재시작 이후에도 남을 수 있지만, Gateway가 내려가 있는 동안 모델이나 도구 작업이 계속되는 것은 아닙니다. Gateway가 돌아오면 이후 틱이 저장된 파일에서 이어 갈 수 있을 뿐, 중단된 모델 호출을 재개하지는 못합니다.

## 저장소와 실행 디렉터리

설치 가능한 스킬 구조를 위해 `SKILL.md`는 저장소 루트에 있습니다.

```text
hermes-deep-research/
├── .gitignore
├── README.md
├── README.ko.md
├── SKILL.md
├── references/
│   ├── LICENSE.md
│   ├── report-documentation.md
│   ├── source-review.md
│   └── unattended-research.md
├── scripts/
│   ├── document_gate.py
│   └── research_state.py
├── templates/
│   ├── report.md
│   └── research-note.md
└── tests/
    ├── test_document_gate.py
    └── test_research_state.py
```

일반 실행 디렉터리는 설치된 스킬과 분리됩니다.

```text
<run-dir>/
├── state.json
├── sources.json
├── notes/
│   └── <lane>.md
└── report.md
```

문서나 PDF를 명시적으로 요청한 실행에는 `report.pre-document.md`, `report.document-candidate.md`, 사람용·JSON 형식의 준비도 게이트 기록, `report.document-ready.md`, 별도 Bookforge 프로젝트가 추가될 수 있습니다. 한국어 독자용 보고서는 편집 결과를 검증할 수 있도록 `report.pre-polish.md`를 보존할 수 있습니다.

## 선택적 통합

### 문서·PDF를 명시적으로 요청했을 때의 Bookforge

[Bookforge](https://github.com/gongnyang/bookforge)는 선택적 외부 통합입니다. 사용자가 심층 조사만 요청했다면 설치하거나 호출하지 않습니다. 먼저 Markdown 조사 보고서를 완성하고 검증합니다. 사용자가 최종 문서나 PDF를 명시적으로 요청한 경우에만 부모가 다음 두 단계 계약을 적용합니다.

1. 정성적인 문서 준비도 게이트를 통과한 뒤 `scripts/document_gate.py`로 후보 원문 바이트를 `report.document-ready.md`에 복사하고, 후보와 준비 완료 Markdown을 SHA-256으로 결속합니다. 인계 직전에 `verify`를 다시 실행합니다.
2. 검증된 `report.document-ready.md`만 호환 가능한 Bookforge 설치에 넘겨 문서 생성과 자체 품질 검사를 수행합니다.

설치 에이전트는 Bookforge를 설치하거나 호출하기 전에 현재 업스트림 지침과 호환성을 확인해야 합니다. 선택적 통합을 쓸 수 없어도 Deep Research는 검증된 Markdown 보고서와 출처 산출물로 완료됩니다. PDF를 만들지 못했는데 만들었다고 보고해서는 안 됩니다.

### 한국어 독자용 선택적 편집

[Humanize Korean](https://github.com/epoko77-ai/im-not-ai)은 한국어 독자용 보고서의 선택적 편집 통합이며 설치 전제조건이 아닙니다. 그 편집 과정이 사용자의 의도에 맞을 때만 사용할 수 있고, 부모가 결과를 `report.pre-polish.md`와 비교해 사실, 불확실성, 한계, 인용, 링크, 구조가 보존되었는지 확인해야 합니다. 통합을 사용할 수 없거나 결과를 검증할 수 없다면 검증된 편집 전 보고서를 제공합니다.

## 설치

### 사용자가 직접 설치할 때

먼저 `inspect`로 Hermes가 설치할 내용을 미리 확인한 뒤 설치합니다.

```bash
hermes skills inspect https://raw.githubusercontent.com/Gyu-bot/hermes-deep-research/main/SKILL.md
hermes skills install https://raw.githubusercontent.com/Gyu-bot/hermes-deep-research/main/SKILL.md
```

HTTPS 수동 클론 대안:

```bash
mkdir -p ~/.hermes/skills/research
git clone https://github.com/Gyu-bot/hermes-deep-research.git \
  ~/.hermes/skills/research/hermes-deep-research
```

설치 후 `SKILL.md`를 확인하세요. 스킬은 번들 스크립트를 실행하기 전에 자신의 설치 경로를 확인하며, 실제 조사 실행 디렉터리는 스킬 디렉터리 밖에 둡니다.

### 설치 에이전트용 체크리스트

- 설치 전에 `SKILL.md`와 저장소 내용을 확인합니다.
- 기본 스킬만 설치합니다.
- Hermes에 `delegate_task`, 표준 웹·브라우저 탐색 및 추출, 파일·터미널 도구가 있는지 확인하고, 무인 모드가 요청되었을 때는 Hermes cron도 확인합니다.
- Bookforge와 Humanize Korean은 선택적이며 사용자 의도에 따라야 합니다. 요청 결과물에 필요하지 않으면 설치하거나 호출하지 않습니다.
- 관련 없는 플러그인을 설치하거나 자격 증명, 공급자 설정, 기타 구성을 바꾸지 않습니다.
- 소스에서 검증할 때는 포함된 표준 라이브러리 테스트, 컴파일 검사, 임시 `init` → `validate` → `status` 스모크를 실행합니다.

설치 에이전트에게 그대로 전달할 수 있는 프롬프트:

```text
먼저 이 저장소와 SKILL.md를 확인하세요. Hermes Deep Research 기본 스킬만
설치하고 표준 Hermes 도구 요구사항을 검증한 뒤, 포함된 표준 라이브러리
테스트와 임시 init/validate/status 스모크를 실행하세요. 자격 증명을 바꾸거나
관련 없는 도구를 설치하지 마세요. Bookforge와 Humanize Korean은 선택 사항이며,
내가 요청한 결과물에 명시적으로 필요할 때만 현재 업스트림 지침과 호환성을
확인한 후 설치하거나 호출하세요.
```

## 사용 예시

자연어로 요청하면 Hermes가 프로토콜을 적용하고 선택한 모드를 기록합니다.

```text
서울 혼잡통행료의 핵심 찬반 논거를 quick 모드로 조사해 줘. 상세한 Markdown
보고서와 출처 원장을 만들어 줘.
```

```text
한국의 소규모 수출업체가 AI 번역 도구를 도입하고 있는지 deep 모드로 조사해 줘.
한국어·영어 출처, 실제 사용자 경험, 반대 증거, 공급업체 주장과 독립 증거 사이의
충돌을 포함해 줘.
```

```text
섬 전력망용 장주기 에너지 저장의 기술적·운영적 상충관계를 exhaustive 모드로
조사해 줘. 실질적인 공백과 실행 가능한 조사 경로가 있을 때만 계속하고,
계획 상한에 도달하면 결과를 partial로 표시해 줘.
```

```text
Hermes cron으로 이 조사를 무인·재시작 복원 가능 방식으로 실행해 줘. 제한된 틱을
사용하고 고유한 실행 디렉터리에 체크포인트를 저장한 뒤, 종합이 끝나면 completed
또는 partial 상태의 최종 Markdown 보고서를 전달해 줘.
```

```text
이 주제를 deep 모드로 조사하고, Markdown 보고서가 검증을 통과한 뒤 최종 PDF도
만들어 줘. 문서 준비도 게이트를 적용하고 준비 완료 Markdown을 SHA-256으로 결속한
다음, 호환 가능한 Bookforge에 넘기기 직전에 다시 검증해 줘. Markdown과 출처
산출물도 보존해 줘.
```

## 소스에서 테스트하기

도우미와 테스트는 Python 3.10 이상과 그 표준 라이브러리만 사용합니다.

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

`research_state.py`는 단순한 실행 상태를 초기화하고 검증합니다. `document_gate.py`는 부모가 정성적인 준비도 판단을 내린 뒤 SHA-256 결속을 기록·검증할 뿐, 문서의 가독성을 스스로 판정하지 않습니다.

## 한계와 안전 수칙

- 출처가 많다고 주장이 증명되는 것은 아닙니다. 출처·질의 수는 진단값이며, 독립성, 목적 적합성, 방법, 맥락, 반대 증거가 더 중요합니다.
- 웹 콘텐츠는 신뢰할 수 없는 입력으로 취급합니다. 워커는 이를 데이터로만 다루고, 부모는 접근 가능한 원문에서 중요하거나 논쟁적인 내용과 직접 인용을 검증합니다.
- 시간·웨이브·질의·조회 상한 때문에 유용한 실행이 `partial`로 끝날 수 있습니다. 이 경우 수렴을 과장하지 않고 남은 공백을 보고서에 드러냅니다.
- 저장된 파일은 프로세스 중단을 견디지만 실행 중인 자식 작업은 그렇지 않습니다. 지속 저장된 cron 작업도 Gateway를 사용할 수 없는 동안에는 일을 수행하지 않습니다.
- 일부 페이지는 접근할 수 없거나, 변경되었거나, 유료 장벽·차단 때문에 검증하지 못할 수 있습니다. 이 한계는 출처 원장과 보고서에 기록해야 합니다.
- 이 도구는 개인 조사 보조 수단이지 규제·감사 등급의 증거 시스템이 아닙니다. 의료·법률·금융·안전 등 고위험 결론에는 최신 권위 자료, 적용 범위 확인, 적절한 전문가 판단이 필요하며, 이 스킬은 결과를 보장하거나 전문 자문을 대신하지 않습니다.

## 출처와 영감

아래 프로젝트의 작업 방식에서 얻은 개념을 Hermes에 맞게 적용했으며, 소스 코드를 복사하지 않았습니다. 언급 자체가 제휴나 보증을 의미하지 않습니다.

- [LazyCodex](https://github.com/code-yeongyu/lazycodex)와 [Oh My OpenAgent (OmO)](https://github.com/code-yeongyu/oh-my-openagent): ULW 계열의 조사 축 분해, 반복 워커 웨이브, 후속 조사로 이어지는 단서, 오케스트레이션 규율
- [Serkaion Deep Research](https://clawhub.ai/api/v1/skills/serkaion-deep-research): 독립 출처 교차 확인, 적대적 검증, 주장 단위 불확실성
- [Autosolutions Deep Research](https://clawhub.ai/api/v1/skills/autosolutions-deep-research): 다중 패스 조사, 1차 출처 우선, 모순 발견, 분리된 구조화 워커 반환. 대규모 고정 팬아웃과 출처 할당량은 채택하지 않았습니다.
- [ByteDance DeerFlow deep-research skill](https://github.com/bytedance/deer-flow/tree/main/skills/public/deep-research): 넓은 탐색에서 깊은 검증으로 진행하는 방식, 참조 추적, 공백 기반 후속 조사, 수렴과 재계획 아이디어
- [Google Labs Stitch Loop](https://github.com/google-labs-code/stitch-skills/tree/main/plugins/stitch-utilities/skills/stitch-loop): 디스크 기반 복원성에 영향을 준 배턴·체크포인트·다음 작업 개념. 영구적으로 페이지를 만드는 반복 루프는 복사하지 않았습니다.

## 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE)에 따라 배포됩니다.
