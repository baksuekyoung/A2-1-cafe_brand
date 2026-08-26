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

필수 패키지는 없습니다. 있으면 결과가 나아지는 선택 항목입니다.
(`python-dotenv` 키 읽기 · `matplotlib` 팔레트에 색 이름 표시 · `pillow` JPEG→PNG 변환)

### 2. API 키 등록

`.env.example`을 `.env`로 복사하고 **아래 중 하나**를 채웁니다.

```
CODYSSEY_OPENAI_KEY=코디세이_공개_API_키    ← 권장
OPENAI_API_KEY=본인의_API_키
GEMINI_API_KEY=본인의_API_키
```

**코디세이 공개 API를 먼저 씁니다.** 소속 기관 키로 정산되어 개인 결제분을 쓰지 않고,
텍스트와 이미지를 한 키로 처리합니다. 콘솔에서 **OpenAI 호환** 키를 발급받으세요
(`Anthropic` 호환 키는 채팅에서 거부됩니다).

```bash
python test_api.py      # 연결 확인
```

공급자는 **코디세이 → OpenAI → Gemini → Pollinations** 순으로 시도합니다.
앞이 막히면 다음으로 넘어가므로 어느 하나만 있어도 됩니다.

> 키가 없으면 [2]·[3]이 예시 값으로 채워집니다. 파이프라인 확인용 폴백이므로
> **실제 AI 생성 결과를 얻으려면 키가 필요합니다.** 예시 값을 쓴 자리는 `run_report.md`에 기록됩니다.

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

인자로 한 번에 돌릴 수도 있습니다. 준 인자만 묻지 않고 건너뜁니다.

```bash
python main.py --brief samples/brief.json --output ./output --logos 3
```

| 인자 | 값 |
| --- | --- |
| `--brief` | 브리프 JSON 경로 |
| `--output` | 출력 폴더 (기본 `./output`) |
| `--logos` | 로고 시안 수 — `2` 또는 `3` (기본 2) |

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
| 선택 | `tone` `competitors` `notes` |

파일 없음 · `.json` 아님 · JSON 문법 오류 · 필수 필드 누락 · 자료형 불일치를
각각 구분해서 안내합니다. JSON 문법 오류는 몇 번째 줄인지 알려 줍니다.

---

## 출력

| 파일 | 내용 |
| --- | --- |
| **`brand_result.json`** | **텍스트 결과 전체** (명세 요구) |
| **`color_palette.png`** | **컬러 팔레트 시각화** (명세 요구) |
| **`logo_01.png` …** | **로고 시안** (명세 요구) — 요청한 장수만큼 `logo_03.png` 까지 |
| `brand_result.md` | 사람이 읽는 결과 문서 |
| `logo_prompts.md` | 로고 생성에 쓴 영어 프롬프트 |
| `run_report.md` | 단계별 성공·실패와 규격 위반 기록 |
| `brand_tokens.css` | 컬러 팔레트를 CSS 변수로 |

### 실제 생성 결과

`output/` 폴더에 실행 결과를 그대로 담아 두었습니다.

**컬러 팔레트**

![컬러 팔레트](output/color_palette.png)

**로고 시안** — `--logos 3`으로 3장 생성

| 시안 1 | 시안 2 | 시안 3 |
| --- | --- | --- |
| <img src="output/logo_01.png" width="220"> | <img src="output/logo_02.png" width="220"> | <img src="output/logo_03.png" width="220"> |
| 면으로 채운 기하 아이콘 | 굵은 획 픽토그램 | 이어진 선 엠블럼 |

시안마다 다른 프롬프트 템플릿을 씁니다. 같은 그림이 여러 장 나오면 시안이 아니기 때문입니다.
셋 다 팔레트 메인 컬러 계열이고, 글자가 들어가지 않습니다.

**네이밍** — 후보마다 다른 유형으로, 한글 이름과 영문 표기를 함께

| 이름 | 영문 표기 | 유형 |
| --- | --- | --- |
| 누크 | NOOK | 은유·조어 |
| 로웰 | LOWELL | 문학·인물 |
| 온즈 | OUNCE | 제품 직관 |
| 멜로우 | MELLOW | 속성 강조 |
| 에이커 | ACRE | 지명·역사 |

**슬로건 3개 · 브랜드 스토리 314자 · 경쟁사 분석 2건**도 함께 나옵니다.
텍스트 결과 전체는 [`output/brand_result.md`](output/brand_result.md)에 있습니다.

> 위 결과는 **코디세이 공개 API**로 생성했습니다. 예시 값으로 대체된 자리는 없습니다
> ([`output/run_report.md`](output/run_report.md) 참고).

---

## 명세 충족 현황

| 명세 요구사항 | 상태 | 구현 |
| --- | :---: | --- |
| 1. `print`·`input` 대화형 입력 | ✅ | `main.py` — `ask_brief` · `ask_output` |
| 2. JSON 브리프 (필수/선택 필드) | ✅ | `main.py` — `load_brief` + `validate.check_brief` |
| 3. LLM으로 브랜드명 3~5개 + 의미 | ✅ | `naming.py` — **4개 이상** 요구 |
| 4. LLM으로 슬로건 3개 | ✅ | `naming.py` |
| 5. LLM으로 스토리 300자 내외 | ✅ | `naming.py` — 280자 미달 시 재요청 |
| 6. LLM으로 컬러 팔레트 + PNG 시각화 | ✅ | `palette.py` · `palette_png.py` |
| 7. 이미지 API로 로고 2~3개 PNG | ✅ | `logo.py` — 코디세이→OpenAI→Gemini→Pollinations |
| 8. `brand_result.json` + 개별 PNG 저장 | ✅ | `store.py` |
| 9. API 실패 시 안내 후 다음 단계 진행 | ✅ | `runner.run_step` |
| 10. 키를 코드에 쓰지 않음 | ✅ | `.env` → `load_dotenv()` |
| 보너스 · 다국어 네이밍 | ✅ **선택** | 한글 + 영문 표기 + 읽는 법 |
| 보너스 · 경쟁사 분석 | ✅ 함께 구현 | 차별화 포인트 제안 |

자세한 대조는 [`docs/명세-점검표.md`](docs/명세-점검표.md)에 있습니다.

---

## 주요 해결 과제

돌려 보고 결과를 열어 확인하며 고친 것들입니다.

| 문제 | 조치 |
| --- | --- |
| **[3] 컬러 팔레트에 LLM 호출이 없었음** — 어떤 브리프를 넣어도 같은 색이 나오는데 리포트는 "완료" | 실제 LLM 생성으로 구현. [2]가 정한 브랜드명·스토리를 프롬프트에 반영 |
| 산출물 PNG가 `.gitignore`에 막혀 저장소에 없었음 | 산출물만 예외 처리해 커밋 |
| 스토리가 204자 (명세 300자 내외) | 280자 미달 시 최대 2회 재요청 |
| 로고가 2장 고정 (명세 2~3개) | 세 번째 프롬프트 템플릿 추가 |
| 네이밍이 `여유카페·감성커피`처럼 평범 | 업종어·키워드 복붙·유형 쏠림을 프롬프트에서 차단 |
| 로고 글자가 깨져 나옴 | `logo` 대신 `icon`·`symbol`, 브랜드명 제외, 글자 금지를 반복 |
| 팔레트 PNG 저장 실패가 실행 전체를 중단 | 예외를 넓게 잡고 내장 렌더러로 폴백 |
| 키가 거부돼도(401) 조용히 넘어감 | 그 사실을 출력 |
| 예시 값 대체가 제출물에 안 남음 | `run_report.md`에 기록 |
| 테스트가 실제 API를 호출 (17.6초) | `conftest.py`가 키 제거 + 네트워크 차단 (2.0초) |
| 이미지 생성에 개인 결제분이 들어감 | **코디세이 공개 API**를 공급자 맨 앞에 붙임 (기관 키로 정산) |
| `brief.py`가 검증을 건너뜀 — 이름만 `main`과 같고 실제로는 샘플 파일을 그냥 읽음 | `main.load_brief`를 부르게 통일. 필수 필드 없는 브리프가 통과하던 문제 해결 |

---

## 구조

```
main.py              진입점 — 대화형 입력과 [1] 브리프 읽기·검증(실제 구현)
integrate.py         [5] 통합 실행
test_api.py          API 연결 테스트

brief.py             [1] load_brief() -> dict  — main 의 검증을 부른다
                         (integrate.py 를 단독으로 돌릴 때만 쓰입니다)
naming.py            [2] generate_naming(brief) -> dict
palette.py           [3] generate_palette(brief, naming) -> dict
logo.py              [4] generate_logos(brief, naming, palette) -> list

brand_result/
  runner.py          단계 호출과 예외 격리
  validate.py        데이터 계약 검증
  store.py           파일 저장 · 명도 대비 계산
  report.py          결과 문서 생성
  palette_png.py     컬러 팔레트 PNG 시각화
  logo_prompt.py     로고용 영어 프롬프트 생성
```

각 단계는 **파일 하나 · 함수 하나**입니다. 넘기는 형식만 지키면 내부 구현은 자유입니다.
규격은 [`docs/데이터-계약.md`](docs/데이터-계약.md)에 있습니다.

---

## 테스트

```bash
python -m pytest -q
```

**185개.** 대부분 실패 상황을 검증합니다 — 단계 파일이 없을 때, 코드가 예외를 던질 때,
규격이 어긋날 때, 저장이 불가능할 때, 입력이 잘못됐을 때,
LLM이 hex를 소문자나 `rgb()`로 줬을 때, 로고 프롬프트에 한국어가 섞였을 때.

테스트는 실제 API를 부르지 않습니다. `conftest.py`가 키를 지우고 네트워크를 막습니다.

---

Windows 11 · **Python 3.14.2**(2025-12-05 배포)에서 확인했습니다.
3.10 이상이면 동작합니다 — `match` 등 3.10 전용 문법은 쓰지 않습니다.
OS 전용 API도 쓰지 않습니다.
