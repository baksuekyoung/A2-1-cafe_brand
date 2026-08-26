# 실행 증빙

터미널 출력을 **그대로 복사한 텍스트**입니다. 캡처가 아닙니다.
확인 시각: 2026-08-26 · 경로는 읽기 쉽게 `...` 으로 줄였습니다.

| 절 | 무엇을 확인하는가 |
| --- | --- |
| [1](#1-정상-실행) | 정상 실행 — 처음부터 끝까지 |
| [2](#2-잘못된-입력) | 잘못된 입력 5가지를 각각 구분해 안내하는가 |
| [3](#3-명령행-인자로-실행) | 인자 실행과 종료 코드 |
| [4](#4-키가-없을-때-명세-9번) | **API가 없어도 멈추지 않는가** |
| [5](#5-받는-사람-상태로-확인) | 새로 클론해도 그대로 도는가 |
| [6](#6-보안-확인) | 키가 저장소에 없는가 |

---

## 1. 정상 실행

```
$ python main.py

🎨 브랜드 아이덴티티 생성기

브리프 JSON 경로를 입력하세요: samples/brief.json
   📋 카페 · 20~30대 직장인, 일상 속 여유를 찾는 사람
      키워드: 여유, 따뜻함, 일상의 쉼표, 감성

출력 폴더 경로를 입력하세요 (엔터 시 ./output):

🎨 브랜드 아이덴티티 — 결과 통합

   🤖 [2] 코디세이 로 생성했습니다
   🤖 [3] 코디세이 로 생성했습니다 (메인 #5B3E2F · 서브 3개)
   🖼️  [4] 로고 시안 1장 생성 (codyssey)
   🖼️  [4] 로고 시안 1장 생성 (codyssey)
   🖼️  [4] 로고 시안 1장 생성 (codyssey)
  ✅ [1] 브리프
  ✅ [2] 네이밍·슬로건·스토리
  ✅ [3] 컬러 팔레트
  ✅ [4] 로고 시안

  💾 ...\output\brand_result.json
  💾 ...\output\brand_result.md
  💾 ...\output\run_report.md
  💾 ...\output\logo_prompts.md
  💾 ...\output\color_palette.png
  💾 ...\output\brand_tokens.css
  💾 ...\output\logo_01.png
  💾 ...\output\logo_02.png
  💾 ...\output\logo_03.png

✅ 완료 단계 4/4 · ...\output
```

명세가 요구하는 산출물이 모두 나왔습니다.

| 파일 | 명세 요구 |
| --- | :---: |
| `brand_result.json` | ⭕ 텍스트 결과 전체 |
| `color_palette.png` | ⭕ 컬러 팔레트 시각화 |
| `logo_01~03.png` | ⭕ 로고 시안 |

### 생성된 내용 (요약)

```
$ python -c "import json,pathlib; d=json.loads(pathlib.Path('output/brand_result.json').read_text(encoding='utf-8')); ..."

네이밍 5개 · 슬로건 3개 · 스토리 286자 · 로고 3장 · 경쟁사 분석 2건
메인 #5B3E2F · 서브 3개
```

| 이름 | 영문 표기 | 읽는 법 | 유형 |
| --- | --- | --- | --- |
| 페이즈 | Paze | PA-zeuh | 은유·조어 |
| 온김 | Ongim | OWN-gim | 제품 직관 |
| 소로우 | Thoreau | thuh-ROW | 문학·인물 |
| 모먼 | Momen | MO-muhn | 속성 강조 |
| 브리엔츠 | Brienz | BREE-enz | 지명·역사 |

전체 결과는 [`../output/brand_result.md`](../output/brand_result.md) 에 있습니다.

---

## 2. 잘못된 입력

**다섯 경우를 각각 구분해서 안내합니다.** "입력이 잘못됐습니다" 한 줄로 뭉뚱그리면
무엇을 고쳐야 할지 알 수 없기 때문입니다.

### 2-1. 빈 입력 · 없는 파일 · 확장자 오류

대화형은 **올바른 값이 올 때까지 다시 묻습니다.**

```
$ python main.py

🎨 브랜드 아이덴티티 생성기

브리프 JSON 경로를 입력하세요:
❌ 파일 경로를 입력해 주십시오.

브리프 JSON 경로를 입력하세요: 없는파일.json
❌ 파일을 찾을 수 없습니다: 없는파일.json

브리프 JSON 경로를 입력하세요: samples/brief.md
❌ JSON 파일이 아닙니다: brief.md

브리프 JSON 경로를 입력하세요: ^C
입력을 취소했습니다.
```

`Ctrl+C` 나 입력 종료는 종료 코드 `130` 으로 끝냅니다.

### 2-2. JSON 문법 오류 — **몇 번째 줄인지** 알려 줍니다

```
$ cat 문법오류.json
{
  "industry": "카페",
  "target": "직장인",
}
```

```
$ python main.py --brief 문법오류.json

❌ JSON 형식이 잘못되었습니다 (3번째 줄): Illegal trailing comma before end of object
```

줄 번호가 없으면 어디를 고쳐야 할지 찾을 수 없습니다.

### 2-3. 필수 필드 누락 — **빠진 필드를 이름으로** 알려 줍니다

```
$ cat 필드누락.json
{"industry": "카페"}
```

```
$ python main.py --brief 필드누락.json

❌ 브리프가 규격과 다릅니다.
   - [1] brief: 'target' 키가 없습니다
   - [1] brief: 'keywords' 키가 없습니다
```

**빠진 것을 한 번에 모두** 보여 줍니다. 하나씩 알려 주면 고치고 다시 돌리기를 반복해야 합니다.

### 2-4. 자료형 불일치

```
$ cat 자료형오류.json
{"industry": "카페", "target": "직장인", "keywords": "여유"}
```

```
$ python main.py --brief 자료형오류.json

❌ 브리프가 규격과 다릅니다.
   - [1] brief: keywords 가 list 가 아닙니다
```

`keywords` 는 낱말 하나가 아니라 **목록**이어야 합니다.

---

## 3. 명령행 인자로 실행

명세는 `print`·`input` 대화형을 요구하므로 그것이 기본입니다.
인자는 같은 결과를 다시 만들어야 할 때(자동화·시연·채점 재현)를 위한 것입니다.

```
$ python main.py --help
usage: main.py [-h] [--brief BRIEF] [--output OUTPUT] [--logos {2,3}]

브랜드 브리프로 네이밍·슬로건·스토리·컬러·로고를 만듭니다.

options:
  -h, --help       show this help message and exit
  --brief BRIEF    브리프 JSON 경로 (생략하면 물어봅니다)
  --output OUTPUT  출력 폴더 (생략하면 물어봅니다, 기본 ./output)
  --logos {2,3}    로고 시안 수 (명세는 2~3장, 기본 2장)

인자를 생략하면 대화형으로 물어봅니다.
```

### 종료 코드

인자로 도는 중에는 되물어 봐야 답할 사람이 없으므로 **멈춥니다.**

```
$ python main.py --brief 없는파일.json > /dev/null 2>&1; echo $?
2

$ python main.py --logos 5 > /dev/null 2>&1; echo $?
2
```

`--logos` 는 명세가 정한 2~3 범위 밖을 `argparse` 가 막습니다.

---

## 4. 키가 없을 때 (명세 9번)

> 명세 9번: *"API 호출 실패 시 에러 메시지를 출력하고 **다음 단계를 계속 진행**한다"*

`.env` 가 없는 폴더에서 돌린 결과입니다.

```
$ ls -a | grep -c '^\.env$'
0

$ python main.py

브리프 JSON 경로를 입력하세요: samples/brief.json
출력 폴더 경로를 입력하세요 (엔터 시 ./output):

   ℹ️  [2] API 키가 없어 예시 값으로 돌립니다 (.env 에 CODYSSEY_OPENAI_KEY · OPENAI_API_KEY · GEMINI_API_KEY 중 하나)
   ℹ️  [3] API 키가 없어 예시 값으로 돌립니다 (.env 에 CODYSSEY_OPENAI_KEY · OPENAI_API_KEY · GEMINI_API_KEY 중 하나)
   🖼️  [4] 로고 시안 1장 생성 (pollinations)
   🖼️  [4] 로고 시안 1장 생성 (pollinations)
  ✅ [1] 브리프
  ✅ [2] 네이밍·슬로건·스토리
  ✅ [3] 컬러 팔레트
  ✅ [4] 로고 시안

✅ 완료 단계 4/4 · ...\output
```

**멈추지 않고 끝까지 갑니다.** 로고는 키가 필요 없는 Pollinations 로 넘어가 실제로 생성됩니다.

### 예시 값을 쓴 사실이 제출물에 남습니다

터미널에만 찍고 지나가면 받는 사람은 실제 생성 결과로 착각합니다.

```
$ cat output/run_report.md

# 실행 리포트

실행 시각: 2026-08-26T23:10:28

| 단계 | 상태 | 비고 |
| --- | :---: | --- |
| [1] 브리프 | ✅ 완료 | — |
| [2] 네이밍·슬로건·스토리 | ✅ 완료 | — |
| [3] 컬러 팔레트 | ✅ 완료 | — |
| [4] 로고 시안 | ✅ 완료 | — |

## LLM 대신 예시 값을 쓴 곳

키가 없거나 호출이 실패해 미리 넣어 둔 값으로 채웠습니다.
제출 전에 키를 넣고 다시 돌려야 실제 생성 결과가 나옵니다.

- [2] 네이밍·슬로건·스토리
- [3] 컬러 팔레트
```

> 제출한 `output/` 에는 이 절이 **없습니다.** 전부 실제 API 생성 결과입니다.

### 키가 잘못됐을 때

조용히 다음 공급자로 넘어가면 사용자는 자기 키가 틀린 줄 모릅니다. 그래서 알립니다.

```
   ⚠️  [4] 코디세이 키가 거부되었습니다 (HTTP 403) — .env 의 CODYSSEY_OPENAI_KEY 와 남은 한도를 확인하세요
```

### 외부 패키지가 없을 때

`matplotlib` 과 `PIL` 을 아예 차단하고 팔레트 PNG 를 만들어 봤습니다.

```
$ python - <<'PY'
import sys
class 막는다:
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in {"matplotlib", "PIL"}:
            raise ModuleNotFoundError(f"No module named {name!r}", name=name)
sys.meta_path.insert(0, 막는다())
from brand_result import palette_png
...
PY

PNG 서명: 89504e470d0a1a0a → 정상
크기: 2775 bytes
```

`zlib` 으로 압축하고 `struct` 로 청크를 조립해 **직접 인코딩**하므로 외부 패키지가 필요 없습니다.

---

## 5. 받는 사람 상태로 확인

"내 컴퓨터에서만 되는" 상태가 아닌지 보려고, 제출할 저장소를 **새로 클론해서** 확인했습니다.

```
$ git clone https://github.com/baksuekyoung/A2-1-cafe_brand.git 검증
Cloning into '검증'...

$ cd 검증 && python -m pytest -q
................................................                         [100%]
192 passed in 5.21s
```

```
$ ls -a | grep -c '^\.env$'
0
```

키 파일은 딸려 오지 않습니다. 그 상태로 `python main.py` 를 돌린 결과가 4절입니다.

---

## 6. 보안 확인

```
$ git ls-files | grep -E "^\.env$"
(출력 없음)
```

`.env` 는 추적되지 않습니다. 추적되는 것은 `.env.example` 하나뿐입니다.

```
$ git log -p | grep -icE "sk-proj-[A-Za-z0-9]{20}|sk-cody-live-[A-Za-z0-9]{10}"
0
```

**커밋 이력 전체를 뒤져도 실제 키가 없습니다.** 한 번 커밋되면 나중에 지워도
이력에 남기 때문에 이력까지 확인했습니다.

```
$ cat .env.example
CODYSSEY_OPENAI_KEY=
CODYSSEY_BASE_URL=https://copa.codyssey.kr
OPENAI_API_KEY=
GEMINI_API_KEY=
```

키 **이름만** 있고 값은 비어 있습니다.

---

## 7. 테스트

```
$ python -m pytest -q
................................................                         [100%]
192 passed in 3.01s
```

**대부분 실패 상황을 검증합니다.** 정상 동작은 한 번 돌려 보면 알지만,
실패는 일부러 만들어 보지 않으면 확인할 수 없기 때문입니다.

| 파일 | 개수 | 무엇을 보는가 |
| --- | ---: | --- |
| `test_naming_bonus.py` | 62 | 네이밍·슬로건·스토리, 다국어 보너스, 개성, 스토리 재요청 |
| `test_palette_png.py` | 34 | 팔레트 PNG 인코딩, 로고 프롬프트 |
| `test_palette.py` | 22 | LLM 호출, hex 형식 보정, 메인 대비 재요청 |
| `test_main_input.py` | 22 | 대화형 입력, 브리프 검증, 명령행 인자 |
| `test_codyssey.py` | 17 | 코디세이 연동 — 주소·JSON모드·응답경로·공급자 순서 |
| `test_store_report.py` | 14 | 저장·결과 문서·실행 리포트 |
| `test_runner.py` | 11 | 단계 호출과 예외 격리 |
| `test_validate_brief.py` | 10 | 브리프 규격, 검증 위임 |

**테스트는 실제 API 를 부르지 않습니다.** `conftest.py` 가 키를 지우고
`urllib.request.urlopen` 자체를 막습니다.

막지 않았을 때 실제로 문제가 있었습니다 — `OPENAI_API_KEY` 만 지운 테스트가
남아 있는 `GEMINI_API_KEY` 를 주워 **진짜 API 를 호출**했습니다.
"키가 없을 때" 를 시험하려던 테스트가 정반대로 돌고 있었습니다.

```
막기 전: 17.6초
막은 뒤:  3.0초
```
