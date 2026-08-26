# 브랜드 아이덴티티 생성기

브랜드 브리프(업종·타깃·키워드)를 JSON으로 입력하면 **브랜드명·슬로건·스토리·컬러 팔레트·로고 시안**을
AI로 생성해 파일로 저장하는 CLI 프로그램입니다.

> [Project A] · 주제 **카페** · Python 3.10 이상

---

## 동작

```
[1] 브리프 입력 ─→ [2] 네이밍·슬로건·스토리 ─→ [3] 컬러 팔레트 ─→ [4] 로고 시안
                        (LLM)                    (LLM)          (이미지 생성)
                                                                      │
                                              [5] 결과 저장 & 에러 처리 통합
```

한 단계가 실패해도 멈추지 않습니다. 진행된 만큼을 저장하고 실패 원인을 `run_report.md`에 남깁니다.

---

## 실행

### 1. 설치

```bash
pip install -r requirements.txt
```

**필수 패키지는 없습니다.** API 호출(`urllib`)도, 컬러 팔레트 PNG 생성(`zlib`·`struct`)도
표준 라이브러리로 합니다. 아래는 **있으면 결과가 나아지는** 선택 항목입니다.

| 패키지 | 없으면 | 있으면 |
| --- | --- | --- |
| `python-dotenv` | 키를 환경변수로 직접 넣어야 합니다 | `.env` 파일에서 읽습니다 |
| `matplotlib` | 팔레트 PNG에 **HEX 코드만** 찍습니다 | 색 **이름까지** 한글로 넣습니다 |
| `pillow` | 이미지 API가 JPEG로 주면 **그 시안을 건너뜁니다** | PNG로 변환합니다 |

<details>
<summary>PNG를 어떻게 만드는지 — 표준 라이브러리의 경계</summary>

**컬러 팔레트 PNG는 외부 패키지가 전혀 필요 없습니다.**
`matplotlib`이 없으면 `zlib`으로 압축하고 `struct`로 청크를 조립해 PNG를 **직접 인코딩**합니다.
HEX 글자는 5×7 비트맵 글꼴로 픽셀에 찍습니다.
(구현: [`brand_result/palette_png.py`](brand_result/palette_png.py)의 `_render_builtin`)

**로고 PNG는 API가 주는 형식에 달렸습니다.**

| 공급자 | 받는 형식 | Pillow 필요? |
| --- | --- | --- |
| OpenAI | PNG | ❌ 그대로 저장 |
| Gemini | PNG | ❌ 그대로 저장 |
| Pollinations | **JPEG** | ⭕ 변환에 필요 |

Pillow 없이 Pollinations로 떨어지면 그 시안은 건너뜁니다.
확장자만 `.png`로 바꿔 저장하면 깨진 파일이 되기 때문입니다.

</details>

### 2. API 키 등록

`.env.example`을 `.env`로 복사한 뒤 키를 채웁니다.

```
OPENAI_API_KEY=본인의_API_키
GEMINI_API_KEY=본인의_API_키
```

**둘 중 하나만 있으면 됩니다.** OpenAI 키가 있으면 그것을, 없으면 Gemini를 씁니다.
연결 확인:

```bash
python test_api.py
```

```
  ✅ OpenAI: gpt-4o-mini → 안녕! 반가워. 무엇을 도와줄까?
  ❌ Gemini: gemini-flash-lite-latest=HTTP 429 / gemini-flash-latest=HTTP 429

✅ 연결 성공 — python main.py 를 돌리면 실제 결과가 나옵니다.
```

키가 하나도 없으면 이렇게 나옵니다.

```
❌ API 키가 없습니다.
   .env.example 을 .env 로 복사한 뒤
   OPENAI_API_KEY 또는 GEMINI_API_KEY 중 하나를 채워 주십시오.
```

> ### ⚠️ 키가 없을 때 — 예시 값은 데모용입니다
>
> 키가 없어도 프로그램은 끝까지 돌아갑니다. 다만 **[2] 네이밍과 [3] 컬러는
> 미리 넣어 둔 예시 값으로 채워집니다.** 이것은 파이프라인이 이어지는지 확인하기 위한
> 폴백(fallback)이지 AI 생성 결과가 아닙니다.
>
> **이 과제가 요구하는 "AI 기반 생성" 결과물을 얻으려면 키가 반드시 필요합니다.**
>
> 예시 값을 쓴 자리는 `run_report.md`에 이렇게 남습니다 — 받는 사람이 실제 생성
> 결과로 착각하면 안 되기 때문입니다.
>
> ```
> ## LLM 대신 예시 값을 쓴 곳
>
> 키가 없거나 호출이 실패해 미리 넣어 둔 값으로 채웠습니다.
> 제출 전에 키를 넣고 다시 돌려야 실제 생성 결과가 나옵니다.
>
> - [2] 네이밍·슬로건·스토리
> - [3] 컬러 팔레트
> ```
>
> 로고는 예시 값이 없습니다. OpenAI → Gemini → Pollinations(키 불필요) 순으로
> 시도하므로 키가 없어도 **실제 이미지 생성 API**를 씁니다.

### 3. 실행

```bash
python main.py
```

```
🎨 브랜드 아이덴티티 생성기

브리프 JSON 경로를 입력하세요: samples/brief.json
   📋 카페 · 20~30대 직장인, 일상 속 여유를 찾는 사람
      키워드: 여유, 따뜻함, 일상의 쉼표, 감성

출력 폴더 경로를 입력하세요 (엔터 시 ./output):

  ✅ [1] 브리프
  ✅ [2] 네이밍·슬로건·스토리
  ✅ [3] 컬러 팔레트
  ✅ [4] 로고 시안

✅ 완료 단계 4/4 · output
```

잘못된 경로나 형식이면 이유를 알려 주고 다시 묻습니다.

#### 인자로 한 번에 돌리기

명세는 `print`와 `input`으로 받는 **대화형을 요구하므로 그것이 기본**입니다.
같은 결과를 다시 만들어야 할 때(자동화·시연·채점 재현)를 위해 인자도 받습니다.
**준 인자만** 묻지 않고 건너뜁니다.

```bash
python main.py --brief samples/brief.json --output ./output
```

| 인자 | 생략하면 | 값 |
| --- | --- | --- |
| `--brief` | 물어봅니다 | 브리프 JSON 경로 |
| `--output` | 물어봅니다 | 출력 폴더 (기본 `./output`) |
| `--logos` | 2장 | 로고 시안 수 — `2` 또는 `3` |

로고 시안을 3장 만들려면:

```bash
python main.py --brief samples/brief.json --logos 3
```

대화형과 달리 `--brief` 경로가 잘못되면 되묻지 않고 종료 코드 `2`로 멈춥니다.
자동화로 도는 중에는 되물어 봐야 답할 사람이 없습니다.

---

## 입력 — 브랜드 브리프

[`samples/brief.json`](samples/brief.json)

```json
{
  "industry": "카페",
  "target": "20~30대 직장인, 일상 속 여유를 찾는 사람",
  "keywords": ["여유", "따뜻함", "일상의 쉼표", "감성"],
  "tone": "따뜻하고 감성적이며 과하지 않게 세련된 분위기",
  "competitors": ["블루보틀", "스타벅스"],
  "notes": "한글과 영어로 모두 활용하기 쉬운 브랜드명을 원함"
}
```

| 구분 | 필드 |
| --- | --- |
| **필수** | `industry` `target` `keywords`(2개 이상) |
| 선택 | `tone` `competitors` `notes` — 기본값을 채워 다음 단계로 넘깁니다 |

파일 없음 · `.json` 아님 · JSON 문법 오류 · 필수 필드 누락 · 자료형 불일치를
각각 구분해서 안내합니다. JSON 문법 오류는 몇 번째 줄인지 알려 줍니다.

---

## 출력

| 파일 | 내용 |
| --- | --- |
| **`brand_result.md`** | **브랜드 아이덴티티 결과 문서** |
| `brand_result.json` | 텍스트 결과 전체 |
| **`color_palette.png`** | **컬러 팔레트 시각화** |
| **`logo_01.png` `logo_02.png`** | **로고 시안** (`--logos 3` 이면 `logo_03.png` 까지) |
| `logo_prompts.md` | 로고 생성에 쓴 영어 프롬프트 |
| `run_report.md` | 단계별 성공·실패와 규격 위반 기록 |
| `brand_tokens.css` | 컬러 팔레트를 CSS 변수·Tailwind 설정으로 |

생성되는 내용

- 브랜드명 후보 **4~5개** — 이름·**영문 표기**·읽는 법·의미·유형
  (명세는 3~5개지만 세 개만 내면 고를 여지가 없어 네 개 이상을 요구합니다)
  후보가 평범해지지 않도록 세 가지를 막습니다 — 업종어를 붙인 이름(`여유카페`),
  브리프 키워드를 그대로 쓴 이름(키워드가 '여유' 인데 이름도 '여유'),
  후보들이 같은 유형으로 쏠리는 것. 어기면 `run_report.md` 에 적힙니다.
- 슬로건 3개, 브랜드 스토리 300자 내외(탄생 배경·철학·비전)
- 메인 컬러 1개 + 서브 컬러 2~3개, 각 색의 **본문 대비 명도비**
  (로고를 메인 컬러로 그리므로, 메인이 흰 배경에 묻히면 다시 고르게 합니다)
- 로고 시안 **2~3장**과 생성에 쓴 프롬프트 (기본 2장, `--logos 3` 으로 3장)

**보너스 과제로 다국어 네이밍 지원을 구현했습니다.**
후보마다 한글 이름과 영문 표기를 함께 만들고, `쉼표 (Comma, COM-ma)` 형태로 표기합니다.
영문 표기는 간판·도메인·SNS 계정에 그대로 쓸 수 있도록 알파벳 12자 안쪽으로 짓습니다.

### 실제 생성 결과

`output/` 폴더에 실행 결과를 그대로 담아 두었습니다.

**컬러 팔레트** — `output/color_palette.png`

![컬러 팔레트](output/color_palette.png)

**로고 시안** — `--logos 3` 으로 3장 생성한 결과입니다.

| 시안 1 | 시안 2 | 시안 3 |
| --- | --- | --- |
| <img src="output/logo_01.png" width="220"> | <img src="output/logo_02.png" width="220"> | <img src="output/logo_03.png" width="220"> |
| 면으로 채운 기하 아이콘 | 굵은 획 픽토그램 | 이어진 선 엠블럼 |

시안마다 다른 프롬프트 템플릿을 씁니다. 같은 그림이 여러 장 나오면 시안이 아니기 때문입니다.

텍스트 결과 전체는 [`output/brand_result.md`](output/brand_result.md) 와
[`output/brand_result.json`](output/brand_result.json) 에 있습니다.

---

## 구조

```
main.py                    진입점 — 대화형 입력과 [1] 브리프 검증
integrate.py               [5] 통합 실행
test_api.py                API 연결 테스트
brief.py             [1] load_brief() -> dict
naming.py            [2] generate_naming(brief) -> dict
palette.py           [3] generate_palette(brief, naming) -> dict
logo.py              [4] generate_logos(brief, naming, palette) -> list
brand_result/
  runner.py                단계 호출과 예외 격리
  validate.py              데이터 계약 검증
  store.py                 파일 저장 · 명도 대비 계산
  report.py                결과 문서 생성
  palette_png.py           컬러 팔레트 PNG 시각화
  logo_prompt.py           로고용 영어 프롬프트 생성
```

각 단계는 **파일 하나 · 함수 하나**로 분리되어 있습니다.
넘기는 형식만 지키면 내부 구현은 자유입니다.

---

## 테스트

```bash
python -m pytest -q
```

**166개.** 전부 실패 상황을 검증합니다 — 단계 파일이 없을 때, 코드가 예외를 던질 때,
규격이 어긋날 때, 저장이 불가능할 때, 입력이 잘못됐을 때,
LLM 이 hex 를 소문자나 `rgb()` 로 줬을 때, 로고 프롬프트에 한국어가 섞였을 때.

테스트는 **실제 API 를 부르지 않습니다.** `conftest.py` 가 키를 지우고 네트워크를 막습니다 —
막지 않으면 "키가 없을 때" 를 시험하려던 테스트가 남아 있는 다른 키를 주워 실제로 호출합니다.

---

## 문서

| 문서 | 내용 |
| --- | --- |
| [`docs/데이터-계약.md`](docs/데이터-계약.md) | 단계 간 입출력 규격 |
| [`docs/명세-점검표.md`](docs/명세-점검표.md) | 명세 요구사항과 구현 대조표 |

---

## 실행 환경

| | |
| --- | --- |
| Python | **3.10 이상** — 과제 명세가 정한 기준입니다 |
| 확인한 환경 | Windows 11 · Python 3.14.2 |
| 운영체제 | 무관 — OS 전용 API를 쓰지 않습니다 |

`str | None` 같은 표기를 쓰지만 모든 파일이 `from __future__ import annotations`로
시작하므로 표기 자체가 하위 버전에서 문제를 일으키지는 않습니다.
다만 **3.10 미만에서는 검증하지 않았습니다.**

한글 Windows 콘솔(cp949)에서 이모지가 깨지지 않도록 표준 출력을 UTF-8로 다시 엽니다.

---

이 저장소는 대전 Code Odyssey · AI 활용 실습 Term Project 제출물입니다.
