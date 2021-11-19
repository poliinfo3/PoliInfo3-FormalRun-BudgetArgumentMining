# PoliInfo3-FormalRun-BudgetArgumentMining

## 更新情報

- (2021/11/19) リポジトリの公開

## 背景

政治には、収入と支出を考慮し、お金の使い道を決める予算作成の役割があります。
国の予算は、内閣で予算案が作成され、その予算案をもとに国会で議論された後に成立します。
また、地方自治体の予算は、知事や市長により予算案が作成され、議会で審議された後に成立します。
しかし、予算は、どのような背景に基づいて予算案が作成され，どのような議論を経て成立しているのかを把握しづらいという問題があります。

## 目的

Budget Argument Mining では、公開されている予算書類を対象として、会議録に含まれる議論と結びつけることを目的としています。
具体的には、予算項目（金額、管轄省庁・部局名、説明）が与えられたときに、議会会議録に含まれる政治家の予算関連の発言（金額表現を含む発言）をみつけだし、以下の 7 つの議論ラベルを付与します．

<!-- 具体的には、予算項目（金額、管轄省庁・部局名、説明）が与えられたときに、議会会議録に含まれる政治家の予算関連の発言（金額表現を含む発言）をみつけだし、３つの議論ラベル[ -->
<!-- Claim（主張）」「Premise（根拠）」「その他」を付与します。 -->

- Premise : 過去・決定事項,
- Premise : 未来（現在以降）・見積
- Premise : その他（例示・訂正事項など）
- Claim : 意見・提案・質問
- Claim : その他
- 金額表現ではない
- その他

### 入力

- 予算項目（予算 ID,金額,管轄省庁・部局名,説明）
- 議会会議録（議会名、発言者、発言内容,金額表現,関連 ID,議論ラベル）

### 出力

- 議会会議録
  - 固有表現抽出器([GINZA 4.0](https://megagonlabs.github.io/ginza/))で付与した金額表現
  - 関連 ID に予算項目の予算 ID を付与する
  - 議論ラベル

### 評価

- 議論ラベル
  - 正解率 ＝ 正解議論ラベル ➗ 議論ラベル数
- 予算表への連結 (F 値)
  - 再現率 ＝ 出力に含まれる正解数 ➗ 正解の数
  - 適合率 ＝ 出力に含まれる正解数 ➗ 出力の数 (連結数)
- 総合評価（リーダーボードに記載される代表スコア）
  - `正しい議論ラベルが付与かつ正しい予算IDが含まれる`金額表現数 ➗ 議論ラベル数

## 配布ファイル

- 対象コード：国会と自治体コード
  - diet 国会
  - 012033 北海道 小樽市 ﾎｯｶｲﾄﾞｳ ｵﾀﾙｼ
  - 080004 茨城県 ｲﾊﾞﾗｷｹﾝ
  - 401307 福岡県 福岡市 ﾌｸｵｶｹﾝ ﾌｸｵｶｼ
- ファイル
  - `PoliInfo3_BAM-budget.json`
    - 予算項目（予算 ID,金額,管轄省庁・部局名,説明）
  - `PoliInfo3_BAM-minutes-training.json`
    - トレーニングデータ用の議会会議録（議会名、発言者、発言内容,金額表現,関連 ID,議論ラベル）
    - 金額表現（`moneyExpressions`)の総数は `1248` です
      - 地方議会（`local`）： `1083`
      - 国会（`diet`）： `165`
  - `PoliInfo3_BAM-minutes-test.json`
    - テストデータ用の議会会議録（議会名、発言者、発言内容,金額表現,関連 ID,議論ラベル）
    - 議論ラベル（`argumentClass`）と予算表への連結（`relatedID`）はマスクされています
    - 金額表現（`moneyExpressions`)の総数は `520` です
      - 地方議会（`local`）： `455`
      - 国会（`diet`）： `65`
  - `bam_random.py`
    - 本タスクのサンプル推論スクリプト
      - ランダムチョイスで議論ラベルや予算表連結を行います
    - 入出力のデータ定義や処理方法の参考にしてください
  - `poliinfo3_eval_bam.py`
    - 本タスクで用いる評価スクリプト

## 評価スクリプト

### 使い方
python 3.8にて動作確認をしています。

- `-g` オプションで正解データ（Gold Standard）を指定してください。
- `-f` オプションで入力データ（Your estimated data）を指定してください。
- 出力は標準出力にJSON文字列として表示されます。

トレーニングデータを正解データとして用いる場合は以下のような使い方になります。

```
python poliinfo3_eval_bam.py -g PoliInfo3_BAM-minutes-training.json -f your_estimated_data.json
```

### 評価結果について
結果はJSON形式です。整形されていないので、必要に応じて整形してください。
書式は以下の通りです。

- `score`: Leaderboardに掲載される代表スコア
- `micro_ave`: 地方議会（local）、国会（diet）、両方における各評価指標
  - `accuracy_ac_rid_完全一致`: `正しい議論ラベルが付与かつ正しい予算IDが含まれる`金額表現数 ➗ 議論ラベル数
  - `accuracy_ac_完全一致`: `正しい議論ラベルが付与された`金額表現数 ➗ 議論ラベル数
  - `accuracy_ac`: `正しい議論ラベルの種類(Premise, Claim or another else)` ➗ 議論ラベル数
  - `precision_ac_Premise`: Premiseに関する適合率
  - `recall_ac_Premise`: Premiseに関する再現率
  - `precision_ac_Claim`: Claimに関する適合率
  - `recall_ac_Claim`: Claimに関する再現率
  - `precision_relatedID`: relatedIDに関する適合率
  - `recall_relatedID`: relatedIDに関する再現率


## データ書式の詳細

予算項目・議会会議録それぞれの JSON の書式を説明します．
説明は Python のクラス定義を用います．
同様の定義は配布ファイルの`bam_random.py`にも含まれています．

### PoliInfo3_BAM-budget.json（予算項目）

JSON は，以下に定義されるクラス`BudgetObject`の形式です．

```python
import dataclasses

@dataclasses.dataclass(frozen=True)
class BudgetObject:
    """
    BAMタスクにおける予算リストの配布用フォーマット．
    地方議会と国会の両方を持つ．

    地方議会（local）は，キーが自治体コード（localGovernmentCode），値がその自治体の予算項目リストとなる辞書型である．
    国会（diet）は，予算項目リストである．
    """

    local: dict[str, list[BudgetItem]]
    diet: list[BudgetItem]

@dataclasses.dataclass(frozen=True)
class BudgetItem:
    """
    予算項目一つ分を保持する．

    budgetIdの命名規則は以下の通り．
    ID-[year]-[localGovernmentCode]-00-[index]
    例：ID-2020-401307-00-000001
    """

    budgetId: str
    budgetTitle: str
    url: Optional[str]
    budgetItem: str
    budget: str
    categories: list[str]
    typesOfAccount: Optional[str]
    department: str
    budgetLastYear: Optional[str]
    description: str
    budgetDifference: Optional[str]
```

### PoliInfo3_BAM-minutes-{traning,test}.json（議会会議録）

JSON は，以下に定義されるクラス`MinutesObject`の形式です．

```python
import dataclasses

@dataclasses.dataclass(frozen=True)
class MinutesObject:
    """
    BAMタスクにおける会議録データのフォーマット．
    地方議会と国会の両方を持つ．
    """

    local: list[LProceedingObject]
    diet: list[DProceedingObject]

@dataclasses.dataclass(frozen=True)
class LProceedingObject:
    """
    地方議会会議録の一つ分の会議を保持する．
    一つ分の会議は発言オブジェクトのリストを持つ．
    """

    date: str
    localGovernmentCode: str
    localGovernmentName: str
    proceedingTitle: str
    url: str
    proceeding: list[LProceedingItem]

@dataclasses.dataclass(frozen=True)
class LProceedingItem:
    """
    地方議会会議録の一つ分の発言を保持する．
    発言には複数の金額表現が含まれる場合がある．
    """

    speakerPosition: str
    speaker: str
    utterance: str
    moneyExpressions: list[MoneyExpression]

@dataclasses.dataclass(frozen=True)
class DProceedingObject:
    """
    国会会議録の一つ分の会議を保持する．
    一つ分の会議は発言オブジェクトのリストを持つ．
    """

    issueID: str
    imageKind: str
    searchObject: int
    session: int
    nameOfHouse: str
    nameOfMeeting: str
    issue: str
    date: str
    closing: Optional[str]
    speechRecord: list[DSpeechRecord]
    meetingURL: str
    pdfURL: str

@dataclasses.dataclass(frozen=True)
class DSpeechRecord:
    """
    国会会議録の一つ分の発言を保持する．
    発言には複数の金額表現が含まれる場合がある．
    """

    speechID: str
    speechOrder: int
    speaker: str
    speakerYomi: Optional[str]
    speakerGroup: Optional[str]
    speakerPosition: Optional[str]
    speakerRole: Optional[str]
    speech: str
    startPage: int
    createTime: str
    updateTime: str
    speechURL: str
    moneyExpressions: list[MoneyExpression]

@dataclasses.dataclass
class MoneyExpression:
    """
    金額表現，関連する予算のID，議論ラベルを保持する．
    """

    moneyExpression: str
    relatedID: Optional[list[str]]
    argumentClass: Optional[str]
```

 <!-- - 対象コード：国会と自治体コード
    - diet	国会 
    - 012033	北海道	小樽市	ﾎｯｶｲﾄﾞｳ	ｵﾀﾙｼ 
    - 080004	茨城県		ｲﾊﾞﾗｷｹﾝ	
    - 401307	福岡県	福岡市	ﾌｸｵｶｹﾝ	ﾌｸｵｶｼ

 - ファイル名の付け方について
   - [自治体コード]-[自治体名]-[minutes or budget]-[西暦年]-[識別番号]-[training, test or testGoldStandard].json
   - ファイル名で、Dry Run と Formal Run の区別をしない
   - training、test、testGoldStandard について  
     - training[A-C] : 同じ年の定例会の3〜4日目以外（1〜2日目、5〜7日目）を訓練データとする。注釈者の違いをA〜Cで表す。
     - test : 同じ年の定例会の3〜4日目を評価データとする。
     - testGoldStandard[A-C] : 同じ年の定例会の3〜4日目を評価データとする。


 - 小樽市のファイル名
    - 会議録
      - PoliInfo3_BAM_012033-otaru-minutes-2019-01-trainingA.json # 2019年 定例会第1回 注釈者Aが注釈付したデータ
      - PoliInfo3_BAM_012033-otaru-minutes-2019-01-trainingB.json 
      - PoliInfo3_BAM_012033-otaru-minutes-2019-01-trainingC.json 
      - PoliInfo3_BAM_012033-otaru-minutes-2019-01-test.json # 2019年 定例会第1回 ３〜４日のみのデータ 
      - PoliInfo3_BAM_012033-otaru-minutes-2019-01-testGoldStandardA.json # 注釈者Aが注釈付したGoldStandard 
      - PoliInfo3_BAM_012033-otaru-minutes-2019-01-testGoldStandardB.json
      - PoliInfo3_BAM_012033-otaru-minutes-2019-01-testGoldStandardC.json
    - 予算  
      - PoliInfo3_BAM_012033-otaru-budget-2019-01.json  
      - PoliInfo3_BAM_012033-otaru-budget-2020-01.json 
 - 福岡市のファイル名
    - 会議録
      - PoliInfo3_BAM_401307-fukuoka-minutes-2019-01-trainingA.json 
      - PoliInfo3_BAM_401307-fukuoka-minutes-2019-01-test.json 
      - PoliInfo3_BAM_401307-fukuoka-minutes-2019-01-testGoldStandardA.json 
      - PoliInfo3_BAM_401307-fukuoka-minutes-2020-01-trainingA.json 
      - PoliInfo3_BAM_401307-fukuoka-minutes-2020-01-test.json
      - PoliInfo3_BAM_401307-fukuoka-minutes-2020-01-testGoldStandardA.json
    - 予算  
      - PoliInfo3_BAM_401307-fukuoka-budget-2019-01.json  
      - PoliInfo3_BAM_401307-fukuoka-budget-2020-01.json 
 - 茨城県のファイル名  
    - 会議録  
      - PoliInfo3_BAM_080004-ibaraki-minutes-2019-01-trainingA.json
      - PoliInfo3_BAM_080004-ibaraki-minutes-2019-01-trainingB.json
      - PoliInfo3_BAM_080004-ibaraki-minutes-2019-01-test.json
      - PoliInfo3_BAM_080004-ibaraki-minutes-2019-01-testGoldStandardA.json
      - PoliInfo3_BAM_080004-ibaraki-minutes-2019-01-testGoldStandardB.json
      - PoliInfo3_BAM_080004-ibaraki-minutes-2020-01-trainingA.json
      - PoliInfo3_BAM_080004-ibaraki-minutes-2020-01-trainingB.json
      - PoliInfo3_BAM_080004-ibaraki-minutes-2020-01-test.json
      - PoliInfo3_BAM_080004-ibaraki-minutes-2020-01-testGoldStandardA.json
      - PoliInfo3_BAM_080004-ibaraki-minutes-2020-01-testGoldStandardB.json
    - 予算  
      - PoliInfo3_BAM_080004-ibaraki-budget-2019-01.json
      - PoliInfo3_BAM_080004-ibaraki-budget-2020-01.json -->
