# 브랜드 아이덴티티 생성기

**저장소: <https://github.com/baksuekyoung/A2-1-cafe_brand>**

브랜드 브리프(업종·타깃·키워드)를 JSON으로 입력하면 **브랜드명·슬로건·스토리·컬러 팔레트·로고 시안**을
AI로 생성해 파일로 저장하는 CLI 프로그램입니다.

> [Project A] · 주제 **카페** · Python 3.10 이상

| 증빙 문서 | 내용 |
| --- | --- |
| [`docs/environment-setup.md`](docs/environment-setup.md) | 개발 환경 · `.gitignore` 근거 |
| [`docs/execution-log.md`](docs/execution-log.md) | 실행 전문 · 오류 5가지 · 보안 확인 |
| [`docs/git-log.md`](docs/git-log.md) | 커밋 이력과 브랜치 그래프 |
| [`docs/명세-점검표.md`](docs/명세-점검표.md) | 명세 요구사항 대조표 |
| [`docs/데이터-계약.md`](docs/데이터-계약.md) | 단계 간 입출력 규격 |

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

`.env.example`을 `.env`로 복사하고 키를 채웁니다.

```
CODYSSEY_OPENAI_KEY=코디세이_공개_API_키
CODYSSEY_BASE_URL=https://copa.codyssey.kr
```

**코디세이 공개 API를 씁니다.** 소속 기관 키로 정산되어 개인 결제분을 쓰지 않고,
텍스트와 이미지를 이 키 하나로 처리합니다.

발급은 [API 콘솔](https://usr.codyssey.kr/daejeon/public-api-console) →
`MY` > `API 키 관리` > `키 발급` 입니다. 호환 방식은 반드시 **OpenAI** 로 고르세요
(`Anthropic` 호환 키는 채팅에서 HTTP 403 이 납니다).

```bash
python test_api.py              # 연결 확인 (채팅만 — 한도를 쓰지 않음)
python test_api.py --image      # 이미지 생성까지 확인 (호출 1회 차감)
```

코디세이가 막히면 **Pollinations**(키 불필요)로 이어져 로고는 계속 생성됩니다.
명세 9번(*"API 실패 시 다음 단계를 계속 진행"*)을 위한 폴백입니다.

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

**네이밍** — 후보마다 다른 유형으로, 한글 이름·영문 표기·읽는 법을 함께

| 이름 | 영문 표기 | 읽는 법 | 유형 |
| --- | --- | --- | --- |
| 페이즈 | Paze | PA-zeuh | 은유·조어 |
| 온김 | Ongim | OWN-gim | 제품 직관 |
| 소로우 | Thoreau | thuh-ROW | 문학·인물 |
| 모먼 | Momen | MO-muhn | 속성 강조 |
| 브리엔츠 | Brienz | BREE-enz | 지명·역사 |

**슬로건 3개 · 브랜드 스토리 286자 · 경쟁사 분석 2건**도 함께 나옵니다.
텍스트 결과 전체는 [`output/brand_result.md`](output/brand_result.md)에 있습니다.

> 위 결과는 **코디세이 공개 API**로 생성했습니다. 예시 값으로 대체된 자리는 없습니다
> ([`output/run_report.md`](output/run_report.md) 참고).

---

## 보너스 — 경쟁사 분석 (1번 선택)

> 명세의 보너스 두 가지 중 **1번** 을 택했습니다.
> *"입력된 경쟁사 브랜드를 분석하여 차별화 포인트를 제안한다"*

브리프의 `competitors` 에 적힌 브랜드를 하나씩 짚어 **세 가지**를 냅니다.

| 필드 | 무엇 |
| --- | --- |
| `competitor` | 경쟁사 이름 |
| `position` | 그 브랜드가 시장에서 차지한 자리 |
| `differentiation` | **우리가 다르게 갈 지점** |

### 실제 생성 결과

| 경쟁사 | 시장에서의 자리 | 우리가 다르게 갈 지점 |
| --- | --- | --- |
| **블루보틀** | 미니멀리즘과 스페셜티 커피의 전문성을 강조하며 브랜드 마니아층을 확보했습니다. | 전문가적인 시선보다는 사용자의 정서적 휴식에 집중하여 보다 포근하고 아늑한 공간 경험을 제공합니다. |
| **스타벅스** | 제3의 공간으로서 표준화된 서비스와 대중적인 접근성을 바탕으로 시장을 점유하고 있습니다. | 표준화된 활기보다는 각 매장만의 고유한 감성과 느린 호흡을 강조하여 대화보다는 사색에 적합한 분위기를 조성합니다. |

### 어떻게 만드는가

프롬프트(`COMPETITOR_RULE`)가 조건을 못 박습니다.

- 경쟁사마다 `competitor` · `position` · `differentiation` 세 가지를 모두 채운다
- **막연한 말 대신 이 브리프의 타깃·키워드에 근거해** 구체적으로 쓴다
- 경쟁사가 없으면 빈 배열로 둔다 (선택 필드이므로 없어도 규격 위반이 아니다)

차별화 포인트는 [2] 단계의 브랜드 스토리·컬러 방향과 이어집니다.
경쟁사를 나열만 하고 끝내면 분석이 아니기 때문입니다.

> **다국어 네이밍(2번)도 함께 구현했습니다.** 택한 것은 1번이지만,
> 후보마다 한글 이름·영문 표기·읽는 법을 함께 내고 검증합니다.
> 자세한 것은 아래 [다국어 네이밍](#덤--다국어-네이밍-2번) 절에 있습니다.

---

## 덤 — 다국어 네이밍 (2번)

택하지 않았지만 동작합니다. 후보마다 **세 가지**를 함께 만듭니다.

| 필드 | 무엇 | 예 |
| --- | --- | --- |
| `name` | 한글 이름 | 쉼표 |
| `english` | 영문 표기 | Comma |
| `reading` | 읽는 법 | COM-ma |

결과 문서에는 `쉼표 (Comma, COM-ma)` 형태로 실립니다.

영문 표기는 **간판·도메인·SNS 계정에 그대로 쓸 수 있게** 알파벳 12자 안쪽으로 짓고,
읽는 법은 영문 표기를 베끼지 않고 음절을 하이픈으로 나눕니다 (`Ongi → OWN-gee`).
어긋나면 `run_report.md`에 기록됩니다. **버리지는 않습니다** — 채택은 사람이 판단할 문제입니다.

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
| **보너스 1번 · 경쟁사 분석** | ✅ **← 우리가 택한 것** | 경쟁사마다 시장 위치 + **차별화 포인트** 제안 |
| 보너스 2번 · 다국어 네이밍 | ✅ 덤으로 구현 | 택하지 않았지만 동작합니다 |

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

## 주요 함수

각 단계는 **파일 하나 · 함수 하나**입니다. 이름과 시그니처는
[`docs/데이터-계약.md`](docs/데이터-계약.md)가 정한 계약이며, `runner.STEPS`가 코드 쪽 표현입니다.

### 파이프라인 — 단계별 진입점

| 함수 | 인수 | 반환 | 역할 |
| --- | --- | --- | --- |
| `brief.load_brief()` | 없음 | `dict` | [1] 브리프를 읽어 검증. `main.load_brief`를 부른다 |
| `naming.generate_naming(brief)` | `dict` | `dict` | [2] 브랜드명·슬로건·스토리·경쟁사 분석 |
| `palette.generate_palette(brief, naming)` | `dict`, `dict` 또는 `None` | `dict` | [3] 메인 1 + 서브 2~3 컬러 |
| `logo.generate_logos(brief, naming, palette)` | `dict`, `dict`/`None`, `dict`/`None` | `list` | [4] 로고 시안 2~3장 |

앞 단계가 실패하면 그 자리에 `None`이 들어옵니다. **뒤 단계는 `None`을 받아도 죽지 않습니다.**

### 진입점과 입력

| 함수 | 인수 | 반환 | 역할 |
| --- | --- | --- | --- |
| `main.main(argv=None)` | `list[str]` 또는 `None` | `int` | 프로그램 시작. 종료 코드를 돌려준다 |
| `main.parse_args(argv=None)` | `list[str]` 또는 `None` | `Namespace` | `--brief` `--output` `--logos`를 읽는다 |
| `main.ask_brief(path_text=None)` | `str` 또는 `None` | `dict` | 경로를 묻고 검증. 인자를 주면 묻지 않는다 |
| `main.ask_output(path_text=None)` | `str` 또는 `None` | `str` | 출력 폴더를 묻는다. 엔터면 `./output` |
| `main.load_brief(path_text)` | `str` | `dict` | **읽고 검증하는 알맹이.** 오류마다 다른 메시지 |

`load_brief`는 `BriefError`를 던집니다 — 파일 없음·확장자 오류·JSON 문법 오류·
필수 필드 누락·자료형 불일치를 각각 구분합니다.

### 통합과 검증

| 함수 | 인수 | 반환 | 역할 |
| --- | --- | --- | --- |
| `integrate.run(output, debug, brief)` | `str`, `bool`, `dict`/`None` | `int` | [5] 네 단계를 돌리고 저장. `0` 정상 / `1` 저장 실패 / `2` 폴더 실패 |
| `runner.run_step(label, module, func, checker, *args)` | — | `StepResult` | 한 단계 실행. **무슨 일이 있어도** `StepResult`를 돌려준다 |
| `runner.run_all(brief, debug)` | `dict`/`None`, `bool` | `list[StepResult]` | [1]→[4] 순서대로. 앞이 무너져도 뒤를 시도 |
| `runner.to_result_dict(results, generated_at)` | `list`, `str` | `dict` | 저장용 형태로. 실패한 자리는 `None` |
| `validate.check_brief(brief)` | `object` | `list[str]` | 규격 위반 목록. **빈 리스트면 통과** |
| `validate.check_naming(naming)` | `object` | `list[str]` | 개수·길이·영문 표기·읽는 법·개성까지 |
| `validate.check_palette(palette)` | `object` | `list[str]` | hex 형식과 개수 |
| `validate.check_logos(logos)` | `object` | `list[str]` | 자리표시자 이미지도 위반으로 잡는다 |

검증 함수는 **예외를 던지지 않고 문자열 목록을 돌려줍니다.** 어긋나도 버리지 않고
`run_report.md`에 적기 위해서입니다 — 채택은 사람이 판단할 문제입니다.

### 저장과 문서

| 함수 | 인수 | 반환 | 역할 |
| --- | --- | --- | --- |
| `store.ensure_output_dir(path)` | `str` | `Path` | 출력 폴더 생성 |
| `store.save_json(result, output_dir)` | `dict`, `Path` | `Path` | `brand_result.json` (한글 그대로) |
| `store.save_logos(logos, output_dir)` | `list`, `Path` | `list[Path]` | `logo_01.png` 형식으로 |
| `store.save_css_tokens(palette, output_dir)` | `dict`, `Path` | `Path` | 컬러를 CSS 변수로 |
| `store.contrast_ratio(fg, bg)` | `str`, `str` | `float` | WCAG 명도 대비 (1.0~21.0) |
| `store.relative_luminance(hex_color)` | `str` | `float` | 상대 휘도 (0.0~1.0) |
| `report.build_markdown(payload)` | `dict` | `str` | 사람이 읽는 결과 문서 |
| `report.build_run_report(payload)` | `dict` | `str` | 단계별 성공·실패·예시 값 사용 여부 |
| `report.strip_bytes(payload)` | `dict` | `dict` | JSON 저장 전 이미지 바이트 제거 |
| `palette_png.save_palette_png(palette, output_dir)` | `dict`, `Path` | `Path` | 팔레트 PNG. matplotlib 없으면 직접 인코딩 |
| `logo_prompt.make_prompts(brief, naming, palette, count)` | — | `list[str]` | 로고용 **영어** 프롬프트 |
| `logo_prompt.build_human_prompts(brief, palette, count)` | — | `list[str]` | ChatGPT 등 대화형 도구용 문장 |

---

## 데이터 구조

단계 사이에 오가는 것은 전부 **`dict`와 `list`** 입니다. 클래스를 두지 않은 이유는
[설계 근거](#설계-근거)에 있습니다.

### [1] 브리프 — 입력

```python
{
    "industry": "카페",                              # 필수 · str
    "target": "20~30대 직장인, 일상 속 여유를 찾는 사람",  # 필수 · str
    "keywords": ["여유", "따뜻함", "일상의 쉼표"],        # 필수 · list[str], 2개 이상
    "tone": "따뜻하고 감성적이며 과하지 않게 세련된 분위기",   # 선택 · str
    "competitors": ["블루보틀", "스타벅스"],             # 선택 · list[str]
    "notes": "한글과 영어로 모두 활용하기 쉬운 이름을 원함",   # 선택 · str
}
```

선택 필드는 **`main.py`가 기본값을 채워** 넘깁니다(`OPTIONAL_DEFAULTS`).
그래서 뒤 단계는 키가 있는지 매번 확인하지 않아도 됩니다.

### [2] 네이밍 — 후보마다 다섯 항목

```python
{
    "naming": [
        {
            "name": "페이즈",          # 한글 이름
            "english": "Paze",        # 영문 표기 (보너스 2번)
            "reading": "PA-zeuh",     # 읽는 법 (보너스 2번)
            "meaning": "Pace(속도)와 Pause(멈춤)를 결합하여…",
            "type": "3",              # 네이밍 유형 1~5. 겹치면 쏠림으로 잡는다
        },
        # … 4~5개
    ],
    "slogans": ["…", "…", "…"],        # 정확히 3개
    "story": "…",                      # 300자 내외
    "competitors": [                   # 보너스 1번 — 택한 것
        {
            "competitor": "블루보틀",
            "position": "미니멀리즘과 스페셜티 커피의 전문성을…",
            "differentiation": "전문가적인 시선보다는 정서적 휴식에…",
        },
    ],
    "used_example": True,              # 예시 값으로 대체됐을 때만 붙는다
}
```

### [3] 컬러 팔레트

```python
{
    "main": {
        "hex": "#5B3E2F",              # '#RRGGBB' 대문자 6자리
        "name": "모카 브라운",
        "reason": "원두를 볶은 색에서 가져왔습니다",
    },
    "subs": [                          # 2~3개
        {"hex": "#F6EDE3", "name": "크림 베이지", "reason": "여백을 만듭니다"},
        {"hex": "#C77A3B", "name": "호박빛", "reason": "포인트 색입니다"},
    ],
}
```

`hex` 형식이 어긋나면 [5]가 **명도 대비를 계산하지 못합니다.** 그래서 소문자나 `#` 누락은
`_normalize_color`가 고치고, 고칠 수 없는 값(`rgb(...)` 등)은 버립니다.

### [4] 로고

```python
[
    {
        "image_bytes": b"...PNG 바이트...",
        "prompt": "minimalist geometric icon, single abstract symbol…",
        "source": "codyssey",     # codyssey|openai|gemini|pollinations|placeholder
    },
    # … 2~3장
]
```

`image_bytes`는 **저장 직후 JSON에서 빠집니다**(`report.strip_bytes`).
바이트를 JSON에 넣을 수 없고, 넣더라도 사람이 읽을 수 없기 때문입니다.

### [5] 최종 결과 — `brand_result.json`

```python
{
    "generated_at": "2026-08-26T15:55:33",
    "brief":   {...},      # [1]
    "naming":  {...},      # [2]
    "palette": {...},      # [3]
    "logos":   [...],      # [4] — 이미지 바이트는 빠지고 프롬프트·출처만
    "steps": [             # 단계별 실행 기록
        {"step": "[1] 브리프", "status": "ok", "message": "", "problems": []},
        # status: ok | missing | failed | skipped
    ],
}
```

**실패한 단계는 그 자리가 `None`** 입니다. 키 자체를 없애지 않는 이유는,
받는 쪽이 "없는 것"과 "실패한 것"을 구분할 수 있어야 하기 때문입니다.

---

## 설계 근거

### 왜 `dict`인가 — 클래스를 두지 않은 이유

네 단계를 네 사람이 나눠 맡았습니다. 클래스를 공유하면 **한 사람이 필드를 바꿀 때마다
나머지 셋이 함께 고쳐야** 합니다. `dict`와 문자열 키로 두면 각자 독립적으로 작업하고,
형식이 맞는지는 `validate.py` 한 곳에서만 봅니다.

그 대가로 오타를 미리 잡지 못합니다. 그래서 **검증 함수와 테스트 192개**로 막습니다.

### 왜 검증이 예외를 안 던지는가

`check_*`는 문제를 **문자열 목록으로** 돌려줍니다. 예외를 던지면 거기서 멈춰
"몇 개가 잘못됐는지"를 한 번에 볼 수 없습니다.

```python
problems = validate.check_brief(brief)   # [] 면 통과
```

브리프 오류를 한 번에 모두 보여 주는 것도 같은 이유입니다 — 하나씩 알려 주면
고치고 다시 돌리기를 반복해야 합니다.

### 왜 폴백 체인인가

명세 9번이 *"API 실패 시 다음 단계를 계속 진행"*을 요구합니다.
LLM API는 쿼터·권한·안전필터로 자주 막힙니다. 한 곳이 막혔다고 전체가 멈추면
**아무 산출물도 못 냅니다.**

```
코디세이 → OpenAI → Gemini → Pollinations → 예시 값
```

앞이 막히면 다음으로 넘어갑니다. 대신 **어느 쪽을 썼는지 반드시 기록**합니다
(`used_example` → `run_report.md`). 안 그러면 받는 사람이 예시 값을 실제 생성 결과로
착각합니다.

### 왜 `openai` 패키지를 안 쓰는가

HTTP 요청 한 번이면 되는 일입니다. 게다가 이 환경에서 그 패키지는 import조차
실패했습니다 — `openai → httpx → httpcore → truststore → ctypes`를 타고 들어가는데
파이썬 설치의 `_ctypes`가 깨져 있었습니다.

`urllib.request`로 직접 부르면 의존성이 하나도 없고, 어느 환경에서든 돕니다.

### 왜 프롬프트 구조를 LLM에게 안 맡기는가

로고 프롬프트를 LLM이 다시 쓰게 했더니 **검증된 규칙이 전부 사라졌습니다.**

```
나간 것 : minimalist geometric icon representing tranquility... warm colors
사라진 것: pure white background / no lettering / roasted coffee brown
```

지금은 `PROMPT_TEMPLATES`가 문장 구조를 쥐고, **LLM은 낱말 번역만** 합니다.

### 왜 산출물을 저장소에 커밋하는가

명세가 *"PNG 파일로 저장"*을 요구합니다. `.gitignore`가 `output/`을 통째로 막고 있어
로고도 팔레트도 올라가지 않았습니다. 산출물(png·json·md·css)만 예외로 두었습니다.

---

## 엣지 케이스 정책

동작이 갈릴 수 있는 곳에서 **무엇을 택했는지** 밝힙니다.

| 상황 | 어떻게 하는가 | 왜 |
| --- | --- | --- |
| 필수 필드가 여러 개 빠짐 | **한 번에 모두** 알려 준다 | 하나씩 알려 주면 고치고 다시 돌리기를 반복해야 함 |
| JSON 문법 오류 | **몇 번째 줄**인지 알려 준다 | 줄 번호가 없으면 찾을 수 없음 |
| 선택 필드가 없음 | 기본값을 채워 다음 단계로 | 뒤 단계가 키 존재를 매번 확인하지 않게 |
| 대화형에서 잘못된 경로 | **다시 묻는다** | 사람이 보고 있으므로 고칠 수 있음 |
| 인자(`--brief`)가 잘못됨 | **종료 코드 2로 멈춘다** | 자동화 중에는 되물어도 답할 사람이 없음 |
| 앞 단계 실패 | 뒤 단계에 `None`을 넘기고 계속 | 명세 9번 |
| 네이밍이 3개 미만 | 예시 값으로 대체 | 이름 하나로 뒤 단계를 돌릴 수 없음 |
| 스토리가 280자 미만 | **최대 2회 다시 청한다** | 명세는 300자 내외. 못 늘리면 가장 긴 것을 씀 |
| 스토리가 빈 문자열 | 브리프로 **새로 써 달라**고 청한다 | 늘릴 원문이 없으므로 |
| 이름에 업종어(`○○카페`) | 잡아서 리포트에 적는다 | **버리지 않음** — 채택은 사람 판단 |
| 후보 유형이 겹침 | 위와 같음 | 후보가 서로 닮으면 고를 여지가 없음 |
| `reading`이 `english`와 같음 | 위와 같음 | 읽는 법을 알려 주지 못함 |
| 후보 글자 수가 모두 같음 | **잡지 않는다** | 한글 브랜드명은 2~3글자가 자연스러움 |
| hex가 소문자거나 `#` 누락 | 고쳐서 쓴다 | 자주 나는 형식 오류 |
| hex가 `rgb(...)`나 3자리 | 버린다 | 명도 대비를 계산할 수 없음 |
| 서브 컬러가 4개 이상 | **앞 3개만** 쓴다 | 계약이 2~3개 |
| 메인이 흰 배경에 묻힘 | 1회 다시 청한다 | 로고를 이 색으로 그림 |
| 다시 받은 것도 밝음 | 원래 것을 쓰고 경고만 남긴다 | 색은 사람이 판단할 문제 |
| 이미지가 JPEG로 옴 | Pillow로 변환. 없으면 **그 시안을 건너뛴다** | 확장자만 바꾸면 깨진 파일 |
| 모든 이미지 API 실패 | 1×1 투명 PNG + **규격 위반으로 기록** | 파일은 있으나 내용이 없음을 알려야 함 |
| 한 파일 저장 실패 | 나머지는 저장한다 | 하나 때문에 전부 잃지 않게 |
| 저장을 한 건도 못 함 | 종료 코드 1 | 조용히 성공한 척하지 않음 |

---

## 알려진 한계

정직하게 적습니다.

### 1. 로고 색이 팔레트와 정확히 같지는 않습니다

이미지 생성 API는 hex 코드를 정밀하게 지키지 못합니다. 프롬프트에 색 **이름**
(`roasted coffee brown`)을 넣으므로 계열은 맞지만 값은 어긋납니다.
정확한 색이 필요하면 벡터 편집기에서 직접 맞춰야 합니다.

### 2. 로고 시안은 최대 3장입니다

프롬프트 템플릿이 3개입니다. 4장 이상을 요청해도 `min(count, len(PROMPT_TEMPLATES))`로
잘려 조용히 모자라게 나옵니다. 지금은 `--logos`가 2~3으로 제한돼 드러나지 않습니다.

### 3. 네이밍 유형은 LLM의 자기 분류입니다

`type`은 모델이 스스로 붙인 번호입니다. `테라스`를 "지명·역사형"으로 분류한 적이
있는데 정확하다고 보기 어렵습니다. **유형 번호는 쏠림을 감지하는 용도**이지
분류의 정확성을 보장하지 않습니다.

### 4. 규격 위반을 걸러 내지 않습니다

업종어·유형 쏠림·읽는 법 베끼기는 **기록만 하고 버리지 않습니다.**
`run_report.md`를 읽지 않으면 그대로 쓰게 됩니다. 의도한 설계이지만
자동으로 걸러 주기를 기대했다면 어긋납니다.

### 5. 한국어 브리프만 검증했습니다

프롬프트가 한국어로 되어 있습니다. 영어 브리프를 넣어도 돌아가지만 결과 품질은
확인하지 않았습니다.

### 6. Python 3.10 미만은 검증하지 않았습니다

명세가 3.10 이상을 요구하므로 그 아래는 시험하지 않았습니다.
`match` 같은 3.10 전용 문법은 쓰지 않으며, 모든 파일이
`from __future__ import annotations`로 시작합니다.

### 7. 로고 생성이 느립니다

3장에 2~4분 걸립니다. 이미지 생성 API가 본래 느리고, 순서대로 부르기 때문입니다.
동시에 부르면 빨라지지만 실패 처리가 복잡해져 택하지 않았습니다.

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

**192개.** 대부분 실패 상황을 검증합니다 — 단계 파일이 없을 때, 코드가 예외를 던질 때,
규격이 어긋날 때, 저장이 불가능할 때, 입력이 잘못됐을 때,
LLM이 hex를 소문자나 `rgb()`로 줬을 때, 로고 프롬프트에 한국어가 섞였을 때.

테스트는 실제 API를 부르지 않습니다. `conftest.py`가 키를 지우고 네트워크를 막습니다.

---

Windows 11 · **Python 3.14.2**(2025-12-05 배포)에서 확인했습니다.
3.10 이상이면 동작합니다 — `match` 등 3.10 전용 문법은 쓰지 않습니다.
OS 전용 API도 쓰지 않습니다.
