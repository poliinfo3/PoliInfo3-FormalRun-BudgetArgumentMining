from __future__ import annotations

"""
Budget Argument Miningタスクの推論スクリプトサンプル．
ランダムにargumentClassとrelatedIDを設定する．

使い方：
    [-m]オプションで会議録データを指定
    [-b]オプションで予算項目リストデータを指定
    [-o]オプションで出力ファイル名を指定

出力：
    標準出力に推論結果が含まれた会議録データがJSON形式で出力される．

更新：2021/08/18 出力をファイルにして文字コードをUTF-8に設定
作成：2021/07/27 乙武北斗
"""

import argparse
import dataclasses
import json
import random
from pathlib import Path
from typing import Optional

# --------------- データ定義ここから ---------------
ARGUMENT_CLASSES = [
    "Premise : 過去・決定事項",
    "Premise : 未来（現在以降）・見積",
    "Premise : その他（例示・訂正事項など）",
    "Claim : 意見・提案・質問",
    "Claim : その他",
    "金額表現ではない",
    "その他",
]


@dataclasses.dataclass
class MoneyExpression:
    """
    金額表現，関連する予算のID，議論ラベルを保持する．
    """

    moneyExpression: str
    relatedID: Optional[list[str]]
    argumentClass: Optional[str]


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

    @staticmethod
    def from_dict(d: dict[str, any]):
        return LProceedingItem(
            speakerPosition=d["speakerPosition"],
            speaker=d["speaker"],
            utterance=d["utterance"],
            moneyExpressions=[MoneyExpression(**m)
                              for m in d["moneyExpressions"]],
        )


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

    @staticmethod
    def from_dict(d: dict[str, any]):
        return LProceedingObject(
            date=d["date"],
            localGovernmentCode=d["localGovernmentCode"],
            localGovernmentName=d["localGovernmentName"],
            proceedingTitle=d["proceedingTitle"],
            url=d["url"],
            proceeding=[LProceedingItem.from_dict(x) for x in d["proceeding"]],
        )


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

    @staticmethod
    def from_dict(d: dict[str, any]):
        return DSpeechRecord(
            speechID=d["speechID"],
            speechOrder=d["speechOrder"],
            speaker=d["speaker"],
            speakerYomi=d["speakerYomi"],
            speakerGroup=d["speakerGroup"],
            speakerPosition=d["speakerPosition"],
            speakerRole=d["speakerRole"],
            speech=d["speech"],
            startPage=d["startPage"],
            createTime=d["createTime"],
            updateTime=d["updateTime"],
            speechURL=d["speechURL"],
            moneyExpressions=[MoneyExpression(**m)
                              for m in d["moneyExpressions"]],
        )


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

    @staticmethod
    def from_dict(d: dict[str, any]):
        return DProceedingObject(
            issueID=d["issueID"],
            imageKind=d["imageKind"],
            searchObject=d["searchObject"],
            session=d["session"],
            nameOfHouse=d["nameOfHouse"],
            nameOfMeeting=d["nameOfMeeting"],
            issue=d["issue"],
            date=d["date"],
            closing=d["closing"],
            speechRecord=[DSpeechRecord.from_dict(
                x) for x in d["speechRecord"]],
            meetingURL=d["meetingURL"],
            pdfURL=d["pdfURL"],
        )


@dataclasses.dataclass(frozen=True)
class MinutesObject:
    """
    BAMタスクにおける会議録データのフォーマット．
    地方議会と国会の両方を持つ．
    """

    local: list[LProceedingObject]
    diet: list[DProceedingObject]

    @staticmethod
    def from_dict(d: dict[str, any]):
        return MinutesObject(
            local=[LProceedingObject.from_dict(x) for x in d["local"]],
            diet=[DProceedingObject.from_dict(x) for x in d["diet"]],
        )


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

    @staticmethod
    def from_dict(d: dict[str, any]):
        return BudgetObject(
            local={k: [BudgetItem(**x) for x in v]
                   for k, v in d["local"].items()},
            diet=[BudgetItem(**x) for x in d["diet"]],
        )


# --------------- データ定義ここまで ---------------


def get_args():
    """
    コマンドライン引数を処理する関数．
    [-m]オプションで会議録データを指定し，
    [-b]オプションで予算項目リストデータを指定する．
    """
    parser = argparse.ArgumentParser(
        description="""Budget Argument Miningタスクの推論スクリプトサンプル．
ランダムにargumentClassとrelatedIDを設定する．"""
    )

    parser.add_argument("-m", "--minute", required=True, help="会議録データを指定します")
    parser.add_argument("-b", "--budget", required=True,
                        help="予算項目リストデータを指定します")
    parser.add_argument("-o", "--output", required=True, help="出力先ファイル名を指定します")
    return parser.parse_args()


def load_minute(minute_path: str) -> MinutesObject:
    """
    指定したパスから会議録データを読み込み，MinutesObjectインスタンスとして返す．
    """
    p = Path(minute_path)
    return MinutesObject.from_dict(json.loads(p.read_text(encoding="utf-8")))


def load_budget(budget_path: str) -> BudgetObject:
    """
    指定したパスから予算項目データを読み込み，BudgetObjectインスタンスとして返す．
    """
    p = Path(budget_path)
    return BudgetObject.from_dict(json.loads(p.read_text(encoding="utf-8")))


def estimate_local(minutesObj: MinutesObject, budgetObj: BudgetObject):
    """
    地方議会を対象としたargumentClassとrelatedIDの推論を行う．
    （ランダム）
    """
    # 地方議会会議録の各会議で繰り返し処理
    for proc_obj in minutesObj.local:
        # その自治体の予算項目リストを取得
        budgets = budgetObj.local[proc_obj.localGovernmentCode]

        # 会議の年
        year = proc_obj.date.split("-")[0]

        # 会議の年と対応する予算項目リストを抽出
        budgets_filtered = [
            x for x in budgets if x.budgetId.split("-")[1] == year]

        # 各発言の繰り返し処理
        for proc in proc_obj.proceeding:
            # 各金額表現の繰り返し処理
            for mex in proc.moneyExpressions:
                # ランダムにargumentClassを設定する
                mex.argumentClass = random.choice(ARGUMENT_CLASSES)

                # ランダムにrelatedIDを設定する
                # relatedIDは付与されないことが多いので，それを考慮したランダム
                random_idx = random.randint(0, len(budgets_filtered) * 3)
                if random_idx < len(budgets_filtered):
                    mex.relatedID = [budgets_filtered[random_idx].budgetId]


def estimate_diet(minutesObj: MinutesObject, budgetObj: BudgetObject):
    """
    国会を対象としたargumentClassとrelatedIDの推論を行う．
    （ランダム）
    """
    # 地方議会会議録の各会議で繰り返し処理
    for proc_obj in minutesObj.diet:
        # 予算項目リストを取得
        budgets = budgetObj.diet

        # 各発言の繰り返し処理
        for sp in proc_obj.speechRecord:
            # 各金額表現の繰り返し処理
            for mex in sp.moneyExpressions:
                # ランダムにargumentClassを設定する
                mex.argumentClass = random.choice(ARGUMENT_CLASSES)

                # ランダムにrelatedIDを設定する
                # relatedIDは付与されないことが多いので，それを考慮したランダム
                random_idx = random.randint(0, len(budgets) * 3)
                if random_idx < len(budgets):
                    mex.relatedID = [budgets[random_idx].budgetId]


# --------------- main ---------------
if __name__ == "__main__":
    # コマンドライン引数の解析
    args = get_args()

    # 会議録の読み込み
    minutesObj = load_minute(args.minute)

    # 予算項目リストの読み込み
    budgetObj = load_budget(args.budget)

    # 地方議会会議録の金額表現に対して推論
    estimate_local(minutesObj, budgetObj)

    # 国会会議録の金額表現に対して推論
    estimate_diet(minutesObj, budgetObj)

    # 結果を出力
    with open(args.output, mode="wt", encoding="utf-8") as fout:
        print(json.dumps(dataclasses.asdict(minutesObj),
                         ensure_ascii=False, indent=4), file=fout)
