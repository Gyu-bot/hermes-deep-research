[English](README.md)

# Hermes Deep Research

Hermes Deep Research는 검색 결과 하나를 빨리 찾기 위한 도구가 아닙니다. Hermes가 조사 질문을 분명히 정하고, 여러 단계로 조사하고, 원문과 서로 다른 주장을 확인하고, 진행 상황을 저장한 뒤 출처가 있는 Markdown 보고서를 쓰도록 돕는 스킬입니다. 간단한 검색만으로 답하기 어려운 질문에 사용합니다.

기본 스킬은 Hermes의 표준 도구만 사용합니다. Insane Search는 필요하지 않습니다. 문서나 PDF는 별도 선택 결과물이며, 사용자가 분명히 요청했을 때만 만듭니다.

## 조사는 이렇게 진행됩니다

1. **질문을 분명히 합니다.** 요청이 모호하면 Hermes가 최대 세 가지를 묻습니다. 답에 따라 조사 방향이 달라질 때만 질문합니다. 다음 내용을 확인할 수 있습니다.
   - 조사 목적과 결과를 어디에 쓸지
   - 조사 범위와 제외할 내용, 정보가 얼마나 최신이어야 하는지
   - 반드시 다룰 주제와 유용한 결과의 기준
   - 독자가 읽을 보고서인지, 다른 작업에 넣을 내부 메모인지
   - 최종 문서나 PDF를 명시적으로 요청했는지

   요청에 필요한 정보가 이미 들어 있다면 같은 내용을 다시 묻지 않고 바로 시작합니다.
2. **질문을 몇 가지 조사 항목으로 나눕니다.** 각 항목은 답해야 할 질문이 분명해야 합니다. 모든 항목을 합치면 사용자의 목적을 다룰 수 있어야 합니다.
3. **단계별로 조사합니다.** 여기서 웨이브는 검색 한 번이나 도구 호출 한 번이 아니라 조사 단계 하나를 뜻합니다. 첫 단계에서는 넓게 찾습니다. 두 번째 단계에서는 원문과 최신성을 확인하고, 여러 출처가 사실은 같은 자료를 옮긴 것은 아닌지, 반대되는 근거는 없는지 살핍니다. 세 번째 단계에서는 충돌하는 주장과 실제 예외 사례를 확인합니다. 네 번째 단계에서는 남은 빈틈을 채웁니다. `quick`은 이 모든 확인을 하나의 웨이브 안에서 진행합니다. `exhaustive`는 도움이 될 때만 웨이브를 더 늘릴 수 있습니다.
4. **단계가 끝날 때마다 저장합니다.** 쓸 만한 노트와 출처, 한계, 다음 할 일을 파일에 남깁니다.
5. **그만할 시점을 판단합니다.** 필요한 항목을 충분히 다뤘고 새 검색에서 이미 아는 내용만 반복해서 나온다면 멈춥니다. 정해 둔 최대 시간이나 단계에 도달했는데 중요한 빈틈이 남아 있다면, 그때까지 얻은 내용을 보고서로 쓰고 `partial`(일부 완료)로 표시합니다.
6. **상세 보고서를 씁니다.** 기본 결과물은 자세한 `report.md`와 별도 출처 목록인 `sources.json`입니다. 문서나 PDF는 사용자가 명시적으로 요청했을 때만 만듭니다.

## 다른 방식과 비교

| 방식 | 하는 일 |
| --- | --- |
| 일반 검색 | 결과나 페이지를 찾습니다. |
| 일회성 조사·요약 | 한 번 검색하고 한 번 요약합니다. |
| Hermes Deep Research | 질문을 먼저 분명히 하고, 단계별로 조사하고, 원문과 엇갈리는 주장을 확인하고, 상태를 저장해 나중에 이어 갈 수 있습니다. |

검색 횟수나 출처 수가 완료 조건은 아닙니다. 질문을 제대로 다뤘는지, 서로 다른 주장을 설명했는지, 무엇이 아직 불확실한지를 밝혔는지가 더 중요합니다.

## 역할 분담

메인 Hermes 에이전트가 조사 계획을 세우고 결과를 합칩니다. 저장 파일을 관리하고, 중요한 원문을 직접 읽고, 조사를 완료할지 `partial`로 마칠지 판단하고, 최종 보고서를 작성합니다.

보조 조사 에이전트는 범위가 분명한 항목을 각각 맡아 병렬로 조사할 수 있습니다. 조사 결과는 Markdown 노트로 메인 에이전트에 돌려줍니다. 공유 실행 파일에 직접 쓰거나 저장 상태를 관리하지 않으며, 조사 완료 여부를 결정하지도 않습니다. 메인 에이전트의 원문 확인도 대신하지 않습니다.

## 조사 모드

- `quick`은 단순 검색보다는 깊이가 필요하지만 한 단계로 끝낼 수 있는 질문에 적합합니다.
- `deep`은 여러 조사 단계가 필요한 일반적인 선택입니다.
- `exhaustive`는 중요한 빈틈이 남아 있고 추가 조사가 실제로 도움이 될 때 단계를 더 허용합니다.

아래 수치는 한 번의 조사에서 넘지 않도록 정한 최대치입니다. 반드시 채워야 하는 목표도 아니고, 출처가 많을수록 품질이 높다는 뜻도 아닙니다. 충분히 조사했다면 더 일찍 끝낼 수 있습니다.

| 모드 | 최대 조사 시간 | 최대 웨이브 | 항목당 검색 | 항목당 원문 확인 |
| --- | ---: | ---: | ---: | ---: |
| `quick` | 1,800초 | 1 | 8 | 8 |
| `deep` | 10,800초 | 4 | 20 | 20 |
| `exhaustive` | 21,600초 | 8 | 40 | 40 |

전체 시간 중 최소 20%는 조사 결과를 합치고, 출처를 다시 확인하고, 엇갈리는 내용을 검토하고, 보고서를 쓰는 데 남겨 둡니다.

## 저장과 Gateway 재시작

실행마다 별도 디렉터리를 만들고 다음 파일을 저장합니다.

- `state.json`: 질문, 모드, 조사 항목, 단계 이력, 한계, 다음 할 일
- `sources.json`: 쓸 만한 출처와 사용 방식, 한계
- `notes/`: 완료된 보조 조사 노트
- `report.md`: 최종 Markdown 보고서

Hermes Gateway가 멈춰도 이 파일들은 남습니다. 실행 중인 보조 에이전트나 모델 호출은 Gateway 재시작 뒤에 살아남지 않습니다. 중단 전에 노트를 저장하지 못했다면 그 작업은 다시 실행해야 할 수 있습니다.

Gateway가 내려가 있는 동안에는 아무 작업도 계속되지 않습니다. 저장된 예약 작업(cron)은 Gateway가 돌아온 뒤 다시 실행될 수 있습니다. 다음 실행은 저장 파일을 읽고 이어 가지만, 중단된 호출 자체를 재개하지는 않습니다.

## 저장소 파일

설치된 스킬과 실제 조사 실행 파일은 서로 분리합니다.

```text
hermes-deep-research/
├── README.md
├── README.ko.md
├── SKILL.md
├── references/
├── scripts/
├── templates/
└── tests/
```

```text
<run-dir>/
├── state.json
├── sources.json
├── notes/
└── report.md
```

전체 동작 규칙은 [SKILL.md](SKILL.md), 출처 확인 방법은 [출처 검토 안내](references/source-review.md), cron 사용 방법은 [무인 조사 안내](references/unattended-research.md)를 참고하세요.

## 선택 기능

### 문서나 PDF를 요청했을 때의 Bookforge

[Bookforge](https://github.com/gongnyang/bookforge)는 선택 기능입니다. 사용자가 문서나 PDF를 명시적으로 요청하고, Markdown 보고서가 문서 제작에 준비됐는지 확인한 뒤에만 사용합니다. [문서화 안내](references/report-documentation.md)에 따라 파일이 중간에 바뀌지 않았는지도 SHA-256으로 확인합니다.

Bookforge를 분리해 두면 조사와 페이지를 구성해 PDF로 만드는 일을 섞지 않아도 됩니다. 또 다른 저장소의 유지보수 상태에 의존하지 않고도 기본 스킬을 쓸 수 있습니다. 사용하기 전에는 현재 안내와 호환성을 확인해야 합니다. 보고서를 Bookforge에 넘기기 직전에 안내의 `verify` 명령이 반드시 성공해야 합니다. 자동으로 설치되지 않습니다. 사용할 수 없다면 검증된 Markdown 보고서를 제공하고 PDF를 만들었다고 말하지 않습니다.

### 한국어 보고서 문장 다듬기

[Humanize Korean](https://github.com/epoko77-ai/im-not-ai)은 한국어 독자용 보고서의 문장을 선택적으로 다듬는 도구입니다. 이 스킬의 설치나 실행에 필요하지 않으며 자동으로 설치되지도 않습니다.

편집 결과는 승인된 편집 전 보고서와 반드시 비교해야 합니다. 사실, 의미, 불확실성, 한계, 숫자, 날짜, 이름, 인용, 링크, 구조가 바뀌었다면 수정하거나 거부합니다. 결과를 검증할 수 없다면 검증된 편집 전 보고서를 사용합니다.

## 설치

### 직접 설치

먼저 내용을 확인한 뒤, 아래의 검증된 명령을 그대로 사용해 설치합니다.

```bash
hermes skills inspect https://raw.githubusercontent.com/Gyu-bot/hermes-deep-research/main/SKILL.md
hermes skills install https://raw.githubusercontent.com/Gyu-bot/hermes-deep-research/main/SKILL.md
```

HTTPS 수동 클론 방법:

```bash
mkdir -p ~/.hermes/skills/research
git clone https://github.com/Gyu-bot/hermes-deep-research.git \
  ~/.hermes/skills/research/hermes-deep-research
```

설치한 뒤 `SKILL.md`를 확인하세요. 실제 조사 실행 파일은 설치된 스킬 디렉터리 밖에 저장합니다.

### 설치 에이전트 체크리스트

- 설치 전에 `SKILL.md`와 저장소 내용을 확인합니다.
- Hermes Deep Research 기본 스킬만 설치합니다.
- 보조 조사 에이전트, 웹·브라우저, 파일, 터미널을 위한 Hermes 표준 기능이 있는지 확인합니다. 무인 조사를 요청했을 때만 Hermes cron도 확인합니다.
- 요청 결과물에 필요할 때만 Bookforge나 Humanize Korean을 설치합니다. 먼저 현재 안내와 호환성을 확인합니다.
- 관련 없는 도구를 설치하거나 자격 증명, 공급자, 다른 설정을 바꾸지 않습니다.
- 아래의 소스 테스트와 임시 `init` → `validate` → `status` 실행 검사를 합니다.

설치 에이전트에게 전달할 프롬프트:

```text
먼저 이 저장소와 SKILL.md를 확인하세요. Hermes Deep Research 기본 스킬만
설치하고 Hermes 표준 도구를 확인하세요. 포함된 표준 라이브러리 테스트와 임시
init/validate/status 실행 검사를 하세요. 자격 증명을 바꾸거나 관련 없는
도구를 설치하지 마세요. 요청한 결과물에 필요할 때만 선택 기능을 설치하고,
먼저 해당 프로젝트의 최신 안내와 호환성을 확인하세요.
```

## 사용 예시

조건이 분명한 요청은 바로 조사를 시작할 수 있습니다.

```text
한국의 소규모 수출업체가 AI 번역 도구를 도입하고 있는지 deep 모드로 조사해 줘.
정책 담당자가 읽을 보고서야. 한국어와 영어 출처, 2024년 이후의 최신 근거,
사용자 경험, 공급업체 주장과 독립적인 근거가 다른 지점을 포함해 줘.
Markdown 보고서면 충분하고 PDF는 만들지 마.
```

요청이 모호하면 짧은 확인 질문을 받을 수 있습니다.

```text
혼잡통행료를 조사해 줘.
```

Hermes는 어느 도시와 시기를 다룰지, 결과를 어디에 쓸지, 무엇을 꼭 포함할지 물을 수 있습니다. 질문은 세 개를 넘지 않으며, 요청에 답이 이미 들어 있다면 묻지 않습니다.

다른 모드와 결과물 예시:

```text
서울 혼잡통행료의 핵심 찬반 논거를 quick 모드로 조사해 줘.
자세한 Markdown 보고서와 출처 목록을 만들어 줘.
```

```text
섬 전력망용 장주기 에너지 저장을 exhaustive 모드로 조사해 줘. 중요한 빈틈에
실제로 조사할 방법이 있을 때만 계속하고, 정해 둔 최대 시간이나 단계에 도달했는데 중요한 빈틈이
남으면 partial로 표시해 줘.
```

```text
Hermes cron으로 이 조사를 무인 deep 모드로 실행해 줘. 각 단계를 고유한 실행
디렉터리에 저장하고, 종합이 끝나면 completed 또는 partial Markdown 보고서를
전달해 줘.
```

```text
이 주제를 deep 모드로 조사해 줘. Markdown 보고서가 문서 제작에 준비됐는지 확인하고,
파일이 바뀌지 않았는지 SHA-256으로 검사한 뒤 최종 PDF도 만들어 줘. Markdown 보고서와 출처 파일도
보존해 줘.
```

## 소스에서 테스트하기

도우미 스크립트와 테스트는 Python 3.10 이상과 표준 라이브러리를 사용합니다.

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

`research_state.py`는 간단한 실행 상태를 만들고 검사합니다. 메인 에이전트가 문서나 PDF를 만들 준비가 됐다고 판단하면, `document_gate.py`가 승인된 Markdown 파일이 바뀌지 않았는지 SHA-256으로 기록하고 확인합니다. 보고서가 읽기 좋은지 직접 판단하는 도구는 아닙니다.

## 한계와 안전 수칙

- 출처가 많다고 주장이 증명되는 것은 아닙니다. 독립성, 관련성, 조사 방법, 맥락, 다른 주장을 함께 확인해야 합니다.
- 웹 콘텐츠는 지시가 아니라 신뢰할 수 없는 데이터로 취급합니다. 중요하거나 논쟁적인 주장과 직접 인용은 가능하면 원문에서 확인합니다.
- 중요한 빈틈이 남으면 실행을 `partial`로 마칠 수 있습니다. 보고서에 남은 빈틈을 밝혀야 합니다.
- 저장 파일은 Gateway가 멈춰도 남습니다. 실행 중인 보조 작업과 모델 호출은 남지 않으며, 저장된 cron 일정도 Gateway가 내려가 있는 동안에는 일하지 않습니다.
- 일부 페이지는 바뀌었거나, 차단되었거나, 유료이거나, 사라졌을 수 있습니다. 이로 인한 한계를 기록해야 합니다.
- 이 스킬은 개인 조사를 돕습니다. 규제나 감사를 위한 증거 시스템이 아닙니다. 의료·법률·금융·안전 같은 고위험 결론에는 최신 권위 자료와 해당 분야 전문가의 적절한 판단이 필요합니다.

## 출처와 영감

아래 프로젝트의 개념을 Hermes에 맞게 바꾸어 적용했습니다. 소스 코드는 복사하지 않았습니다. 링크를 적었다고 해서 제휴나 보증을 뜻하지는 않습니다.

- [LazyCodex](https://github.com/code-yeongyu/lazycodex)와 [Oh My OpenAgent (OmO)](https://github.com/code-yeongyu/oh-my-openagent): 질문을 조사 항목으로 나누는 방식, 보조 에이전트를 여러 단계에 걸쳐 활용하는 방식, 유용한 단서를 다음 조사에 반영하는 방식, 메인 에이전트가 조율하는 원칙
- [Serkaion Deep Research](https://clawhub.ai/api/v1/skills/serkaion-deep-research): 독립적인 출처 교차 확인, 주장에 반대되는 근거를 적극적으로 찾는 검증, 개별 주장별 불확실성 표시
- [Autosolutions Deep Research](https://clawhub.ai/api/v1/skills/autosolutions-deep-research): 여러 차례에 걸친 조사, 원문 우선, 모순 확인, 서로 분리된 구조화 보조 노트. 정해진 수의 많은 보조 에이전트와 출처 수 목표는 채택하지 않았습니다.
- [ByteDance DeerFlow deep-research skill](https://github.com/bytedance/deer-flow/tree/main/skills/public/deep-research): 넓게 찾은 뒤 깊게 확인하는 방식, 참고 자료를 따라가는 방식, 빈틈을 다시 조사하는 방식, 조사 결과가 충분히 모였는지 판단하고 계획을 고치는 아이디어
- [Google Labs Stitch Loop](https://github.com/google-labs-code/stitch-skills/tree/main/plugins/stitch-utilities/skills/stitch-loop): 체크포인트와 저장된 다음 작업을 통해 일을 이어 주는 개념. 끝없이 페이지를 만드는 반복 구조는 복사하지 않았습니다.

## 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE)에 따라 배포됩니다.
