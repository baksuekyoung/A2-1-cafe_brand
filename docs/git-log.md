# 커밋 이력

`git` 명령 출력을 **그대로 복사한 텍스트**입니다. 캡처가 아닙니다.
확인 시각: 2026-08-26

---

## 요약

```
$ git rev-list --count HEAD
43
```

커밋 **43개**. 제출 점검표 기준(10개 이상)을 넘습니다.

### 커밋 메시지 타입별

| 타입 | 개수 | 무엇 |
| --- | ---: | --- |
| `feat:` | 16 | 기능 추가 |
| `docs:` | 14 | 문서 |
| `fix:` | 9 | 버그 수정 |
| `chore:` | 3 | 잡일 |
| `merge:` | 1 | 브랜치 병합 |

커밋 메시지는 **한글**로 쓰고 `<타입>: <내용>` 형식을 지킵니다.
무엇이 달라졌는지가 제목에서 읽히게 했습니다.

---

## 브랜치

```
$ git branch -a
  feature/submission-docs
* main
  remotes/origin/HEAD -> origin/main
  remotes/origin/feature/submission-docs
  remotes/origin/main
  remotes/team/HEAD -> team/main
  remotes/team/feature/submission-docs
  remotes/team/main
```

```
$ git log --oneline --merges
dce0564 merge: feature/submission-docs — 제출 증빙 문서를 본선에 반영한다
```

기능 브랜치 `feature/submission-docs` 에서 제출 증빙 문서를 작업한 뒤
**`--no-ff` 로 병합**했습니다. 병합 커밋이 남아 있어 어디서 갈라졌다 합쳐졌는지
이력에서 보입니다.

---

## 전체 그래프

```
$ git log --oneline --graph --all
* ca9713a feat: 생성된 내용을 화면에 바로 보여 준다
* dd5e4a6 chore: .env.example 에서 개인 키 항목을 빼고 코디세이만 남긴다
* d76baea docs: 커밋 이력과 브랜치 그래프를 텍스트로 남긴다
*   dce0564 merge: feature/submission-docs — 제출 증빙 문서를 본선에 반영한다
|\  
| * 34ce2d6 docs: 제출 점검표가 요구하는 증빙 문서를 채운다
|/  
* b66ce1f docs: 보너스 선택을 1번(경쟁사 분석)으로 바꿔 적는다
* 9c114ac feat: 보너스 2번의 읽는 법(reading)을 검증한다
* 341fdba chore: 로컬 확인용 도구를 저장소에서 제외한다
* 5c54410 fix: 연결 확인이 매번 이미지 호출을 쓰던 것을 선택으로 바꾼다
* bd4bf98 fix: 키가 없을 때 안내에서 코디세이가 빠져 있었다
* c6a36d3 docs: 코디세이로 생성한 최종 산출물과 연결 확인 도구를 반영한다
* a9ab905 feat: 코디세이 공개 API 를 공급자 맨 앞에 붙인다
* 467e721 fix: brief.py 가 검증을 건너뛰던 문제를 고친다
* fc6ef45 docs: README 를 제출 요건 중심으로 간결하게 정리한다
* 2b9d823 feat: 네이밍 후보가 평범해지지 않게 세 가지를 막는다
* 1509224 feat: 네이밍을 4~5개로 늘리고, 메인 컬러가 흰 배경에 묻히면 다시 청한다
* 2b431f5 feat: 로고를 3장까지 만들고 실행 인자를 받는다 · README 모순 정리
* 3a61ab6 docs: 명세 점검표를 현재 구현에 맞춰 갱신
* 9334083 feat: 컬러 팔레트를 LLM 생성으로 구현하고 파일명에서 step 접두어 제거
* 998db57 feat: 산출물 PNG 를 저장소에 포함하고 스토리 길이 기준을 명세에 맞춤
* d78eaa3 fix: 스토리가 짧게 오면 그 자리에서 한 번만 다시 청한다
* 0e6df45 docs: README 를 과제 설명 중심으로 정리한다
* 4099ba4 fix: LLM 은 낱말 번역만 맡고 프롬프트 구조는 템플릿이 쥔다
* cda6b3b feat: 보너스를 '다국어 네이밍 지원' 으로 선택하고 제대로 구현한다
* 4ada7c4 fix: 각 단계 파일을 저장소 루트로 옮겨 바로 실행되게 한다
* 9082938 fix: 사람이 직접 쓸 로고 프롬프트를 따로 낸다
* dae7a7d feat: Gemini 를 대체 공급자로 넣고 실제 호출로 검증한다
* ad5de64 feat: 보너스 과제 두 가지를 구현하고 제출용으로 정리한다
* 08d2cbb feat: 명세가 요구하는 팔레트 PNG 와 로고 프롬프트를 낸다
* 3fbe5d9 feat: 명세가 요구하는 대화형 입력을 main.py 에 넣는다
* 45b074c chore: [1] 담당자가 정한 환경 설정을 맞춘다
* 896e5ee feat: [2] 담당자가 제출한 실제 자료를 반영한다
* 7ec54c6 docs: README 를 줄인다 (207 → 98줄)
* f11e53b docs: 문서에서 팀 진행 대화를 걷어내고 과제 산출물 문서로 정리한다
* 5cf5347 docs: README 를 팀 저장소용으로 다시 쓴다
* 2e94ba9 feat: [2] LLM 연결을 붙인다 (박연수님 요청)
* 3bcfd9f fix: [1] 규격을 김준오님이 정한 것으로 맞춘다
* df666cd fix: [2] 규격을 박연수님이 정한 것으로 맞춘다
* 46ce036 docs: 팀원용 시작점 파일 4개
* 3cd852a docs: 협업자 초대는 팀원 전원으로
* 97d81b2 docs: 팀장님 저장소로 이관하는 절차
* a8c7c51 docs: 주제 확정(카페) 반영과 최종 보고서
* 98e9bcf feat: [5] 결과 저장 & 에러 처리 통합
```

---

## 원격

```
$ git remote -v
origin	https://github.com/linkcontent7-huisun/A2-1-team-step5.git (fetch)
origin	https://github.com/linkcontent7-huisun/A2-1-team-step5.git (push)
team	https://github.com/baksuekyoung/A2-1-cafe_brand.git (fetch)
team	https://github.com/baksuekyoung/A2-1-cafe_brand.git (push)
```

**`team` 이 제출 대상**입니다(팀장 저장소). `origin` 은 같은 내용의 개인 백업입니다.
